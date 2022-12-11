from __future__ import annotations

import asyncio
import operator
import re
import typing

import discord
from discord import app_commands
from thefuzz import fuzz

if typing.TYPE_CHECKING:
    import core

CODE_VERIFICATION = re.compile(r"^[A-Z0-9]{4,6}$")


async def delete_interaction(itx: core.Interaction[core.Doom], *, minutes: int | float):
    """Delete an itx message after x minutes. Fails silently.
    Args:
        itx (discord.Interaction): Interaction to find original message.
        minutes (int): Minutes (use 0 for no delay)
    """
    if minutes < 0:
        raise ValueError("Time cannot be negative.")
    await asyncio.sleep(60 * minutes)
    try:
        await itx.delete_original_response()
    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
        ...


def fuzz_(string: str, iterable: typing.Iterable[str]) -> str:
    """Fuzz a value."""
    values = [(val, fuzz.partial_ratio(string, val)) for val in iterable]
    return str(max(values, key=operator.itemgetter(1))[0])


def fuzz_multiple(string: str, iterable: typing.Iterable[str]) -> list[str]:
    """Fuzz a value."""
    values = [(val, fuzz.partial_ratio(string, val)) for val in iterable]
    values = sorted(values, key=operator.itemgetter(1), reverse=True)[:10]
    values = list(map(lambda x: x[0], values))
    return values


class MapCacheData(typing.TypedDict):
    levels: list[str]
    user_ids: list[int]
    choices: list[app_commands.Choice]


class UserCacheData(typing.TypedDict):
    nickname: str
    alertable: bool


NUMBER_EMOJI = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
}
