from __future__ import annotations

import typing

from discord import app_commands

import cogs
import utils
from cogs.tournament.utils.utils import parse

if typing.TYPE_CHECKING:
    import core
import datetime


class SeasonsTransformer(app_commands.Transformer):

    async def transform(self, itx: core.DoomItx, value: str) -> int:
        try:
            value = int(value)
            return value
        except ValueError:
            pass

        query = "SELECT name, number FROM tournament_seasons;"
        rows = await itx.client.database.fetch(query)
        values = {row["name"]: row["number"] for row in rows}
        if value not in values:
            value = utils.fuzz_(value, values)
        return values[value]

    async def autocomplete(
        self, itx: core.DoomItx, value: str
    ) -> list[app_commands.Choice[str]]:
        query = "SELECT name, number FROM tournament_seasons ORDER BY similarity(name, $1::text) DESC LIMIT 12;"
        rows = await itx.client.database.fetch(query, value)
        choices = [
            app_commands.Choice(
                name=f"{row['name']} (ID {row['number']})", value=row['name']
            ) async for row in rows
        ]
        return choices



class DateTransformer(app_commands.Transformer):
    async def transform(
        self, interaction: core.DoomItx, value: str
    ) -> datetime.datetime:
        return parse(value).astimezone(datetime.timezone.utc)


class TALevelTransformer(app_commands.Transformer):
    async def transform(self, itx: core.DoomItx, value: str) -> str:
        return await map_level_transform(itx, value, "ta_code")

    async def autocomplete(
        self,
        itx: core.DoomItx,
        value: str,
    ) -> list[app_commands.Choice[str]]:
        return await map_level_autocomplete(itx, value, "ta_code")


class MCLevelTransformer(app_commands.Transformer):
    async def transform(self, itx: core.DoomItx, value: str) -> str:
        return await map_level_transform(itx, value, "mc_code")

    async def autocomplete(
        self,
        itx: core.DoomItx,
        value: str,
    ) -> list[app_commands.Choice[str]]:
        return await map_level_autocomplete(itx, value, "mc_code")


class HCLevelTransformer(app_commands.Transformer):
    async def transform(self, itx: core.DoomItx, value: str) -> str:
        return await map_level_transform(itx, value, "hc_code")

    async def autocomplete(
        self,
        itx: core.DoomItx,
        value: str,
    ) -> list[app_commands.Choice[str]]:
        return await map_level_autocomplete(itx, value, "hc_code")


class BOLevelTransformer(app_commands.Transformer):
    async def transform(self, itx: core.DoomItx, value: str) -> str:
        return await map_level_transform(itx, value, "bo_code")

    async def autocomplete(
        self,
        itx: core.DoomItx,
        value: str,
    ) -> list[app_commands.Choice[str]]:
        return await map_level_autocomplete(itx, value, "bo_code")


async def map_level_autocomplete(
    itx: core.DoomItx, value: str, arg: str
) -> list[app_commands.Choice[str]]:
    return await cogs.autocomplete(
        value,
        (itx.client.map_cache.get(getattr(itx.namespace, arg), {})).get(
            "choices", None
        ),
    )


async def map_level_transform(itx: core.DoomItx, value: str, arg: str) -> str:
    if value not in itx.client.map_cache[getattr(itx.namespace, arg)]["levels"]:
        value = utils.fuzz_(
            value, itx.client.map_cache[getattr(itx.namespace, arg)]["levels"]
        )
    return value
