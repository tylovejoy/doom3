from __future__ import annotations

from typing import TYPE_CHECKING

import discord.ui
from discord import ButtonStyle

if TYPE_CHECKING:
    import core
from cogs.duels.utils.models import Duel

player_num_convert = {
    1: "player1",
    2: "player2",
}


class ReadyUp(discord.ui.View):
    def __init__(self, timeout: float, duel: Duel):
        super().__init__(timeout=timeout)
        self.duel = duel
        self.player1 = ReadyUpButton(1, duel.player1.user_id, duel.player1.ready)
        self.player2 = ReadyUpButton(2, duel.player2.user_id, duel.player2.ready)
        self.add_item(self.player1)
        self.add_item(self.player2)


class ReadyUpButton(discord.ui.Button):
    view: ReadyUp

    def __init__(self, player_num: int, user_id: int, ready: bool):
        self.user_id = user_id
        self.player_num = player_num
        self.ready = ready
        super().__init__(custom_id=f"ready_up_{self.player_num}")
        self.update_button()

    async def callback(self, itx: core.DoomItx):
        if itx.user.id != self.user_id:
            return
        await itx.response.defer(ephemeral=True)
        self.ready = not self.ready
        getattr(self.view.duel, player_num_convert[self.player_num]).ready = self.ready
        self.update_button()
        await itx.message.edit(view=self.view)

    def update_button(self):
        self.label = (
            f"Player {self.player_num} is ready!"
            if self.ready
            else f"Player {self.player_num} is not ready!"
        )
        self.style = ButtonStyle.green if self.ready else ButtonStyle.red
        self.emoji = "✔️" if self.ready else "✖️"

    async def _update_db(self):
        query = "UPDATE user_duels SET ready = $1 WHERE duel_id = $2 AND user_id = $3;"
        await self.view.duel.client.database.execute(
            query,
            self.ready,
            self.view.duel.id,
            self.user_id,
        )
