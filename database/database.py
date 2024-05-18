import typing

import asyncpg


class DatabaseConnection:
    """Handles asyncronous context manager for database connection."""

    def __init__(self, dsn: str):
        self.connection: asyncpg.Pool | None = None
        self.dsn = dsn

    async def __aenter__(self):
        self.connection = await asyncpg.create_pool(self.dsn)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        assert self.connection
        await self.connection.close()


class DotRecord(asyncpg.Record):
    """Adds dot access to asyncpg.Record."""

    def __getattr__(self, attr: str):
        return super().__getitem__(attr)


class Database:
    """Handles all database transactions."""

    def __init__(self, conn: asyncpg.Pool):
        self.pool = conn

    async def fetch(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ) -> list[asyncpg.Record] | None:
        _connection = connection or self.pool
        return await _connection.fetch(query, *args, record_class=DotRecord)

    async def fetchval(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ) -> typing.Any:
        _connection = connection or self.pool
        return await _connection.fetchval(query, *args)

    async def fetchrow(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ) -> asyncpg.Record | None:
        _connection = connection or self.pool
        return await _connection.fetchrow(query, *args, record_class=DotRecord)

    async def execute(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ) -> None:
        _connection = connection or self.pool
        await _connection.execute(query, *args)

    async def executemany(
        self,
        query: str,
        args: typing.Iterable[typing.Any],
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ) -> None:
        _connection = connection or self.pool
        await _connection.executemany(query, args)

    async def _fetch_map_names(self, query: str, value: str | None) -> list[str] | None:
        if value:
            rows = await self.fetch(query, value)
        else:
            rows = await self.fetch(query)
        if not rows:
            return
        map_names = [name for name, in rows]
        return map_names

    async def fetch_all_map_names(self) -> list[str] | None:
        query = "SELECT name FROM all_map_names"
        return await self._fetch_map_names(query, None)

    async def fetch_similar_map_names(self, value: str) -> list[str] | None:
        query = "SELECT name FROM all_map_names ORDER BY similarity(upper(name), upper($1)) DESC LIMIT 6;"
        return await self._fetch_map_names(query, value)

    async def _fetch_map_types(self, query: str, value: str | None = None) -> list[str] | None:
        if value:
            rows = await self.fetch(query, value)
        else:
            rows = await self.fetch(query)
        if not rows:
            return
        map_types = [name for name, in rows]
        return map_types

    async def fetch_all_map_types(self) -> list[str] | None:
        query = "SELECT name FROM all_map_types"
        return await self._fetch_map_types(query)

    async def fetch_similar_map_types(self, value: str) -> list[str] | None:
        query = "SELECT name FROM all_map_types ORDER BY similarity(upper(name), upper($1)) DESC LIMIT 6;"
        return await self._fetch_map_types(query, value)

    async def fetch_level_names_of_map_code(self, map_code: str) -> list[str]:
        query = "SELECT level FROM map_levels WHERE map_code=$1;"
        rows = await self.fetch(query, map_code)
        if not rows:
            raise ValueError("This map code has no levels.")
        all_levels = [row["level"] for row in rows]
        return all_levels

    async def add_multiple_map_levels(
        self, map_code: str, levels: list[str], *, connection: asyncpg.Connection | asyncpg.Pool | None = None
    ):
        query = "INSERT INTO map_levels (map_code, level) VALUES ($1, $2);"
        _levels = [(map_code, level_name) for level_name in levels]
        _connection = connection or self
        await _connection.executemany(query, _levels)

    async def add_map_level_to_map_code(
        self, map_code: str, new_level_name: str, *, connection: asyncpg.Connection | asyncpg.Pool | None = None
    ) -> None:
        _connection = connection or self.pool
        await self.add_multiple_map_levels(map_code, [new_level_name], connection=_connection)

    async def remove_map_level_from_map_code(self, map_code: str, level_name: str) -> None:
        query = "DELETE FROM map_levels WHERE map_code=$1 AND level=$2;"
        await self.execute(
            query,
            map_code,
            level_name,
        )

    async def rename_level_name_for_map_code(self, map_code: str, level_name: str, new_level_name: str) -> None:
        query = "UPDATE map_levels SET level=$3 WHERE map_code=$1 AND level=$2;"
        await self.execute(
            query,
            map_code,
            level_name,
            new_level_name,
        )

    async def fetch_creator_ids_for_map_code(self, map_code: str) -> list[int]:
        query = "SELECT 1 FROM map_creators WHERE map_code=$1;"
        rows = await self.fetch(query, map_code)
        if not rows:
            raise ValueError("This map code has no creators.")
        return [row["user_id"] for row in rows]

    async def remove_creator_from_map_code(self, creator: int, map_code: str) -> None:
        query = "DELETE FROM map_creators WHERE map_code=$1 AND user_id=$2;"
        await self.execute(query, map_code, creator)

    async def add_creator_to_map_code(
        self, creator_id: int, map_code: str, *, connection: asyncpg.Connection | asyncpg.Pool | None = None
    ) -> None:
        query = "INSERT INTO map_creators (map_code, user_id) VALUES ($1, $2);"
        _connection = connection or self
        await _connection.execute(query, map_code, creator_id)

    async def fetch_user_nickname(self, user_id: int, *, connection: asyncpg.Connection | asyncpg.Pool | None = None) -> str:
        query = "SELECT nickname FROM users WHERE user_id=$1;"
        return await self.fetchval(query, user_id, connection=connection)

    async def insert_map_data(
        self,
        map_code: str,
        map_name: str,
        map_types: list[str],
        description: str,
        image_url: str,
        *,
        connection: asyncpg.Connection | asyncpg.Pool,
    ) -> None:
        query = """
            INSERT INTO maps 
            (map_code, map_name, map_type, "desc", image) 
            VALUES ($1, $2, $3, $4, $5);
        """
        _connection = connection or self
        await _connection.execute(
            query,
            map_code,
            map_name,
            map_types,
            description,
            image_url,
        )

    async def fetch_previous_record_submission(self, map_code: str, level_name: str, user_id: int) -> asyncpg.Record | None:
        query = """
                    SELECT record, hidden_id FROM records r 
                    LEFT OUTER JOIN maps m on r.map_code = m.map_code
                    WHERE r.map_code = $1 AND level_name = $2 AND user_id = $3
                    ORDER BY inserted_at DESC
                """
        return await self.fetchrow(
            query,
            map_code,
            level_name,
            user_id,
        )
