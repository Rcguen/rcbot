import discord
from translator import translate_text
from storage import load_json, save_json
from config import LANGUAGES

CHANNEL_FILE = "data/channels.json"

translation_channels = load_json(CHANNEL_FILE)

def add_channel(channel_id):
    translation_channels[str(channel_id)] = True
    save_json(CHANNEL_FILE, translation_channels)

def remove_channel(channel_id):
    translation_channels.pop(str(channel_id), None)
    save_json(CHANNEL_FILE, translation_channels)

def is_translation_channel(channel_id):
    return str(channel_id) in translation_channels

async def translate_channel_message(message):

    text = message.content

    embed = discord.Embed(
        title="🌍 Channel Translation",
        color=0x00ffcc
    )

    for code, name in LANGUAGES.items():

        translated = translate_text(text, code)

        if translated:
            embed.add_field(
                name=name,
                value=translated,
                inline=False
            )

    await message.channel.send(embed=embed)