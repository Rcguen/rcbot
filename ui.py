import discord
from config import LANGUAGES
from translator import translate_text

class LanguageDropdown(discord.ui.Select):

    def __init__(self,text):

        self.text = text

        options = []

        for code,name in LANGUAGES.items():

            options.append(
                discord.SelectOption(
                    label=name,
                    value=code
                )
            )

        options = options[:25]

        super().__init__(
            placeholder="Select language",
            options=options
        )

    async def callback(self,interaction:discord.Interaction):

        lang = self.values[0]

        translated = translate_text(self.text,lang)

        await interaction.response.send_message(
            f"🌍 **{LANGUAGES[lang]}**\n{translated}",
            ephemeral=True
        )

class TranslateView(discord.ui.View):

    def __init__(self,text):

        super().__init__(timeout=120)

        self.add_item(LanguageDropdown(text))