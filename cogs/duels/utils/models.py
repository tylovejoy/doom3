from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord.channel import ThreadWithMessage

if TYPE_CHECKING:
    import core


class DuelMap:
    def __init__(self, map_code: str, level_name: str):
        self.map_code = map_code
        self.level_name = level_name


class DuelPlayer:
    def __init__(
        self, user_id: int, ready: bool, record: float | None = None, url: str | None = None
    ):
        self._user_id = user_id
        self._ready = ready
        self._record = record
        self._screenshot = url

    @property
    def user_id(self):
        return self._user_id

    @property
    def record(self):
        return self._record

    @property
    def screenshot(self):
        return self._screenshot

    @property
    def ready(self):
        return self._ready

    def set_record(self, record: float):
        self._record = record

    def set_screenshot(self, url: str):
        self._screenshot = url

    def update_values(self, record: float, url: str):
        self.set_record(record)
        self.set_screenshot(url)


class Duel:
    def __init__(
        self,
        client: core.Doom,
        thread: ThreadWithMessage,
        map_data: DuelMap,
        player1: DuelPlayer,
        player2: DuelPlayer,
        wager: int,
        start: datetime,
        end: datetime,
        duel_id: int | None = None,

    ):
        self.client = client
        self.thread = thread
        self.map_data = map_data
        self.player1 = player1
        self.player2 = player2
        self.wager = wager
        self.start = start
        self.end = end
        self.id = duel_id

    @property
    def ready(self):
        return self.player1.ready and self.player2.ready

