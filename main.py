import asyncio
import os

import aiohttp

import core
import database


async def main() -> None:
    """
    The main function is the entry point of the program.
    It creates a bot instance and runs it.
    """
    async with aiohttp.ClientSession() as session:
        async with database.DatabaseConnection(
            f"postgres://"
            f"{os.environ['PSQL_USER']}:"
            f"{os.environ['PSQL_PASSWORD']}@"
            f"{os.environ['PSQL_HOST']}:"
            f"{os.environ['PSQL_PORT']}/"
            f"{os.environ['PSQL_DATABASE']}"
        ) as connection:
            print("WAAAAAAAAAA")
            bot = core.Doom(session=session, db=database.Database(connection))
            print("WEEEEEEEEEEEEe")
            async with bot:
                print("WIIII")
                await bot.start(os.environ["TOKEN"])
                print("ASDDDDDDDD")


if __name__ == "__main__":
    asyncio.run(main())
