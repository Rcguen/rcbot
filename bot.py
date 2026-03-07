import discord
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

# ---------- Render Web Server ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "r.cBot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()
# ---------------------------------------


languages = {
    "en": "English",
    "zh-CN": "Chinese",
    "ja": "Japanese",
    "vi": "Vietnamese",
    "tl": "Filipino"
}

flag_languages = {
    "🇯🇵": "ja",
    "🇨🇳": "zh-CN",
    "🇻🇳": "vi",
    "🇺🇸": "en"
}

LANG_FILE = "user_languages.json"
PREFIX_FILE = "user_prefixes.json"

translation_cache = {}
cooldowns = {}
translation_room = set()

stats = {"translations": 0}


# ---------- File Handling ----------
def load_file(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

user_languages = load_file(LANG_FILE)
user_prefixes = load_file(PREFIX_FILE)

def save_files():
    with open(LANG_FILE, "w") as f:
        json.dump(user_languages, f)

    with open(PREFIX_FILE, "w") as f:
        json.dump(user_prefixes, f)


# ---------- Translation Cache ----------
def translate_text(text, target):

    key = (text, target)

    if key in translation_cache:
        return translation_cache[key]

    try:
        translated = GoogleTranslator(source="auto", target=target).translate(text)
        translation_cache[key] = translated
        return translated
    except:
        return None


# ---------- Translation Buttons ----------
class TranslateButtons(discord.ui.View):

    def __init__(self, text):
        super().__init__(timeout=120)
        self.text = text

    async def translate(self, interaction, lang):

        translated = translate_text(self.text, lang)

        if translated:
            await interaction.response.send_message(
                f"🌍 **{languages[lang]}:** {translated}",
                ephemeral=True
            )

    @discord.ui.button(label="🇺🇸 English", style=discord.ButtonStyle.primary)
    async def en(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.translate(interaction, "en")

    @discord.ui.button(label="🇯🇵 Japanese", style=discord.ButtonStyle.primary)
    async def ja(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.translate(interaction, "ja")

    @discord.ui.button(label="🇨🇳 Chinese", style=discord.ButtonStyle.primary)
    async def zh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.translate(interaction, "zh-CN")

    @discord.ui.button(label="🇻🇳 Vietnamese", style=discord.ButtonStyle.primary)
    async def vi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.translate(interaction, "vi")


# ---------- Bot Ready ----------
@client.event
async def on_ready():

    print(f"r.cBot is online as {client.user}")

    await client.change_presence(
        activity=discord.Game("🌍 Multilingual Chat | !help")
    )


# ---------- Message Handling ----------
@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)
    content = message.content.strip()

    prefix = user_prefixes.get(user_id, DEFAULT_PREFIX)

    # cooldown
    if user_id in cooldowns:
        if time.time() - cooldowns[user_id] < 1.5:
            return
    cooldowns[user_id] = time.time()

    # -------- HELP --------
    if content.startswith(prefix + "help"):

        embed = discord.Embed(
            title="🤖 r.cBot Help",
            description="Multilingual translation bot 🌍",
            color=0x00ffcc
        )

        embed.add_field(name="Quick Translate", value=f"`{prefix} hello`", inline=False)
        embed.add_field(name="Set Language", value=f"`{prefix}setlang en`", inline=False)
        embed.add_field(name="Join Translation Room", value=f"`{prefix}joinroom`", inline=False)
        embed.add_field(name="Leave Room", value=f"`{prefix}leaveroom`", inline=False)
        embed.add_field(name="Room Users", value=f"`{prefix}roomusers`", inline=False)
        embed.add_field(name="Change Prefix", value=f"`{prefix}setprefix $`", inline=False)
        embed.add_field(name="Stats", value=f"`{prefix}stats`", inline=False)
        embed.add_field(name="Languages", value=f"`{prefix}languages`", inline=False)
        embed.add_field(name="Emoji Translate", value="🇯🇵 🇨🇳 🇻🇳 🇺🇸", inline=False)

        await message.channel.send(embed=embed)
        return

    # -------- STATS --------
    if content.startswith(prefix + "stats"):

        embed = discord.Embed(title="Bot Stats", color=0x00ffcc)
        embed.add_field(name="Translations", value=str(stats["translations"]))
        embed.add_field(name="Servers", value=str(len(client.guilds)))
        embed.add_field(name="Cache", value=str(len(translation_cache)))

        await message.channel.send(embed=embed)
        return

    # -------- LANGUAGES --------
    if content.startswith(prefix + "languages"):

        text = ""
        for code, name in languages.items():
            text += f"{code} — {name}\n"

        embed = discord.Embed(title="Supported Languages", description=text, color=0x00ffcc)
        await message.channel.send(embed=embed)
        return

    # -------- SET PREFIX --------
    if content.startswith(prefix + "setprefix"):

        parts = content.split()

        if len(parts) < 2:
            return

        user_prefixes[user_id] = parts[1]
        save_files()

        await message.channel.send(f"Prefix changed to `{parts[1]}`")
        return

    # -------- SET LANGUAGE --------
    if content.startswith(prefix + "setlang"):

        parts = content.split()

        if len(parts) < 2:
            return

        lang = parts[1]

        if lang not in languages:
            await message.channel.send("Unsupported language")
            return

        user_languages[user_id] = lang
        save_files()

        await message.channel.send(f"Language set to **{languages[lang]}**")
        return

    # -------- JOIN ROOM --------
    if content.startswith(prefix + "joinroom"):

        translation_room.add(user_id)

        await message.channel.send(
            f"🌍 {message.author.name} joined multilingual chat."
        )
        return

    # -------- LEAVE ROOM --------
    if content.startswith(prefix + "leaveroom"):

        translation_room.discard(user_id)

        await message.channel.send(
            f"👋 {message.author.name} left multilingual chat."
        )
        return

    # -------- ROOM USERS --------
    if content.startswith(prefix + "roomusers"):

        if not translation_room:
            await message.channel.send("Room empty.")
            return

        text = "🌍 **Multilingual Room Users**\n\n"

        for uid in translation_room:
            lang = user_languages.get(uid, "unknown")
            text += f"<@{uid}> → {languages.get(lang, lang)}\n"

        await message.channel.send(text)
        return

    # -------- QUICK TRANSLATE --------
    if content.startswith(prefix + " "):

        text = content[len(prefix)+1:].strip()

        embed = discord.Embed(title="🌍 Translation", color=0x00ffcc)

        for code, name in languages.items():
            translated = translate_text(text, code)

            if translated:
                embed.add_field(name=name, value=translated, inline=False)

        await message.channel.send(embed=embed)
        stats["translations"] += 1
        return

    # -------- MULTILINGUAL ROOM (OPTIMIZED) --------
    if user_id in translation_room:

        try:
            detected = detect(content)
        except:
            detected = None

        target_languages = set()

        for uid in translation_room:

            if uid == user_id:
                continue

            lang = user_languages.get(uid)

            if lang and lang != detected:
                target_languages.add(lang)

        if target_languages:

            embed = discord.Embed(
                title="🌍 Multilingual Translation",
                color=0x00ffcc
            )

            for lang in target_languages:

                translated = translate_text(content, lang)

                if translated:

                    users = [
                        f"<@{uid}>"
                        for uid in translation_room
                        if user_languages.get(uid) == lang
                    ]

                    embed.add_field(
                        name=f"{languages[lang]} → {' '.join(users)}",
                        value=translated,
                        inline=False
                    )

            await message.channel.send(embed=embed)
            stats["translations"] += 1

    # -------- TRANSLATION BUTTONS --------
    if not content.startswith(prefix):

        if len(content) < 200:

            await message.reply(
                "🌍 Translate this message:",
                view=TranslateButtons(content),
                mention_author=False
            )


# ---------- Emoji Reaction Translation ----------
@client.event
async def on_reaction_add(reaction, user):

    if user.bot:
        return

    if reaction.emoji in flag_languages:

        lang = flag_languages[reaction.emoji]
        text = reaction.message.content

        translated = translate_text(text, lang)

        if translated:

            await reaction.message.channel.send(
                f"{reaction.emoji} **{languages[lang]}:** {translated}"
            )

            stats["translations"] += 1


# ---------- Auto Restart ----------
while True:
    try:
        client.run(TOKEN)
    except Exception as e:
        print("Bot crashed:", e)
        time.sleep(5)