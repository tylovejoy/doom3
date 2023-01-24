from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs
import utils
import views

if typing.TYPE_CHECKING:
    import core


class Records(commands.Cog):
    """Records"""

    def __init__(self, bot: core.Doom):
        self.bot = bot
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name="personal-records",
                callback=self.pr_context_callback,
                guild_ids=[utils.GUILD_ID],
            )
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name="world-records",
                callback=self.wr_context_callback,
                guild_ids=[utils.GUILD_ID],
            )
        )

    @app_commands.command(name="submit-record")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(
        map_code=cogs.map_codes_autocomplete, level_name=cogs.map_levels_autocomplete
    )
    @app_commands.choices(rating=utils.ALL_STARS_CHOICES)
    async def submit_record(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
        record: app_commands.Transform[float, utils.RecordTransformer],
        screenshot: discord.Attachment,
        video: app_commands.Transform[str, utils.URLTransformer] | None,
        rating: int | None,
    ) -> None:
        """
        Submit a record to the database. Video proof is required for full verification!

        Args:
            itx: Interaction
            map_code: Overwatch share code
            level_name: Map level name
            record: Record in HH:MM:SS.ss format
            screenshot: Screenshot of completion
            video: Video of play through. REQUIRED FOR FULL VERIFICATION!
            rating: What would you rate the quality of this level?
        """
        await itx.response.defer(ephemeral=False)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        if level_name not in itx.client.map_cache[map_code]["levels"]:
            raise utils.InvalidMapLevelError

        search = [
            x
            async for x in itx.client.database.get(
                "SELECT record, screenshot, video, verified, m.map_name "
                "FROM records r LEFT JOIN maps m on r.map_code = m.map_code "
                "WHERE r.map_code=$1 AND level_name=$2 AND user_id=$3;",
                map_code,
                level_name,
                itx.user.id,
            )
        ]

        if search:
            search = search[0]
            if search.record < record:
                raise utils.RecordNotFasterError

        user = itx.client.all_users[itx.user.id]

        view = views.Confirm(
            itx,
            f"{utils.TIME} Waiting for verification...\n",
        )
        new_screenshot = await screenshot.to_file(filename="image.png")

        embed = utils.record_embed(
            {
                "map_code": map_code,
                "map_level": level_name,
                "record": utils.pretty_record(record),
                "video": video,
                "user_name": user["nickname"],
                "user_url": itx.user.display_avatar.url,
            }
        )
        channel_msg = await itx.edit_original_response(
            content=f"{itx.user.mention}, is this correct?",
            embed=embed,
            view=view,
            attachments=[new_screenshot],
        )
        await view.wait()
        if not view.value:
            return
        new_screenshot2 = await screenshot.to_file(filename="image.png")
        verification_msg = await itx.client.get_channel(utils.VERIFICATION_QUEUE).send(
            embed=embed, file=new_screenshot2
        )

        view = views.VerificationView()
        await verification_msg.edit(view=view)
        await itx.client.database.set(
            """
            INSERT INTO records_queue 
            (map_code, user_id, level_name, record, screenshot,
            video, message_id, channel_id, hidden_id, rating) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            map_code,
            itx.user.id,
            level_name,
            record,
            channel_msg.jump_url,
            video,
            channel_msg.id,
            channel_msg.channel.id,
            verification_msg.id,
            rating,
        )

    @app_commands.command(name="leaderboard")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(
        map_code=cogs.map_codes_autocomplete, level_name=cogs.map_levels_autocomplete
    )
    async def view_records(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
        verified: bool | None = False,
    ) -> None:
        """
        View leaderboard of any map in the database.

        Args:
            itx: Interaction
            map_code: Overwatch share code
            level_name: Name of level
            verified: Only show fully verified video submissions.
        """
        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        query = f"""
        SELECT * FROM (
        SELECT u.nickname, 
               level_name, 
               record, 
               screenshot,
               video, 
               verified,
               r.map_code,
               r.channel_id,
               r.message_id,
               m.map_name,
        RANK() OVER (
            PARTITION BY level_name
            ORDER BY record
        ) rank_num
        FROM records r
            LEFT JOIN users u on r.user_id = u.user_id
            LEFT JOIN maps m on m.map_code = r.map_code
        ) as ranks
        WHERE map_code=$1 AND
        ($1 IS FALSE OR verified=TRUE) AND
        ($2 IS NOT NULL OR rank_num=1) AND
        ($2 IS NULL OR level_name=$2)
        ORDER BY substr(level_name, 1, 5) <> 'Level', level_name;
        """
        args = [map_code]
        if level_name:
            if level_name not in itx.client.map_cache[map_code]["levels"]:
                raise utils.InvalidMapLevelError
            args.append(level_name)

        records = [x async for x in itx.client.database.get(query, *args)]
        if not records:
            raise utils.NoRecordsFoundError

        if level_name:
            embeds = utils.all_levels_records_embed(
                records, f"Leaderboard - {map_code} - {level_name}", True
            )
        else:
            embeds = utils.all_levels_records_embed(
                records, f"Leaderboard - {map_code}"
            )

        view = views.Paginator(embeds, itx.user)
        await view.start(itx)

    @app_commands.command(name="personal-records")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def personal_records_slash(
        self,
        itx: core.Interaction[core.Doom],
        user: discord.Member | discord.User | None = None,
        wr_only: bool | None = None,
    ):
        await self._personal_records(itx, user, wr_only)

    async def pr_context_callback(
        self, itx: core.Interaction[core.Doom], user: discord.Member
    ):
        await self._personal_records(itx, user, False)

    async def wr_context_callback(
        self, itx: core.Interaction[core.Doom], user: discord.Member
    ):
        await self._personal_records(itx, user, True)

    @staticmethod
    async def _personal_records(itx, user, wr_only):
        await itx.response.defer(ephemeral=True)
        if not user:
            user = itx.user
        query = """
        SELECT *
        FROM (SELECT u.nickname,
                     r.user_id,
                     level_name,
                     record,
                     screenshot,
                     video,
                     verified,
                     r.map_code,
                     r.channel_id,
                     r.message_id,
                     m.map_name,
                     m.creators,
                     RANK() OVER (
                         PARTITION BY level_name
                         ORDER BY record
                         ) rank_num
              FROM records r
                       LEFT JOIN users u on r.user_id = u.user_id
                       LEFT JOIN (SELECT m.map_code,
                                         m.map_name,
                                         string_agg(distinct (nickname), ', ') as creators
                                  FROM maps m
                                           LEFT JOIN map_creators mc on m.map_code = mc.map_code
                                           LEFT JOIN users u on mc.user_id = u.user_id
                                  GROUP BY m.map_code, m.map_name) m
                                 on m.map_code = r.map_code) as ranks
        WHERE user_id = $1 AND ($2 IS FALSE OR rank_num = 1)
        ORDER BY map_code, substr(level_name, 1, 5) <> 'Level', level_name;
        """
        records = [x async for x in itx.client.database.get(query, user.id, wr_only)]
        if not records:
            raise utils.NoRecordsFoundError
        embeds = utils.pr_records_embed(
            records,
            f"Personal {'World ' if wr_only else ''}Records | {itx.client.all_users[user.id]['nickname']}",
        )
        view = views.Paginator(embeds, itx.user)
        await view.start(itx)


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Records(bot))
