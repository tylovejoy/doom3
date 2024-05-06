from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

import utils

if TYPE_CHECKING:
    import core

PLAYTEST_CHANNEL = 1230921381550624819

tags_map = {
    "Time Attack": 1230921437154512976,
    "Mildcore": 1230921453000593530,
    "Hardcore": 1230921474681081886,
    "Bonus": 1230921498370248744,
    "Open": 1230921514547941376,
    "Closed": 1230921533002747987,
}


class PlaytestButton(
    discord.ui.DynamicItem[discord.ui.Button], template=r"button:user:(?P<id>[0-9]+)"
):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            discord.ui.Button(
                label="Finish Playtesting",
                style=discord.ButtonStyle.red,
                custom_id=f"button:user:{user_id}",
                emoji="\N{THUMBS UP SIGN}",
            )
        )
        self.user_id: int = user_id

    # This is called when the button is clicked and the custom_id matches the template.
    @classmethod
    async def from_custom_id(
        cls,
        interaction: discord.Interaction,
        item: discord.ui.Button,
        match: re.Match[str],
        /,
    ):
        user_id = int(match["id"])
        return cls(user_id)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the user who created the button to interact with it.
        return interaction.user.id == self.user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Closing playtest.")
        channel: discord.Thread = interaction.channel
        closed_tag = channel.parent.get_tag(tags_map["Closed"])
        tags = [tag for tag in channel.applied_tags if tag.name != "Open"]

        await channel.edit(
            applied_tags=tags + [closed_tag],
            locked=True,
            archived=True,
        )


class Playtesting(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command(
        name="submit-playtest", description="Submit a level into playtesting."
    )
    @app_commands.guilds(195387617972322306, utils.GUILD_ID)
    async def submit_playtest(
        self,
        itx: core.DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        map_name: app_commands.Transform[str, utils.MapNameTransformer],
        category: Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"],
        level_name: str,
    ):
        """Submit a level into playtesting."""
        await itx.response.send_message(
            "Sending to playtest. Please wait.", ephemeral=True
        )
        channel: discord.ForumChannel = itx.guild.get_channel(PLAYTEST_CHANNEL)
        chosen_tag = channel.get_tag(tags_map[category])
        open_tag = channel.get_tag(tags_map["Open"])
        name = (
            f"{map_code} - {level_name} by "
            f"{itx.client.all_users[itx.user.id]['nickname']} [{map_name}]"
        )
        content = f"{itx.user.mention}, please add any additional information here.\n"
        view = discord.ui.View(timeout=None)
        view.add_item(PlaytestButton(itx.user.id))
        thread = await channel.create_thread(
            name=name,
            applied_tags=[chosen_tag, open_tag],
            content=content,
            view=view,
        )
        try:
            await thread.message.pin()
        except discord.HTTPException:
            pass
