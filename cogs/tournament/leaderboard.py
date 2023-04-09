from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils
import views
from cogs.tournament.utils import Categories, Rank
from cogs.tournament.utils.data import rank_display
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
        category: Categories,
        rank: typing.Literal[
            "Unranked", "Gold", "Diamond", "Grandmaster", "All"
        ] = "All",
    ):
        if rank == "All":
            rank = None
        await itx.response.defer(ephemeral=True)
        query = """
            WITH all_records AS (SELECT nickname,
                                        record,
                                        screenshot,
                                        value,
                                        rank()
                                        over (partition by nickname, value, tr.category, ur.category order by inserted_at DESC) as date_rank
                                 FROM tournament_records tr
                                          LEFT JOIN users u on u.user_id = tr.user_id
                                          LEFT JOIN user_ranks ur on u.user_id = ur.user_id
                                 WHERE tournament_id =
                                       (SELECT tournament_id FROM tournament WHERE id = (SELECT max(id) FROM tournament))
                                   AND tr.category = $1
                                   AND ur.category = $1
                                   AND ($2::text IS NULL OR ur.value = $2)
                                 ORDER BY record)
            SELECT *
            FROM all_records
            WHERE date_rank = 1;
        """
        records = [x async for x in self.bot.database.get(query, category, rank)]
        if not records:
            raise utils.NoRecordsFoundError
        embeds = self._split_records(records, category, rank)
        view = views.Paginator(embeds, itx.user)
        await view.start(itx)

    def _split_records(self, records: DotRecord, category: Categories, rank: Rank):
        embed_list = []
        embed = self.bot.current_tournament.leaderboard_embed(
            description="",
            category=category,
            rank=rank,
        )
        for i, record in enumerate(records):
            embed.add_field(
                name=f"{utils.make_ordinal(i + 1)} - {record.nickname} {rank_display[record.value]}",
                value=(
                    f"> *Record:* {pretty_record(record.record)}\n"
                    f"> [Screenshot]({record.screenshot})\n\n"
                ),
                inline=False,
            )
            if utils.split_nth_conditional(i, 9, records):
                embed_list.append(embed)
                embed = self.bot.current_tournament.leaderboard_embed(
                    description="",
                    category=category,
                    rank=rank,
                )
        return embed_list
