from __future__ import annotations

import re

import discord


class DoomEmbed(discord.Embed):
    def __init__(
        self,
        *,
        color: int | discord.Color | None = None,
        title: str | None = None,
        url: str | None = None,
        description: str | None = None,
        thumbnail: str | None = None,
        image: str | None = None,
    ):
        if not color:
            color = discord.Color.from_rgb(1, 1, 1)

        super().__init__(color=color, title=title, url=url, description=description)

        if not thumbnail:
            self.set_thumbnail(url="https://i.imgur.com/kxjwdYi.png")
        else:
            self.set_thumbnail(url=thumbnail)

        if not image:
            self.set_image(url="https://i.imgur.com/YhJokJW.png")
        else:
            self.set_image(url=image)


class ErrorEmbed(DoomEmbed):
    def __init__(
        self,
        *,
        description: str,
        unknown: bool = False,
    ):
        if unknown:
            super().__init__(
                title="Uh oh! Something went wrong.",
                description=description,
                color=discord.Color.red(),
                thumbnail="http://bkan0n.com/assets/images/icons/error.png",
            )
        else:
            super().__init__(
                title="What happened?",
                description=description,
                color=discord.Color.yellow(),
            )

            self.set_footer(text="If you have any questions, message nebula#6662")


def set_embed_thumbnail_maps(
    map_name: str, embed: discord.Embed
) -> discord.Embed | DoomEmbed:
    """
    The embed_thumbnail_setter function takes a map name
    and an embed object as parameters.
    It then uses the map name to search for a thumbnail image
    and sets that image as the embed's thumbnail.
    Args:
        map_name (str): Set the map name to be used in the embed
        embed (discord.Embed): Set the thumbnail of the embed
    Returns:
        The embed object with the thumbnail set to a map's image
    """
    map_name = re.sub(r"[:'\s]", "", map_name).lower()
    embed.set_thumbnail(url=f"http://bkan0n.com/assets/images/maps/{map_name}.png")
    return embed
