import discord
from deep_translator import GoogleTranslator
import json
import os

TOKEN = os.getenv("TOKEN")

DEFAULT_PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

languages = {
    "en": "English",
    "zh-CN": "Chinese",
    "ja": "Japanese",
    "vi": "Vietnamese",
    "tl": "Filipino"
}

stats = {"translations": 0}

LANG_FILE = "user_languages.json"
PREFIX_FILE = "user_prefixes.json"

if os.path.exists(LANG_FILE):
    with open(LANG_FILE, "r") as f:
        user_languages = json.load(f)
else:
    user_languages = {}

if os.path.exists(PREFIX_FILE):
    with open(PREFIX_FILE, "r") as f:
        user_prefixes = json.load(f)
else:
    user_prefixes = {}

def save_data():
    with open(LANG_FILE, "w") as f:
        json.dump(user_languages, f)

    with open(PREFIX_FILE, "w") as f:
        json.dump(user_prefixes, f)


def translate_text(text, target):
    try:
        return GoogleTranslator(source="auto", target=target).translate(text)
    except:
        return None


@client.event
async def on_ready():
    print(f"r.cBot is online as {client.user}")


@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)
    content = message.content.strip()
    prefix = user_prefixes.get(user_id, DEFAULT_PREFIX)

    # HELP
    if content.startswith(prefix + "help"):

        embed = discord.Embed(
            title="🤖 r.cBot Help",
            description="Commands list",
            color=0x00ffcc
        )

        embed.add_field(
            name="Translate",
            value=f"`{prefix} <text>`",
            inline=False
        )

        embed.add_field(
            name="Translate specific language",
            value=f"`{prefix}translate <lang> <text>`",
            inline=False
        )

        embed.add_field(
            name="Set language",
            value=f"`{prefix}setlang <code>`",
            inline=False
        )

        embed.add_field(
            name="Change prefix",
            value=f"`{prefix}setprefix <symbol>`",
            inline=False
        )

        embed.add_field(
            name="Other commands",
            value=f"`{prefix}ping` `{prefix}languages` `{prefix}about` `{prefix}stats`",
            inline=False
        )

        await message.channel.send(embed=embed)
        return

    # PING
    if content.startswith(prefix + "ping"):
        latency = round(client.latency * 1000)
        await message.channel.send(f"🏓 Pong! {latency}ms")
        return

    # ABOUT
    if content.startswith(prefix + "about"):

        embed = discord.Embed(
            title="r.cBot",
            description="Multilingual translator bot",
            color=0x00ffcc
        )

        embed.add_field(name="Languages", value="Chinese, English, Japanese, Vietnamese, Filipino")
        embed.add_field(name="Version", value="Pro")

        await message.channel.send(embed=embed)
        return

    # STATS
    if content.startswith(prefix + "stats"):

        embed = discord.Embed(title="Bot Stats", color=0x00ffcc)

        embed.add_field(name="Translations", value=str(stats["translations"]))
        embed.add_field(name="Servers", value=str(len(client.guilds)))

        await message.channel.send(embed=embed)
        return

    # LANGUAGES
    if content.startswith(prefix + "languages"):

        text = ""

        for code, name in languages.items():
            text += f"{code} — {name}\n"

        embed = discord.Embed(
            title="Supported Languages",
            description=text,
            color=0x00ffcc
        )

        await message.channel.send(embed=embed)
        return

    # SET PREFIX
    if content.startswith(prefix + "setprefix"):

        parts = content.split()

        if len(parts) < 2:
            await message.channel.send("Usage: setprefix <symbol>")
            return

        new_prefix = parts[1]

        user_prefixes[user_id] = new_prefix
        save_data()

        await message.channel.send(f"Prefix changed to `{new_prefix}`")
        return

    # SET LANGUAGE
    if content.startswith(prefix + "setlang"):

        parts = content.split()

        if len(parts) < 2:
            await message.channel.send("Usage: setlang en / zh-CN / ja / vi / tl")
            return

        lang = parts[1]

        if lang not in languages:
            await message.channel.send("Unsupported language")
            return

        user_languages[user_id] = lang
        save_data()

        await message.channel.send(f"Language set to **{languages[lang]}**")
        return

    # TRANSLATE SPECIFIC LANGUAGE
    if content.startswith(prefix + "translate"):

        parts = content.split(maxsplit=2)

        if len(parts) < 3:
            await message.channel.send("Usage: translate <lang> <text>")
            return

        lang = parts[1]
        text = parts[2]

        translated = translate_text(text, lang)

        if translated:

            embed = discord.Embed(
                title=f"{languages.get(lang, lang)}",
                description=translated,
                color=0x00ffcc
            )

            await message.channel.send(embed=embed)
            stats["translations"] += 1

        return

    # REPLY TRANSLATION
    if content.startswith(prefix) and message.reference:

        replied = await message.channel.fetch_message(message.reference.message_id)
        text = replied.content

        embed = discord.Embed(title="Reply Translation", color=0x00ffcc)

        for code, name in languages.items():

            translated = translate_text(text, code)

            if translated and translated.lower() != text.lower():
                embed.add_field(name=name, value=translated, inline=False)

        await message.channel.send(embed=embed)
        stats["translations"] += 1
        return

    # PREFIX TRANSLATE
    if content.startswith(prefix + " "):

        text = content[len(prefix)+1:].strip()

        embed = discord.Embed(title="🌍 Translation", color=0x00ffcc)

        for code, name in languages.items():

            translated = translate_text(text, code)

            if translated and translated.lower() != text.lower():
                embed.add_field(name=name, value=translated, inline=False)

        await message.channel.send(embed=embed)

        stats["translations"] += 1


@client.event
async def on_reaction_add(reaction, user):

    if user.bot:
        return

    if str(reaction.emoji) == "🌍":

        message = reaction.message
        text = message.content

        embed = discord.Embed(title="🌍 Reaction Translation", color=0x00ffcc)

        for code, name in languages.items():

            translated = translate_text(text, code)

            if translated and translated.lower() != text.lower():
                embed.add_field(name=name, value=translated, inline=False)

        await message.channel.send(embed=embed)

        stats["translations"] += 1


client.run(TOKEN)