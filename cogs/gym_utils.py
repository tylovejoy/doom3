from __future__ import annotations

import math
import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs
import utils
import views

if typing.TYPE_CHECKING:
    from core import DoomCtx, DoomItx


Units = typing.Literal["kg", "lb"]


TARGETS = typing.Literal[
    "abductors",
    "abs",
    "adductors",
    "biceps",
    "calves",
    "cardiovascular system",
    "delts",
    "forearms",
    "glutes",
    "hamstrings",
    "lats",
    "levator scapulae",
    "pectorals",
    "quads",
    "serratus anterior",
    "spine",
    "traps",
    "triceps",
    "upper back",
]

BODY_PARTS = typing.Literal[
    "back",
    "cardio",
    "chest",
    "lower arms",
    "lower legs",
    "neck",
    "shoulders",
    "upper arms",
    "upper legs",
    "waist",
]

EQUIPMENT = typing.Literal[
    "assisted",
    "band",
    "barbell",
    "body weight",
    "bosu ball",
    "cable",
    "dumbbell",
    "elliptical machine",
    "ez barbell",
    "kettlebell",
    "leverage machine",
    "medicine ball",
    "resistance band",
    "skierg machine",
    "sled machine",
    "smith machine",
    "stability ball",
    "stationary bike",
    "stepmill machine",
    "trap bar",
    "upper body ergometer",
    "weighted",
    "wheel roller",
]


