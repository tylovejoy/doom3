from __future__ import annotations

import pkgutil
import typing

from discord import app_commands

if typing.TYPE_CHECKING:
    import core

EXTENSIONS = [
    module.name for module in pkgutil.iter_modules(__path__, f"{__package__}.")
]


def case_ignore_compare(string1: str | None, string2: str | None) -> bool:
    """
    Compare two strings, case-insensitive.
    Args:
        string1 (str): String 1 to compare
        string2 (str): String 2 to compare
    Returns:
        True if string2 is in string1
    """
    if None in [string1, string2]:
        return False
    return string2.casefold() in string1.casefold()


async def autocomplete(
    current: str,
    choices: list[app_commands.Choice],
) -> list[app_commands.Choice[str]]:
    if not choices:  # Quietly ignore empty choices
        return []
    if current == "":
        response = choices[:25]
    else:
        response = [x for x in choices if case_ignore_compare(x.name, current)][:25]
    return response


async def exercise_name_autocomplete(
    itx: core.Interaction[core.Doom], current: str
) -> list[app_commands.Choice[str]]:
    return await autocomplete(current, itx.client.exercise_names)


async def tags_autocomplete(
    itx: core.Interaction[core.Doom], current: str
) -> list[app_commands.Choice[str]]:
    return await autocomplete(current, itx.client.tag_choices)


async def exercise_name_search_autocomplete(
    itx: core.Interaction[core.Doom], current: str
) -> list[app_commands.Choice[str]]:
    return await autocomplete(current, itx.client.exercise_names_search)
