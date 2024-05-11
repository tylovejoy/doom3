from __future__ import annotations

import asyncio
import io
from math import ceil
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import Transform
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

import utilities.utils
import utils
import views
from cogs.tournament.utils.transformers import SeasonsTransformer
from config import CONFIG
from utils import NoDataOnCurrentSeason

if TYPE_CHECKING:
    import core


LOGO_FILE_PATH = {
    "Unranked": "data/ranks/bronze.png",
    "Gold": "data/ranks/gold.png",
    "Diamond": "data/ranks/diamond.png",
    "Grandmaster": "data/ranks/grandmaster.png",
}


class RankCard(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @staticmethod
    def format_xp(xp):
        """Truncate/format numbers over 1000 to 1k format."""
        if 1000000 > xp > 999:
            xp = f"{str(float(xp) / 1000)[:-2]}k"
        elif xp > 1000000:
            xp = f"{str(float(xp) / 1000000)[:-3]}m"

        return str(xp)

    @staticmethod
    def find_level(player_xp):
        """Find a player's level from their XP amount."""
        total = 0
        for level in range(101):
            total += 5 * (level**2) + (50 * level) + 100
            if total > player_xp:
                return level

    @staticmethod
    def find_portrait(level) -> str:
        """Find which portrait to use."""
        number = str(ceil(level % 20 / 4))
        if number == "0":
            number = "1"
        if level <= 20:
            rank = "bronze"
        elif 20 <= level < 40:
            rank = "silver"
        elif 40 <= level < 60:
            rank = "gold"
        elif 60 <= level < 80:
            rank = "platinum"
        elif 80 <= level < 100:
            rank = "diamond"
        else:
            rank = "diamond"
            number = "5"
        return rank + number + ".png"

    @app_commands.command()
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def rank(self, itx: core.DoomItx, user: discord.Member | None):
        await itx.response.defer(ephemeral=True)

        if user is None:
            user = itx.user

        search = await self._get_card_data(itx, user)
        if not search:
            raise NoDataOnCurrentSeason

        with io.BytesIO() as avatar_binary:
            await user.display_avatar.save(fp=avatar_binary)
            image = await asyncio.to_thread(self._create_card, avatar_binary, search, user)
            with io.BytesIO() as image_binary:
                image.save(image_binary, "PNG")
                image_binary.seek(0)

                await itx.edit_original_response(
                    content="",
                    attachments=[discord.File(fp=image_binary, filename="rank_card.png")],
                )

    async def _get_card_data(self, itx: core.DoomItx, user: discord.Member):
        season = self.bot.current_season
        if season is None:
            raise RuntimeError("Season not set")
        query = """
            WITH all_users AS (SELECT u.user_id,
                                          coalesce(xp, 0) as xp, nickname
                                   FROM user_xp ux
                                        RIGHT JOIN users u ON ux.user_id = u.user_id WHERE season = $2),
                 all_positions as (SELECT user_id, nickname,
                                              xp,
                                              rank() OVER (
                                                  ORDER BY xp DESC
                                                  ) AS pos
                                       FROM all_users),
                 ranks AS (SELECT u.user_id,
                                      COALESCE((SELECT value
                                                FROM user_ranks
                                                WHERE category = 'Time Attack'
                                                  AND user_id = $1),
                                               'Unranked') as "Time Attack",
                                      COALESCE((SELECT value
                                                FROM user_ranks
                                                WHERE category = 'Mildcore'
                                                  AND user_id = $1),
                                               'Unranked') as "Mildcore",
                                      COALESCE((SELECT value
                                                FROM user_ranks
                                                WHERE category = 'Hardcore'
                                                  AND user_id = $1),
                                               'Unranked') as "Hardcore",
                                      COALESCE((SELECT value FROM user_ranks WHERE category = 'Bonus' AND user_id = $1),
                                               'Unranked') as "Bonus"
                               FROM users u
                                        LEFT JOIN user_ranks ur on u.user_id = ur.user_id)
                
                SELECT all_positions.user_id, nickname,
                       xp,
                       pos,
                       "Time Attack",
                       "Mildcore",
                       "Hardcore",
                       "Bonus",
                       coalesce(wins, 0)   as wins,
                       coalesce(losses, 0) as losses
                FROM all_positions
                         RIGHT JOIN ranks ON all_positions.user_id = ranks.user_id
                         LEFT JOIN user_duels ON all_positions.user_id = user_duels.user_id
                
                WHERE all_positions.user_id = $1
                GROUP BY all_positions.user_id, xp, pos, "Time Attack", "Mildcore", "Hardcore", "Bonus", wins, losses, nickname
        """
        return await itx.client.database.fetchrow(query, user.id, season)

    def _create_card(self, avatar_binary, search, user):
        name = f"{user.name[:18]}#{user.discriminator}"
        if search.nickname != user.nick:
            name = search.nickname[:18]
        ta_logo = Image.open(LOGO_FILE_PATH[search["Time Attack"]]).convert("RGBA")
        mc_logo = Image.open(LOGO_FILE_PATH[search["Mildcore"]]).convert("RGBA")
        hc_logo = Image.open(LOGO_FILE_PATH[search["Hardcore"]]).convert("RGBA")
        # bo_logo = Image.open(LOGO_FILE_PATH[search.rank.bo]).convert("RGBA")
        ta_logo.thumbnail((100, 100))
        mc_logo.thumbnail((100, 100))
        hc_logo.thumbnail((100, 100))
        # bo_logo.thumbnail((100, 100))
        rank_card = Image.open("data/rankcard_bg_duels.png").convert("RGBA")
        old_x = 15
        old_y = 66
        x = rank_card.size[0]  # 1165 + 10
        y = rank_card.size[1]  # 348
        x_offset = 10
        img = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        img.paste(rank_card)
        avatar = Image.open(avatar_binary).convert("RGBA")
        avatar.thumbnail((200, 200))
        av_mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(av_mask)
        draw.ellipse((0, 0, 200, 200), fill=255)
        a_height = avatar.size[1]
        img.paste(avatar, (x_offset * 4 + old_x, (y - a_height) // 2), av_mask)
        # Portrait PFP
        level = self.find_level(search.xp)
        portrait_file = self.find_portrait(level)
        portrait = Image.open(f"data/portraits/{portrait_file}").convert("RGBA")
        img.paste(portrait, (-60, -30), portrait)
        rank_x_offset = 50
        rank_y_offset = 37
        for x_val, logo in zip([375, 508, 641, 774], [ta_logo, mc_logo, hc_logo]):  # bo_logo]
            img.paste(
                logo,
                (x_val + old_x - rank_x_offset, 98 + old_y // 2 - rank_y_offset),
                logo,
            )
        font_file = "data/fonts/segoeui.ttf"
        font2_file = "data/fonts/avenir.otf"
        # Username/Discriminator
        name_font = ImageFont.truetype(font2_file, 50)
        name_pos = x // 2 - d.textlength(name, font=name_font) // 2 + old_x
        d.text((name_pos, 170 + old_y // 2), name, fill=(255, 255, 255), font=name_font)
        # W/L Duels
        duels_font = ImageFont.truetype(font_file, 30)
        losses = search.losses
        wins = search.wins
        wins = f"{str(wins)} W"
        losses = f"{str(losses)} L"
        wins_pos = 729 + (849 - 729) // 2 - d.textlength(wins, font=duels_font) // 2
        losses_pos = 729 + (849 - 729) // 2 - d.textlength(losses, font=duels_font) // 2
        # between 729 -> 849 is box
        d.text((wins_pos, 98), wins, fill=(255, 255, 255), font=duels_font)
        d.text((losses_pos, 138), losses, fill=(255, 255, 255), font=duels_font)
        # XP
        xp_font = ImageFont.truetype(font_file, 40)
        xp = self.format_xp(search.xp)
        xp_length = x // 2 - d.textlength(f"Total XP: {xp}", font=xp_font) // 2 + old_x
        d.text(
            (xp_length, 215 + old_y // 2),
            f"Total XP: {xp}",
            fill=(255, 255, 255),
            font=xp_font,
        )
        # Highest Position
        # xp_circle_r_pad = 100
        # xp_circle_dia = 160
        place = search.pos
        if place == 1:
            pos_portrait_f = "gold_position.png"
        elif place == 2:
            pos_portrait_f = "silver_position.png"
        elif place == 3:
            pos_portrait_f = "bronze_position.png"
        else:
            pos_portrait_f = "no_position.png"
        color = (9, 10, 11, 255)
        place_circle_x1 = x - (x_offset * 4) - 200 - 5
        place_circle_x2 = x - (x_offset * 4) + 5
        place_circle_y1 = (y - 200) // 2 - 5
        place_circle_y2 = (y - 200) // 2 + 200 + 5
        d.ellipse(
            (place_circle_x1, place_circle_y1, place_circle_x2, place_circle_y2),
            fill=color,
        )
        if len(str(place)) == 1:
            place_font_size = 120
        elif len(str(place)) == 2:
            place_font_size = 110
        elif place < 999:
            place_font_size = 100
        else:
            place_font_size = 85
        place_font = ImageFont.truetype(font_file, place_font_size)
        place_x = place_circle_x1 + (place_circle_x2 - place_circle_x1) // 2 - d.textlength(str(place), font=place_font) // 2
        ascent, _ = place_font.getmetrics()
        (_, _), (_, offset_y) = place_font.font.getsize(str(place))
        place_y = y // 2 - (ascent - offset_y)
        d.text((place_x, place_y), str(place), fill=(255, 255, 255, 255), font=place_font)
        pos_portrait = Image.open(f"data/portraits/{pos_portrait_f}").convert("RGBA")
        img.paste(pos_portrait, (x - 350, -28), pos_portrait)
        width, height = img.size
        img = img.resize((width // 2, height // 2))
        return img

    @app_commands.command()
    @app_commands.guilds(CONFIG["GUILD_ID"])
    async def xp_leaderboard(
        self,
        itx: core.DoomItx,
        season: Transform[str, SeasonsTransformer] | None = None,
    ):
        if season is None:
            season = self.bot.current_season
        query = """
            SELECT nickname, xp, rank() over(order by xp DESC)
            FROM user_xp LEFT JOIN users u on user_xp.user_id = u.user_id 
            WHERE season = $1
            ORDER BY xp DESC
        """
        await itx.response.defer(ephemeral=True)
        embed = utils.DoomEmbed(title=f"XP Leaderboard - {season}")
        embed_list = []
        records = await itx.client.database.fetch(query, season)
        for i, record in enumerate(records):
            embed.add_field(
                name=f"{utils.make_ordinal(record['rank'])} - {record['nickname']}",
                value=f"XP: {record['xp']}",
                inline=False,
            )
            if utilities.utils.split_nth_conditional(i, 9, records):
                embed_list.append(embed)
                embed = utils.DoomEmbed(title="XP Leaderboard")
        if not embed_list:
            await itx.edit_original_response(content="The XP Leaderboard for this season is currently empty.")
            return
        view = views.Paginator(embed_list, itx.user)
        await view.start(itx)


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(RankCard(bot))
