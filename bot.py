import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import os
from dotenv import load_dotenv
import imageio_ffmpeg

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Konfigurasi FFmpeg otomatis dari imageio_ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
    'executable': ffmpeg_path,
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Dictionary antrean lagu per guild: {guild_id: [YTDLSource, ...]}
queues = {}
current_playing = {}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f'Bot {bot.user} siap! {len(synced)} slash command synced.')
    except Exception as e:
        print(f'Gagal sync command: {e}')

def play_next(guild_id, guild, channel):
    if guild_id in queues and len(queues[guild_id]) > 0:
        next_source = queues[guild_id].pop(0)
        current_playing[guild_id] = next_source
        guild.voice_client.play(next_source, after=lambda e: play_next(guild_id, guild, channel))
        async def _announce():
            await channel.send(f'▶️ Memutar: **{next_source.title}**')
        asyncio.run_coroutine_threadsafe(_announce(), bot.loop)
    else:
        current_playing[guild_id] = None

@bot.tree.command(name='join', description='Bot masuk ke voice channel')
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("Anda harus berada di voice channel!", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client is not None:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    await interaction.response.send_message(f'Bergabung ke {channel.name}')

@bot.tree.command(name='play', description='Putar musik dari URL atau judul YouTube')
@app_commands.describe(query='URL YouTube atau judul lagu')
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    voice_client = interaction.guild.voice_client
    if not voice_client:
        if interaction.user.voice:
            voice_client = await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("Anda harus berada di voice channel!")
            return

    try:
        player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
    except Exception as e:
        await interaction.followup.send(f'Gagal memuat lagu: {e}')
        return

    guild_id = interaction.guild_id
    if guild_id not in queues:
        queues[guild_id] = []

    if voice_client.is_playing() or voice_client.is_paused():
        queues[guild_id].append(player)
        await interaction.followup.send(f'➕ Ditambahkan ke antrean: **{player.title}**')
    else:
        current_playing[guild_id] = player
        voice_client.play(player, after=lambda e: play_next(guild_id, interaction.guild, interaction.channel))
        await interaction.followup.send(f'▶️ Memutar: **{player.title}**')

@bot.tree.command(name='skip', description='Lewati lagu yang sedang diputar')
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message('⏭️ Lagu dilewati.')
    else:
        await interaction.response.send_message('Tidak ada lagu yang sedang diputar.', ephemeral=True)

@bot.tree.command(name='pause', description='Jeda musik')
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message('⏸️ Musik dijeda.')
    else:
        await interaction.response.send_message('Tidak ada musik yang diputar.', ephemeral=True)

@bot.tree.command(name='resume', description='Lanjutkan musik')
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message('▶️ Musik dilanjutkan.')
    else:
        await interaction.response.send_message('Musik tidak dalam keadaan jeda.', ephemeral=True)

@bot.tree.command(name='stop', description='Hentikan musik dan kosongkan antrean')
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    if guild_id in queues:
        queues[guild_id].clear()
    voice_client = interaction.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        await interaction.response.send_message('⏹️ Pemutar dihentikan dan bot keluar dari channel.')
    else:
        await interaction.response.send_message('Bot tidak berada di voice channel.', ephemeral=True)

@bot.tree.command(name='queue', description='Tampilkan antrean lagu')
async def queue_info(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    if guild_id not in queues or len(queues[guild_id]) == 0:
        await interaction.response.send_message('Antrean kosong.', ephemeral=True)
        return
    
    msg = "📜 **Antrean Lagu:**\n"
    for i, song in enumerate(queues[guild_id], 1):
        msg += f"{i}. {song.title}\n"
    await interaction.response.send_message(msg)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN tidak ditemukan di file .env")
    else:
        bot.run(TOKEN)
