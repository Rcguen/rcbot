import discord
import yt_dlp
import asyncio
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ---------- CONFIG ----------

DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"

SPOTIFY_CLIENT_ID = "ef09cb0e0faf45798431825e8ef75365"
SPOTIFY_CLIENT_SECRET = "a6f92f69c0834177a784423b00d9c829"

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

ydl_opts = {
    "format": "bestaudio",
    "quiet": True
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

queues = {}
volumes = {}
autoplay = {}

# ---------- BOT SETUP ----------

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ---------- PLAYER UI ----------

class PlayerControls(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(label="▶ Resume", style=discord.ButtonStyle.green)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("⏹ Stopped", ephemeral=True)

# ---------- JOIN VC ----------

async def join_channel(message):

    if not message.author.voice:
        await message.channel.send("❌ Join a voice channel first.")
        return None

    channel = message.author.voice.channel
    vc = message.guild.voice_client

    if not vc:
        vc = await channel.connect()

    return vc

# ---------- PLAY SONG ----------

async def play_song(message, query):

    guild_id = message.guild.id
    vc = await join_channel(message)

    if not vc:
        return

    if "spotify.com" in query:
        await handle_spotify_playlist(message, query)
        return

    if "playlist" in query:
        await handle_youtube_playlist(message, query)
        return

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]

    url = info["url"]
    title = info["title"]

    queues.setdefault(guild_id, []).append((url, title))

    await message.channel.send(f"🎶 Added: **{title}**")

    if not vc.is_playing():
        await play_next(message)

# ---------- PLAY NEXT ----------

async def play_next(message):

    guild_id = message.guild.id
    vc = message.guild.voice_client

    if guild_id not in queues or not queues[guild_id]:

        if autoplay.get(guild_id):
            await autoplay_song(message)

        return

    url, title = queues[guild_id].pop(0)

    volume = volumes.get(guild_id, 0.5)

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
        volume=volume
    )

    vc.play(
        source,
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(message), vc.loop
        )
    )

    view = PlayerControls()

    await message.channel.send(
        f"🎵 Now playing **{title}**",
        view=view
    )

# ---------- YOUTUBE PLAYLIST ----------

async def handle_youtube_playlist(message, url):

    guild_id = message.guild.id

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    for entry in info["entries"]:
        queues.setdefault(guild_id, []).append((entry["url"], entry["title"]))

    await message.channel.send("📀 YouTube playlist added.")

    vc = message.guild.voice_client

    if not vc.is_playing():
        await play_next(message)

# ---------- SPOTIFY PLAYLIST ----------

async def handle_spotify_playlist(message, url):

    guild_id = message.guild.id

    playlist_id = url.split("/")[-1].split("?")[0]

    results = sp.playlist_items(playlist_id)

    while results:

        for item in results["items"]:
            track = item["track"]

            if not track:
                continue

            name = track["name"]
            artist = track["artists"][0]["name"]

            search = f"{artist} {name}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    f"ytsearch:{search}",
                    download=False
                )["entries"][0]

            queues.setdefault(guild_id, []).append(
                (info["url"], info["title"])
            )

        results = sp.next(results) if results["next"] else None

    await message.channel.send("🎵 Spotify playlist added.")

    vc = message.guild.voice_client

    if not vc.is_playing():
        await play_next(message)

# ---------- AUTOPLAY ----------

async def autoplay_song(message):

    guild_id = message.guild.id

    query = "lofi hip hop"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"ytsearch:{query}",
            download=False
        )["entries"][0]

    queues.setdefault(guild_id, []).append(
        (info["url"], info["title"])
    )

    await play_next(message)

# ---------- COMMANDS ----------

async def show_queue(message):

    guild_id = message.guild.id

    if guild_id not in queues or not queues[guild_id]:
        await message.channel.send("📭 Queue empty.")
        return

    text = "**🎶 Queue**\n\n"

    for i, song in enumerate(queues[guild_id], start=1):
        text += f"{i}. {song[1]}\n"

    await message.channel.send(text)


async def shuffle_queue(message):

    guild_id = message.guild.id

    if guild_id in queues:
        random.shuffle(queues[guild_id])

    await message.channel.send("🔀 Queue shuffled")


async def set_volume(message, vol):

    guild_id = message.guild.id
    volumes[guild_id] = vol / 100

    vc = message.guild.voice_client

    if vc and vc.source:
        vc.source.volume = vol / 100

    await message.channel.send(f"🔊 Volume {vol}%")

# ---------- MESSAGE HANDLER ----------

@client.event
async def on_message(message):

    if message.author.bot:
        return

    if message.content.startswith("!play"):
        query = message.content.replace("!play ", "")
        await play_song(message, query)

    elif message.content == "!queue":
        await show_queue(message)

    elif message.content == "!shuffle":
        await shuffle_queue(message)

    elif message.content.startswith("!volume"):
        vol = int(message.content.split(" ")[1])
        await set_volume(message, vol)

    elif message.content == "!autoplay":
        guild_id = message.guild.id
        autoplay[guild_id] = not autoplay.get(guild_id, False)
        await message.channel.send(
            f"🤖 Autoplay: {autoplay[guild_id]}"
        )

# ---------- READY ----------

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

client.run(DISCORD_TOKEN)