from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils

if typing.TYPE_CHECKING:
    import core


class Completions(commands.Cog):
    """Completions"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="submit-completion")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def submit_completion(
        self,
        interaction: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        # second: str
    ) -> None:
        await interaction.response.send_message(f"{map_code}")


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Completions(bot))
