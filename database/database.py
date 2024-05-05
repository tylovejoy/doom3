import logging
import typing

import asyncpg

import utils


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
        return await _connection.fetch(query, *args)

    async def fetchval_(
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
        return await _connection.fetchrow(query, *args)

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

    async def get(
        self,
        query: str,
        *args: typing.Any,
    ) -> typing.Generator[None, None, DotRecord]:
        """
        The get_query_handler function is a helper function
        that takes in a model and query string.
        It then returns the results of the query as an array of records.
        Args:
            query (str) Specify the query that will be executed
            *args (Any) Pass in any additional arguments that are
                needed to be passed into the query
        Yields:
            DotRecords
        """
        if self.pool is None:
            raise utils.DatabaseConnectionError()

        # self.logger.debug(query)
        # self.logger.debug(args)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor(
                    query,
                    *args,
                    record_class=DotRecord,
                ):
                    yield record

    async def get_one(
        self,
        query: str,
        *args: typing.Any,
    ) -> DotRecord | None:
        res = None
        async for x in self.get(query, *args):
            res = x
            break
        return res

    async def fetchval(self, query: str, *args: typing.Any):
        if self.pool is None:
            raise utils.DatabaseConnectionError()

        # self.logger.debug(query)
        # self.logger.debug(args)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(query, *args)

    async def _set(
        self,
        query: str,
        *args: typing.Any,
        single: bool = True,
    ):
        if self.pool is None:
            raise utils.DatabaseConnectionError()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                if single:
                    return await conn.execute(query, *args)
                else:
                    return await conn.executemany(query, *args)

    async def set_return_val(
        self,
        query: str,
        *args: typing.Any,
    ):
        if self.pool is None:
            raise utils.DatabaseConnectionError()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(query, *args)

    async def set(
        self,
        query: str,
        *args: typing.Any,
    ):
        """
        The set_query_handler function takes a query string
        and an arbitrary number of arguments.
        It then executes the given query with the given arguments.
        Used for INSERT queries.
        Args:
            query (str) Store the query string
            *args (Any) Pass any additional arguments to the query
        """
        return await self._set(query, *args, single=True)

    async def set_many(
        self,
        query: str,
        *args: typing.Any,
    ):
        """
        The set_query_handler function takes a query string
        and an arbitrary number of arguments.
        It then executes the given query with the given arguments.
        Used for INSERT queries.
        Args:
            query (str) Store the query string
            *args (Any) Pass any additional arguments to the query
        """
        await self._set(query, *args, single=False)
