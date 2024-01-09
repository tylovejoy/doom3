from __future__ import annotations

import typing
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

import utils
import views
from cogs.tournament.utils import Categories_NoGen, Ranks
from cogs.tournament.utils.errors import ModalError
from cogs.tournament.utils.utils import ANNOUNCEMENTS, role_map
from cogs.tournament.views.announcement import (
    TournamentAnnouncementModal,
    TournamentRolesDropdown,
)
from cogs.tournament.views.seasons import SeasonManager
from utils import DoomEmbed

if TYPE_CHECKING:
    import core


class OrgCommands(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    org = app_commands.Group(
        name="org",
        description="org only commands",
        guild_ids=[195387617972322306, utils.GUILD_ID],
    )

    async def cog_load(self) -> None:
        query = "SELECT number FROM tournament_seasons WHERE active = TRUE ORDER BY number DESC LIMIT 1"
        res = await self.bot.database.fetchval(query)
        if not res:
            raise RuntimeError("No tournament season found... Stopping bot.")
        self.bot.current_season = res

    @org.command()
    async def change_rank(
        self,
        itx: core.DoomItx,
        member: discord.Member,
        category: typing.Literal["Time Attack", "Mildcore", "Hardcore"],
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

    @org.command()
    async def xp(self, itx: core.DoomItx, member: discord.Member, xp: int):
        await itx.response.defer(ephemeral=True)
        query = """
            INSERT INTO user_xp (user_id, xp, season) 
            VALUES ($1, $2)
            ON CONFLICT (user_id, season) DO UPDATE 
            SET xp = user_xp.xp + EXCLUDED.xp
            RETURNING user_xp.xp
        """
        total = await itx.client.database.set_return_val(query, member.id, xp)
        pre_total = total - xp
        await itx.edit_original_response(
            content=f"{member.mention} was given {xp} XP. \nNew total: {total}\n Previous total: {pre_total}."
        )

    @org.command()
    async def announcement(
        self,
        itx: core.DoomItx,
        thumbnail: discord.Attachment | None,
        image: discord.Attachment | None,
    ):
        modal = TournamentAnnouncementModal()
        await itx.response.send_modal(modal)
        await modal.wait()
        if not modal.value:
            raise ModalError

        if not thumbnail:
            thumbnail = "https://bkan0n.com/assets/images/icons/gold_cup.png"
        else:
            thumbnail = thumbnail.url
        if not image:
            image = "https://bkan0n.com/assets/images/icons/tournament_announcement_banner.png"
        else:
            image = image.url

        embed = DoomEmbed(
            **modal.values,
            color=discord.Color.gold(),
            thumbnail=thumbnail,
            image=image,
        )
        select = TournamentRolesDropdown()
        view = views.Confirm(modal.itx)
        view.add_item(select)

        await modal.itx.edit_original_response(
            content="Is this correct?", embed=embed, view=view
        )
        await view.wait()
        if not view.value:
            return

        mentions = "".join(
            [itx.guild.get_role(role_map[x]).mention for x in select.values]
        )
        await itx.guild.get_channel(ANNOUNCEMENTS).send(mentions, embed=embed)

    @org.command()
    async def season_manager(
        self,
        itx: core.DoomItx,
    ):
        await itx.response.defer(ephemeral=True)
        query = "SELECT * FROM tournament_seasons ORDER BY number;"
        data = {row['number']: {"name": row['name'], "active": row['active']} async for row in self.bot.database.get(query)}
        view = SeasonManager(itx, data)
        await itx.edit_original_response(view=view)
        await view.wait()

