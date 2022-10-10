from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs
import utils
import views

if typing.TYPE_CHECKING:
    import core


class Maps(commands.Cog):
    """Maps"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="submit-map")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(map_name=cogs.map_name_autocomplete)
    async def submit_map(
        self,
        interaction: core.Interaction[core.Doom],
        map_code: app_commands.Range[str, 4, 6],
        map_name: str,
    ) -> None:
        ...
        modal = views.MapSubmit()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="map-search")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def map_search(
        self,
        interaction: core.Interaction[core.Doom],
    ) -> None:
        await interaction.response.defer(ephemeral=False)
        embed = utils.DoomEmbed(title="Map Search")
        async for _map in interaction.client.database.get(
            """
            SELECT mc.map_code,
                   array_to_string(array_agg(map_type), ', ') as map_type,
                   map_name,
                   "desc",
                   official,
                   string_agg(nickname, ', ') as creators
            FROM maps
                     JOIN map_creators mc on maps.map_code = mc.map_code
                     JOIN users u on u.user_id = mc.creator_id
            GROUP BY map_type, mc.map_code, map_name, "desc", official;
            """,
        ):
            embed.add_field(
                name=f"{_map.map_code} - {_map.map_name}",
                value=(
                    self.display_official(_map.official)
                    + f"┣ **Creator(s):** {_map.creators}\n"
                    f"┣ **Type(s):** {_map.map_type}\n"
                    f"┗ **Description:** {_map.desc}\n"
                ),
            )
        await interaction.edit_original_response(embed=embed)

    @staticmethod
    def display_official(official: bool):
        return (
            (
                "┃<:_:998055526468423700>"
                "<:_:998055528355860511>"
                "<:_:998055530440437840>"
                "<:_:998055532030079078>"
                "<:_:998055534068510750>"
                "<:_:998055536346021898>\n"
                "┃<:_:998055527412142100>"
                "<:_:998055529219887154>"
                "<:_:998055531346415656>"
                "<:_:998055533225455716>"
                "<:_:998055534999654480>"
                "<:_:998055537432338532>\n"
            )
            if official
            else ""
        )


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Maps(bot))
