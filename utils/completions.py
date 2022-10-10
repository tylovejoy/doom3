from __future__ import annotations

import re
import typing

import discord
from discord import app_commands

import utils

if typing.TYPE_CHECKING:
    import core


class MapCodeTransformer(app_commands.Transformer):
    async def transform(
        self, interaction: core.Interaction[core.Doom], value: str
    ) -> str:
        value = value.upper().replace("O", "0").lstrip().rstrip()
        if not re.match(utils.CODE_VERIFICATION, value):
            raise utils.IncorrectCodeFormatError
        return value
