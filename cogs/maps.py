from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING

import views
from config import CONFIG
from utilities import (
    ConfirmationBaseView,
    CreatorTransformer,
    Embed,
    ExistingMapCodeAutocompleteTransformer,
    ExistingMapCodeTransformer,
    Map,
    MapLevelTransformer,
    MapMetadata,
    MapNameTransformer,
    MapTypeTransformer,
    UserTransformer,
    create_stars,
    errors,
    translations,
    split_nth_conditional,
    URLTransformer,
)

if typing.TYPE_CHECKING:
    import core
    from core import DoomItx


class Maps(commands.Cog):
    """Maps"""

    def __init__(self, bot: core.Doom):
        self.bot = bot

    _map_maker = app_commands.Group(
        **translations.map_maker_,
        guild_ids=[CONFIG["GUILD_ID"]],
    )

    _level = app_commands.Group(
        **translations.map_maker_level,
        guild_ids=[CONFIG["GUILD_ID"]],
        parent=_map_maker,
    )

    _creator = app_commands.Group(
        **translations.map_maker_creator,
        guild_ids=[CONFIG["GUILD_ID"]],
        parent=_map_maker,
    )

    async def cog_load(self):
        query = "SELECT name, color FROM all_map_names;"
        rows = await self.bot.database.fetch(query)
        if not rows:
            return
        metadata = [MapMetadata(name, color) for name, color in rows]
        self.bot.map_metadata = {const.NAME: const for const in metadata}

    @_creator.command(
        **translations.remove_creator,
    )
    @app_commands.describe(**translations.creator_args)
    async def remove_creator(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
        creator: app_commands.Transform[int, CreatorTransformer],
    ) -> None:
        await itx.response.defer(ephemeral=True)
        creator_ids = await self.bot.database.fetch_creator_ids_for_map_code(map_code)
        if itx.user.id not in creator_ids:
            raise errors.NoPermissionsError
        if creator not in creator_ids:
            raise errors.CreatorDoesntExist
        await self.bot.database.remove_creator_from_map_code(creator, map_code)
        nickname = await self.bot.database.fetch_user_nickname(itx.user.id)

        await itx.edit_original_response(
            content=f"Removing **{nickname}** from list of creators for map code **{map_code}**."
        )

    @_creator.command(**translations.add_creator)
    @app_commands.describe(**translations.creator_args)
    async def add_creator(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
        creator: app_commands.Transform[int, UserTransformer],
    ) -> None:
        await itx.response.defer(ephemeral=True)
        creator_ids = await self.bot.database.fetch_creator_ids_for_map_code(map_code)
        if itx.user.id not in creator_ids:
            raise errors.NoPermissionsError
        if creator in creator_ids:
            raise errors.CreatorAlreadyExists
        await self.bot.database.add_creator_to_map_code(creator, map_code)
        nickname = await self.bot.database.fetch_user_nickname(itx.user.id)
        await itx.edit_original_response(content="Adding **{nickname}** to list of creators for map code **{map_code}**.")

    @_level.command(**translations.add_level)
    @app_commands.describe(**translations.add_level_args)
    async def add_level_name(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
        new_level_name: str,
    ) -> None:
        creator_ids = await self.bot.database.fetch_creator_ids_for_map_code(map_code)
        if itx.user.id not in creator_ids:
            raise errors.NoPermissionsError

        all_levels = await self.bot.database.fetch_level_names_of_map_code(map_code)
        if new_level_name in all_levels:
            raise errors.LevelExistsError

        view = ConfirmationBaseView(itx, "Is this correct?\n" f"Adding level name: {new_level_name}\n")
        await view.start()

        if not view.value:
            return

        await self.bot.database.add_map_level_to_map_code(map_code, new_level_name)

    @_level.command(**translations.remove_level)
    @app_commands.describe(**translations.remove_level_args)
    async def delete_level_names(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
        level_name: app_commands.Transform[str, MapLevelTransformer],
    ) -> None:

        creator_ids = await self.bot.database.fetch_creator_ids_for_map_code(map_code)
        if itx.user.id not in creator_ids:
            raise errors.NoPermissionsError

        all_levels = await self.bot.database.fetch_level_names_of_map_code(map_code)
        if level_name not in all_levels:
            raise errors.LevelDoesntExistError

        view = ConfirmationBaseView(itx, "Is this correct?\nDeleting level name: {map_level}\n")
        await view.start()

        if not view.value:
            return

        await self.bot.database.remove_map_level_from_map_code(map_code, level_name)

    @_level.command(**translations.edit_level)
    @app_commands.describe(**translations.edit_level_args)
    async def edit_level_names(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
        level_name: app_commands.Transform[str, MapLevelTransformer],
        new_level_name: str,
    ) -> None:
        creator_ids = await self.bot.database.fetch_creator_ids_for_map_code(map_code)
        if itx.user.id not in creator_ids:
            raise errors.NoPermissionsError

        all_levels = await self.bot.database.fetch_level_names_of_map_code(map_code)
        if level_name not in all_levels:
            raise errors.LevelDoesntExistError

        if new_level_name in all_levels:
            raise errors.LevelExistsError

        view = ConfirmationBaseView(
            itx,
            "Is this correct?\nOriginal level name: {level_name}\nUpdated level name: {new_level_name}\n",
        )
        await view.start()
        if not view.value:
            return

        await self.bot.database.rename_level_name_for_map_code(map_code, level_name, new_level_name)

    @app_commands.command(**translations.submit_map)
    @app_commands.describe(**translations.submit_map_args)
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def submit_map(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeTransformer],
        map_name: app_commands.Transform[str, MapNameTransformer],
        image: discord.Attachment | None,
    ) -> None:
        map_data = Map(
            bot=self.bot,
            map_code=map_code,
            map_name=map_name,
            primary_creator=itx.user.id,
            image=image,
        )
        modal = MapSubmissionModal(map_data)
        await itx.response.send_modal(modal)

    @app_commands.command(**translations.map_search)
    @app_commands.describe(**translations.map_search_args)
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def map_search(
        self,
        itx: DoomItx,
        map_type: app_commands.Transform[str, MapTypeTransformer] | None = None,
        map_name: app_commands.Transform[str, MapNameTransformer] | None = None,
        creator: app_commands.Transform[int, UserTransformer] | None = None,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer] | None = None,
    ) -> None:
        await itx.response.defer(ephemeral=True)

        query = f"""
            WITH valid_ratings AS (
                SELECT mr.map_code, level, rating, mr.user_id, level_name 
                FROM map_level_ratings mr
                LEFT JOIN records r on mr.user_id = r.user_id 
                    AND level_name = level
                    AND r.map_code = mr.map_code
            )
            SELECT map_code,
                   map_type,
                   map_name,
                   "desc" AS description,
                   official,
                   image,
                   creators,
                   creators_ids,
                   avg(rating) as rating
            FROM (SELECT mc.map_code,
                         array_to_string((map_type), ', ')     as map_type,
                         map_name,
                         "desc",
                         official,
                         image,
                         string_agg(distinct (nickname), ', ') as creators,
                         array_agg(distinct mc.user_id)        as creators_ids,
                         AVG(COALESCE(rating, 0))              as rating
                  FROM maps
                           JOIN map_creators mc on maps.map_code = mc.map_code
                           JOIN users u on u.user_id = mc.user_id
                           LEFT JOIN valid_ratings vr on maps.map_code = vr.map_code
                  WHERE ($1::text IS NULL OR $1 = ANY (map_type))
                    AND ($2::text IS NULL OR map_name = $2)
                    AND ($3::text IS NULL OR maps.map_code = $3)
                  GROUP BY map_type, mc.map_code, map_name, "desc", official, rating, image
                  HAVING ($4::bigint IS NULL OR $4 = ANY(array_agg(distinct (mc.user_id))))
                  ORDER BY map_code) layer0
            GROUP BY map_code, map_type, map_name, "desc", official, creators, creators_ids, image
            ORDER BY map_code
            """
        rows = await itx.client.database.fetch(
            query,
            map_type,
            map_name,
            map_code,
            creator,
        )
        if not rows:
            raise errors.NoMapsFoundError
        maps = [Map(self.bot, **row) for row in rows]
        embeds = self.create_map_embeds(maps)
        if map_code and maps[0].image_url:
            embeds[0].set_image(url=maps[0].image_url)
        view = views.Paginator(embeds, itx.user, None)
        await view.start(itx)

    @app_commands.command()
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def random_map(self, itx: DoomItx, random_level: bool | None = False) -> None:
        await itx.response.defer(ephemeral=True)
        query = """
            WITH valid_ratings AS (
                SELECT m.map_code, ml.level, rating, mr.user_id 
                FROM maps m
                LEFT JOIN map_levels ml on m.map_code = ml.map_code
                LEFT JOIN map_level_ratings mr ON m.map_code = mr.map_code AND ml.level = mr.level
                LEFT JOIN records r on mr.user_id = r.user_id 
                    AND level_name = ml.level
                    AND r.map_code = mr.map_code
            ),
            levels_with_ratings AS (
                SELECT map_code, level, avg(rating) as avg_rating FROM valid_ratings GROUP BY map_code, level
                ),
            random_map_level AS (
            SELECT map_code, level, avg_rating FROM levels_with_ratings offset random() * (select count(*) from levels_with_ratings) limit 1)
            SELECT map_code,
                   map_type,
                   map_name,
                   "desc" as description,
                   official,
                   image as image_url,
                   creators,
                   creators_ids,
                   level,
                   avg_rating,
                   avg(rating) as rating
            FROM (SELECT mc.map_code,
                         array_to_string((map_type), ', ')     as map_type,
                         map_name,
                         "desc",
                         official,
                         image,
                         rml.level,
                         avg_rating,
                         string_agg(distinct (nickname), ', ') as creators,
                         array_agg(distinct mc.user_id)        as creators_ids,
                         AVG(rating)              as rating
                  FROM maps
                           JOIN map_creators mc on maps.map_code = mc.map_code
                           JOIN users u on u.user_id = mc.user_id
                           LEFT JOIN random_map_level rml on maps.map_code = rml.map_code
                            LEFT JOIN valid_ratings vr on maps.map_code = vr.map_code
                    WHERE (maps.map_code = rml.map_code)
                  GROUP BY map_type, mc.map_code, map_name, "desc", official, image, rml.level, rml.avg_rating
                  ORDER BY map_code) layer0 GROUP BY map_code,
                   map_type,
                   map_name,
                   "desc",
                   official,
                   image,
                   creators,
                   creators_ids,
                   level, avg_rating
                   LIMIT 1
        """

        row = await itx.client.database.fetchrow(query)
        if not row:
            raise errors.NoMapsFoundError

        _map = Map(self.bot, **row)
        embed = self.create_random_map_embed(_map, random_level)
        if _map.image_url:
            embed.set_image(url=_map.image_url)
        view = views.Paginator([embed], itx.user, None)
        await view.start(itx)

    def create_map_embeds(self, maps: list[Map]) -> list[Embed | discord.Embed]:
        embed_list = []
        embed = Embed(title="Map Search")
        for i, _map in enumerate(maps):
            embed.add_description_field(**_map.map_search_embed_to_dict())
            if split_nth_conditional(i, 10, maps):
                embed_list.append(embed)
                embed = Embed(title="Map Search")
        return embed_list

    def create_random_map_embed(self, _map: Map, level: bool | None) -> Embed | discord.Embed:
        embed = Embed(title="Map Search")
        embed.add_description_field(**_map.map_search_embed_to_dict())
        if level:
            embed.add_field(
                name="Random Level",
                value=f"{_map.level} - {create_stars(_map.avg_rating)}",
            )
        return embed

    @app_commands.command(**translations.view_guide)
    @app_commands.describe(**translations.view_guide_args)
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def view_guide(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
    ):
        guides = await self._check_guides(itx, map_code)
        if not guides:
            raise errors.NoGuidesExistError

        view = views.Paginator(guides, itx.user)
        await view.start(itx)

    @app_commands.command(**translations.add_guide)
    @app_commands.describe(**translations.add_guide_args)
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def add_guide(
        self,
        itx: DoomItx,
        map_code: app_commands.Transform[str, ExistingMapCodeAutocompleteTransformer],
        url: app_commands.Transform[str, URLTransformer],
    ):
        guides = await self._check_guides(itx, map_code)

        if url in guides:
            raise errors.GuideExistsError

        view = ConfirmationBaseView(itx, f"Is this correct?\nMap code: {map_code}\nURL: {url}")
        await view.start()

        if not view.value:
            return
        query = "INSERT INTO guides (map_code, url) VALUES ($1, $2);"
        await itx.client.database.execute(
            query,
            map_code,
            url,
        )

    @staticmethod
    async def _check_guides(itx: DoomItx, map_code: str) -> list[str]:
        await itx.response.defer(ephemeral=True)
        query = "SELECT url FROM guides WHERE map_code=$1"
        guides = await itx.client.database.fetch(
            query,
            map_code,
        )
        if not guides:
            return []
        return [x["url"] for x in guides]


