from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils
import views

if typing.TYPE_CHECKING:
    import core
    from core import DoomItx


class Records(commands.Cog):
    """Records"""

    def __init__(self, bot: core.Doom):
        self.bot = bot
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                **utils.personal_records_c,
                callback=self.pr_context_callback,
                guild_ids=[utils.GUILD_ID],
            )
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                **utils.world_records_c,
                callback=self.wr_context_callback,
                guild_ids=[utils.GUILD_ID],
            )
        )

    @app_commands.command(**utils.submit_record)
    @app_commands.describe(**utils.submit_record_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.choices(rating=utils.ALL_STARS_CHOICES)
    async def submit_record(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
        record: app_commands.Transform[float, utils.RecordTransformer],
        screenshot: discord.Attachment,
        video: app_commands.Transform[str, utils.URLTransformer] | None,
        rating: int | None,
    ) -> None:
        await itx.response.defer(ephemeral=False)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        if level_name not in itx.client.map_cache[map_code]["levels"]:
            raise utils.InvalidMapLevelError

        if search := [
            x
            async for x in itx.client.database.get(
                "SELECT record, screenshot, video, verified, m.map_name "
                "FROM records r LEFT JOIN maps m on r.map_code = m.map_code "
                "WHERE r.map_code=$1 AND level_name=$2 AND user_id=$3;",
                map_code,
                level_name,
                itx.user.id,
            )
        ]:
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

        old_hidden_id = await self.bot.database.set_return_val(
            """
            DELETE FROM records_queue
            WHERE map_code = $1
            AND user_id = $2
            AND level_name = $3
            RETURNING hidden_id;
            """,
            map_code,
            itx.user.id,
            level_name,
        )
        if old_hidden_id:
            await itx.guild.get_channel(utils.VERIFICATION_QUEUE).get_partial_message(
                old_hidden_id
            ).delete()

        view = views.VerificationView()
        await verification_msg.edit(view=view)
        await itx.client.database.set(
            """
            INSERT INTO records_queue
            (map_code, user_id, level_name, record, screenshot,
            video, message_id, channel_id, hidden_id, rating) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            # ON CONFLICT (map_code, user_id, level_name)
            # DO UPDATE SET record = EXCLUDED.record, screenshot = EXCLUDED.screenshot,
            # video = EXCLUDED.video, message_id = EXCLUDED.message_id, channel_id = EXCLUDED.channel_id,
            # hidden_id = EXCLUDED.hidden_id, rating = EXCLUDED.rating
            ,
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

    @app_commands.command(**utils.leaderboard)
    @app_commands.describe(**utils.leaderboard_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def view_records(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
        verified: bool | None = False,
    ) -> None:
        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        query = """
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
        WHERE map_code = $1 AND
            ($4::boolean IS FALSE OR verified = TRUE) AND
            ($2::boolean IS NOT NULL OR rank_num = 1) AND
            ($3::text IS NULL OR level_name = $3)
        ORDER BY substr(level_name, 1, 5) <> 'Level', level_name;
        """

        records = [
            x
            async for x in itx.client.database.get(
                query, map_code, bool(level_name), level_name, verified
            )
        ]
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

    @app_commands.command(**utils.personal_records)
    @app_commands.describe(**utils.personal_records_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def personal_records_slash(
        self,
        itx: DoomItx,
        user: discord.Member | discord.User | None = None,
        wr_only: bool | None = None,
    ):
        await self._personal_records(itx, user, wr_only)

    async def pr_context_callback(self, itx: DoomItx, user: discord.Member):
        await self._personal_records(itx, user, False)

    async def wr_context_callback(self, itx: DoomItx, user: discord.Member):
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

    @app_commands.command(name="verification-stats")
    @app_commands.describe(**utils.u_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def verification_stats(
        self,
        itx: DoomItx,
        user: app_commands.Transform[int, utils.UserTransformer] | None = None,
    ):
        await itx.response.defer(ephemeral=True)
        if user:
            res = await itx.client.database.get_one(
                """
                SELECT v.user_id, amount, nickname
                FROM verification_counts v
                         LEFT JOIN users u on v.user_id = u.user_id
                WHERE v.user_id = $1;
                """,
                user,
            )
            await itx.edit_original_response(
                content=f"{res.nickname} has **{res.amount}** verifications!"
            )
        else:
            res = [
                x
                async for x in itx.client.database.get(
                    """
                SELECT v.user_id,
                       amount,
                       nickname,
                       RANK() OVER (
                           ORDER BY amount DESC
                           ) rank
                FROM verification_counts v
                         LEFT JOIN users u on v.user_id = u.user_id
                ORDER BY amount DESC;
                """,
                )
            ]
            leaderboard = "".join(
                f"`{utils.make_ordinal(record.rank):^6}` `{record.amount:^6}` `{record.nickname}`\n"
                for record in res
            )
            await itx.edit_original_response(content=leaderboard)


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Records(bot))
