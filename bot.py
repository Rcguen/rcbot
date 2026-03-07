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

# ---------------- DATA ----------------

users = load_json("data/user_languages.json")
prefixes = load_json("data/user_prefixes.json")
stats = load_json("data/stats.json")

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

    await interaction.response.send_message(
        f"🌍 **{LANGUAGES.get(language, language)}**\n{translated}"
    )

# ---------------- MESSAGE EVENT ----------------

@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)

    prefix = prefixes.get(user_id, DEFAULT_PREFIX)

    content = message.content.strip()

# ---------- PREFIX ----------

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

# ---------- HELP ----------

    if content.startswith(prefix + "help"):

        embed = discord.Embed(
            title="🤖 r.cBot Commands",
            color=0x00ffcc
        )

        embed.add_field(name="Translate", value="/translate text language", inline=False)
        embed.add_field(name="Set Language", value=f"{prefix}setlang vi", inline=False)
        embed.add_field(name="Languages", value=f"{prefix}languages", inline=False)
        embed.add_field(name="Prefix", value=f"{prefix}prefix ,", inline=False)
        embed.add_field(name="Join Room", value=f"{prefix}joinroom", inline=False)
        embed.add_field(name="Leave Room", value=f"{prefix}leaveroom", inline=False)
        embed.add_field(name="Room Users", value=f"{prefix}roomusers", inline=False)
        embed.add_field(name="Stats", value=f"{prefix}stats", inline=False)

        await message.channel.send(embed=embed)
        return

# ---------- STATS ----------

    if content.startswith(prefix + "stats"):

        embed = discord.Embed(
            title="📊 r.cBot Statistics",
            color=0x00ffcc
        )

        embed.add_field(
            name="Translations",
            value=stats.get("translations", 0)
        )

        embed.add_field(
            name="Servers",
            value=len(client.guilds)
        )

        embed.add_field(
            name="Users",
            value=len(client.users)
        )

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

# ---------- LANGUAGES ----------

    if content.startswith(prefix + "languages"):

        text = ""

        for code, name in LANGUAGES.items():
            text += f"{code} — {name}\n"

        embed = discord.Embed(
            title="🌍 Supported Languages",
            description=text,
            color=0x00ffcc
        )

        await message.channel.send(embed=embed)
        return

# ---------- JOIN ROOM ----------

    if content.startswith(prefix + "joinroom"):

        translation_room.add(user_id)

        await message.channel.send(
            f"🌍 {message.author.name} joined multilingual room."
        )
        return

# ---------- LEAVE ROOM ----------

    if content.startswith(prefix + "leaveroom"):

        translation_room.discard(user_id)

        await message.channel.send(
            f"👋 {message.author.name} left multilingual room."
        )
        return

# ---------- ROOM USERS ----------

    if content.startswith(prefix + "roomusers"):

        text = "🌍 Multilingual Room Users\n\n"

        for uid in translation_room:

            lang = users.get(uid, "unknown")

            text += f"<@{uid}> → {LANGUAGES.get(lang, lang)}\n"

        await message.channel.send(text)
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

            await message.channel.send(embed=embed)

            stats["translations"] += 1
            save_json("data/stats.json", stats)

# ---------- IMAGE OCR ----------

    if message.attachments:

        url = message.attachments[0].url

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

        if translated:

            await reaction.message.channel.send(
                f"{reaction.emoji} **{LANGUAGES[lang]}**\n{translated}"
            )

# ---------------- RUN BOT ----------------

client.run(TOKEN)