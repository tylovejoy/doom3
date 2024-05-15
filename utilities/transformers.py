from __future__ import annotations

import re
from typing import TYPE_CHECKING

from discord import app_commands

from utilities import errors
import utilities

if TYPE_CHECKING:
    from core import DoomItx


def sanitize_map_code_input(value: str) -> str:
    return value.upper().replace("O", "0").lstrip().rstrip()


class MapCodeFormattingTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        value = sanitize_map_code_input(value)
        if not re.match(utilities.CODE_VERIFICATION, value):
            raise errors.IncorrectCodeFormatError
        return value


class ExistingMapCodeTransformer(MapCodeFormattingTransformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        transformed = await super().transform(itx, value)
        query = "SELECT EXISTS(SELECT 1 FROM maps WHERE maps.map_code=$1);"
        exists = await itx.client.database.fetchval(query, transformed)
        if not exists:
            raise errors.InvalidMapCodeError
        return value


class ExistingMapCodeAutocompleteTransformer(ExistingMapCodeTransformer):
    async def autocomplete(self, itx: DoomItx, value: str) -> list[app_commands.Choice[str]] | None:
        query = """
            SELECT maps.map_code
            FROM maps
            ORDER BY similarity(maps.map_code, upper($1)) DESC
            LIMIT 6;
        """
        rows = await itx.client.database.fetch(query, value)
        if not rows:
            return
        return [app_commands.Choice(name=a, value=a) for a, in rows]


class UserTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> int:
        query = "SELECT user_id FROM users ORDER BY similarity(nickname, $1) LIMIT 1"
        user_id = await itx.client.database.fetchval(query, value)
        if not user_id:
            raise errors.UserNotFoundError
        return int(user_id)

    async def autocomplete(self, itx: DoomItx, value: str) -> list[app_commands.Choice[str]] | None:
        query = """
            SELECT users.nickname, users.user_id
            FROM users
            ORDER BY similarity(users.nickname, $1) DESC
            LIMIT 6;
        """
        rows = await itx.client.database.fetch(query, value)
        if not rows:
            return
        return [app_commands.Choice(name=f"{nickname} ({user_id})", value=str(user_id)) for nickname, user_id in rows]


class CreatorTransformer(UserTransformer):
    async def autocomplete(self, itx: DoomItx, value: str) -> list[app_commands.Choice[str]] | None:

        query = """
            SELECT u.nickname, mc.user_id
            FROM map_creators mc
                LEFT JOIN users u ON mc.user_id = u.user_id
            WHERE map_code=$2
            ORDER BY similarity(u.nickname, $1) DESC
            LIMIT 6;
        """
        sanitized_map_code = sanitize_map_code_input(itx.namespace.map_code)
        rows = await itx.client.database.fetch(query, value, sanitized_map_code)
        if not rows:
            return
        return [app_commands.Choice(name=f"{nickname} ({user_id})", value=str(user_id)) for nickname, user_id in rows]


class MapLevelTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        query = """
            SELECT level
            FROM map_levels
            WHERE map_code=$1
            ORDER BY similarity(level, upper($2)) DESC
            LIMIT 1;
        """
        level_name = await itx.client.database.fetchval(query, itx.namespace.map_code, value)
        if not level_name:
            level_names = await itx.client.database.fetch_level_names_of_map_code(itx.namespace.map_code)
            return utilities.fuzz_(value, level_names)
        return level_name

    async def autocomplete(self, itx: DoomItx, value: str) -> list[app_commands.Choice[str]] | None:
        query = """
            SELECT level
            FROM map_levels
            WHERE map_code=$1
            ORDER BY similarity(level, upper($2)) DESC
            LIMIT 6;
        """
        sanitized_map_code = sanitize_map_code_input(itx.namespace.map_code)
        rows = await itx.client.database.fetch(query, value, sanitized_map_code)
        if not rows:
            return
        return [app_commands.Choice(name=level, value=level) for level, in rows]


class MapNameTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        map_names = await itx.client.database.fetch_all_map_names()
        if not map_names:
            raise errors.InvalidMapNameError
        return utilities.fuzz_(value, map_names)

    async def autocomplete(self, itx: DoomItx, value: str) -> list[app_commands.Choice[str]] | None:
        map_names = await itx.client.database.fetch_similar_map_names(value)
        if not map_names:
            return
        return [app_commands.Choice(name=name, value=name) for name in map_names]


class MapTypeTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        map_types = await itx.client.database.fetch_all_map_types()
        if not map_types:
            raise errors.InvalidMapTypeError
        return utilities.fuzz_(value, map_types)

    async def autocomplete(self, itx: DoomItx, value: str) -> list[app_commands.Choice[str]] | None:
        map_types = await itx.client.database.fetch_similar_map_types(value)
        if not map_types:
            return
        return [app_commands.Choice(name=name, value=name) for name in map_types]


class URLTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        value = value.strip()
        if not value.startswith("https://") and not value.startswith("http://"):
            value = "https://" + value
        async with itx.client.session.get(value) as resp:
            if resp.status != 200:
                raise errors.IncorrectURLFormatError
            return str(resp.url)
