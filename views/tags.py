from __future__ import annotations

import typing

import discord.ui
from discord import app_commands

import views
from cogs.tags import NUMBER_EMOJI

if typing.TYPE_CHECKING:
    from core import DoomItx


class TagFuzzView(discord.ui.View):
    def __init__(self, itx: DoomItx, options: list[str]):
        super().__init__(timeout=None)
        self.itx = itx
        self.matches.options = [
            discord.SelectOption(label=x, value=x, emoji=NUMBER_EMOJI[i + 1]) for i, x in enumerate(options)
        ]

    @discord.ui.select()
    async def matches(self, itx: DoomItx, select: discord.ui.Select):
        await itx.response.defer()
        query = "SELECT * FROM tags WHERE name=$1;"
        tag = await itx.client.database.fetchrow(query, select.values[0])
        await itx.edit_original_response(content=f"**{tag['name']}**\n\n{tag['value']}", view=None, embed=None)


class TagCreate(discord.ui.Modal, title="Create Tag"):
    name = discord.ui.TextInput(label="Name")
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph)

    async def on_submit(self, itx: DoomItx):
        view = views.Confirm(itx)
        await itx.response.send_message(content=f"Is this correct?\n\n{self.name}\n{self.value}", view=view)
        await view.wait()
        if not view.value:
            return
        query = "INSERT INTO tags (name, value) VALUES ($1, $2);"
        await itx.client.database.execute(
            query,
            self.name.value,
            self.value.value,
        )
        itx.client.tag_cache.append(self.name.value)
        itx.client.tag_choices.append(app_commands.Choice(name=self.name.value, value=self.name.value))
