from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from core import DoomItx

import database
import utils


class RejectReasonModal(discord.ui.Modal, title="Rejection Reason"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long)

    async def on_submit(self, itx: DoomItx):
        await itx.response.send_message("Sending reason to user.", ephemeral=True)


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:accept",
    )
    async def green(self, itx: DoomItx, button: discord.ui.Button):
        await self.verification(itx, True)

    @discord.ui.button(
        label="Reject",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:reject",
    )
    async def red(self, itx: DoomItx, button: discord.ui.Button):
        modal = RejectReasonModal()
        await itx.response.send_modal(modal)
        await modal.wait()
        await self.verification(itx, False, modal.reason.value)

    async def verification(
        self,
        itx: DoomItx,
        verified: bool,
        rejection: str | None = None,
    ):
        """Verify a record."""
        query = "SELECT * FROM records WHERE hidden_id=$1"
        row = await itx.client.database.fetchrow(
            query,
            itx.message.id,
        )
        original_message = await self.find_original_message(itx, row["channel_id"], row["message_id"])
        if not original_message:
            return

        user = itx.guild.get_member(row["user_id"])

        if verified:
            data = self.accepted(itx, row)
            await self.increment_verification_count(itx)
            query = "UPDATE records SET verified=TRUE, hidden_id=null WHERE hidden_id=$1;"
            await itx.client.database.execute(
                query,
                itx.message.id,
            )
        else:
            data = self.rejected(itx, row, rejection)
            query = "DELETE FROM records WHERE user_id=$1 AND map_code=$2 AND level_name=$3;"
            await itx.client.database.execute(
                query,
                row["user_id"],
                row["map_code"],
                row["level_name"],
            )
        await original_message.edit(content=data["edit"])
        query = "SELECT alertable FROM users WHERE user_id=$1;"
        if await itx.client.database.fetchval(
            query,
            row["user_id"],
        ):
            try:
                await user.send(
                    "`- - - - - - - - - - - - - -`\n" + data["direct_message"] + "\n`- - - - - - - - - - - - - -`"
                )
            except Exception as e:
                itx.client.logger.info(e)
        await self.stop_view(itx)

    async def stop_view(self, itx: DoomItx):
        self.stop()
        await itx.message.delete()

    @staticmethod
    async def increment_verification_count(itx: DoomItx):
        query = """
            INSERT INTO verification_counts (user_id, amount)
            VALUES ($1, 1)
            ON CONFLICT (user_id)
                DO UPDATE SET amount = verification_counts.amount + 1;
        """
        await itx.client.database.execute(
            query,
            itx.user.id,
        )

    @staticmethod
    async def find_original_message(itx: DoomItx, channel_id: int, message_id: int) -> discord.Message | None:
        """Try to fetch message from either Records channel."""
        try:
            res = await itx.guild.get_channel(channel_id).fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException):
            res = None
        return res

    @staticmethod
    def accepted(
        itx: DoomItx,
        search: database.DotRecord,
    ) -> dict[str, str]:
        """Data for verified records."""

        record = (
            f"**Record:** {utils.pretty_record(search['record'])} "
            f"{utils.VERIFIED if search['video'] else utils.HALF_VERIFIED}"
        )
        if search["video"]:
            edit = f"{utils.VERIFIED} Complete verification by {itx.user.mention}!"
        else:
            edit = f"{utils.HALF_VERIFIED} Partial verification by {itx.user.mention}! " f"No video proof supplied."
        message = itx.guild.get_channel(search["channel_id"]).get_partial_message(search["message_id"])
        return {
            "edit": edit,
            "direct_message": (
                f"**Map Code:** {search['map_code']}\n"
                f"**Level:** {search['level_name']}\n"
                + record
                + f"\nVerified by {itx.user.mention}!\n{message.jump_url}\n\n"
                + ALERT
            ),
        }

    @staticmethod
    def rejected(
        itx: DoomItx,
        search: database.DotRecord,
        rejection: str,
    ) -> dict[str, str]:
        """Data for rejected records."""

        record = f"**Record:** {utils.pretty_record(search['record'])}\n"

        return {
            "edit": (f"{utils.UNVERIFIED} " f"Rejected by {itx.user.mention}!"),
            "direct_message": (
                f"**Map Code:** {search['map_code']}\n" + record + f"Your record got {utils.UNVERIFIED} "
                f"rejected by {itx.user.mention}!\n\n"
                f"**Reason:** {rejection}\n\n" + ALERT
            ),
        }


ALERT = (
    "Don't like these alerts? "
    "Turn it off by using the command `/alerts false`.\n"
    "You can change your display name "
    "for records in the bot with the command `/name`!"
)
