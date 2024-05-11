import asyncio
import os

import aiohttp
import discord.utils

import core
import database
from config import CONFIG


async def main() -> None:
    """
    The main function is the entry point of the program.
    It creates a bot instance and runs it.
    """
    discord.utils.setup_logging()
    async with aiohttp.ClientSession() as session:
        async with database.DatabaseConnection(CONFIG["POSTGRESQL"]) as pool:
            assert pool is not None
            async with core.Doom() as bot:
                bot.session = session
                bot.pool = pool
                bot.database = database.Database(pool)
                await bot.start(CONFIG["TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
