from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import asyncpg
import discord

from .embeds import EmbedFormatter
from .stars import create_stars

if TYPE_CHECKING:
    from core import Doom


_MAPS_BASE_URL = "https://bkan0n.com/assets/images/map_banners/"


@dataclass
class MapMetadata:
    NAME: str
    COLOR: discord.Color
    IMAGE_URL: str = ""

    def __post_init__(self):
        self.IMAGE_URL = _MAPS_BASE_URL + self._remove_extra_chars(self.NAME) + ".png"

    def _remove_extra_chars(self, string: str):
        return string.lower().replace(" ", "").replace(":", "").replace("'", "")


@dataclass
class Map:
    bot: Doom
    map_code: str
    map_name: str
    primary_creator: int | None = None
    image: discord.Attachment | None = None
    image_url: str = ""
    description: str = ""
    creators: str = ""
    map_type: list[str] = field(default_factory=list)
    levels: list[str] = field(default_factory=list)
    official: bool = False
    rating: int | float | None = None
    level: str = ""  # for random level
    avg_rating: int | float | None = None  # for random level
    creators_ids: list[int] = field(default_factory=list)

    def set_map_types(self, map_types: list[str]):
        self.map_type = map_types

    def set_levels(self, levels: list[str]):
        self.levels = levels

    def set_description(self, description: str | None):
        if description:
            self.description = description

    def preview_embed_to_dict(self):
        return {"Code": self.map_code, "Map": self.map_name, "Type": ", ".join(self.map_type), "Desc": self.description}

    def build_preview_embed(self):
        color = discord.Color.from_str(f"#{self.bot.map_metadata[self.map_name].COLOR}")
        embed = discord.Embed(
            title="Map Submission - Confirmation",
            description=EmbedFormatter.format(self.preview_embed_to_dict()),
            color=color,
        )
        if self.image:
            url = "attachment://image.png"
        else:
            url = self.bot.map_metadata[self.map_name].IMAGE_URL
        embed.set_image(url=url)
        assert self.bot.user
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(
            name="Level Names (Each should be on separate lines)",
            value="\n".join(self.levels),
        )
        return embed

    @staticmethod
    def display_official(official: bool) -> str:
        return (
            (
                "┃<:_:998055526468423700><:_:998055528355860511><:_:998055530440437840>"
                "<:_:998055532030079078><:_:998055534068510750><:_:998055536346021898>\n"
                "┃<:_:998055527412142100><:_:998055529219887154><:_:998055531346415656>"
                "<:_:998055533225455716><:_:998055534999654480><:_:998055537432338532>\n"
            )
            if official
            else ""
        )

    def map_search_embed_to_dict(self):
        return {
            "name": self.map_code,
            "value": (
                f"{self.display_official(self.official)}"
                f"`  Rating ` {create_stars(self.rating)}\n"
                f"` Creator ` {discord.utils.escape_markdown(self.creators)}\n"
                f"`     Map ` {self.map_name}\n"
                f"`    Type ` {self.map_type}\n"
                f"`    Desc ` {self.description}"
            ),
        }

    async def commit(self):
        async with self.bot.database.pool.acquire() as conn:
            conn: asyncpg.Connection
            async with conn.transaction():
                await self.bot.database.insert_map_data(
                    self.map_code,
                    self.map_name,
                    self.map_type,
                    self.description,
                    self.image.url if self.image else "",
                    connection=conn,
                )
                await self.bot.database.add_creator_to_map_code(self.primary_creator, self.map_code, connection=conn)
                await self.bot.database.add_multiple_map_levels(self.map_code, self.levels, connection=conn)
