from __future__ import annotations

import typing

from discord import app_commands
from discord.ext import commands, tasks

import utils.utils

if typing.TYPE_CHECKING:
    import core


class Tasks(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot
        self.cache_all_users.start()
        self.cache_map_code_choices.start()
        self.cache_map_names.start()
        self.cache_map_types.start()
        self.cache_map_data.start()
        self.cache_exercise_names.start()
        self.cache_exercise_names_search.start()
        self.cache_tags.start()
        self.cache_keep_alives.start()
        self.cache_auto_join.start()

    @commands.command()
    @commands.is_owner()
    async def refresh_cache(
        self,
        ctx: commands.Context[core.Doom],
    ):
        self.cache_all_users.restart()
        self.cache_map_code_choices.restart()
        self.cache_map_names.restart()
        self.cache_map_types.restart()
        self.cache_map_data.restart()
        self.cache_exercise_names.restart()
        self.cache_exercise_names_search.restart()
        self.cache_tags.restart()
        self.cache_keep_alives.restart()
        self.cache_auto_join.restart()
        await ctx.message.delete()

    @tasks.loop(hours=24, count=1)
    async def cache_map_code_choices(self):
        self.bot.logger.debug("Caching map codes...")
        self.bot.map_codes_choices = [
            app_commands.Choice(name=x.map_code, value=x.map_code)
            async for x in self.bot.database.get(
                "SELECT map_code FROM maps ORDER BY 1;",
            )
        ]

        self.bot.logger.debug("Map codes cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_map_names(self):
        self.bot.logger.debug("Caching map names...")
        self.bot.map_names_choices = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_map_names ORDER BY 1;",
            )
        ]
        self.bot.map_names = [x.name for x in self.bot.map_names_choices]
        self.bot.logger.debug("Map names cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_map_types(self):
        self.bot.logger.debug("Caching map types...")
        self.bot.map_types_choices = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_map_types ORDER BY 1;",
            )
        ]
        self.bot.map_types = [x.name for x in self.bot.map_types_choices]
        self.bot.logger.debug("Map types cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_exercise_names(self):
        self.bot.exercise_names = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_exercises ORDER BY 1;"
            )
        ]

    @tasks.loop(hours=24, count=1)
    async def cache_exercise_names_search(self):
        self.bot.exercise_names_search = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get("SELECT * FROM exercises ORDER BY 1;")
        ]

    @tasks.loop(hours=24, count=1)
    async def cache_map_data(self):
        async for x in self.bot.database.get(
            """
            SELECT DISTINCT array_agg(DISTINCT level) as levels,
                            m.map_code,
                            array_agg(distinct user_id) as user_ids
            FROM maps m
                     LEFT JOIN map_levels ml ON m.map_code = ml.map_code
                     LEFT JOIN map_creators mc ON m.map_code = mc.map_code
            GROUP BY m.map_code
            ORDER BY levels;
            """
        ):
            self.bot.map_cache[x.map_code] = utils.utils.MapCacheData(
                levels=[y for y in x.levels],
                user_ids=[y for y in x.user_ids],
                choices=[app_commands.Choice(name=y, value=y) for y in x.levels],
            )

    @tasks.loop(hours=24, count=1)
    async def cache_all_users(self):
        self.bot.users_choices = []
        async for x in self.bot.database.get("SELECT * FROM users"):
            self.bot.all_users[x.user_id] = utils.utils.UserCacheData(
                nickname=x.nickname, alertable=x.alertable
            )
            self.bot.users_choices.append(
                app_commands.Choice(name=x.nickname, value=str(x.user_id))
            )

    @tasks.loop(hours=24, count=1)
    async def cache_tags(self):
        self.bot.tag_cache = []
        self.bot.tag_choices = []
        async for x in self.bot.database.get("SELECT * FROM tags;"):
            self.bot.tag_cache.append(x.name)
            self.bot.tag_choices.append(app_commands.Choice(name=x.name, value=x.name))

    @tasks.loop(hours=24, count=1)
    async def cache_keep_alives(self):
        self.bot.keep_alives = []
        async for x in self.bot.database.get("SELECT * FROM keep_alives;"):
            self.bot.keep_alives.append(x.thread_id)

    @tasks.loop(hours=24, count=1)
    async def cache_auto_join(self):
        self.bot.auto_join_threads = []
        async for x in self.bot.database.get("SELECT * FROM auto_join_thread;"):
            self.bot.auto_join_threads.append((x.channel_id, x.thread_id))


async def setup(bot: core.Doom):
    await bot.add_cog(Tasks(bot))
