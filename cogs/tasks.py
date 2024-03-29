from __future__ import annotations

import typing
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands, tasks

import utils.utils
from cogs.tournament.utils import CategoryData
from cogs.tournament.utils.data import TournamentData

if typing.TYPE_CHECKING:
    import core
    from core import DoomCtx

logger = getLogger(__name__)


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
        self.cache_insults.start()
        self.cache_tournament.start()

    @commands.command()
    @commands.is_owner()
    async def refresh_cache(
        self,
        ctx: DoomCtx,
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
        self.cache_insults.restart()
        await ctx.message.delete()

    @tasks.loop(hours=24, count=1)
    async def cache_tournament(self):
        logger.debug("Caching tournament...")
        tournament = await self.bot.database.get_one(
            """
                SELECT *
                FROM (SELECT title,
                             start,
                             "end",
                             active,
                             bracket,
                             roles,
                             id,
                             start > now()                as needs_start_task,
                             "end" > now()                as needs_end_task,
                             start < now() and "end" > now() and not active as needs_start_now,
                             "end" < now() and active     as needs_end_now
                      FROM tournament) t
                WHERE id = (SELECT max(id) FROM tournament)
            """
        )
        if not tournament:
            return
        maps = [
            x
            async for x in self.bot.database.get(
                "SELECT * FROM tournament_maps WHERE id = $1", tournament.id
            )
        ]
        map_data = {
            row.category: CategoryData(
                code=row.code, level=row.level, creator=row.creator
            )
            for row in maps
        }

        self.bot.current_tournament = TournamentData(
            client=self.bot,
            title=tournament.title,
            start=tournament.start,
            end=tournament.end,
            bracket=tournament.bracket,
            data=map_data,
            id_=tournament.id,
        )

        if tournament.needs_start_task:
            utils.start_tournament_task.change_interval(
                time=self.bot.current_tournament.start.time()
            )
            utils.start_tournament_task.start(self.bot.current_tournament)

        if tournament.needs_end_task:
            utils.end_tournament_task.change_interval(
                time=self.bot.current_tournament.end.time()
            )
            utils.end_tournament_task.start(self.bot.current_tournament)

        if tournament.needs_start_now:
            await utils.start_tournament(self.bot.current_tournament)

        if tournament.needs_end_now:
            await utils.end_tournament(self.bot.current_tournament)

        logger.debug("Tournament cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_map_code_choices(self):
        logger.debug("Caching map codes...")
        self.bot.map_codes_choices = [
            app_commands.Choice(name=x.map_code, value=x.map_code)
            async for x in self.bot.database.get(
                "SELECT map_code FROM maps ORDER BY 1;",
            )
        ]
        logger.debug("Map codes cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_map_names(self):
        logger.debug("Caching map names...")
        self.bot.map_names_choices = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_map_names ORDER BY 1;",
            )
        ]
        self.bot.map_names = [x.name for x in self.bot.map_names_choices]
        logger.debug("Map names cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_map_types(self):
        logger.debug("Caching map types...")
        self.bot.map_types_choices = [
            app_commands.Choice(name=x.name, value=x.name)
            async for x in self.bot.database.get(
                "SELECT * FROM all_map_types ORDER BY 1;",
            )
        ]
        self.bot.map_types = [x.name for x in self.bot.map_types_choices]
        logger.debug("Map types cached.")

    @tasks.loop(hours=24, count=1)
    async def cache_exercise_names(self):
        self.bot.exercise_names = []
        self.bot.exercise_category_map = {}
        async for x in self.bot.database.get(
            "SELECT name, type FROM all_exercises ORDER BY 1;"
        ):
            self.bot.exercise_names.append(app_commands.Choice(name=x.name, value=x.name))
            self.bot.exercise_category_map[x.name] = x.type

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

    @tasks.loop(hours=24, count=1)
    async def cache_insults(self):
        self.bot.insults = []
        async for x in self.bot.database.get("SELECT * FROM insults;"):
            self.bot.insults.append(x.value)


async def setup(bot: core.Doom):
    await bot.add_cog(Tasks(bot))
