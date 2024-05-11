from __future__ import annotations

import datetime
import functools
from typing import TYPE_CHECKING, Any

import discord
from discord.ui import Item

from config import CONFIG

from .utils import delete_interaction

if TYPE_CHECKING:
    from core import DoomItx

MISSING: Any = discord.utils.MISSING


class ConfirmationBaseView(discord.ui.View):
    timeout: float

    def __init__(
        self,
        itx: DoomItx,
        initial_message: str,
        embed: discord.Embed = MISSING,
        attachment: discord.File = MISSING,
    ):
        super().__init__(timeout=600)
        self.itx = itx
        self.initial_message = initial_message + self._get_timeout_message()
        self.value = False
        self.embed = embed
        if attachment:
            self.attachments = [attachment]
        else:
            self.attachments = attachment

    def _get_timeout_message(self):
        view_expires_at = self.itx.created_at + datetime.timedelta(seconds=self.timeout)
        formatted_timestamp = discord.utils.format_dt(view_expires_at, style="R")
        return f"\n\nThis form will timeout {formatted_timestamp}."

    async def on_error(self, itx: DoomItx, error: Exception, item: Item[Any]) -> None:
        if isinstance(error, (discord.HTTPException, discord.Forbidden)):
            return  # Ignore unknown interaction errors
        await super().on_error(itx, error, item)

    @discord.ui.button(
        label="Yes, everything is correct.",
        emoji=CONFIG["VERIFIED"],
        style=discord.ButtonStyle.green,
        row=4,
    )
    async def accept(self, itx: DoomItx, button: discord.ui.Button):
        self.value = True
        await itx.response.send_message("Confirmed.", ephemeral=True)
        self.stop()

    @discord.ui.button(
        label="No, not everything is correct.",
        emoji=CONFIG["UNVERIFIED"],
        style=discord.ButtonStyle.red,
        row=4,
    )
    async def reject(self, itx: DoomItx, button: discord.ui.Button):
        self.value = False
        await itx.response.send_message("Rejected.", ephemeral=True)
        self.stop()

    async def start(self):
        if self.itx.response.is_done():
            send = functools.partial(self.itx.edit_original_response, attachments=self.attachments)
        else:
            send = functools.partial(self.itx.response.send_message, ephemeral=True, files=self.attachments)
        await send(content=self.initial_message, view=self, embed=self.embed)
        await delete_interaction(self.itx, seconds=self.timeout)
        await self.wait()
