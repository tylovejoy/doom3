from logging import getLogger

import discord.ui
from discord.ui import TextInput

from views import ConfirmButton

logger = getLogger(__name__)


class TournamentStartModal(discord.ui.Modal, title="Tournament Submit Wizard"):
    children: list[TextInput]

    def __init__(self, category: str) -> None:
        super().__init__()
        self.category = category
        self.add_item(TextInput(label="Map Code"))
        self.add_item(TextInput(label="Level Name"))
        self.add_item(TextInput(label="Map Creator"))
        self.code = None
        self.level = None
        self.creator = None

    async def on_submit(self, itx: discord.Interaction):
        logger.info("helo")
        self.code = self.children[0].value.upper()
        self.level = self.children[1].value.capitalize()
        self.creator = self.children[2].value
        await itx.response.send_message(
            f"{self.category} has been set. Continue adding maps or proceed above.\n"
            f"Code: {self.code}\nLevel: {self.level}\nCreator: {self.creator}",
            ephemeral=True,
        )


class TournamentStartView(discord.ui.View):
    """View for Tournament Start wizard."""

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.confirm_button = ConfirmButton()
        self.original_itx = interaction
        self.ta_modal = None
        self.mc_modal = None
        self.hc_modal = None
        self.bo_modal = None
        self.bracket = False

    @discord.ui.button(
        label="Bracket Toggle Off", style=discord.ButtonStyle.grey, row=0
    )
    async def bracket_toggle(
        self,
        itx: discord.Interaction,
        button: discord.ui.Button,
    ):
        await itx.response.defer(ephemeral=True)
        self.bracket = not self.bracket
        toggles = (
            ("On", discord.ButtonStyle.blurple)
            if self.bracket
            else ("Off", discord.ButtonStyle.grey)
        )
        button.label = f"Bracket Toggle {toggles[0]}"
        button.style = toggles[1]
        await self.original_itx.edit_original_response(view=self)

    @discord.ui.button(label="TA", style=discord.ButtonStyle.red, row=1)
    async def ta(
        self,
        itx: discord.Interaction,
        button: discord.ui.Button,
    ):
        """Time Attack button."""
        button.style = discord.ButtonStyle.green
        self.ta_modal = TournamentStartModal("Time Attack")
        await itx.response.send_modal(self.ta_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="MC", style=discord.ButtonStyle.red, row=1)
    async def mc(
        self,
        itx: discord.Interaction,
        button: discord.ui.Button,
    ):
        """Mildcore button."""
        button.style = discord.ButtonStyle.green
        self.mc_modal = TournamentStartModal("Mildcore")
        await itx.response.send_modal(self.mc_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="HC", style=discord.ButtonStyle.red, row=1)
    async def hc(
        self,
        itx: discord.Interaction,
        button: discord.ui.Button,
    ):
        """Hardcore button."""
        button.style = discord.ButtonStyle.green
        self.hc_modal = TournamentStartModal("Hardcore")
        await itx.response.send_modal(self.hc_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="BO", style=discord.ButtonStyle.red, row=1)
    async def bo(
        self,
        itx: discord.Interaction,
        button: discord.ui.Button,
    ):
        """Bonus button."""
        button.style = discord.ButtonStyle.green
        self.bo_modal = TournamentStartModal("Bonus")
        await itx.response.send_modal(self.bo_modal)
        await self.enable_accept_button()

    async def enable_accept_button(self):
        """Enable confirm button when other buttons are pressed."""
        if any(
            [
                x is discord.ButtonStyle.green
                for x in [self.bo.style, self.ta.style, self.mc.style, self.hc.style]
            ]
        ):
            self.add_item(self.confirm_button)
        await self.original_itx.edit_original_response(view=self)
