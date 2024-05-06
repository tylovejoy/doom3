from __future__ import annotations

import typing

import discord

import database
from cogs.tournament.utils.utils import (
    TA_ROLE,
    MC_ROLE,
    HC_ROLE,
    BO_ROLE,
    TRIFECTA_ROLE,
)

if typing.TYPE_CHECKING:
    from core import DoomItx


async def add_remove_roles(itx: DoomItx, role):
    if role in itx.user.roles:
        await itx.user.remove_roles(role)
        # await itx.edit_original_response(
        #     content=f" ",
        # )
    else:
        await itx.user.add_roles(role)
        # await itx.edit_original_response(
        #     content=f" ",
        # )


class ColorSelect(discord.ui.Select):
    def __init__(self, options: list[database.DotRecord]):
        super().__init__(
            custom_id="colors",
        )
        self.add_option(
            label="None",
            value="None",
            description="Remove color role.",
        )
        for option in options:
            self.add_option(
                label=option["label"], value=str(option["role_id"]), emoji=option["emoji"]
            )

    async def callback(self, itx: DoomItx):
        await itx.response.defer()
        all_roles = [
            itx.guild.get_role(int(role.value))
            for role in self.options
            if role.value != "None"
        ]
        for role in all_roles:
            if role in itx.user.roles:
                await itx.user.remove_roles(role)

        if self.values[0] == "None":
            return

        await itx.user.add_roles(itx.guild.get_role(int(self.values[0])))


class ColorRolesView(discord.ui.View):
    """Persistent reaction color roles."""

    def __init__(self, options):
        super().__init__(timeout=None)
        self.select = ColorSelect(options)
        self.add_item(self.select)


class ServerRelatedPings(discord.ui.View):
    """Persistent reaction server related roles."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Announcements",
        style=discord.ButtonStyle.blurple,
        custom_id="announcements",
    )
    async def announcements(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(802259719229800488)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="EU Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="eu_sleep_ping",
        row=1,
    )
    async def eu_ping(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(805542050060828682)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="NA Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="na_sleep_ping",
        row=1,
    )
    async def na_ping(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(808478386825330718)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Asia Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="asia_sleep_ping",
        row=1,
    )
    async def asia_ping(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(874438907763228743)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="OCE Sleep Ping",
        style=discord.ButtonStyle.grey,
        custom_id="oce_sleep_ping",
        row=1,
    )
    async def oce_ping(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(937726966080094229)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Movie Night",
        style=discord.ButtonStyle.grey,
        custom_id="movie_night",
        row=2,
    )
    async def movie_night(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(903667495922180167)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Game Night",
        style=discord.ButtonStyle.grey,
        custom_id="game_night",
        row=2,
    )
    async def game_night(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(903667578549968896)
        await add_remove_roles(itx, role)


class PronounRoles(discord.ui.View):
    """Persistent reaction server related roles."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="They/Them",
        style=discord.ButtonStyle.grey,
        custom_id="they_pronoun",
    )
    async def they(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(884346785949167616)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="She/Her",
        style=discord.ButtonStyle.grey,
        custom_id="she_pronoun",
    )
    async def she(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(884346748334653481)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="He/Him",
        style=discord.ButtonStyle.grey,
        custom_id="he_pronoun",
    )
    async def he(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(884346610652446720)
        await add_remove_roles(itx, role)


class TherapyRole(discord.ui.View):
    """Persistent reaction server related roles."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Serious Chat",
        style=discord.ButtonStyle.green,
        custom_id="therapy",
    )
    async def therapy_access(self, itx: DoomItx, button: discord.Button):
        return
        await itx.response.defer(ephemeral=True)

        await itx.edit_original_response(
            content="This function is current unavailable. "
            "If you would like access to #serious-chat, talk to a staff member.",
        )
        return
        # user = await ExperiencePoints.find_user(itx.user.id)
        # if getattr(user, "therapy_banned", None):
        #     await itx.response.send_message(
        #         ephemeral=True,
        #         content="You are blocked from serious-chat. Please contact a staff member for more information.",
        #     )
        #     return
        # role = itx.guild.get_role(815041888566116422)
        # await add_remove_roles(itx, role)


class TournamentRoles(discord.ui.View):
    """Persistent reaction tournament related roles."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Time Attack",
        style=discord.ButtonStyle.grey,
        custom_id="ta_role_",
    )
    async def time_attack(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(TA_ROLE)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Mildcore",
        style=discord.ButtonStyle.grey,
        custom_id="mc_role_",
    )
    async def mildcore(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(MC_ROLE)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Hardcore",
        style=discord.ButtonStyle.grey,
        custom_id="hc_role_",
    )
    async def hardcore(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(HC_ROLE)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Bonus",
        style=discord.ButtonStyle.grey,
        custom_id="bo_role_",
    )
    async def bonus(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(BO_ROLE)
        await add_remove_roles(itx, role)

    @discord.ui.button(
        label="Trifecta",
        style=discord.ButtonStyle.grey,
        custom_id="tr_role_",
    )
    async def trifecta(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        role = itx.guild.get_role(TRIFECTA_ROLE)
        await add_remove_roles(itx, role)
