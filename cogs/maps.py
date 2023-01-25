from __future__ import annotations

import textwrap
import typing

import discord
from discord import app_commands
from discord.ext import commands

import database
import utils
import views

if typing.TYPE_CHECKING:
    import core
    from core import DoomItx


class Maps(commands.Cog):
    """Maps"""

    def __init__(self, bot: core.Doom):
        self.bot = bot

    _map_maker = app_commands.Group(
        **utils.map_maker_,
        guild_ids=[utils.GUILD_ID],
    )

    _level = app_commands.Group(
        **utils.map_maker_level,
        guild_ids=[utils.GUILD_ID],
        parent=_map_maker,
    )

    _creator = app_commands.Group(
        **utils.map_maker_creator,
        guild_ids=[utils.GUILD_ID],
        parent=_map_maker,
    )

    @_creator.command(
        **utils.remove_creator,
    )
    @app_commands.describe(**utils.creator_args)
    async def remove_creator(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
        creator: app_commands.Transform[int, utils.UserTransformer],
    ) -> None:
        await itx.response.defer(ephemeral=True)
        if itx.user.id not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.NoPermissionsError

        if creator not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.CreatorDoesntExist

        await itx.client.database.set(
            "DELETE FROM map_creators WHERE map_code = $1 AND user_id = $2;",
            map_code,
            creator,
        )
        itx.client.map_cache[map_code]["user_ids"].remove(creator)

        await itx.edit_original_response(
            content=(
                f"Removing **{itx.client.all_users[creator]['nickname']}** "
                f"from list of creators for map code **{map_code}**."
            )
        )

    @_creator.command(**utils.add_creator)
    @app_commands.describe(**utils.creator_args)
    async def add_creator(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
        creator: app_commands.Transform[int, utils.UserTransformer],
    ) -> None:
        await itx.response.defer(ephemeral=True)
        if itx.user.id not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.NoPermissionsError

        if creator in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.CreatorAlreadyExists

        await itx.client.database.set(
            "INSERT INTO map_creators (map_code, user_id) VALUES ($1, $2)",
            map_code,
            creator,
        )
        itx.client.map_cache[map_code]["user_ids"].append(creator)

        await itx.edit_original_response(
            content=(
                f"Adding **{itx.client.all_users[creator]['nickname']}** "
                f"to list of creators for map code **{map_code}**."
            )
        )

    @_level.command(**utils.add_level)
    @app_commands.describe(**utils.add_level_args)
    async def add_level_name(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
        new_level_name: str,
    ) -> None:
        view = await self._check_creator_code(itx, map_code, new_level_name)

        await itx.edit_original_response(
            content="Is this correct?\n" f"Adding level name: {new_level_name}\n",
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

    @_level.command(**utils.remove_level)
    @app_commands.describe(**utils.remove_level_args)
    async def delete_level_names(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
    ) -> None:
        view = await self._check_creator_code(itx, map_code)
        await itx.edit_original_response(
            content="Is this correct?\nDeleting level name: {map_level}\n",
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        await itx.client.database.set(
            "DELETE FROM map_levels WHERE map_code=$1 AND level=$2",
            map_code,
            level_name,
        )
        itx.client.map_cache[map_code]["levels"].remove(level_name)
        itx.client.map_cache[map_code]["choices"] = list(
            filter(
                lambda x: x.name != level_name,
                itx.client.map_cache[map_code]["choices"],
            )
        )

    @staticmethod
    async def _check_creator_code(itx, map_code, new_level_name=None):
        await itx.response.defer(ephemeral=True)
        if map_code not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError
        if itx.user.id not in itx.client.map_cache[map_code]["user_ids"]:
            raise utils.NoPermissionsError
        if (
            new_level_name
            and new_level_name in itx.client.map_cache[map_code]["levels"]
        ):
            raise utils.LevelExistsError
        return views.Confirm(itx, ephemeral=True)

    @_level.command(**utils.edit_level)
    @app_commands.describe(**utils.edit_level_args)
    async def edit_level_names(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
        new_level_name: str,
    ) -> None:
        view = await self._check_creator_code(itx, map_code)

        await itx.edit_original_response(
            content=(
                "Is this correct?\n"
                f"Original level name: {level_name}\n"
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
            level_name,
            new_level_name,
        )

        itx.client.map_cache[map_code]["levels"] = list(
            map(
                lambda x: new_level_name if x == level_name else x,
                itx.client.map_cache[map_code]["levels"],
            )
        )
        itx.client.map_cache[map_code]["choices"] = list(
            map(
                lambda x: app_commands.Choice(name=new_level_name, value=new_level_name)
                if x.name == level_name
                else x,
                itx.client.map_cache[map_code]["choices"],
            )
        )

    @app_commands.command(**utils.submit_map)
    @app_commands.describe(**utils.submit_map_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def submit_map(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
        map_name: app_commands.Transform[str, utils.MapNameTransformer],
    ) -> None:
        modal = views.MapSubmit()
        modal.data = {
            "map_code": map_code,
            "map_name": map_name,
            "creator_name": itx.user.name,
        }
        await itx.response.send_modal(modal)

    @app_commands.command(**utils.map_search)
    @app_commands.describe(**utils.map_search_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def map_search(
        self,
        itx: DoomItx,
        map_type: app_commands.Transform[str, utils.MapTypeTransformer] | None = None,
        map_name: app_commands.Transform[str, utils.MapNameTransformer] | None = None,
        creator: app_commands.Transform[int, utils.UserTransformer] | None = None,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer]
        | None = None,
    ) -> None:
        await itx.response.defer(ephemeral=True)
        embed = utils.DoomEmbed(title="Map Search")
        embed.set_thumbnail(url=None)
        maps = []

        if not any([map_type, map_name, creator, map_code]):
            raise utils.InvalidFiltersError

        async for _map in itx.client.database.get(
            textwrap.dedent(
                f"""
                SELECT map_code,
                       map_type,
                       map_name,
                       "desc",
                       official,
                       creators,
                       avg(rating) as rating
                FROM (SELECT mc.map_code,
                             array_to_string((map_type), ', ')     as map_type,
                             map_name,
                             "desc",
                             official,
                             string_agg(distinct (nickname), ', ') as creators,
                             AVG(COALESCE(rating, 0))              as rating
                      FROM maps
                               JOIN map_creators mc on maps.map_code = mc.map_code
                               JOIN users u on u.user_id = mc.user_id
                               LEFT JOIN map_level_ratings mlr on maps.map_code = mlr.map_code
                      WHERE ($1::text IS NULL OR $1 = ANY (map_type))
                        AND ($2::text IS NULL OR map_name = $2)
                        AND ($3::text IS NULL OR maps.map_code = $3)
                      GROUP BY map_type, mc.map_code, map_name, "desc", official, rating
                      HAVING ($4::text IS NULL OR string_agg(distinct (nickname), ', ') ILIKE $4)
                      ORDER BY map_code) layer0
                GROUP BY map_code, map_type, map_name, "desc", official, creators
                ORDER BY map_code;
                """
            ),
            map_type,
            map_name,
            map_code,
            "%" + creator + "%" if creator else None, # TODO: use IDs??
        ):
            _map: database.DotRecord
            maps.append(_map)
        if not maps:
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
            if utils.split_nth_conditional(i, 10, maps):
                embed_list.append(embed)
                embed = utils.DoomEmbed(title="Map Search")
        return embed_list

    @staticmethod
    def display_official(official: bool) -> str:
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

    @app_commands.command(**utils.view_guide)
    @app_commands.describe(**utils.view_guide_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def view_guide(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
    ):
        guides = await self._check_guides(itx, map_code)
        if not guides:
            raise utils.NoGuidesExistError

        view = views.Paginator(guides, itx.user)
        await view.start(itx)

    @app_commands.command(**utils.add_guide)
    @app_commands.describe(**utils.add_guide_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def add_guide(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeAutoTransformer],
        url: app_commands.Transform[str, utils.URLTransformer],
    ):
        guides = await self._check_guides(itx, map_code)

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

    @staticmethod
    async def _check_guides(
        itx: DoomItx, map_code: str
    ) -> list[str]:
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
        return guides


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Maps(bot))
