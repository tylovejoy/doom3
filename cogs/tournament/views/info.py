from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    import core

rules_embed = discord.Embed(
    description=(
        "# Tournament Rules\n"
        "1. Any tech that is possible in the chosen framework is allowed.\n"
        "2. Map creators ARE allowed to run their own maps.\n"
        "3. Post your screenshots in a timely manner. "
        "Holding onto good times and sniping on the last day is not allowed.\n"
        "4. Do not cheat and submit false times (See Cheating section below).\n"
        "5. Strategies that require more than one player are not allowed. "
        "Every strategy must be possible in a single player environment.\n"
        "# Cheating/Submitting False Times\n"
        "Submitting a cheated or modified time. Anyone caught cheating with, but not limited to, "
        "any of the following is subject to punishment by mod and org discretion based on severity.\n"
        "*(Breaking any more than 1 rule will get you immediately perma-banned from further tournaments)*\n"
        "1. Faking your time in any way.\n"
        "2. Changing the positions of the checkpoints on your own accord "
        "(this is not applied to the makers of the map if there is an "
        "issue on that level that needs to be addressed).\n"
        "3. Changing any other setting in either workshop or in the lobby unless otherwise specified "
        "(e.g. changing cancel timings or cooldowns on time attack maps).\n"
        "4. Letting another person play for you (including account sharing). "
        "If you contact the Orgs beforehand, we can take a look at the situation "
        "e.g. playing at another persons house on their account.\n\n"
        "**This is not an inclusive list. "
        "If you feel someone has altered a map or time in any way, bring it up to the Orgs or Mods.**"
    )
)
submit_embed = discord.Embed(
    description=(
        "# Submissions\n"
        "To submit a time for the tournament use the command "
        "`/tournament submit` in the <#698003925168816139> channel.\n"
        "There are shorter variations as well:\n"
        "- `/ta` - Time Attack\n"
        "- `/mc` - Mildcore\n"
        "- `/hc` - Hardcore\n"
        "- `/bo` - Bonus\n"
    )
)
bracket_embed = discord.Embed(
    description=(
        "# Bracket Information\n"
        "> Each person has 2 lives.\n"
        "> You get bonus XP for winning games in the normal bracket.\n"
        "> Submitting any time in the tournament will grant you participation XP (250).\n"
        "> Any win in both losers and winners bracket will grant you 1000xp MINIMUM.\n "
        "> Getting #1 time on a round will grant you 1000 XP bonus "
        "(this applies to everyone, not just people in the bracket)."
        "On SOME of the rounds getting the #1 time will grant you a bypass in the bracket so you skip 1 round "
        "(and get full points for it)."
        "\n\n"
        "**+10000xp** for 1st place\n"
        "**+7500xp** for 2nd place\n"
        "**+5000xp** for 3rd place\n"
        "# Bracket Tournament XP Multipliers\n"
        "> For the tournament we have decided on a Scalar XP for the Winners Bracket. "
        "For every win you get in the winners bracket, "
        "you get a multiplier to the experience earned in the next round. "
        "That also includes the tournament missions. "
        "If you lose in the winners bracket and make it back to winners your multiplier is reset. "
        "Losers bracket does not get a multiplier.\n\n"

        "> Round 1 -> **1.0x** multiplier\n"
        "> Round 2 -> **1.1x** multiplier\n"
        "> Round 3 -> **1.2x** multiplier\n"
        "> etc.\n\n"
        "If someone wins 3 rounds, and completes a mission on Round 3 he gets "
        "`(win XP + missions XP)*1.2 XP` for that round, and guarantees 1.3x multiplier for Round 4."
    )
)
ranks_embed = discord.Embed(
    description=(
        "To separate hard competition from a more casual approach, "
        "we divide the tournament players by three ranks.\n"
        "- Gold (Bottom)\n"
        "- Diamond (Middle)\n"
        "- Grandmaster (Top)\n"
        "* This is in each category. So, you may be Gold in Hardcore but Grandmaster in Time Attack.\n\n"

        "Currently, Tournament Orgs decide on which rank each player will have. "
        "Criteria for the ranks depend on one's records over time versus how the leaderboard does."
        "Depending on your performance, you may go up or down a rank at a Tournament Orgs discretion.\n\n"

        "The top time in the Gold leaderboard is awarded the same amount of points as Grandmaster, "
        "barring completed missions. "
        "XP will be better spread across the board and let different skill levels compete.\n\n"

        "If you think you're in the wrong rank, you could always contact an org to reconsider your rank.\n\n"
        "If you're unsure what your rank is, ask any online org."
    )
)
map_contest_embed = discord.Embed(
    description=(
        "# Map Making Challenge!\n"
        "### - Keep your map anonymous to keep as much bias out of judging as possible!\n"
        "### - Create a ***single level*** __not__ a multilevel map\n"
        "- We will give you a base framework to work off\n"
        "  - Sometimes there may be specific restrictions or requirements to spice things up "
        "(including difficulty, abilities, map choice)\n"
        "- The base code will be released at the beginning of the regular tournament\n"
        "- Submissions will be locked at the end of the regular tournament\n"
        "- Levels should be built for future tournament usage\n"
        "- Submit using the command `/map-contest` in the <#698003925168816139> channel\n"
        "## Judging\n"
        "- 3 judges will rate your map based on specific criteria\n"
        "- 1 referee to ensure fairness\n"
        "- Depending on the contest, some categories may be included or excluded\n"
        "- Each category will be scored 1-3 by each judge\n"
        "- Add all up for overall score\n"
        "### Categories\n"
        "- Flow/Ergonomics\n"
        "- Fulfils Restrictions/Requirements\n"
        "- Details\n"
        "- Aesthetic\n"
        "- Fun factor\n"
        "### Scoring\n"
        "- 1 -- Doesn't meet expectations\n"
        "- 2 -- Meets expectations\n"
        "- 3 -- Exceeds expectations\n"
        "## Prizes\n"
        "- XP based on score\n"
        "- Winning level guaranteed to be used in next tournament\n"
        "- Runner ups, while not guaranteed, may be used in future tournaments\n"
    )
)


all_info_embeds = {
    "Rules": rules_embed,
    "How to submit": submit_embed,
    "Ranks": ranks_embed,
    "Bracket Tournament": bracket_embed,
    "Map Contest": map_contest_embed,
}


class InfoButton(discord.ui.Button):
    def __init__(self, label: str, embed: discord.Embed):
        custom_id = "tournament-info-button" + label.replace(" ", "-").lower()
        super().__init__(label=label, custom_id=custom_id)
        self.embed = embed

    async def callback(self, itx: core.DoomItx):
        await itx.response.send_message(embed=self.embed, ephemeral=True)


class TournamentInfoView(discord.ui.View):
    def __init__(self, embeds: dict[str, discord.Embed]):
        super().__init__(timeout=None)
        for label, embed in embeds.items():
            self.add_item(InfoButton(label, embed))