class GymUtils(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    async def cog_check(self, ctx: DoomCtx) -> bool:
        return ctx.message.channel.id == 999000079283273911

    @staticmethod
    def _convert_lb_to_kg(value: float) -> float:
        return round(round(value, 2) / 2.2, 2)

    @staticmethod
    def _convert_kg_to_lb(value: float) -> float:
        return round(2.2 * round(value, 2), 2)

    @commands.command()
    async def convert(self, ctx: DoomCtx, value: float, unit: str = None):
        kg = self._convert_lb_to_kg(value)
        lb = self._convert_kg_to_lb(value)
        if not unit:
            output = f"{value} lb ≈ {kg} kg\n{value} kg ≈ {lb} lb"
        elif unit.lower() in {"lb", "lbs", "pounds", "pound"}:
            output = f"{value} lb ≈ {kg} kg\n"
        elif unit.lower() in {
            "kg",
            "kgs",
            "kilogram",
            "kilograms",
            "kilogramme",
            "kilogrammes",
        }:
            output = f"{value} kg ≈ {lb} lb"
        else:
            output = (
                "Invalid unit, use one of the following:\n"
                "`lb, lbs, pounds, pound, kg, kgs, "
                "kilogram, kilograms, kilogramme, kilogrammes` "
            )
        await ctx.send(output)

    @commands.command()
    @commands.is_owner()
    async def add_exercise(self, ctx: DoomCtx, *, name: str):
        await ctx.bot.database.set(
            "INSERT INTO all_exercises (name) VALUES ($1)",
            name,
        )
        ctx.bot.exercise_names.append(app_commands.Choice(name=name, value=name))
        await ctx.send(f"Added {name} to exercise list.")

    # @app_commands.check(lambda x: x.channel_id == 999000079283273911)
    @app_commands.command(name="add-pr")
    @app_commands.autocomplete(exercise=cogs.exercise_name_autocomplete)
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def add_gym_pr(
        self,
        itx: DoomItx,
        exercise: str,
        weight: float,
        unit: Units,
    ) -> None:
        """
        Add your gym PR per exercise

        Args:
            itx: Interaction
            exercise: The exercise to add a PR for
            weight: Amount of weight
            unit: Units of weight

        """
        await itx.response.defer(ephemeral=False)
        if exercise not in [x.name for x in itx.client.exercise_names]:
            return
        if unit == "lb":
            kg = self._convert_lb_to_kg(weight)
            lb = weight
        else:
            kg = weight
            lb = self._convert_kg_to_lb(weight)
        await itx.client.database.set(
            "INSERT INTO gym_prs(user_id, exercise, weight) "
            "VALUES ($1, $2, $3) "
            "ON CONFLICT (user_id, exercise)"
            "DO UPDATE SET weight=$3;",
            itx.user.id,
            exercise,
            kg,
        )
        await itx.edit_original_response(
            content=f"{itx.user.mention} your {exercise} PR is set to {kg} kg / {lb} lb. <:_:1029045690829115402>"
        )

    @app_commands.command(name="show-pr")
    # @app_commands.autocomplete(exercise=cogs.exercise_name_autocomplete)
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def show_prs(
        self,
        itx: DoomItx,
        exercise: app_commands.Transform[str, utils.ExerciseTransformer],
    ):
        """
        Show a leaderboard for submitted PRs per exercise

        Args:
            itx: Interaction
            exercise: The exercise leaderboard to view

        Returns:

        """
        await itx.response.defer(ephemeral=False)
        prs = sorted(
            [
                x
                async for x in itx.client.database.get(
                    "SELECT * FROM gym_prs WHERE exercise=$1", exercise
                )
            ],
            key=lambda x: x.weight,
            reverse=True,
        )
        leaderboard = f"{exercise} Leaderboard\n"
        for i, x in enumerate(prs):
            lb = self._convert_kg_to_lb(float(x.weight))
            user_data = itx.client.all_users.get(x.user_id, {})
            name = user_data.get("nickname", "Unknown User")

            leaderboard += f"{i + 1}. {name} - {x.weight} kg / {lb} lb\n"

        await itx.edit_original_response(content=leaderboard)

    @app_commands.command(name="one-rep-max")
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def one_rep_max(
        self,
        interaction: DoomItx,
        weight: float,
        unit: Units,
        reps: int,
        formula: typing.Literal[
            "Brzycki", "Epley", "Lander", "Lombardi", "Mayhew", "O'Conner", "Wathen"
        ]
        | None = "Brzycki",
    ):
        """
        Calculate your one rep maximum weight

        Args:
            interaction: Interaction
            weight: The weight used in your exercise
            unit: Unit of the weight used
            reps: The number of reps used in your exercise
            formula: 1RM formula to use. Default: Brzycki

        Returns:

        """
        if unit == "lb":
            kg = self._convert_lb_to_kg(weight)
            lb = weight
        else:
            kg = weight
            lb = self._convert_kg_to_lb(weight)
        max_kg = round(
            {
                "Brzycki": self.brzycki_1rm,
                "Epley": self.epley_1rm,
                "Lander": self.lander_1rm,
                "Lombardi": self.lombardi_1rm,
                "Mayhew": self.mayhew_1rm,
                "O'Conner": self.oconner_1rm,
                "Wathen": self.wathen_1rm,
            }[formula](kg, reps),
            2,
        )
        max_lb = self._convert_kg_to_lb(max_kg)

        await interaction.response.send_message(
            f"Using the {formula} formula:\n"
            f"Your 1RM based on {reps} reps of {kg} kg / {lb} lb should be "
            f"≈ {max_kg} kg / {max_lb} lb."
        )

    @staticmethod
    def brzycki_1rm(weight: float, reps: int) -> float:
        return weight * (36 / (37 - reps))

    @staticmethod
    def epley_1rm(weight: float, reps: int) -> float:
        return weight * (1 + reps / 30)

    @staticmethod
    def lander_1rm(weight: float, reps: int) -> float:
        return 100 * (weight / (101.3 - 2.67123 * reps))

    @staticmethod
    def lombardi_1rm(weight: float, reps: int) -> float:
        return (weight * reps) ** 0.1

    @staticmethod
    def mayhew_1rm(weight: float, reps: int) -> float:
        return (100 * weight) / (52.2 + 41.9 * math.e ** (-0.055 * reps))

    @staticmethod
    def oconner_1rm(weight: float, reps: int) -> float:
        return weight * (1 + reps / 40)

    @staticmethod
    def wathen_1rm(weight: float, reps: int) -> float:
        return (100 * weight) / (48.8 + 53.8 * math.e ** (-0.075 * reps))

    @app_commands.command(name="exercise-search")
    @app_commands.guilds(discord.Object(id=689587520496730129))
    @app_commands.autocomplete(exercise_name=cogs.exercise_name_search_autocomplete)
    async def exercise_search(
        self,
        itx: DoomItx,
        location: BODY_PARTS | None,
        equipment: EQUIPMENT | None,
        exercise_name: str | None,
    ):
        await itx.response.defer(ephemeral=True)
        if not location and not equipment and not exercise_name:
            # TODO: Random.
            return

        search = [
            x
            async for x in itx.client.database.get(
                """
                SELECT * FROM exercises 
                WHERE 
                    ($1 IS NULL OR location = $1) AND
                    ($2 IS NULL OR equipment = $2) AND
                    ($3 IS NULL OR name = $3)
                ORDER BY name;
                """,
                location,
                equipment,
                exercise_name,
            )
        ]

        if not search:
            raise utils.NoExercisesFound
        embed = utils.DoomEmbed(title="Exercises")
        view = views.ExerciseView(itx, search)
        await itx.edit_original_response(embed=embed, view=view)
        await view.start()


async def setup(bot: core.Doom):
    await bot.add_cog(GymUtils(bot))
