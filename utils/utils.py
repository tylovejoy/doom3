from __future__ import annotations

import asyncio
import re
import typing

import discord

if typing.TYPE_CHECKING:
    import core

CODE_VERIFICATION = re.compile(r"^[A-Z0-9]{4,6}$")


async def delete_interaction(interaction: core.Interaction[core.Doom], *, minutes: int):
    """Delete an interaction message after x minutes. Fails silently.
    Args:
        interaction (discord.Interaction): Interaction to find original message.
        minutes (int): Minutes (use 0 for no delay)
    """
    if minutes < 0:
        raise ValueError("Time cannot be negative.")
    await asyncio.sleep(60 * minutes)
    try:
        await interaction.delete_original_response()
    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
        ...


