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
# --------------------------------------


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
AUTO_FILE = "auto_translate.json"

translation_cache = {}
cooldowns = {}
stats = {"translations": 0}


def load_file(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

user_languages = load_file(LANG_FILE)
user_prefixes = load_file(PREFIX_FILE)
auto_translate = load_file(AUTO_FILE)


def save_all():
    with open(LANG_FILE, "w") as f:
        json.dump(user_languages, f)

    with open(PREFIX_FILE, "w") as f:
        json.dump(user_prefixes, f)

    with open(AUTO_FILE, "w") as f:
        json.dump(auto_translate, f)


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


@client.event
async def on_ready():
    print(f"r.cBot is online as {client.user}")

    await client.change_presence(
        activity=discord.Game("🌍 Translating languages | !help")
    )


@client.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)
    content = message.content.strip()

    prefix = user_prefixes.get(user_id, DEFAULT_PREFIX)

    # -------- Cooldown --------
    if user_id in cooldowns:
        if time.time() - cooldowns[user_id] < 1.5:
            return

    cooldowns[user_id] = time.time()

    # -------- HELP --------
    if content.startswith(prefix + "help"):

        embed = discord.Embed(
            title="🤖 r.cBot Help",
            description="A multilingual translation bot 🌍",
            color=0x00ffcc
        )

        embed.add_field(
            name="🌍 Quick Translate",
            value=(
                f"`{prefix} hello world`\n"
                "Translate text into all supported languages."
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 Translate to Specific Language",
            value=(
                f"`{prefix}translate en 你好`\n"
                "Translate text to a specific language."
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Set Your Language",
            value=f"`{prefix}setlang en`",
            inline=False
        )

        embed.add_field(
            name="🔄 Auto Translation",
            value=f"`{prefix}autotranslate on/off`",
            inline=False
        )

        embed.add_field(
            name="🔧 Custom Prefix",
            value=f"`{prefix}setprefix $`",
            inline=False
        )

        embed.add_field(
            name="📊 Information",
            value=f"`{prefix}stats`\n`{prefix}languages`",
            inline=False
        )

        embed.add_field(
            name="🌎 Emoji Translation",
            value="React with 🇯🇵 🇨🇳 🇻🇳 🇺🇸 to translate.",
            inline=False
        )

        await message.channel.send(embed=embed)
        return

    # -------- STATS --------
    if content.startswith(prefix + "stats"):

        embed = discord.Embed(title="Bot Stats", color=0x00ffcc)

        embed.add_field(name="Translations", value=str(stats["translations"]))
        embed.add_field(name="Servers", value=str(len(client.guilds)))
        embed.add_field(name="Cache size", value=str(len(translation_cache)))

        await message.channel.send(embed=embed)
        return

    # -------- LANGUAGES --------
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

    # -------- SET PREFIX --------
    if content.startswith(prefix + "setprefix"):

        parts = content.split()

        if len(parts) < 2:
            return

        user_prefixes[user_id] = parts[1]
        save_all()

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
        save_all()

        await message.channel.send(f"Language set to **{languages[lang]}**")
        return

    # -------- AUTO TRANSLATE --------
    if content.startswith(prefix + "autotranslate"):

        parts = content.split()

        if len(parts) < 2:
            return

        if parts[1] == "on":
            auto_translate[user_id] = True
            await message.channel.send("Auto translation enabled")

        elif parts[1] == "off":
            auto_translate[user_id] = False
            await message.channel.send("Auto translation disabled")

        save_all()
        return

    # -------- QUICK TRANSLATE --------
    if content.startswith(prefix + " "):

        text = content[len(prefix)+1:].strip()

        embed = discord.Embed(title="🌍 Translation", color=0x00ffcc)

        for code, name in languages.items():

            translated = translate_text(text, code)

            if translated and translated.lower() != text.lower():
                embed.add_field(name=name, value=translated, inline=False)

        await message.channel.send(embed=embed)

        stats["translations"] += 1
        return

    # -------- REPLY TRANSLATION --------
    if content.startswith(prefix) and message.reference:

        replied = await message.channel.fetch_message(message.reference.message_id)
        text = replied.content

        embed = discord.Embed(title="🌍 Reply Translation", color=0x00ffcc)

        for code, name in languages.items():

            translated = translate_text(text, code)

            if translated:
                embed.add_field(name=name, value=translated, inline=False)

        await message.channel.send(embed=embed)

        stats["translations"] += 1
        return

    # -------- AUTO CONVERSATION TRANSLATION --------
    if auto_translate.get(user_id):

        target = user_languages.get(user_id)

        if target:

            try:
                detected = detect(content)
            except:
                detected = None

            if detected != target:

                translated = translate_text(content, target)

                if translated:

                    await message.channel.send(
                        f"🌍 **{languages[target]}:** {translated}"
                    )

                    stats["translations"] += 1


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


while True:
    try:
        client.run(TOKEN)
    except Exception as e:
        print("Bot crashed:", e)
        time.sleep(5)