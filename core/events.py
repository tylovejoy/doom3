from __future__ import annotations

import typing

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

import utils
import views
from views.roles import (
    ColorRolesView,
    PronounRoles,
    ServerRelatedPings,
    TherapyRole,
    TournamentRoles,
)

if typing.TYPE_CHECKING:
    from .doom import Doom

ASCII_LOGO = r"""                                                                                
               @@@@@@@@@@@@@@    @@@@@@@@@@@@@    @@@@@    @@@@@                
               @@@@@    @@@@@@   @@@@@    @@@@@@  @@@@@   @@@@@                 
               @@@@@      @@@@@  @@@@@     @@@@@  @@@@@ @@@@@                   
               @@@@@      @@@@@  @@@@@     @@@@@  @@@@@@@@@@                    
               @@@@@      @@@@@  @@@@@@@@@@@@@@   @@@@@@@@@@                    
               @@@@@      @@@@@  @@@@@@@@@@@@@    @@@@@ @@@@@                   
          @    @@@@@     @@@@@@  @@@@@            @@@@@  @@@@@      @@@@        
    @@@        @@@@@@@@@@@@@@@   @@@@@            @@@@@   @@@@@@          @@@*  
  @@@@@        @@@@@@@@@@@@.     @@@@@            @@@@@     @@@@@         @@@@@ 
   @@@@@@@                                                            .@@@@@@@% 
      @@@@@@@@@@@@@*                                         @@@@@@@@@@@@@@@    
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&
"""


