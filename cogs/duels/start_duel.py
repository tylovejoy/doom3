from __future__ import annotations

import datetime
import typing
from enum import Enum, IntEnum

import dateparser
import discord
from discord import EntityType, PrivacyLevel, app_commands
from discord.ext import commands

import utils
from cogs.duels.utils.errors import PlayerAlreadyInMatch, NotEnoughXP
from cogs.duels.utils.models import DuelMap, DuelPlayer, Duel
from cogs.duels.views.ready_up import ReadyUp
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


class Result(IntEnum):
    LOSS = -1
    IN_PROGRESS = 0
    WON = 1


class Duels(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    duel = app_commands.Group(
        name="duel",
        description="duel",
        guild_ids=[195387617972322306, utils.GUILD_ID],
    )

    @duel.command()
    @app_commands.choices(
        length=[
            app_commands.Choice(name="1 Day", value="1 Day"),
        ]
        + [
            app_commands.Choice(name=f"{x} Days", value=f"{x} Days")
            for x in range(2, 8)
        ]
    )
    async def request(
        self,
        itx: core.DoomItx,
        user: discord.Member,
        length: app_commands.Choice[str],
        wager: int,
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer] | None,
        level: app_commands.Transform[str, utils.MapLevelTransformer] | None,
    ):
        await itx.response.defer(ephemeral=True)
        if await self._check_if_in_match(itx.user.id, user.id):
            raise PlayerAlreadyInMatch

        if not await self._check_xp(itx.user.id, user.id, wager):
            raise NotEnoughXP

        if not map_code:
            map_code = await self._get_random_map()
            level = await self._get_random_level(map_code)
        elif map_code and not level:
            level = await self._get_random_level(map_code)

        start = discord.utils.utcnow() + datetime.timedelta(days=1)
        end = (
            dateparser.parse(
                length.value,
                settings={"PREFER_DATES_FROM": "future"},
            ).astimezone(datetime.timezone.utc)
            - discord.utils.utcnow()
            + start
        )

        forum: discord.ForumChannel = itx.guild.get_channel(1095368893591203861)
        thread = await forum.create_thread(
            name=f"{itx.user.name} VS. {user.name}",
            content=(
                "**Details:**\n"
                f"`Code` {map_code}\n"
                f"`Level` {level}\n"
                f"`Wager` {wager}\n"
                f"`Start` {discord.utils.format_dt(start, style='F')}{discord.utils.format_dt(start, style='R')}\n"
                f"`End` {discord.utils.format_dt(end, style='F')}{discord.utils.format_dt(end, style='R')}"
            ),
        )
        map_data = DuelMap(map_code, level)
        player1 = DuelPlayer(itx.user.id, True)
        player2 = DuelPlayer(user.id, False)
        duel = Duel(
            self.bot,
            thread,
            map_data,
            player1,
            player2,
            wager,
            start,
            end,
        )
        # await self._add_to_database(duel)
        view = ReadyUp((start - discord.utils.utcnow()).total_seconds(), duel)
        await thread.thread.send(
            f"Standing by until "
            f"{discord.utils.format_dt(start, style='F')}"
            f"{discord.utils.format_dt(start, style='R')}... "
            f"Duel will be cancelled if both players do not ready up."
            f"\n\n"
            f"Waiting for Ready Up! {user.mention}",
            view=view,
        )

    async def _add_to_database(self, duel: Duel):
        query = """
            INSERT INTO duels (thread_id, thread_msg, wager, start, "end") 
            VALUES ($1, $2, $3, $4, $5) 
            RETURNING id;
        """
        duel_id = await self.bot.database.set_return_val(
            query,
            duel.thread.thread.id,
            duel.thread.message.id,
            duel.wager,
            duel.start,
            duel.end,
        )
        query = """
            INSERT INTO user_duels (user_id, ready, duel_id, num) 
            VALUES ($1, $2, $3, $4)
        """
        await self.bot.database.set_many(
            query,
            [
                (player.user_id, player.ready, duel_id, i)
                for i, player in enumerate((duel.player1, duel.player2), start=1)
            ],
        )

    async def _check_if_in_match(self, player1: int, player2: int):
        query = """
            SELECT 1 FROM user_duels WHERE (user_id = $1 or user_id = $2) AND result = 0 LIMIT 1;
        """
        return bool(await self.bot.database.get_one(query, player1, player2))

    async def _check_xp(self, player1: int, player2: int, wager: int):
        query = """
        with p1 as (SELECT 1 as id, xp >= $3 as p1_xp FROM user_xp WHERE user_id = $1),
             p2 as (SELECT 1 as id, xp >= $3 as p2_xp FROM user_xp WHERE user_id = $2)
        SELECT p1_xp, p2_xp FROM
             p1 JOIN p2 ON p1.id = p2.id
        """
        row = await self.bot.database.get_one(query, player1, player2, wager)
        return False if not row else all((row.p1_xp, row.p2_xp))

    async def _get_random_map(self):
        query = """
            SELECT map_code FROM maps OFFSET floor(random() * (SELECT count(*) FROM maps)) LIMIT 1;
        """
        return await self.bot.database.fetchval(query)

    async def _get_random_level(self, map_code: str):
        query = """
            SELECT level 
            FROM map_levels 
            WHERE map_code = $1 
            OFFSET floor(random() * (SELECT count(*) FROM map_levels WHERE map_code = $1)) 
            LIMIT 1;
        """
        return await self.bot.database.fetchval(query, map_code)
