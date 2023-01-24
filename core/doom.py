from __future__ import annotations

import logging
import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs
from core.translations import DoomTranslator
from utils import MapCacheData, UserCacheData

if typing.TYPE_CHECKING:
    import aiohttp

    import database


class Doom(commands.Bot):
    """Doom bot class inherited from commands.Bot."""

    def __init__(
        self, *, session: aiohttp.ClientSession, db: database.Database
    ) -> None:
        super().__init__("?", intents=self._generate_intents(), help_command=None)
        self.session = session
        self.database = db
        self.logger = self._setup_logging()
        self.database.logger = self.logger
        # Caches
        self.map_names: list[str] | None = None
        self.map_types: list[str] | None = None
        self.map_cache: dict[str, MapCacheData] | None = {}
        self.all_users: dict[int, UserCacheData] | None = {}

        self.map_names_choices: list[app_commands.Choice] | None = None
        self.map_codes_choices: list[app_commands.Choice] | None = None
        self.map_types_choices: list[app_commands.Choice] | None = None
        self.users_choices: list[app_commands.Choice] | None = None

        self.exercise_names: list[app_commands.Choice] | None = None
        self.exercise_names_search: list[app_commands.Choice] | None = None

        self.tag_cache: list[str] | None = None
        self.tag_choices: list[app_commands.Choice] | None = None

        self.keep_alives: list[int] | None = None
        self.auto_join_threads: list[tuple[int, int]] | None = None

        self.persistent_views_added = False

    async def setup_hook(self) -> None:
        """
        The setup_hook function is called when the bot is starting up.
        It's responsible for loading all the cogs that are in
        the initial_extensions list. This function is also used
        to start a connection with the database,
        and register any tasks that need to be run on a loop.

        Args:
            self: bot instance

        Returns:
            None
        """
        await self.tree.set_translator(DoomTranslator())
        for ext in cogs.EXTENSIONS + ["jishaku", "core.events"]:
            self.logger.info(f"Loading {ext}...")
            await self.load_extension(ext)

    @staticmethod
    def _setup_logging() -> logging.Logger:
        """
        The _setup_logging function sets up the logging module for use with Discord.
        It sets the log level to INFO and creates a StreamHandler that prints to stdout.
        The formatter is set to display the name of the logger,
        its level, and its message.

        Returns:
            The logger object
        """
        logger = logging.getLogger("discord")
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                "{asctime} | {levelname: <8} | "
                "{module}:{funcName}:{lineno} - {message}",
                style="{",
            )
        )
        logger.addHandler(console_handler)
        return logger

    @staticmethod
    def _generate_intents() -> discord.Intents:
        """
        The _generate_intents function generates the intents for the bot.
        This is used to generate a discord.Intents object that can be passed into
        the Bot constructor as an argument.

        Args:

        Returns:
            Intents
        """
        intents = discord.Intents(
            guild_messages=True,
            guilds=True,
            integrations=True,
            dm_messages=True,
            webhooks=True,
            members=True,
            message_content=True,
            guild_reactions=True,
            # invites=True,
            # emojis=True,
            # bans=True,
            # presences=True,
            # dm_typing=True,
            # voice_states=True,
            # dm_reactions=True,
            # guild_typing=True,
        )
        return intents
