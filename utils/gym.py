from __future__ import annotations

import typing

from discord import app_commands

import cogs
import utils

if typing.TYPE_CHECKING:
    import core


class ExerciseTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        names = list(map(lambda x: x.name, itx.client.exercise_names))
        if value not in names:
            value = utils.fuzz_(value, names)
        return value

    async def autocomplete(
        self,
        itx: core.Interaction[core.Doom],
        value: int | float | str
    ) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(value, itx.client.exercise_names)
