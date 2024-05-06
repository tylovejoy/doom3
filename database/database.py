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
        await self.connection.close()


class Acquire:
    def __init__(self, *, pool: asyncpg.Pool) -> None:
        self.pool: asyncpg.Pool = pool

    async def __aenter__(self) -> asyncpg.Connection:
        self._connection = c = await self.pool.acquire()
        return c

    async def __aexit__(self, *args) -> None:
        await self.pool.release(self._connection)


class DotRecord(asyncpg.Record):
    """Adds dot access to asyncpg.Record."""

    def __getattr__(self, attr: str):
        return super().__getitem__(attr)


class Database:
    """Handles all database transactions."""

    def __init__(self, conn: asyncpg.Pool):
        # self.logger: logging.Logger | None = None
        self.pool = conn

    async def fetch(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ):
        _connection = connection or self.pool
        return await _connection.fetch(query, *args, record_class=DotRecord)

    async def fetchval(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ):
        _connection = connection or self.pool
        return await _connection.fetchval(query, *args)

    async def fetchrow(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ):
        _connection = connection or self.pool
        return await _connection.fetchrow(query, *args, record_class=DotRecord)

    async def execute(
        self,
        query: str,
        *args: typing.Any,
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ):
        _connection = connection or self.pool
        await _connection.execute(query, *args)

    async def executemany(
        self,
        query: str,
        args: typing.Iterable[typing.Any],
        connection: asyncpg.Connection | asyncpg.Pool | None = None,
    ):
        _connection = connection or self.pool
        await _connection.executemany(query, args)
