from __future__ import annotations

import typing

from discord import app_commands

import utils

if typing.TYPE_CHECKING:
    import core


class MapNameTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        if value not in itx.client.map_names:
            value = utils.fuzz_(value, itx.client.map_names)
        return value


class MapTypeTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        if value not in itx.client.map_names:
            value = utils.fuzz_(value, itx.client.map_names)
        return value
