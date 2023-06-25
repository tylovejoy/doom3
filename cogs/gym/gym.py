from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

import cogs
import database
import utils
from cogs.gym.utils import Units, OneRepMax, DuplicateExercise, ExerciseDoesntExist, BODY_PARTS, EQUIPMENT, \
    ExerciseTransformer
from cogs.gym.views import ExerciseView

if TYPE_CHECKING:
    from core import Doom, DoomItx, DoomCtx


class Gym(commands.Cog):
    def __init__(self, bot: Doom):
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
        elif unit.lower() in ["lb", "lbs", "pounds", "pound"]:
            output = f"{value} lb ≈ {kg} kg\n"
        elif unit.lower() in [
            "kg",
            "kgs",
            "kilogram",
            "kilograms",
            "kilogramme",
            "kilogrammes",
        ]:
            output = f"{value} kg ≈ {lb} lb"
        else:
            output = (
                "Invalid unit, use one of the following:\n"
                "`lb, lbs, pounds, pound, kg, kgs, "
                "kilogram, kilograms, kilogramme, kilogrammes` "
            )
        await ctx.send(output)

    @app_commands.command(name="one-rep-max")
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def one_rep_max(
        self,
        interaction: DoomItx,
        weight: float,
        unit: Units,
        reps: int,

    ):
        """
        Calculate your one rep maximum weight

        Args:
            interaction: Interaction
            weight: The weight used in your exercise
            unit: Unit of the weight used
            reps: The number of reps used in your exercise

        Returns:

        """
        if unit == "lb":
            kg = self._convert_lb_to_kg(weight)
            lb = weight
        else:
            kg = weight
            lb = self._convert_kg_to_lb(weight)

        res = f"### Your 1RM based on {reps} reps of {kg} kg / {lb} lb should be\n"
        for formula, method in OneRepMax.formulas().items():
            max_kg = round(method(kg, reps), 2)
            max_lb = self._convert_kg_to_lb(max_kg)
            res += (
                f"- {formula} formula:\n"
                f"  - ≈ {max_kg} kg / {max_lb} lb.\n"
            )
        await interaction.response.send_message(res)

    @app_commands.command(name="add-pr")
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def add_gym_pr(
        self,
        itx: DoomItx,
        exercise: app_commands.Transform[str, ExerciseTransformer],
        value: float,
        unit: Units | None,
    ) -> None:
        """
        Add your gym PR per exercise

        Args:
            itx: Interaction
            exercise: The exercise to add a PR for
            value: Weight, or Reps, or Time (in seconds)
            unit: Units of weight (if applicable)

        """
        await itx.response.defer(ephemeral=False)
        if exercise not in itx.client.exercise_category_map:
            raise ExerciseDoesntExist
        category = itx.client.exercise_category_map[exercise]
        if category == "Max":
            content = await self._one_rep_max_pr_submit(exercise, itx, unit, value)
        elif category == "Reps":
            content = await self._reps_pr_submit(exercise, itx, value)
        elif category == "Time":
            content = await self._time_pr_submit(exercise, itx, value)
        else:
            raise ExerciseDoesntExist
        await itx.edit_original_response(content=content)

    async def _one_rep_max_pr_submit(self, exercise: str, itx: DoomItx, unit: str, weight: float) -> str:
        if unit == "lb":
            kg = self._convert_lb_to_kg(weight)
            lb = weight
        else:
            kg = weight
            lb = self._convert_kg_to_lb(weight)
        async with database.Acquire(pool=itx.client.pool) as con:
            query = """
                INSERT INTO gym_records(user_id, exercise, value)
                VALUES ($1, $2, $3) 
                ON CONFLICT (user_id, exercise)
                DO UPDATE SET value=$3;
            """
            await con.execute(
                query,
                itx.user.id,
                exercise,
                kg,
            )
        return f"{itx.user.mention} your {exercise} PR is set to {kg} kg / {lb} lb. <:_:1029045690829115402>"

    @staticmethod
    async def _reps_pr_submit(exercise: str, itx: DoomItx, value: float):
        async with database.Acquire(pool=itx.client.pool) as con:
            query = """
                INSERT INTO gym_records(user_id, exercise, value)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, exercise)
                DO UPDATE SET value=$3;
            """
            await con.execute(
                query,
                itx.user.id,
                exercise,
                int(value),
            )

        return f"{itx.user.mention} your {exercise} PR is set to {int(value)} reps. <:_:1029045690829115402>"

    @staticmethod
    async def _time_pr_submit(exercise: str, itx: DoomItx, value: float):
        async with database.Acquire(pool=itx.client.pool) as con:
            query = """
                INSERT INTO gym_records(user_id, exercise, value) 
                VALUES ($1, $2, $3) 
                ON CONFLICT (user_id, exercise)
                DO UPDATE SET value=$3;
            """
            await con.execute(
                query,
                itx.user.id,
                exercise,
                value,
            )
        return f"{itx.user.mention} your {exercise} PR is set to {value} seconds. <:_:1029045690829115402>"

    @app_commands.command()
    @commands.is_owner()
    async def add_exercise(self, itx: DoomItx, name: str, category: Literal["Max", "Reps", "Time"]):
        if name in itx.client.exercise_category_map:
            raise DuplicateExercise
        await itx.response.send_message(f"Added {name} to exercise list.")
        await itx.client.database.set(
            "INSERT INTO all_exercises (name, type) VALUES ($1, $2)",
            name,
            category,
        )
        itx.client.exercise_names.append(app_commands.Choice(name=name, value=name))
        itx.client.exercise_category_map[name] = category

    @app_commands.command(name="show-pr")
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def show_prs(
        self,
        itx: DoomItx,
        exercise: app_commands.Transform[str, ExerciseTransformer],
    ):
        """
        Show a leaderboard for submitted PRs per exercise

        Args:
            itx: Interaction
            exercise: The exercise leaderboard to view

        Returns:

        """
        await itx.response.defer(ephemeral=False)
        async with database.Acquire(pool=itx.client.pool) as con:
            query = """
                SELECT * FROM gym_records WHERE exercise = $1 ORDER BY value DESC;
            """
            prs = await con.fetch(query, exercise)

        category = itx.client.exercise_category_map[exercise]
        leaderboard = f"# {exercise} Leaderboard\n"
        for position, record in enumerate(prs, start=1):
            user_data = itx.client.all_users.get(record['user_id'], {})
            name = user_data.get("nickname", "Unknown User")
            if category == "Max":
                lb = self._convert_kg_to_lb(float(record['value']))
                leaderboard += f"{position}. {name} - {record['value']} kg / {lb} lb\n"
            elif category == "Reps":
                leaderboard += f"{position}. {name} - {int(record['value'])} reps\n"
            elif category == "Time":
                leaderboard += f"{position}. {name} - {record['value']} seconds\n"
            else:
                raise ExerciseDoesntExist

        await itx.edit_original_response(content=leaderboard)

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
                    ($1::text IS NULL OR location = $1::text) AND
                    ($2::text IS NULL OR equipment = $2::text) AND
                    ($3::text IS NULL OR name = $3::text)
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
        view = ExerciseView(itx, search)
        await itx.edit_original_response(embed=embed, view=view)
        await view.start()
