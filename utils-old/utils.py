from __future__ import annotations

import datetime
import typing

import discord
from discord import app_commands
from discord.ext import tasks

from cogs.tournament.utils.data import TournamentData, end_embed
from cogs.tournament.utils.end_tournament import ExperienceCalculator, SpreadsheetCreator
from cogs.tournament.utils.utils import ANNOUNCEMENTS
from config import CONFIG

if typing.TYPE_CHECKING:
    pass


class MapCacheData(typing.TypedDict):
    levels: list[str]
    user_ids: list[int]
    choices: list[app_commands.Choice]


class UserCacheData(typing.TypedDict):
    nickname: str
    alertable: bool


async def tournament_task(
    data: TournamentData,
    start: bool,
    func: typing.Callable[[TournamentData], typing.Awaitable[None]],
):
    time = "start" if start else "end"

    await func(data)


@tasks.loop()
async def start_tournament_task(data: TournamentData):
    current_date = datetime.datetime.utcnow().date()
    start_date = data.start.date()

    if current_date == start_date:
        await start_tournament(data)


@tasks.loop()
async def end_tournament_task(data: TournamentData):
    current_date = datetime.datetime.utcnow().date()
    end_date = data.end.date()

    if current_date == end_date:
        await end_tournament(data)


async def start_tournament(data: TournamentData):
    # Post announcement
    mentions = [data.client.get_guild(CONFIG["GUILD_ID"]).get_role(_id).mention for _id in data.mention_ids]

    await data.client.get_guild(CONFIG["GUILD_ID"]).get_channel(ANNOUNCEMENTS).send(
        "".join(mentions), embed=data.start_embed()
    )
    # Open submissions channel
    guild = data.client.get_guild(CONFIG["GUILD_ID"])
    add_perms = guild.get_channel(CONFIG["TOURNAMENT_SUBMISSIONS"]).overwrites_for(guild.default_role)
    add_perms.update(send_messages=True)
    await guild.get_channel(CONFIG["TOURNAMENT_SUBMISSIONS"]).set_permissions(
        guild.default_role,
        overwrite=add_perms,
        reason="Tournament Ended.",
    )
    query = "UPDATE tournament SET active=TRUE WHERE id=$1;"
    await data.client.database.execute(query, data.id)


async def end_tournament(data: TournamentData):
    guild = data.client.get_guild(CONFIG["GUILD_ID"])
    query = "UPDATE tournament SET active=FALSE WHERE id=$1;"
    await data.client.database.execute(query, data.id)
    remove_perms = guild.get_channel(CONFIG["TOURNAMENT_SUBMISSIONS"]).overwrites_for(guild.default_role)
    remove_perms.update(send_messages=False)
    await guild.get_channel(CONFIG["TOURNAMENT_SUBMISSIONS"]).set_permissions(
        guild.default_role,
        overwrite=remove_perms,
        reason="Tournament Ended.",
    )

    xp = await ExperienceCalculator(data).compute_xp()
    users_xp = [(k, v["Total XP"], data.client.current_season) for k, v in xp.items()]
    query = """
        INSERT INTO user_xp (user_id, xp, season) 
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id, season) DO UPDATE 
        SET xp = user_xp.xp + EXCLUDED.xp
        RETURNING user_xp.xp
    """
    await data.client.database.executemany(query, users_xp)

    await SpreadsheetCreator(data, xp).create()

    mentions = [
        data.client.get_guild(CONFIG["GUILD_ID"]).get_role(_id).mention for _id in data.client.current_tournament.mention_ids
    ]

    await guild.get_channel(ANNOUNCEMENTS).send(
        "".join(mentions),
        embed=end_embed(),
    )

    hof_embed, lb_embeds = await data.hall_of_fame()
    hof_msg = await guild.get_channel(CONFIG["HALL_OF_FAME_ID"]).send(embed=hof_embed)
    hof_thread = await hof_msg.create_thread(name="Records Archive")
    file = discord.File(
        fp=r"DPK_Tournament.xlsx",
        filename=f"DPK_Tournament_{datetime.datetime.now().strftime('%d-%m-%Y')}.xlsx",
    )
    await hof_thread.send(embeds=lb_embeds, file=file)

    data.client.current_tournament = None