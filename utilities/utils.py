from __future__ import annotations

import asyncio
import operator
import re
from typing import TYPE_CHECKING, Iterable, Sequence

import discord
from thefuzz import fuzz

if TYPE_CHECKING:
    from core import DoomItx


CODE_VERIFICATION = re.compile(r"^[A-Z0-9]{4,6}$")


async def delete_interaction(itx: DoomItx, *, seconds: int | float):
    """Delete an itx message after x minutes. Fails silently.
    Args:
        itx (discord.Interaction): Interaction to find original message.
        seconds (int): Minutes (use 0 for no delay)
    """
    if seconds < 0:
        raise ValueError("Time cannot be negative.")
    await asyncio.sleep(seconds)
    try:
        await itx.delete_original_response()
    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
        ...


def fuzz_(string: str, iterable: Iterable[str]) -> str:
    """Fuzz a value."""
    values = [(val, fuzz.partial_ratio(string, val)) for val in iterable]
    return str(max(values, key=operator.itemgetter(1))[0])


def fuzz_multiple(string: str, iterable: Iterable[str]) -> list[str]:
    """Fuzz a value."""
    values = [(val, fuzz.partial_ratio(string, val)) for val in iterable]
    values = sorted(values, key=operator.itemgetter(1), reverse=True)[:10]
    values = list(map(lambda x: x[0], values))
    return values


def split_nth_conditional(cur_i: int, n: int, collection: Sequence) -> bool:
    return (cur_i != 0 and cur_i % n == 0) or (cur_i == 0 and len(collection) == 1) or cur_i == len(collection) - 1


def time_convert(string: str) -> float:
    """Convert HH:MM:SS.ss string into seconds (float)."""
    negative = -1 if string[0] == "-" else 1
    time = string.split(":")
    match len(time):
        case 1:
            res = float(time[0])
        case 2:
            res = float((int(time[0]) * 60) + (negative * float(time[1])))
        case 3:
            res = float((int(time[0]) * 3600) + (negative * (int(time[1]) * 60)) + (negative * float(time[2])))
        case _:
            raise ValueError("Failed to match any cases.")
    return res
