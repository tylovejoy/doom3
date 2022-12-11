from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    import core

import database
import utils


class RejectReasonModal(discord.ui.Modal, title="Rejection Reason"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long)

    async def on_submit(self, itx: core.Interaction[core.Doom]):
        await itx.response.send_message("Sending reason to user.", ephemeral=True)


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:accept",
    )
    async def green(self, itx: core.Interaction[core.Doom], button: discord.ui.Button):
        await self.verification(itx, True)

    @discord.ui.button(
        label="Reject",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:reject",
    )
    async def red(self, itx: core.Interaction[core.Doom], button: discord.ui.Button):
        modal = RejectReasonModal()
        await itx.response.send_modal(modal)
        await modal.wait()
        await self.verification(itx, False, modal.reason.value)

    async def verification(
        self,
        itx: core.Interaction[core.Doom],
        verified: bool,
        rejection: str | None = None,
    ):
        """Verify a record."""
        search = [
            x
            async for x in itx.client.database.get(
                "SELECT * FROM records_queue WHERE hidden_id=$1",
                itx.message.id,
            )
        ][0]
        original_message = await self.find_original_message(
            itx, search.channel_id, search.message_id
        )
        if not original_message:
            return

        user = itx.guild.get_member(search.user_id)

        if verified:
            data = self.accepted(itx, search)
            await itx.client.database.set(
                """
                INSERT INTO records (map_code, user_id, level_name, record, screenshot, video, verified, message_id, channel_id) 
                VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (map_code, user_id, level_name) DO UPDATE SET record=$4;
                """,
                search.map_code,
                search.user_id,
                search.level_name,
                search.record,
                search.screenshot,
                search.video,
                bool(search.video),
                search.message_id,
                search.channel_id,
            )
            await itx.client.database.set(
                """
                INSERT INTO map_level_ratings (map_code, level, user_id, rating) 
                VALUES($1, $2, $3, $4)
                ON CONFLICT (map_code, level, user_id) DO UPDATE SET rating=$4;
                """,
                search.map_code,
                search.level_name,
                search.user_id,
                search.rating,
            )
        else:
            data = self.rejected(itx, search, rejection)
        await original_message.edit(content=data["edit"])
        if [
            x
            async for x in itx.client.database.get(
                "SELECT alertable FROM users WHERE user_id=$1",
                search.user_id,
            )
        ][0].alertable:
            try:
                await user.send(
                    "`- - - - - - - - - - - - - -`\n"
                    + data["direct_message"]
                    + "\n`- - - - - - - - - - - - - -`"
                )
            except Exception as e:
                itx.client.logger.info(e)
        await self.stop_view(itx)

    async def stop_view(self, itx: core.Interaction[core.Doom]):
        self.stop()
        await itx.message.delete()
        await itx.client.database.set(
            "DELETE FROM records_queue WHERE hidden_id=$1",
            itx.message.id,
        )

    @staticmethod
    async def find_original_message(
        itx: core.Interaction[core.Doom], channel_id: int, message_id: int
    ) -> discord.Message | None:
        """Try to fetch message from either Records channel."""
        try:
            res = await itx.guild.get_channel(channel_id).fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException):
            res = None
        return res

    @staticmethod
    def accepted(
        itx: core.Interaction[core.Doom],
        search: database.DotRecord,
    ) -> dict[str, str]:
        """Data for verified records."""

        record = (
            f"**Record:** {utils.pretty_record(search.record)} "
            f"{utils.VERIFIED if search.video else utils.HALF_VERIFIED}"
        )
        if search.video:
            edit = f"{utils.VERIFIED} Complete verification by {itx.user.mention}!"
        else:
            edit = (
                f"{utils.HALF_VERIFIED} Partial verification by {itx.user.mention}! "
                f"No video proof supplied."
            )
        return {
            "edit": edit,
            "direct_message": (
                f"**Map Code:** {search.map_code}\n"
                + record
                + f"verified by {itx.user.mention}!\n\n"
                + ALERT
            ),
        }

    @staticmethod
    def rejected(
        itx: core.Interaction[core.Doom],
        search: database.DotRecord,
        rejection: str,
    ) -> dict[str, str]:
        """Data for rejected records."""

        record = f"**Record:** {utils.pretty_record(search.record)}\n"

        return {
            "edit": (f"{utils.UNVERIFIED} " f"Rejected by {itx.user.mention}!"),
            "direct_message": (
                f"**Map Code:** {search.map_code}\n"
                + record
                + f"Your record got {utils.UNVERIFIED} "
                f"rejected by {itx.user.mention}!\n\n"
                f"**Reason:** {rejection}\n\n" + ALERT
            ),
        }


ALERT = (
    # "Don't like these alerts? "
    # "Turn it off by using the command `/alerts false`.\n"
    "You can change your display name "
    "for records in the bot with the command `/name`!"
)
