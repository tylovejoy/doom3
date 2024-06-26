from __future__ import annotations

import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    import core

    DoomItx: typing.TypeAlias = discord.Interaction[core.Doom]
    DoomCtx: typing.TypeAlias = commands.Context[core.Doom]
