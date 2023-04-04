from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.utils import MISSING

import utils
import utils.utils
import views

if TYPE_CHECKING:
    from core import DoomItx


_MAPS_BASE_URL = "http://207.244.249.145/assets/images/map_banners/"


@dataclass
class MapMetadata:
    NAME: str
    COLOR: discord.Color
    IMAGE_URL: str = ""

    def __post_init__(self):
        self.IMAGE_URL = _MAPS_BASE_URL + self._remove_extra_chars(self.NAME) + ".png"

    def _remove_extra_chars(self, string: str):
        return string.lower().replace(" ", "").replace(":", "").replace("'", "")


all_map_constants = [
    MapMetadata("Antarctic Peninsula", discord.Color.from_str("#29A0CC")),
    MapMetadata("Ayutthaya", discord.Color.gold()),
    MapMetadata("Black Forest", discord.Color.from_str("#94511C")),
    MapMetadata("Blizzard World", discord.Color.from_str("#39AAFF")),
    MapMetadata("Busan", discord.Color.from_str("#FF9F00")),
    MapMetadata("Castillo", discord.Color.from_str("#E13C3C")),
    MapMetadata("Chateau Guillard", discord.Color.from_str("#BCBCBC")),
    MapMetadata("Circuit Royal", discord.Color.from_str("#00008B")),
    MapMetadata("Colosseo", discord.Color.from_str("#BF7F00")),
    MapMetadata("Dorado", discord.Color.from_str("#008a8a")),
    MapMetadata("Ecopoint: Antarctica", discord.Color.from_str("#29A0CC")),
    MapMetadata("Eichenwalde", discord.Color.from_str("#53E500")),
    MapMetadata("Esperanca", discord.Color.from_str("#7BD751")),
    MapMetadata("Hanamura", discord.Color.from_str("#EF72A3")),
    MapMetadata("Havana", discord.Color.from_str("#00D45B")),
    MapMetadata("Hollywood", discord.Color.from_str("#FFFFFF")),
    MapMetadata("Horizon Lunar Colony ", discord.Color.from_str("#000000")),
    MapMetadata("Ilios", discord.Color.from_str("#008FDF")),
    MapMetadata("Junkertown", discord.Color.from_str("#EC9D00")),
    MapMetadata("Kanezaka", discord.Color.from_str("#DF3A4F")),
    MapMetadata("King's Row", discord.Color.from_str("#105687")),
    MapMetadata("Lijiang Tower", discord.Color.from_str("#169900")),
    MapMetadata("Malevento", discord.Color.from_str("#DDD816")),
    MapMetadata("Midtown", discord.Color.from_str("#BCBCBC")),
    MapMetadata("Necropolis", discord.Color.from_str("#409C00")),
    MapMetadata("Nepal", discord.Color.from_str("#93C0C7")),
    MapMetadata("New Queen Street", discord.Color.from_str("#CD1010")),
    MapMetadata("Numbani", discord.Color.from_str("#3F921B")),
    MapMetadata("Oasis", discord.Color.from_str("#C98600")),
    MapMetadata("Paraiso", discord.Color.from_str("#19FF00")),
    MapMetadata("Paris", discord.Color.from_str("#6260DA")),
    MapMetadata("Petra", discord.Color.from_str("#DDD816")),
    MapMetadata("Practice Range", discord.Color.from_str("#000000")),
    MapMetadata("Rialto", discord.Color.from_str("#21E788")),
    MapMetadata("Route 66", discord.Color.from_str("#FF9E2F")),
    MapMetadata("Shambali", discord.Color.from_str("#2986CC")),
    MapMetadata("Temple of Anubis", discord.Color.from_str("#D25E00")),
    MapMetadata("Volskaya Industries", discord.Color.from_str("#8822DC")),
    MapMetadata("Watchpoint: Gibraltar", discord.Color.from_str("#BCBCBC")),
    MapMetadata("Workshop Chamber", discord.Color.from_str("#000000")),
    MapMetadata("Workshop Expanse", discord.Color.from_str("#000000")),
    MapMetadata("Workshop Green Screen", discord.Color.from_str("#3BB143")),
    MapMetadata("Workshop Island", discord.Color.from_str("#000000")),
    MapMetadata("Framework", discord.Color.from_str("#000000")),
    MapMetadata("Tools", discord.Color.from_str("#000000")),
]

MAP_DATA: dict[str, MapMetadata] = {const.NAME: const for const in all_map_constants}


class MapSubmit(discord.ui.Modal, title="MapSubmit"):
    desc = discord.ui.TextInput(
        label="Description", style=discord.TextStyle.paragraph, required=False
    )
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
        map_types = list(view.map_type.values)
        levels = list(
            map(str.strip, filter(lambda x: bool(x), self.levels.value.split("\n")))
        )

        description = f"` Desc ` {self.desc}\n" if self.desc.value else ""
        embed = utils.DoomEmbed(
            title="Map Submission - Confirmation",
            description=f">>> ` Code ` {self.data['map_code']}\n`  Map ` {self.data['map_name']}\n` Type ` {', '.join(map_types)}\n{description}",
            color=MAP_DATA.get(
                self.data["map_name"], discord.Color.from_str("#000000")
            ).COLOR,
            image=MAP_DATA.get(self.data["map_name"], None).IMAGE_URL,
            thumbnail=itx.client.user.display_avatar.url,
        )
        embed.add_field(
            name="Level Names (Each should be on separate lines)",
            value="\n".join(levels),
        )
        # embed = utils.set_embed_thumbnail_maps(self.data["map_name"], embed)
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
        embed.remove_field(0)
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
