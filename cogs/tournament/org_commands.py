from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

import utils
from cogs.tournament.utils import Categories_NoGen, Ranks

if TYPE_CHECKING:
    import core


class OrgCommands(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def change_rank(
        self,
        itx: core.DoomItx,
        member: discord.Member,
        category: Categories_NoGen,
        rank: Ranks,
    ):
        await itx.response.defer(ephemeral=True)
        query = """
            INSERT INTO user_ranks (user_id, category, value) 
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, category) DO UPDATE 
            SET value = EXCLUDED.value
        """
        await itx.client.database.set(query, member.id, category, rank)
        await itx.edit_original_response(
            content=f"{member.mention}'s {category} rank was changed to {rank}"
        )

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def xp(self, itx: core.DoomItx, member: discord.Member, xp: int):
        await itx.response.defer(ephemeral=True)
        query = """
                    INSERT INTO user_xp (user_id, xp) 
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE 
                    SET xp = user_xp.xp + EXCLUDED.xp
                    RETURNING user_xp.xp
                """
        total = await itx.client.database.set_return_val(query, member.id, xp)
        pre_total = total - xp
        await itx.edit_original_response(
            content=f"{member.mention} was given {xp} XP. \nNew total: {total}\n Previous total: {pre_total}."
        )
