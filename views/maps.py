import discord


class MapSubmit(discord.ui.Modal, title="MapSubmit"):
    code = discord.ui.TextInput(label="Share Code")
    desc = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph)
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

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Thanks for your response, {self.code}!", ephemeral=True
        )
