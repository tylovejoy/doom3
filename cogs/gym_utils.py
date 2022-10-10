from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs

if typing.TYPE_CHECKING:
    import core


class GymUtils(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    async def cog_check(self, ctx: discord.Context[core.Doom]) -> bool:
        return ctx.message.channel.id == 999000079283273911

    @staticmethod
    def _convert_lb_to_kg(value: float) -> float:
        return round(0.45359237 * round(value, 2), 2)

    @staticmethod
    def _convert_kg_to_lb(value: float) -> float:
        return round(2.2 * round(value, 2), 2)

    @commands.command()
    async def convert(
        self, ctx: commands.Context[core.Doom], value: float, unit: str | None = None
    ):
        kg = self._convert_lb_to_kg(value)
        lb = self._convert_kg_to_lb(value)
        if not unit:
            await ctx.send(f"{value} lb ≈ {kg} kg\n{value} kg ≈ {lb} lb")
        elif unit.lower() in ["lb", "lbs"]:
            await ctx.send(f"{value} lb ≈ {kg} kg\n")
        elif unit.lower() in ["kg", "kgs"]:
            await ctx.send(f"{value} kg ≈ {lb} lb")

    @commands.command()
    @commands.is_owner()
    async def add_exercise(self, ctx: commands.Context[core.Doom], *, name: str):
        await ctx.bot.database.set(
            "INSERT INTO all_exercises (name) VALUES ($1)",
            name,
        )
        ctx.bot.exercise_names.append(app_commands.Choice(name=name, value=name))
        await ctx.send(f"Added {name} to exercise list.")

    @app_commands.command(name="add-pr")
    @app_commands.autocomplete(exercise=cogs.exercise_name_autocomplete)
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def add_gym_pr(
        self,
        interaction: core.Interaction[core.Doom],
        exercise: str,
        weight: float,
        unit: typing.Literal["kg", "lb"],
    ) -> None:
        await interaction.response.defer(ephemeral=False)
        if exercise not in [x.name for x in interaction.client.exercise_names]:
            return
        if unit == "lb":
            kg = self._convert_lb_to_kg(weight)
            lb = weight
        else:
            kg = weight
            lb = self._convert_kg_to_lb(weight)
        await interaction.client.database.set(
            "INSERT INTO gym_prs(user_id, exercise, weight) "
            "VALUES ($1, $2, $3) "
            "ON CONFLICT (user_id, exercise)"
            "DO UPDATE SET weight=$3;",
            interaction.user.id,
            exercise,
            kg,
        )
        await interaction.edit_original_response(
            content=f"{interaction.user.mention} your {exercise} PR is set to {kg} kg / {lb} lb. <:_:1029045690829115402>"
        )

    @app_commands.command(name="show-pr")
    @app_commands.autocomplete(exercise=cogs.exercise_name_autocomplete)
    @app_commands.guilds(discord.Object(id=689587520496730129))
    async def show_prs(self, interaction: core.Interaction[core.Doom], exercise: str):
        await interaction.response.defer(ephemeral=False)
        prs = sorted(
            [
                x
                async for x in interaction.client.database.get(
                    "SELECT * FROM gym_prs WHERE exercise=$1", exercise
                )
            ],
            key=lambda x: x.weight,
            reverse=True,
        )
        leaderboard = f"{exercise} Leaderboard\n"
        for i, x in enumerate(prs):
            lb = self._convert_kg_to_lb(float(x.weight))
            leaderboard += f"{i + 1}. {interaction.client.get_user(x.user_id).name} - {x.weight} kg / {lb} lb\n"

        await interaction.edit_original_response(content=leaderboard)


async def setup(bot: core.Doom):
    await bot.add_cog(GymUtils(bot))
