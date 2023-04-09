from __future__ import annotations

import datetime
import typing

import discord
from discord import EntityType, PrivacyLevel, app_commands
from discord.ext import commands

import utils
from cogs.tournament.utils import Category, CategoryData
from cogs.tournament.utils.data import TournamentData
from cogs.tournament.utils.end_tournament import (
    ExperienceCalculator,
    SpreadsheetCreator,
)
from cogs.tournament.utils.errors import TournamentAlreadyExists
from cogs.tournament.utils.transformers import DateTransformer
from cogs.tournament.views.start import TournamentStartView
from utils import start_tournament_task

if typing.TYPE_CHECKING:
    import core


class Tournament(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def start(
        self,
        itx: core.DoomItx,
        start: app_commands.Transform[datetime.datetime, DateTransformer],
        end: app_commands.Transform[datetime.datetime, DateTransformer],
    ):
        await itx.response.defer(ephemeral=True)
        end = end - discord.utils.utcnow() + start

        view = TournamentStartView(itx)
        await itx.edit_original_response(
            content="Click on the buttons to add necessary info.", view=view
        )
        await view.wait()

        categories = [
            (Category.TIME_ATTACK, view.ta_modal),
            (Category.MILDCORE, view.mc_modal),
            (Category.HARDCORE, view.hc_modal),
            (Category.BONUS, view.bo_modal),
        ]
        category_data = [
            (
                cat,
                CategoryData(
                    code=cat_data.code, level=cat_data.level, creator=cat_data.creator
                ),
            )
            for cat, cat_data in categories
            if cat_data
        ]

        data = self.clean_categories_input(category_data)
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

        await self.create_discord_event(itx, x)
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
            raise TournamentAlreadyExists

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
            [
                (data.id, v["code"], v["level"], v["creator"], k)
                for k, v in data.map_data.items()
            ],
        )
        self.bot.current_tournament = data

        start_tournament_task.change_interval(time=data.start.time())
        start_tournament_task.start(data)
