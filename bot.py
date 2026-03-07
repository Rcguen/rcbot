import discord
from discord import app_commands
from flask import Flask
from threading import Thread
import os

from config import *
from storage import load_json, save_json
from translator import translate_text
from ui import TranslateView
from globalchat import send_global
from ocr_translate import translate_image

# ---------------- DISCORD SETUP ----------------

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- WEB SERVER (Render) ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "r.cBot running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

# ---------------- LOAD DATA ----------------

users = load_json("data/user_languages.json")
prefixes = load_json("data/user_prefixes.json")
stats = load_json("data/stats.json")

if "translations" not in stats:
    stats["translations"] = 0

# ---------------- READY EVENT ----------------

@client.event
async def on_ready():

    print("Bot online:", client.user)

    await tree.sync()

    await client.change_presence(
        activity=discord.Game("🌍 Translation Bot | !help")
    )

# ---------------- SLASH TRANSLATE ----------------

@tree.command(name="translate", description="Translate text")

async def translate_cmd(interaction: discord.Interaction, text: str, language: str):

    translated = translate_text(text, language)

    stats["translations"] += 1
    save_json("data/stats.json", stats)

    await interaction.response.send_message(
        f"🌍 **{LANGUAGES.get(language, language)}**\n{translated}"
    )

# ---------------- MESSAGE EVENT ----------------

@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)

    # get user prefix or default
    prefix = prefixes.get(user_id, DEFAULT_PREFIX)

    content = message.content.strip()

    # ---------------- PREFIX COMMAND ----------------

    if content.startswith(prefix + "prefix"):

        parts = content.split()

        if len(parts) < 2:

            await message.channel.send(
                f"Current prefix: `{prefix}`\n"
                f"Change it with `{prefix}prefix ,`\n"
                f"Reset with `{prefix}prefix reset`"
            )
            return

        new_prefix = parts[1]

        if new_prefix.lower() == "reset":

            prefixes.pop(user_id, None)
            save_json("data/user_prefixes.json", prefixes)

            await message.channel.send(
                "✅ Prefix reset to default `!`"
            )
            return

        prefixes[user_id] = new_prefix
        save_json("data/user_prefixes.json", prefixes)

        await message.channel.send(
            f"✅ Your prefix is now `{new_prefix}`"
        )
        return

    # ---------------- HELP COMMAND ----------------

    if content.startswith(prefix + "help"):

        embed = discord.Embed(
            title="🤖 r.cBot Commands",
            color=0x00ffcc
        )

        embed.add_field(
            name="Translate",
            value="/translate text language",
            inline=False
        )

        embed.add_field(
            name="Change Prefix",
            value=f"{prefix}prefix ,",
            inline=False
        )

        embed.add_field(
            name="Reset Prefix",
            value=f"{prefix}prefix reset",
            inline=False
        )

        embed.add_field(
            name="Stats",
            value=f"{prefix}stats",
            inline=False
        )

        embed.add_field(
            name="Help",
            value=f"{prefix}help",
            inline=False
        )

        await message.channel.send(embed=embed)
        return

    # ---------------- STATS COMMAND ----------------

    if content.startswith(prefix + "stats"):

        embed = discord.Embed(
            title="📊 r.cBot Statistics",
            color=0x00ffcc
        )

        embed.add_field(
            name="Total Translations",
            value=stats.get("translations", 0),
            inline=False
        )

        embed.add_field(
            name="Servers",
            value=len(client.guilds),
            inline=True
        )

        embed.add_field(
            name="Users",
            value=len(client.users),
            inline=True
        )

        await message.channel.send(embed=embed)
        return

    # ---------------- IMAGE OCR ----------------

    if message.attachments:

        url = message.attachments[0].url

        result = translate_image(url, "en")

        if result:

            stats["translations"] += 1
            save_json("data/stats.json", stats)

            await message.channel.send(
                f"🖼 **Image Translation**\n{result}"
            )

    # ---------------- DROPDOWN TRANSLATION ----------------

    if len(message.content) < 200 and not content.startswith(prefix):

        await message.reply(
            "🌍 Translate message",
            view=TranslateView(message.content),
            mention_author=False
        )

    # ---------------- GLOBAL CHAT ----------------

    await send_global(client, message)

# ---------------- REACTION TRANSLATE ----------------

@client.event
async def on_reaction_add(reaction, user):

    if user.bot:
        return

    if reaction.emoji in FLAG_LANGUAGES:

        lang = FLAG_LANGUAGES[reaction.emoji]

        translated = translate_text(
            reaction.message.content,
            lang
        )

        if translated:

            await reaction.message.channel.send(
                f"{reaction.emoji} **{LANGUAGES[lang]}**\n{translated}"
            )

# ---------------- RUN BOT ----------------

client.run(TOKEN)