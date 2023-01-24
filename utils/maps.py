from __future__ import annotations

import typing

from discord import app_commands

import cogs
import utils

if typing.TYPE_CHECKING:
    import core


def _transform(value: str, collection: typing.Sequence) -> str:
    if value not in collection:
        value = utils.fuzz_(value, collection)
    return value


class MapNameTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        return _transform(value, itx.client.map_names)

    async def autocomplete(
        self,
        itx: core.Interaction[core.Doom],
        value: str
    ) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(value, itx.client.map_names_choices)


class MapTypeTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        return _transform(value, itx.client.map_types)

    async def autocomplete(
        self,
        itx: core.Interaction[core.Doom],
        value: str
    ) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(value, itx.client.map_types_choices)
