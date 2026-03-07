import discord
from discord import app_commands
from flask import Flask
from threading import Thread
import os

from config import *
from storage import load_json,save_json
from translator import translate_text
from ui import TranslateView
from globalchat import send_global
from ocr_translate import translate_image

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- WEB SERVER ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "r.cBot running"

def run_web():

    port = int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0",port=port)

Thread(target=run_web).start()

# ---------------- DATA ----------------

users = load_json("data/user_languages.json")
prefixes = load_json("data/user_prefixes.json")
stats = load_json("data/stats.json")

if "translations" not in stats:
    stats["translations"] = 0

# ---------------- READY ----------------

@client.event
async def on_ready():

    print("Bot online:",client.user)

    await tree.sync()

# ---------------- SLASH COMMAND ----------------

@tree.command(name="translate",description="Translate text")

async def translate_cmd(interaction:discord.Interaction,text:str,language:str):

    translated = translate_text(text,language)

    stats["translations"] += 1

    save_json("data/stats.json",stats)

    await interaction.response.send_message(
        f"🌍 **{LANGUAGES.get(language,language)}**\n{translated}"
    )

# ---------------- MESSAGE EVENT ----------------

@client.event
async def on_message(message):

    if message.author.bot:
        return

# image translation

    if message.attachments:

        url = message.attachments[0].url

        result = translate_image(url,"en")

        if result:

            await message.channel.send(
                f"🖼 Image Translation\n{result}"
            )

# dropdown translate

    if len(message.content) < 200:

        await message.reply(
            "🌍 Translate message",
            view=TranslateView(message.content),
            mention_author=False
        )

# global chat

    await send_global(client,message)

# ---------------- REACTION TRANSLATE ----------------

@client.event
async def on_reaction_add(reaction,user):

    if user.bot:
        return

    if reaction.emoji in FLAG_LANGUAGES:

        lang = FLAG_LANGUAGES[reaction.emoji]

        translated = translate_text(
            reaction.message.content,
            lang
        )

        await reaction.message.channel.send(
            f"{reaction.emoji} {translated}"
        )

# ---------------- RUN ----------------

client.run(TOKEN)