class ConfirmationMapSubmit(ConfirmationBaseView):
    def __init__(
        self,
        itx: DoomItx,
        initial_message: str,
        map_type_select: MapTypesSelect,
        embed: discord.Embed = MISSING,
        attachment: discord.File = MISSING,
    ):
        super().__init__(itx, initial_message, embed, attachment)
        self.map_type = map_type_select
        self.add_item(self.map_type)

    async def map_submit_enable(self):
        values = getattr(self, "map_type").values
        if all(values):
            self.accept.disabled = False
            await self.itx.edit_original_response(view=self)

    @property
    def map_types(self):
        return [x for x in self.map_type.values]


class MapTypesSelect(discord.ui.Select):
    view: ConfirmationMapSubmit

    def __init__(self, options: list[str]) -> None:
        _options = [discord.SelectOption(label=option, value=option) for option in options]
        super().__init__(options=_options, placeholder="Map type(s)?", max_values=len(options), row=0)

    async def callback(self, itx: DoomItx):
        await itx.response.defer(ephemeral=True)
        for x in self.options:
            x.default = x.value in self.values
        await self.view.map_submit_enable()


class MapSubmissionModal(discord.ui.Modal):
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)
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

    def __init__(self, data: Map):
        super().__init__(title="Map Submission")
        self.data = data

    async def on_submit(self, itx: DoomItx):
        await itx.response.defer(ephemeral=True, thinking=True)
        map_types = await itx.client.database.fetch_all_map_types()
        if not map_types:
            raise ValueError("Map types are missing.")
        select = MapTypesSelect(map_types)
        view = ConfirmationMapSubmit(itx, "", select)
        await view.start()
        if not view.value:
            return

        self.data.set_map_types(view.map_types)
        self.data.set_levels(self.sanitized_levels)
        self.data.set_description(self.description.value)
        embed = self.data.build_preview_embed()

        attachment = self.data.image
        image = MISSING
        new_map_image = MISSING
        if isinstance(attachment, discord.Attachment):
            image = await attachment.to_file(filename="image.png")
            new_map_image = await attachment.to_file(filename="image.png")

        view = ConfirmationBaseView(itx, "Is this correct?", embed, image)
        await view.start()
        if not view.value:
            return
        try:
            await self.data.commit()
        except Exception as e:
            ...
        assert self.data.primary_creator
        nickname = await itx.client.database.fetch_user_nickname(self.data.primary_creator)
        embed.title = f"New Map by {nickname}"
        embed.remove_field(0)
        embed.set_image(url="attachment://image.png")
        assert itx.guild
        new_map_channel = itx.guild.get_channel(CONFIG["NEW_MAPS"])
        assert isinstance(new_map_channel, discord.TextChannel)
        new_map_alert = await new_map_channel.send(embed=embed, file=new_map_image)
        if new_map_alert.attachments:
            query = "UPDATE maps SET image = $2 WHERE map_code = $1;"
            await itx.client.database.execute(
                query,
                self.data.map_code,
                new_map_alert.attachments[0].url,
            )
        await new_map_alert.create_thread(name=f"Discuss {self.data.map_code} here.")
        map_maker = itx.guild.get_role(CONFIG["MAP_MAKER"])
        assert isinstance(itx.user, discord.Member) and map_maker
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

    @property
    def sanitized_levels(self):
        return list(set(map(str.strip, filter(lambda x: bool(x), self.levels.value.split("\n")))))


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Maps(bot))
