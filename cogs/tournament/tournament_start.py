from __future__ import annotations

import datetime
import typing

import discord
from discord import EntityType, PrivacyLevel, app_commands
from discord.ext import commands, tasks

import utils
from cogs.tournament.utils import Category, CategoryData
from cogs.tournament.utils.data import TournamentData
from cogs.tournament.utils.end_tournament import ExperienceCalculator
from cogs.tournament.utils.transformers import (
    BOLevelTransformer,
    DateTransformer,
    HCLevelTransformer,
    MCLevelTransformer,
    TALevelTransformer,
)
from cogs.tournament.utils.utils import ANNOUNCEMENTS, parse, role_map
from utils import end_tournament_task, start_tournament_task

if typing.TYPE_CHECKING:
    import core


class Tournament(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def fake_end(self, ctx: core.DoomCtx):
        calculator = ExperienceCalculator(self.bot.current_tournament)
        print(await calculator.compute_xp())
        print(calculator.mission_totals)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def start(
        self,
        itx: core.DoomItx,
        start: app_commands.Transform[datetime.datetime, DateTransformer],
        end: app_commands.Transform[datetime.datetime, DateTransformer],
        ta_code: app_commands.Transform[str, utils.MapCodeAutoTransformer] | None,
        ta_level: app_commands.Transform[str, TALevelTransformer] | None,
        mc_code: app_commands.Transform[str, utils.MapCodeAutoTransformer] | None,
        mc_level: app_commands.Transform[str, MCLevelTransformer] | None,
        hc_code: app_commands.Transform[str, utils.MapCodeAutoTransformer] | None,
        hc_level: app_commands.Transform[str, HCLevelTransformer] | None,
        bo_code: app_commands.Transform[str, utils.MapCodeAutoTransformer] | None,
        bo_level: app_commands.Transform[str, BOLevelTransformer] | None,
    ):
        await itx.response.defer(ephemeral=True)
        ta = Category.TIME_ATTACK, CategoryData(code=ta_code, level=ta_level)
        mc = Category.MILDCORE, CategoryData(code=mc_code, level=mc_level)
        hc = Category.HARDCORE, CategoryData(code=hc_code, level=hc_level)
        bo = Category.BONUS, CategoryData(code=bo_code, level=bo_level)

        categories = [ta, mc, hc, bo]
        # TODO: TIME END NEEDS TO BE EXTENSTION FROM START!!!!!!!!
        data = self.clean_categories_input(categories)
        x = TournamentData(
            client=self.bot,
            title="Doomfist Parkour Tournament",
            start=start,
            end=end,
            data=data,
            bracket=False,
        )

        embed = x.start_embed()
        mentions = [
            self.bot.get_guild(195387617972322306).get_role(_id).mention
            for _id in x.mention_ids
        ]
        await self.insert_tournament_db(x)

        await self.create_discord_event(
            itx, x
        )  # TODO: Try and except this if start time is too fast
        await itx.edit_original_response(content="".join(mentions), embed=embed)

    @staticmethod
    async def create_discord_event(itx: core.DoomItx, tournament: TournamentData):
        with open("assets/event_banner.png", "rb") as fp:
            image_bytes = fp.read()
        await itx.guild.create_scheduled_event(
            name=tournament.title,
            start_time=tournament.start,
            end_time=tournament.end,
            privacy_level=PrivacyLevel.guild_only,
            entity_type=EntityType.external,
            location="#tournament-chat",
            image=bytearray(image_bytes),
            description="Submit your best times in the tournament for XP!",
        )

    @staticmethod
    def clean_categories_input(
        categories: list[tuple[Category, CategoryData]]
    ) -> dict[Category, CategoryData]:
        data = {}
        for cat in categories:
            if cat[1]["code"] and cat[1]["level"]:
                data[cat[0]] = cat[1]
        return data

    async def insert_tournament_db(self, data: TournamentData):
        if bool(
            await self.bot.database.get_one(
                'SELECT * FROM tournament WHERE start > now() or "end" > now()'
            )
        ):
            return  # TODO: Raise

        data.id = await self.bot.database.set_return_val(
            """
            INSERT INTO tournament (start, "end", active, bracket)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            data.start,
            data.end,
            False,
            data.bracket,
        )

        await self.bot.database.set_many(
            """
                INSERT INTO tournament_maps (id, code, level, category)
                VALUES ($1, $2, $3, $4)
            """,
            [(data.id, v["code"], v["level"], k) for k, v in data.map_data.items()],
        )
        self.bot.current_tournament = data

        start_tournament_task.change_interval(time=data.start.time())
        start_tournament_task.start(data)
