from __future__ import annotations

import typing

import discord.ui

import database
import utils

if typing.TYPE_CHECKING:
    from core import DoomItx


class PageNumModal(discord.ui.Modal, title="Enter Page Number"):
    number = discord.ui.TextInput(label="Number")

    async def on_submit(self, itx: DoomItx):
        await itx.response.defer(ephemeral=True)


class ExerciseView(discord.ui.View):
    def __init__(self, itx: DoomItx, all_exercises: list[database.DotRecord]):
        super().__init__()
        self.itx = itx
        self.all = all_exercises
        self.cur_page = self.all[:10]
        self.page_num = 0
        self.max_page = 0

    @discord.ui.select(
        placeholder="Select an exercise.",
        options=[discord.SelectOption(label="Loading...", value="0")],
    )
    async def exercises(self, itx: DoomItx, select: discord.SelectMenu):
        await itx.response.defer(ephemeral=True)
        selected = self.cur_page[int(self.exercises.values[0])]
        embed = utils.DoomEmbed(
            title=selected.name,
            description=(
                f"Location: {selected.location}\n"
                f"Target Muscle: {selected.target}\n"
                f"Equipment: {selected.equipment}\n"
            ),
            image=selected.url,
        )
        await self.itx.edit_original_response(embed=embed)

    @discord.ui.button(emoji="⬅")
    async def prev_page(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        self.page_num -= 1
        if self.page_num < 0:
            self.page_num = self.max_page - 1
        self.page_num_button.label = f"{self.page_num + 1} / {self.max_page}"
        await self._set_options()

    @discord.ui.button(label="...")
    async def page_num_button(self, itx: DoomItx, button: discord.Button):
        modal = PageNumModal()
        await itx.response.send_modal(modal)
        await modal.wait()

        try:
            value = int(modal.number.value)
        except ValueError:
            value = None

        if value is not None and 0 < value <= self.max_page:
            self.page_num = value - 1
        else:
            self.page_num = 0
        self.page_num_button.label = f"{self.page_num + 1} / {self.max_page}"
        await self._set_options()

    @discord.ui.button(emoji="➡")
    async def next_page(self, itx: DoomItx, button: discord.Button):
        await itx.response.defer(ephemeral=True)
        self.page_num += 1
        if self.page_num > self.max_page - 1:
            self.page_num = 0
        self.page_num_button.label = f"{self.page_num + 1} / {self.max_page}"
        await self._set_options()

    async def start(self):
        self.max_page = len(self.all) // 10
        if len(self.all) / 10 != len(self.all) // 10:
            self.max_page += 1
        self.page_num_button.label = f"{self.page_num + 1} / {self.max_page}"
        await self._set_options()
        await self.wait()

    async def _set_options(self):
        self.cur_page = self.all[
            (self.page_num + 1) * 10 - 10 : (self.page_num + 1) * 10
        ]
        self.exercises.options = [
            discord.SelectOption(label=x.name, value=str(i))
            for i, x in enumerate(self.cur_page)
        ]
        await self.itx.edit_original_response(view=self)

    async def _create_embed(self):
        ...
