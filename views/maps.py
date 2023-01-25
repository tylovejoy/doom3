from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

import utils
import utils.utils
import views

if TYPE_CHECKING:
    from core import DoomItx


class MapSubmit(discord.ui.Modal, title="MapSubmit"):
    desc = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph)
    levels = discord.ui.TextInput(
        label="Level Names",
        style=discord.TextStyle.paragraph,
        placeholder=(
            "Add all level names, each on a new line.\n"
            "Level 1\n"
            "Level 2\n"
            "Trial of Agony\n"
            "Speedrunning Death\n"
            "Etc.\n"
        ),
    )
    data: dict[str, str] | None = None

    async def on_submit(self, itx: DoomItx):
        view = views.Confirm(
            itx,
            preceding_items={
                "map_type": views.MapTypeSelect(
                    [
                        discord.SelectOption(label=x.name, value=x.name)
                        for x in itx.client.map_types_choices
                    ]
                )
            },
            ephemeral=True,
        )
        await itx.response.send_message(view=view, ephemeral=True)
        await view.wait()

        if not view.value:
            return
        map_types = [x for x in view.map_type.values]
        levels = list(
            map(str.strip, filter(lambda x: bool(x), self.levels.value.split("\n")))
        )

        embed = utils.DoomEmbed(
            title="Map Submission - Confirmation",
            description=(
                f"┣ `Code` {self.data['map_code']}\n"
                f"┣ `Map` {self.data['map_name']}\n"
                f"┣ `Type` {', '.join(map_types)}\n"
                f"┣ `Desc` {self.desc}\n"
                f"┗ `Levels` {', '.join(levels)}\n"
            ),
        )
        embed = utils.set_embed_thumbnail_maps(self.data["map_name"], embed)
        view = views.Confirm(itx, ephemeral=True)
        await itx.edit_original_response(
            content="Is this correct?", view=view, embed=embed
        )
        await view.wait()
        if not view.value:
            return
        await itx.client.database.set(
            (
                "INSERT INTO maps "
                '(map_name, map_type, map_code, "desc") '
                "VALUES ($1, $2, $3, $4); "
            ),
            self.data["map_name"],
            map_types,
            self.data["map_code"],
            self.desc.value,
        )
        await itx.client.database.set(
            "INSERT INTO map_creators (map_code, user_id) VALUES ($1, $2); ",
            self.data["map_code"],
            itx.user.id,
        )
        await itx.client.database.set_many(
            "INSERT INTO map_levels (map_code, level) VALUES ($1, $2)",
            [(self.data["map_code"], x) for x in levels],
        )

        # Cache data
        itx.client.map_cache[self.data["map_code"]] = utils.MapCacheData(
            levels=levels,
            user_ids=[itx.user.id],
            choices=[app_commands.Choice(name=x, value=x) for x in levels],
        )
        # Cache map code choice
        itx.client.map_codes_choices.append(
            app_commands.Choice(name=self.data["map_code"], value=self.data["map_code"])
        )

        embed.title = f"New Map by {self.data['creator_name']}"
        new_map = await itx.guild.get_channel(utils.NEW_MAPS).send(embed=embed)
        await new_map.create_thread(name=f"Discuss {self.data['map_code']} here.")
        map_maker = itx.guild.get_role(746167804121841744)
        if map_maker not in itx.user.roles:
            await itx.user.add_roles(map_maker)

        reminder = (
            "**Friendly Reminder**\n\n"
            "You have access to a few commands to edit the map once it has been submitted.\n\n"
            "Do you have multiple creators on this map? Add them or remove them with these commands:\n"
            "`/map-maker creator add`\n"
            "`/map-maker creator remove`\n\n"
            "Do you want to edit a level name in the bot? Use one of these:\n"
            "`/map-maker level add`\n"
            "`/map-maker level remove`\n"
            "`/map-maker level edit`\n"
        )
        await itx.user.send(reminder)


class MapTypeSelect(discord.ui.Select):
    def __init__(self, options) -> None:
        super().__init__(
            options=options,
            placeholder="Map type(s)?",
            max_values=len(options),
        )

    async def callback(self, itx: DoomItx):
        await itx.response.defer(ephemeral=True)
        for x in self.options:
            x.default = x.value in self.values
        await self.view.map_submit_enable()
