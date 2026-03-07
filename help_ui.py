import discord
from config import DEFAULT_PREFIX

class HelpView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=180)

    # ---------- COMMANDS ----------
    @discord.ui.button(label="Commands", emoji="🔧", style=discord.ButtonStyle.primary)
    async def commands(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="🔧 Commands",
            description="Main bot commands",
            color=0x00ffcc
        )

        embed.add_field(name="Translate", value="/translate text language", inline=False)
        embed.add_field(name="Set Language", value=f"{DEFAULT_PREFIX}setlang vi", inline=False)
        embed.add_field(name="Languages", value=f"{DEFAULT_PREFIX}languages", inline=False)
        embed.add_field(name="Prefix", value=f"{DEFAULT_PREFIX}prefix ,", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    # ---------- LANGUAGES ----------
    @discord.ui.button(label="Languages", emoji="🌍", style=discord.ButtonStyle.success)
    async def languages(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="🌍 Language System",
            description="How languages work",
            color=0x00ffcc
        )

        embed.add_field(
            name="Set Your Language",
            value=f"{DEFAULT_PREFIX}setlang vi",
            inline=False
        )

        embed.add_field(
            name="View Languages",
            value=f"{DEFAULT_PREFIX}languages",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    # ---------- ROOMS ----------
    @discord.ui.button(label="Rooms", emoji="💬", style=discord.ButtonStyle.secondary)
    async def rooms(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="💬 Multilingual Rooms",
            description="Chat with people in different languages",
            color=0x00ffcc
        )

        embed.add_field(name="Join Room", value=f"{DEFAULT_PREFIX}joinroom", inline=False)
        embed.add_field(name="Leave Room", value=f"{DEFAULT_PREFIX}leaveroom", inline=False)
        embed.add_field(name="Room Users", value=f"{DEFAULT_PREFIX}roomusers", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    # ---------- STATS ----------
    @discord.ui.button(label="Stats", emoji="📊", style=discord.ButtonStyle.danger)
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="📊 Bot Statistics",
            description="View bot stats",
            color=0x00ffcc
        )

        embed.add_field(name="Stats Command", value=f"{DEFAULT_PREFIX}stats", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)