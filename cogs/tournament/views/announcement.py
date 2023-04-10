from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ui import TextInput

if TYPE_CHECKING:
    import core


class TournamentAnnouncementModal(
    discord.ui.Modal, title="Tournament Announcement Wizard"
):
    def __init__(self) -> None:
        super().__init__()
        self.title_ = TextInput(label="Title")
        self.content = TextInput(
            label="Announcement Content",
            style=discord.TextStyle.long,
        )
        self.add_item(self.title_)
        self.add_item(self.content)
        self.itx: core.DoomItx | None = None

    async def on_submit(self, itx: discord.Interaction):
        self.itx = itx
        await itx.response.send_message("Please wait...", ephemeral=True)

    @property
    def value(self):
        return bool(self.title_.value) and bool(self.content.value)

    @property
    def values(self):
        return {
            "title": self.title_.value,
            "description": self.content.value,
        }


class TournamentRolesDropdown(discord.ui.Select):
    def __init__(self):
        super().__init__(
            max_values=6,
            placeholder="Which roles?",
            options=[
                discord.SelectOption(
                    label=x,
                    value=x,
                )
                for x in [
                    "Time Attack",
                    "Mildcore",
                    "Hardcore",
                    "Bonus",
                    "Trifecta",
                    "Bracket",
                ]
            ],
        )

    async def callback(self, itx: core.DoomItx):
        await itx.response.defer(ephemeral=True)