class BotEvents(commands.Cog):
    def __init__(self, bot: Doom):
        self.bot = bot
        bot.tree.on_error = utils.on_app_command_error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # TODO: parkour help what is this thread
        if message.channel.id == 1027419450275790898:
            await message.delete()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        The on_ready function is called when the bot
        is ready to receive and process commands.
        It prints a string containing the name of the bot,
        its owner, and which version of discord.py it's using.
        Args:
            self: Bot instance
        """
        app_info = await self.bot.application_info()
        self.bot.logger.info(
            f"{ASCII_LOGO}"
            f"\nLogged in as: {self.bot.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {app_info.owner}\n"
        )
        if not self.bot.persistent_views_added:
            query = "SELECT * FROM colors ORDER BY sort_order;"
            colors = await self.bot.database.fetch(query)

            query = "SELECT hidden_id FROM records WHERE hidden_id is not null;"
            queue = await self.bot.database.fetch(query)
            for row in queue:
                self.bot.add_view(views.VerificationView(), message_id=row["hidden_id"])

            view = ColorRolesView(colors)
            self.bot.add_view(view, message_id=960946616288813066)
            await self.bot.get_channel(752273327749464105).get_partial_message(
                960946616288813066
            ).edit(view=view)

            self.bot.add_view(ServerRelatedPings(), message_id=960946617169612850)
            self.bot.add_view(PronounRoles(), message_id=960946618142699560)
            self.bot.add_view(TherapyRole(), message_id=1005874559037231284)
            self.bot.add_view(TournamentRoles(), message_id=1096968488544911491)

            self.bot.logger.debug(f"Added persistent views.")
            self.bot.persistent_views_added = True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        if payload.channel_id not in [utils.SPR_RECORDS, utils.RECORDS]:
            return
        if payload.emoji != discord.PartialEmoji.from_str(
            "<:upper:787788134620332063>"
        ):
            return
        query = "SELECT user_id, hidden_id FROM records WHERE message_id = $1;"
        row: asyncpg.Record = await self.bot.database.fetchrow(
            query, payload.message_id
        )
        if not row:
            return
        is_record = bool(row.get("user_id", None))
        is_record_queue = bool(row.get("hidden_id", None))
        if not (is_record or is_record_queue):
            return
        vote_exists = await self._check_for_existing_vote(
            payload.message_id, payload.channel_id, payload.user_id
        )
        if vote_exists:
            return
        query = """
            SELECT 
              COUNT(*) as count, 
              max(top_record_id) as top_record_id
            FROM top_records
            WHERE original_message_id = $1
              AND channel_id = $2
            GROUP BY original_message_id, channel_id
        """
        top_record_data = await self.bot.database.fetchrow(
            query, payload.message_id, payload.channel_id
        )
        if top_record_data is None:
            top_record_id = None
            count = 0
        else:
            top_record_id = top_record_data.get("top_record_id", None)
            count = top_record_data.get("count", None)

        async with self.bot.database.pool.acquire() as connection:
            async with connection.transaction():
                await self._insert_top_record_vote(
                    payload.user_id,
                    payload.message_id,
                    payload.channel_id,
                    top_record_id,
                    connection=connection,
                )
                count += 1
                if count < 10:
                    return
                content = f"{count} {self.upper_emoji_converter(count)} <#{payload.channel_id}>"
                top_record_channel = self.bot.get_channel(utils.TOP_RECORDS)
                if not top_record_id:
                    await self._post_new_top_record(
                        content, payload, top_record_channel, connection=connection
                    )
                else:
                    await top_record_channel.get_partial_message(top_record_id).edit(
                        content=content
                    )

    async def _post_new_top_record(
        self, content, payload, top_record_channel, /, connection: asyncpg.Connection
    ):
        original_msg = await self.bot.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )
        if not original_msg.embeds:
            # return
            ...
        embed = original_msg.embeds[0]
        embed.add_field(name="Original", value=f"[Jump!]({original_msg.jump_url})")
        embed.colour = discord.Color.gold()
        top_record_msg = await top_record_channel.send(content, embed=embed)
        query = """UPDATE top_records SET top_record_id = $1 WHERE original_message_id = $2 AND channel_id = $3;"""
        await self.bot.database.execute(
            query,
            top_record_msg.id,
            payload.message_id,
            payload.channel_id,
            connection=connection,
        )

    async def _insert_top_record_vote(
        self,
        user_id: int,
        message_id: int,
        channel_id: int,
        top_record_id: int,
        /,
        connection: asyncpg.Connection,
    ):
        query = """
            INSERT INTO top_records (user_id, original_message_id, channel_id, top_record_id) 
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, original_message_id, channel_id)
            DO NOTHING;
        """
        await self.bot.database.execute(
            query,
            user_id,
            message_id,
            channel_id,
            top_record_id,
            connection=connection,
        )

    async def _check_for_existing_vote(
        self, message_id: int, channel_id: int, user_id: int
    ):
        query = """
            SELECT user_id
            FROM top_records
            WHERE original_message_id = $1
              AND channel_id = $2
              AND user_id = $3
            LIMIT 1;
        """
        row = await self.bot.database.fetchrow(query, message_id, channel_id, user_id)
        return row

    @staticmethod
    def upper_emoji_converter(stars: int) -> str:
        if 5 > stars >= 0:
            return "<:upper:929871697555914752>"
        elif 10 > stars >= 15:
            return "<:ds2:873791529876082758>"
        elif 15 > stars >= 10:
            return "<:ds3:873791529926414336>"
        else:
            return "<:ds4:873791530018701312>"

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Add user to DB
        query = "INSERT INTO users VALUES ($1, $2, true) ON CONFLICT DO NOTHING;"
        await self.bot.database.execute(
            query,
            member.id,
            member.name[:25],
        )

        # Add user to cache
        self.bot.all_users[member.id] = utils.UserCacheData(
            nickname=member.nick, alertable=True
        )
        self.bot.users_choices.append(
            app_commands.Choice(name=member.nick, value=str(member.id))
        )
        self.bot.logger.debug(f"Adding user to DB/cache: {member.name}: {member.id}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # members = [(member.id, member.name[:25]) for member in guild.members]
        # await self.bot.database.set_many(
        #     "INSERT INTO users (user_id, nickname, alertable) VALUES ($1, $2, true)",
        #     [(_id, nick) for _id, nick in members],
        # )
        ...

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        if before.id not in self.bot.keep_alives:
            return

        if after.archived and not after.locked:
            await after.edit(archived=False)
            self.bot.logger.debug(f"Auto-unarchived thread: {after.id}")


async def setup(bot: Doom) -> None:
    await bot.add_cog(BotEvents(bot))
