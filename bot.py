
import discord
from discord import app_commands
from flask import Flask
from threading import Thread
import os
from langdetect import detect

from config import *
from storage import load_json, save_json
from translator import translate_text
from ui import TranslateView
from help_ui import HelpView
from globalchat import send_global
from ocr_translate import translate_image

from features.channel_control import add_channel, remove_channel, is_enabled, get_channels
from features.music import (
    play_song,
    pause_music,
    resume_music,
    skip_music,
    leave_channel,
    show_queue,
    shuffle_queue,
    set_volume
)

from dashboard.server import register_routes

# ---------------- DISCORD SETUP ----------------

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- WEB SERVER ----------------

app = Flask(__name__, template_folder="dashboard/templates")
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret")


@app.route("/health")
def health():
    return "Bot running"


register_routes(app, client)


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)


Thread(target=run_web, daemon=True).start()

# ---------------- DATA ----------------

users = load_json("data/user_languages.json")
prefixes = load_json("data/user_prefixes.json")
stats = load_json("data/stats.json")
lang_stats = load_json("data/language_stats.json")

translation_room = set()

if "translations" not in stats:
    stats["translations"] = 0

# ---------------- READY ----------------


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

    lang_stats[language] = lang_stats.get(language, 0) + 1
    save_json("data/language_stats.json", lang_stats)

    await interaction.response.send_message(
        f"🌍 **{LANGUAGES.get(language, language)}**\n{translated}"
    )

# ---------------- MESSAGE EVENT ----------------


@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)
    content = message.content.strip()

    prefix = prefixes.get(user_id, DEFAULT_PREFIX)

    # ---------- SET CHANNEL ----------

    if content.startswith(prefix + "setchannel"):

        add_channel(message.channel.id)
        await message.channel.send("✅ Bot enabled in this channel.")
        return

    # ---------- CHANNEL RESTRICTION ----------

    if not is_enabled(message.channel.id):
        return

    # ---------- MUSIC PLAY ----------

    if content.startswith(prefix + "play"):

        query = content[len(prefix)+5:]

        if not query:
            await message.channel.send("❌ Usage: !play <song>")
            return

        await play_song(message, query)
        return

    # ---------- MUSIC COMMANDS ----------

    if content.startswith(prefix + "queue"):
        await show_queue(message)
        return

    if content.startswith(prefix + "shuffle"):
        await shuffle_queue(message)
        return

    if content.startswith(prefix + "pause"):
        await pause_music(message)
        return

    if content.startswith(prefix + "resume"):
        await resume_music(message)
        return

    if content.startswith(prefix + "skip"):
        await skip_music(message)
        return

    if content.startswith(prefix + "leave"):
        await leave_channel(message)
        return

    if content.startswith(prefix + "volume"):

        parts = content.split()

        if len(parts) < 2:
            return

        try:
            vol = int(parts[1])
        except:
            return

        await set_volume(message, vol)
        return

    # ---------- REMOVE CHANNEL ----------

    if content.startswith(prefix + "removechannel"):

        remove_channel(message.channel.id)
        await message.channel.send("❌ Bot disabled in this channel.")
        return

    # ---------- LIST CHANNELS ----------

    if content.startswith(prefix + "channels"):

        text = "🌍 Enabled Channels\n\n"

        for cid in get_channels():
            text += f"<#{cid}>\n"

        await message.channel.send(text)
        return

    # ---------- HELP ----------

    if content.startswith(prefix + "help"):

        embed = discord.Embed(
            title="🤖 r.cBot Help",
            description="Use buttons below to navigate commands",
            color=0x00ffcc
        )

        embed.add_field(
            name="Features",
            value="🌍 Translation\n🎵 Music\n💬 Multilingual Rooms\n🔧 Prefix System\n📊 Stats",
            inline=False
        )

        await message.channel.send(embed=embed, view=HelpView())
        return

    # ---------- STATS ----------

    if content.startswith(prefix + "stats"):

        embed = discord.Embed(
            title="📊 r.cBot Statistics",
            color=0x00ffcc
        )

        embed.add_field(name="Translations", value=stats.get("translations", 0))
        embed.add_field(name="Servers", value=len(client.guilds))
        embed.add_field(name="Users", value=len(client.users))

        await message.channel.send(embed=embed)
        return

    # ---------- IMAGE OCR ----------

    if message.attachments:

        file = message.attachments[0]

        if file.size > 3_000_000:
            await message.channel.send("⚠ Image too large for OCR.")
            return

        url = file.url

        result = translate_image(url, "en")

        if result:
            await message.channel.send(
                f"🖼 Image Translation\n{result}"
            )

    # ---------- DROPDOWN TRANSLATE ----------

    if len(content) < 200 and not content.startswith(prefix):

        await message.reply(
            "🌍 Translate message",
            view=TranslateView(content),
            mention_author=False
        )

    # ---------- GLOBAL CHAT ----------

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

        lang_stats[lang] = lang_stats.get(lang, 0) + 1
        save_json("data/language_stats.json", lang_stats)

        await reaction.message.channel.send(
            f"{reaction.emoji} **{LANGUAGES[lang]}**\n{translated}"
        )

# ---------------- RUN BOT ----------------

if __name__ == "__main__":

    token = TOKEN

    if not token:
        raise ValueError("TOKEN environment variable is not set")

    client.run(token)
