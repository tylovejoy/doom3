from __future__ import annotations

import typing

from discord import app_commands
from discord.ext import commands, tasks

if typing.TYPE_CHECKING:
    import core


class Tasks(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot
        # TODO:
        # self.cache_map_codes.start()
        # self.cache_map_names.start()
        # self.cache_map_types.start()
        self.cache_exercise_names.start()

    @tasks.loop(minutes=5)
    async def cache_map_codes(self):
        self.bot.logger.debug("Caching map codes...")
        self.bot.map_codes = [
            app_commands.Choice(name=x.map_code, value=x.map_code)
            async for x in self.bot.database.get(
                "SELECT map_code FROM maps ORDER BY 1;",
            )
        ]
        self.bot.logger.debug("Map codes cached.")

    @tasks.loop(hours=24)
    async def cache_map_names(self):
        self.bot.logger.debug("Caching map names...")
        self.bot.map_names = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_map_names ORDER BY 1;",
            )
        ]
        self.bot.logger.debug("Map names cached.")

    @tasks.loop(hours=24)
    async def cache_map_types(self):
        self.bot.logger.debug("Caching map types...")
        self.bot.map_types = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_map_types ORDER BY 1;",
            )
        ]
        self.bot.logger.debug("Map types cached.")

    @tasks.loop(hours=24)
    async def cache_exercise_names(self):
        self.bot.exercise_names = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_exercises ORDER BY 1;"
            )
        ]


async def setup(bot: core.Doom):
    await bot.add_cog(Tasks(bot))
