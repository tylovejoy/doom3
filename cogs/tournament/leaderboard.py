from __future__ import annotations

import typing

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

import utils
import views
from cogs.tournament.utils import Categories, Rank, Categories_NoGen
from cogs.tournament.utils.data import rank_display, leaderboard_embed
from database import DotRecord
from utils import pretty_record

if typing.TYPE_CHECKING:
    import core


class TournamentLeaderboards(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def tournament_leaderboard(
        self,
        itx: core.DoomItx,
        category: Categories_NoGen,
        rank: typing.Literal[
            "Unranked", "Gold", "Diamond", "Grandmaster", "All"
        ] = "All",
    ):
        if rank == "All":
            rank = None
        await itx.response.defer(ephemeral=True)
        query = """
            WITH all_ranks AS (SELECT u.user_id, nickname, cats.value as category, COALESCE(ur.value, 'Unranked') as value
                               FROM users u
                                        JOIN tournament_ranks cats ON TRUE
                                        LEFT JOIN user_ranks ur on u.user_id = ur.user_id AND cats.value = ur.category),
                 all_records AS (SELECT nickname,
                                        record,
                                        screenshot,
                                        value,
                                        rank()
                                        over (partition by nickname, value, tr.category, ar.category order by inserted_at DESC) as date_rank
                                 FROM tournament_records tr
                                          LEFT JOIN all_ranks ar ON ar.user_id = tr.user_id
                                 WHERE tournament_id =
                                       (SELECT id FROM tournament WHERE id = (SELECT max(id) FROM tournament))
                                   AND tr.category = $1
                                   AND ar.category = $1
                                   AND ($2::text IS NULL OR ar.value = $2)
                                 ORDER BY record)
            SELECT *
            FROM all_records
            WHERE date_rank = 1;
        """
        records = await self.bot.database.fetch(query, category, rank)
        if not records:
            raise utils.NoRecordsFoundError
        embeds = self._split_records(records, category, rank)
        view = views.Paginator(embeds, itx.user)
        await view.start(itx)

    def _split_records(self, records: DotRecord, category: Categories, rank: Rank):
        embed_list = []
        embed = leaderboard_embed(
            description="",
            category=category,
            rank=rank,
        )
        for i, record in enumerate(records):
            embed.add_field(
                name=f"{utils.make_ordinal(i + 1)} - {record['nickname']} {rank_display[record['value']]}",
                value=(
                    f"> *Record:* {pretty_record(record['record'])}\n"
                    f"> [Screenshot]({record['screenshot']})\n\n"
                ),
                inline=False,
            )
            if utils.split_nth_conditional(i, 9, records):
                embed_list.append(embed)
                embed = leaderboard_embed(
                    description="",
                    category=category,
                    rank=rank,
                )
        return embed_list
