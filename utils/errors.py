from __future__ import annotations

import io
import traceback
import typing

import discord
from discord import app_commands

import utils

if typing.TYPE_CHECKING:
    from core import Doom, Interaction


class BaseParkourException(Exception):
    def __init__(self):
        super().__init__(self.__doc__)


class DatabaseConnectionError(Exception):
    """Connection failed. This will be logged. Try again later."""


class IncorrectCodeFormatError(BaseParkourException):
    """Map code must be a valid Overwatch share code."""


async def on_app_command_error(
    interaction: Interaction[Doom], error: app_commands.errors.CommandInvokeError
):
    exception = getattr(error, "original", error)
    if isinstance(exception, utils.BaseParkourException):
        embed = utils.ErrorEmbed(description=str(exception))
        if interaction.response.is_done():
            await interaction.edit_original_response(
                embed=embed,
            )
        else:
            await interaction.response.send_message(
                embed=embed,
            )
    else:
        edit = (
            interaction.edit_original_response
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        embed = utils.ErrorEmbed(
            description=(
                "Unknown.\n"
                "It has been logged and sent to <@141372217677053952>.\n"
                "Please try again later."
            ),
            unknown=True,
        )
        await edit(
            embed=embed,
        )

        channel = interaction.client.get_channel(849878847310528523)

        command_name = f"**Command:** `{interaction.command.name}`\n"
        channel_name = f"**Channel:** `{interaction.channel}`\n"
        user_name = f"**User:** `{interaction.user}`"
        args = [
            f"┣ **{k}:** `{v}`\n" for k, v in interaction.namespace.__dict__.items()
        ]
        if args:
            args[-1] = "┗" + args[-1][1:]
        args_name = "**Args:**\n" + "".join(args)
        formatted_tb = "".join(
            traceback.format_exception(None, exception, exception.__traceback__)
        )
        if len(formatted_tb) < 1850:
            await channel.send(
                f"{command_name}{args_name}{channel_name}{user_name}\n```py\n"
                + formatted_tb
                + "\n```"
            )
        else:
            await channel.send(
                f"{command_name} {args_name} {channel_name} {user_name}",
                file=discord.File(
                    fp=io.BytesIO(
                        bytearray(
                            str(exception) + formatted_tb,
                            "utf-8",
                        )
                    ),
                    filename="error.log",
                ),
            )
    await utils.delete_interaction(interaction, minutes=15)
