import discord
from discord import app_commands
from deep_translator import GoogleTranslator
from langdetect import detect
import json
import os
import time
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN")
DEFAULT_PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- Web Server ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "r.cBot running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run).start()

# ---------------- Languages ----------------

languages = {
    "en":"English",
    "vi":"Vietnamese",
    "ja":"Japanese",
    "zh-CN":"Chinese",
    "ko":"Korean",
    "tl":"Filipino",
    "es":"Spanish",
    "fr":"French",
    "de":"German",
    "ru":"Russian",
    "pt":"Portuguese",
    "it":"Italian",
    "ar":"Arabic",
    "hi":"Hindi",
    "th":"Thai",
    "id":"Indonesian",
    "tr":"Turkish",
    "pl":"Polish",
    "nl":"Dutch",
    "sv":"Swedish",
    "fi":"Finnish",
    "da":"Danish",
    "no":"Norwegian"
}

flag_languages = {
    "🇺🇸":"en",
    "🇻🇳":"vi",
    "🇯🇵":"ja",
    "🇨🇳":"zh-CN",
    "🇰🇷":"ko",
    "🇪🇸":"es",
    "🇫🇷":"fr",
    "🇩🇪":"de",
    "🇷🇺":"ru",
    "🇮🇹":"it",
    "🇸🇦":"ar",
    "🇮🇳":"hi",
    "🇹🇭":"th",
    "🇮🇩":"id",
    "🇹🇷":"tr"
}

# ---------------- Files ----------------

LANG_FILE="user_languages.json"
CHANNEL_FILE="channels.json"

def load_file(file):
    if os.path.exists(file):
        with open(file) as f:
            return json.load(f)
    return {}

user_languages = load_file(LANG_FILE)
translation_channels = load_file(CHANNEL_FILE)

def save():
    with open(LANG_FILE,"w") as f:
        json.dump(user_languages,f)

    with open(CHANNEL_FILE,"w") as f:
        json.dump(translation_channels,f)

# ---------------- Cache ----------------

translation_cache={}
cooldowns={}
translation_room=set()

stats={"translations":0}

# ---------------- Translation ----------------

def translate_text(text,target):

    key=(text,target)

    if key in translation_cache:
        return translation_cache[key]

    try:
        result = GoogleTranslator(source="auto",target=target).translate(text)
        translation_cache[key]=result
        return result
    except:
        return None

# ---------------- Dropdown ----------------

class LanguageSelect(discord.ui.Select):

    def __init__(self,text):

        self.text=text

        options=[
            discord.SelectOption(label=name,value=code)
            for code,name in list(languages.items())[:25]
        ]

        super().__init__(
            placeholder="Choose language",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self,interaction:discord.Interaction):

        lang=self.values[0]
        translated=translate_text(self.text,lang)

        await interaction.response.send_message(
            f"🌍 **{languages[lang]}**\n{translated}",
            ephemeral=True
        )

class TranslateView(discord.ui.View):

    def __init__(self,text):
        super().__init__(timeout=120)
        self.add_item(LanguageSelect(text))

# ---------------- Ready ----------------

@client.event
async def on_ready():

    await tree.sync()

    print("Bot online:",client.user)

    await client.change_presence(
        activity=discord.Game("🌍 Multilingual Chat | !help")
    )

# ---------------- Slash Command ----------------

@tree.command(name="translate",description="Translate text")
async def translate(interaction:discord.Interaction,text:str,language:str):

    translated=translate_text(text,language)

    if translated:
        await interaction.response.send_message(
            f"🌍 **{languages.get(language,language)}**\n{translated}"
        )

# ---------------- Message ----------------

@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id=str(message.author.id)
    content=message.content.strip()

    # cooldown
    if user_id in cooldowns:
        if time.time()-cooldowns[user_id] < 1.5:
            return

    cooldowns[user_id]=time.time()

    # help
    if content.startswith("!help"):

        embed=discord.Embed(
            title="🌍 Translation Bot",
            description="Multilingual communication",
            color=0x00ffcc
        )

        embed.add_field(name="Slash Translate",value="/translate text language")
        embed.add_field(name="Set Language",value="!setlang en")
        embed.add_field(name="Join Room",value="!joinroom")
        embed.add_field(name="Leave Room",value="!leaveroom")
        embed.add_field(name="Stats",value="!stats")

        await message.channel.send(embed=embed)
        return

    # set language
    if content.startswith("!setlang"):

        parts=content.split()

        if len(parts)<2:
            return

        lang=parts[1]

        if lang not in languages:
            await message.channel.send("Unsupported language")
            return

        user_languages[user_id]=lang
        save()

        await message.channel.send(
            f"Language set to {languages[lang]}"
        )

        return

    # join room
    if content.startswith("!joinroom"):

        translation_room.add(user_id)

        await message.channel.send(
            f"{message.author.name} joined multilingual room"
        )

        return

    # leave room
    if content.startswith("!leaveroom"):

        translation_room.discard(user_id)

        await message.channel.send(
            f"{message.author.name} left multilingual room"
        )

        return

    # multilingual room
    if user_id in translation_room:

        try:
            detected=detect(content)
        except:
            detected=None

        targets=set()

        for uid in translation_room:

            if uid==user_id:
                continue

            lang=user_languages.get(uid)

            if lang and lang!=detected:
                targets.add(lang)

        if targets:

            embed=discord.Embed(
                title="🌍 Multilingual Translation",
                color=0x00ffcc
            )

            for lang in targets:

                translated=translate_text(content,lang)

                if translated:

                    embed.add_field(
                        name=languages[lang],
                        value=translated,
                        inline=False
                    )

            await message.channel.send(embed=embed)

            stats["translations"]+=1

    # dropdown translation
    if len(content)<200 and not content.startswith("!"):

        await message.reply(
            "🌍 Translate message",
            view=TranslateView(content),
            mention_author=False
        )

# ---------------- Reaction Translate ----------------

@client.event
async def on_reaction_add(reaction,user):

    if user.bot:
        return

    if reaction.emoji in flag_languages:

        lang=flag_languages[reaction.emoji]

        translated=translate_text(
            reaction.message.content,
            lang
        )

        if translated:

            await reaction.message.channel.send(
                f"{reaction.emoji} **{languages[lang]}**\n{translated}"
            )

# ---------------- Auto Restart ----------------

while True:

    try:
        client.run(TOKEN)

    except Exception as e:

        print("Crash:",e)

        time.sleep(5)