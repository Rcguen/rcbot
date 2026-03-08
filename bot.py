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

intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- WEB SERVER ----------------

app = Flask(__name__, template_folder="dashboard/templates")
app.secret_key = "rcbot_secret_key"


@app.route("/health")
def health():
    return "Bot running"


register_routes(app, client)


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)


Thread(target=run_web).start()

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

# ---------- MUSIC QUEUE ----------

    if content.startswith(prefix + "queue"):

        await show_queue(message)
        return

# ---------- MUSIC SHUFFLE ----------

    if content.startswith(prefix + "shuffle"):

        await shuffle_queue(message)
        return

# ---------- MUSIC VOLUME ----------

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

# ---------- MUSIC PAUSE ----------

    if content.startswith(prefix + "pause"):

        await pause_music(message)
        return

# ---------- MUSIC RESUME ----------

    if content.startswith(prefix + "resume"):

        await resume_music(message)
        return

# ---------- MUSIC SKIP ----------

    if content.startswith(prefix + "skip"):

        await skip_music(message)
        return

# ---------- MUSIC LEAVE ----------

    if content.startswith(prefix + "leave"):

        await leave_channel(message)
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

# ---------- PREFIX COMMAND ----------

    if content.startswith(prefix + "prefix"):

        parts = content.split()

        if len(parts) < 2:

            await message.channel.send(
                f"Current prefix: `{prefix}`\n"
                f"Change with `{prefix}prefix ,`\n"
                f"Reset with `{prefix}prefix reset`"
            )
            return

        new_prefix = parts[1]

        if new_prefix.lower() == "reset":

            prefixes.pop(user_id, None)
            save_json("data/user_prefixes.json", prefixes)

            await message.channel.send("✅ Prefix reset to default `!`")
            return

        prefixes[user_id] = new_prefix
        save_json("data/user_prefixes.json", prefixes)

        await message.channel.send(
            f"✅ Your prefix is now `{new_prefix}`"
        )
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

# ---------- SET LANGUAGE ----------

    if content.startswith(prefix + "setlang"):

        parts = content.split()

        if len(parts) < 2:
            await message.channel.send(
                f"Usage: {prefix}setlang <code>\nExample: {prefix}setlang vi"
            )
            return

        lang = parts[1]

        if lang not in LANGUAGES:
            await message.channel.send("❌ Unsupported language")
            return

        users[user_id] = lang
        save_json("data/user_languages.json", users)

        await message.channel.send(
            f"✅ Your language is now **{LANGUAGES[lang]}**"
        )
        return

# ---------- JOIN ROOM ----------

    if content.startswith(prefix + "joinroom"):

        translation_room.add(user_id)

        await message.channel.send(
            f"🌍 {message.author.name} joined multilingual room."
        )
        return

# ---------- MULTILINGUAL ROOM ----------

    if user_id in translation_room:

        try:
            detected = detect(content)
        except:
            detected = None

        target_languages = set()

        for uid in translation_room:

            if uid == user_id:
                continue

            lang = users.get(uid)

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

                    embed.add_field(
                        name=LANGUAGES[lang],
                        value=translated,
                        inline=False
                    )

                    lang_stats[lang] = lang_stats.get(lang, 0) + 1

            save_json("data/language_stats.json", lang_stats)

            await message.channel.send(embed=embed)

            stats["translations"] += 1
            save_json("data/stats.json", stats)

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

# ---------------- RUN BOT (AUTO RESTART) ----------------

while True:
    try:
        client.run(TOKEN)
    except Exception as e:
        print("Bot crashed:", e)