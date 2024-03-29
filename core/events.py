from __future__ import annotations

import typing

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
            colors = [
                x
                async for x in self.bot.database.get(
                    "SELECT * FROM colors ORDER BY sort_order;",
                )
            ]

            queue = [
                x.hidden_id
                async for x in self.bot.database.get(
                    "SELECT hidden_id FROM records WHERE hidden_id is not null;",
                )
            ]
            for x in queue:
                self.bot.add_view(views.VerificationView(), message_id=x)

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

        query = """SELECT user_id, hidden_id FROM records WHERE message_id = $1;"""
        row = await self.bot.database.get_one(query, payload.message_id)

        is_record = bool(row.user_id)
        is_record_queue = bool(row.hidden_id)

        if not (is_record or is_record_queue):
            return

        query = """
            SELECT user_id
            FROM top_records
            WHERE original_message_id = $1
              AND channel_id = $2
              AND user_id = $3
            LIMIT 1;
        """

        row = await self.bot.database.get_one(
            query, payload.message_id, payload.channel_id, payload.user_id
        )

        if row:
            return

        query = """
            SELECT COUNT(*) as count, top_record_id
            FROM top_records
            WHERE original_message_id = $1
              AND channel_id = $2
            GROUP BY original_message_id, channel_id, top_record_id
        """

        top_record_id = None
        count = 0
        async for row in self.bot.database.get(
            query, payload.message_id, payload.channel_id
        ):
            count += row.count
            if not top_record_id and row.top_record_id:
                top_record_id = row.top_record_id

        query = """
            INSERT INTO top_records (user_id, original_message_id, channel_id, top_record_id) 
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, original_message_id, channel_id)
            DO NOTHING;
        """

        await self.bot.database.set(
            query,
            payload.user_id,
            payload.message_id,
            payload.channel_id,
            top_record_id,
        )

        count += 1
        if count < 10:
            return

        content = f"{count} {self.upper_emoji_converter(count)} <#{payload.channel_id}>"
        top_record_channel = self.bot.get_channel(utils.TOP_RECORDS)

        if not top_record_id:
            original_msg = await self.bot.get_channel(payload.channel_id).fetch_message(
                payload.message_id
            )
            if not original_msg.embeds:
                return
            embed = original_msg.embeds[0]
            embed.add_field(name="Original", value=f"[Jump!]({original_msg.jump_url})")
            embed.colour = discord.Color.gold()

            top_record_msg = await top_record_channel.send(content, embed=embed)
            query = """UPDATE top_records SET top_record_id = $1 WHERE original_message_id = $2 AND channel_id = $3;"""
            await self.bot.database.set(
                query, top_record_msg.id, payload.message_id, payload.channel_id
            )
        else:
            await top_record_channel.get_partial_message(top_record_id).edit(
                content=content
            )

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
        await self.bot.database.set(
            "INSERT INTO users VALUES ($1, $2, true) ON CONFLICT DO NOTHING;",
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
