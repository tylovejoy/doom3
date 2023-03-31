from __future__ import annotations

import typing

import discord
from discord.ext import commands
from discord import app_commands

import utils
import views
from cogs.tournament.utils.utils import Category, full_title_map, reverse_title_map

if typing.TYPE_CHECKING:
    import core


class TournamentLeaderboards(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def tournament_leaderboard(
        self,
        itx: core.DoomItx,
        category: typing.Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"],
        rank: typing.Literal[
            "Unranked", "Gold", "Diamond", "Grandmaster", "All"
        ] = "All",
    ):
        if rank == "All":
            rank = None
        await itx.response.defer(ephemeral=True)
        query = """
            SELECT nickname, record, screenshot, value
            FROM tournament_records tr 
            LEFT JOIN users u on u.user_id = tr.user_id
            LEFT JOIN user_ranks_new ur on u.user_id = ur.user_id
            WHERE tournament_id = (SELECT tournament_id FROM tournament WHERE id = (SELECT max(id) FROM tournament))
            AND tr.category = $1
            AND ur.category = $1
            AND ($2::text IS NULL OR ur.value = $2)
            ORDER BY record;
        """
        records = [
            x
            async for x in self.bot.database.get(
                query, reverse_title_map[category], rank
            )
        ]
        total_text = 0
        descriptions = []
        description = f"**{category} Leaderboard**\n"
        for i, record in enumerate(records, start=1):
            cur_text = f"`{utils.make_ordinal(i):^6}` `{record.record:^10}` `{record.nickname}` [Link]({record.screenshot})\n"
            if total_text + len(cur_text) >= 4095:
                descriptions.append(description)
                description = f"**{category} Leaderboard**\n"
                total_text = 0
            total_text += len(cur_text)
            description += cur_text
        if description:
            descriptions.append(description)

        embeds = [
            self.bot.current_tournament.base_embed(
                description=x, embed_type="leaderboard"
            )
            for x in descriptions
        ]
        view = views.Paginator(embeds, itx.user)
        await view.start(itx)
