from __future__ import annotations

import textwrap
import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs
import database
import utils
import views

if typing.TYPE_CHECKING:
    import core


class Maps(commands.Cog):
    """Maps"""

    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command(name="add-level-name")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(
        map_code=cogs.map_codes_autocomplete,
    )
    async def add_level_name(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        new_level_name: str,
    ) -> None:
        """
        Add a level name to your map.

        Args:
            itx: Interaction obj
            map_code: Overwatch share code
            new_level_name: Name of new level
        """

        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        if itx.user.id not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.NoPermissionsError

        if new_level_name in itx.client.map_cache[map_code]["levels"]:
            raise utils.LevelExistsError

        view = views.Confirm(itx, ephemeral=True)
        await itx.edit_original_response(
            content=("Is this correct?\n" f"Adding level name: {new_level_name}\n"),
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        await itx.client.database.set(
            "INSERT INTO map_levels (map_code, level) VALUES ($1, $2)",
            map_code,
            new_level_name,
        )
        itx.client.map_cache[map_code]["levels"].append(new_level_name)
        itx.client.map_cache[map_code]["choices"].append(
            app_commands.Choice(name=new_level_name, value=new_level_name)
        )

    @app_commands.command(name="delete-level-name")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(
        map_code=cogs.map_codes_autocomplete,
        map_level=cogs.map_levels_autocomplete,
    )
    async def delete_level_names(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        map_level: app_commands.Transform[str, utils.MapLevelTransformer],
    ) -> None:
        """
        Delete a level from your map.

        Args:
            itx: Interaction obj
            map_code: Overwatch share code
            map_level: Name of level
        """
        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        if itx.user.id not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.NoPermissionsError

        view = views.Confirm(itx, ephemeral=True)
        await itx.edit_original_response(
            content=("Is this correct?\n" f"Deleting level name: {map_level}\n"),
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        await itx.client.database.set(
            "DELETE FROM map_levels WHERE map_code=$1 AND level=$2",
            map_code,
            map_level,
        )
        itx.client.map_cache[map_code]["levels"].remove(map_level)
        itx.client.map_cache[map_code]["choices"] = list(
            filter(
                lambda x: x.name != map_level, itx.client.map_cache[map_code]["choices"]
            )
        )

    @app_commands.command(name="edit-level-name")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(
        map_code=cogs.map_codes_autocomplete,
        map_level=cogs.map_levels_autocomplete,
    )
    async def edit_level_names(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        map_level: app_commands.Transform[str, utils.MapLevelTransformer],
        new_level_name: str,
    ) -> None:
        """
        Rename a level in your map.

        Args:
            itx: Interaction
            map_code: Overwatch share code
            map_level: Name of level
            new_level_name: New name of level
        """
        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        if itx.user.id not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.NoPermissionsError

        view = views.Confirm(itx, ephemeral=True)
        await itx.edit_original_response(
            content=(
                "Is this correct?\n"
                f"Original level name: {map_level}\n"
                f"Updated level name: {new_level_name}\n"
            ),
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        await itx.client.database.set(
            "UPDATE map_levels SET level=$3 WHERE map_code=$1 AND level=$2",
            map_code,
            map_level,
            new_level_name,
        )

        itx.client.map_cache[map_code]["levels"] = list(
            map(
                lambda x: new_level_name if x == map_level else x,
                itx.client.map_cache[map_code]["levels"],
            )
        )
        itx.client.map_cache[map_code]["choices"] = list(
            map(
                lambda x: app_commands.Choice(name=new_level_name, value=new_level_name)
                if x.name == map_level
                else x,
                itx.client.map_cache[map_code]["choices"],
            )
        )

    @app_commands.command(name="submit-map")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    @app_commands.autocomplete(map_name=cogs.map_name_autocomplete)
    async def submit_map(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        map_name: app_commands.Transform[str, utils.MapNameTransformer],
    ) -> None:
        """
        Submit your map to the database.

        Args:
            itx: Interaction
            map_code: Overwatch share code
            map_name: Overwatch map
        """
        modal = views.MapSubmit()
        modal.data = {
            "map_code": map_code,
            "map_name": map_name,
            "creator_name": itx.user.name,
        }
        await itx.response.send_modal(modal)

    @app_commands.command(name="map-search")
    @app_commands.autocomplete(
        map_name=cogs.map_name_autocomplete, map_type=cogs.map_type_autocomplete
    )
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def map_search(
        self,
        itx: core.Interaction[core.Doom],
        map_type: str | None = None,
        map_name: app_commands.Transform[str, utils.MapNameTransformer] | None = None,
        creator: str | None = None,
        map_code: app_commands.Transform[str, utils.MapCodeTransformer] | None = None,
    ) -> None:
        """
        Search for maps based on various filters.

        Args:
            itx: Interaction
            map_type: Type of parkour map
            map_name: Overwatch map
            creator: Creator name
            map_code: Specific map code
        """
        await itx.response.defer(ephemeral=True)
        embed = utils.DoomEmbed(title="Map Search")
        embed.set_thumbnail(url=None)
        maps = []

        where_clause = []
        outer_where = ""
        args = []
        tracking_number = 1
        if not any([map_type, map_name, creator, map_code]):
            raise utils.InvalidFiltersError

        if map_type:
            if map_type not in itx.client.map_types:
                raise utils.InvalidMapTypeError
            where_clause.append(f"map_type <@ ${tracking_number}")
            args.append([map_type])
            tracking_number += 1

        if map_name:
            if map_name not in itx.client.map_names:
                raise utils.InvalidMapNameError

            where_clause.append(f"map_name = ${tracking_number}")
            args.append(map_name)
            tracking_number += 1

        if map_code:
            where_clause.append(f"maps.map_code = ${tracking_number}")
            args.append(map_code)
            tracking_number += 1

        if creator:
            creator = "%" + creator + "%"
            outer_where = f" WHERE creators ILIKE ${tracking_number}"
            args.append(creator)
            tracking_number += 1

        async for _map in itx.client.database.get(
            textwrap.dedent(
                f"""SELECT map_code, map_type, map_name, "desc", official, creators, avg(rating) as rating
            FROM (SELECT mc.map_code,
                         array_to_string((map_type), ', ')     as map_type,
                         map_name,
                         "desc",
                         official,
                         string_agg(distinct (nickname), ', ') as creators,
                         AVG(rating)                           as rating
                  FROM maps
                           JOIN map_creators mc on maps.map_code = mc.map_code
                           JOIN users u on u.user_id = mc.user_id
                           LEFT JOIN map_level_ratings mlr on maps.map_code = mlr.map_code
            
                  {(" WHERE " + ' AND '.join(where_clause)) if where_clause else ""}
                  GROUP BY map_type, mc.map_code, map_name, "desc", official, rating) layer0
            {outer_where}
            GROUP BY map_code, map_type, map_name, "desc", official, creators ORDER BY map_code"""
            ),
            *args,
        ):
            maps.append(_map)
        if maps is None:
            raise utils.NoMapsFoundError

        embeds = self.create_map_embeds(maps)

        view = views.Paginator(embeds, itx.user, None)
        await view.start(itx)

    def create_map_embeds(
        self, maps: list[database.DotRecord]
    ) -> list[utils.Embed | utils.DoomEmbed]:
        embed_list = []
        embed = utils.DoomEmbed(title="Map Search")
        for i, _map in enumerate(maps):

            embed.add_description_field(
                name=f"{_map.map_code}",
                value=(
                    self.display_official(_map.official)
                    + f"┣ `Rating` {utils.create_stars(_map.rating)}\n"
                    f"┣ `Creator` {discord.utils.escape_markdown(_map.creators)}\n"
                    f"┣ `Map` {_map.map_name}\n"
                    f"┣ `Type` {_map.map_type}\n"
                    f"┗ `Description` {_map.desc}"
                ),
            )
            if (
                (i != 0 and i % 10 == 0)
                or (i == 0 and len(maps) == 1)
                or i == len(maps) - 1
            ):
                embed_list.append(embed)
                embed = utils.DoomEmbed(title="Map Search")
        return embed_list

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

    @app_commands.command(name="guide")
    @app_commands.autocomplete(map_code=cogs.map_codes_autocomplete)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def view_guide(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer] | None = None,
    ):
        await itx.response.defer(ephemeral=False)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        guides = [
            x
            async for x in itx.client.database.get(
                "SELECT url FROM guides WHERE map_code=$1",
                map_code,
            )
        ]
        guides = [x.url for x in guides]
        if not guides:
            raise utils.NoGuidesExistError

        view = views.Paginator(guides, itx.user)
        await view.start(itx)

    @app_commands.command(name="add-guide")
    @app_commands.autocomplete(map_code=cogs.map_codes_autocomplete)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def add_guide(
        self,
        itx: core.Interaction[core.Doom],
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        url: app_commands.Transform[str, utils.URLTransformer],
    ):
        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        guides = [
            x
            async for x in itx.client.database.get(
                "SELECT url FROM guides WHERE map_code=$1",
                map_code,
            )
        ]
        guides = [x.url for x in guides]
        if not guides:
            raise utils.NoGuidesExistError
        if url in guides:
            raise utils.GuideExistsError

        view = views.Confirm(itx, ephemeral=True)
        await itx.edit_original_response(
            content=f"Is this correct?\nMap code: {map_code}\nURL: {url}",
            view=view,
        )
        await view.wait()

        if not view.value:
            return

        await itx.client.database.set(
            "INSERT INTO guides (map_code, url) VALUES ($1, $2)",
            map_code,
            url,
        )


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Maps(bot))
