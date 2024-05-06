from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from cogs.tournament.utils.data import SeasonData, Seasons
from cogs.tournament.utils.utils import ANNOUNCEMENTS
from views import Confirm

if TYPE_CHECKING:
    from core import DoomItx


class SeasonManager(discord.ui.View):
    def __init__(self, itx: DoomItx, data: Seasons):
        super().__init__()
        self.itx = itx
        self.dropdown = SeasonsDropdown(data)
        self.add_item(self.dropdown)
        self.value: int | None = None

    # Add season with modal
    @discord.ui.button(label="New season", style=discord.ButtonStyle.green)
    async def add_season(self, itx: DoomItx, button: discord.ui.Button):
        modal = AddSeasonModal()
        await itx.response.send_modal(modal)
        await modal.wait()
        if modal.name.value is None:
            return
        self.dropdown.add_season(modal.name.value, modal.number)
        await itx.edit_original_response(view=self)

    @discord.ui.button(label="Change season", style=discord.ButtonStyle.red)
    async def change_season(self, itx: DoomItx, button: discord.ui.Button):
        if self.value is None:
            await itx.response.send_message("Please select a season from the dropdown.", ephemeral=True)
            return
        view = Confirm(itx)
        await itx.response.send_message(
            (
                f"Are you sure you want change the current season "
                f"({self.dropdown.get_season_name(itx.client.current_season)}) "
                f"to {self.dropdown.get_season_name(self.value)}?"
            ),
            view=view,
            ephemeral=True,
        )
        await view.wait()
        if not view.value:
            return
        query = "UPDATE tournament_seasons SET active = FALSE WHERE active = TRUE;"
        await itx.client.database.execute(query)
        query = "UPDATE tournament_seasons SET active = TRUE WHERE number = $1;"
        await itx.client.database.execute(query, self.value)
        self.dropdown.activate_season(self.value)
        itx.client.current_season = self.value
        await itx.edit_original_response(view=self)
        await itx.guild.get_channel(ANNOUNCEMENTS).send(
            f"# {self.dropdown.get_season_name(self.value)}\n"
            f"## Welcome to the new tournament season!\n"
            f"All XP has been reset. Don't worry, the old XP amounts and leaderboard are still saved!"
        )


    # Delete season
    # @discord.ui.button(label="New season", style=discord.ButtonStyle.red)
    # async def delete_season(self, itx: DoomItx, button: discord.ui.Button):


class SeasonsDropdown(discord.ui.Select[SeasonManager]):
    def __init__(self, data: Seasons):
        options = self._build_options(data)
        self.data = data
        super().__init__(options=options)

    async def callback(self, itx: DoomItx):
        await itx.response.defer(ephemeral=True)
        self.view.value = int(self.values[0])

    @staticmethod
    def _build_options(data: Seasons):
        return [
            discord.SelectOption(
                label=f"{k} | {v['name']}",
                value=str(k),
                emoji="✅" if v["active"] else None,
            ) for k, v in data.items()
        ]

    def add_season(self, name: str, number: int):
        self.data[number] = {"name": name, "active": False}
        self.options = self._build_options(self.data)

    def activate_season(self, number: int):
        for k, v in self.data.items():
            if k == number:
                v["active"] = True
            else:
                v["active"] = False
        self.options = self._build_options(self.data)

    def get_season_name(self, number: int):
        return self.data[number]['name']


class AddSeasonModal(discord.ui.Modal, title="Add New Season"):
    name = discord.ui.TextInput(label='Season Name')
    number: int | None = None

    async def on_submit(self, itx: DoomItx):
        view = Confirm(itx)
        await itx.response.send_message(
            f"Are you sure you want to add `{self.name.value}` as a new season?",
            view=view,
            ephemeral=True,
        )
        await view.wait()
        query = "INSERT INTO tournament_seasons (name) VALUES ($1) RETURNING number;"
        self.number = await itx.client.database.fetchval(query, self.name.value)
