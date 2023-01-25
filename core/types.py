from __future__ import annotations

import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    import core

    DoomItx = discord.Interaction[core.Doom]
    DoomCtx = commands.Context[core.Doom]
