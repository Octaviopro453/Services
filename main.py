import discord
from discord.ext import commands
import youtube_dl
import asyncio
from flask import Flask, request

bot = commands.Bot(command_prefix='!', help_command=None)  # No registrar comandos

ytdl_format_options = {
    'format': 'bapest',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_format_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_format_options), data=data)

async def play_music(url, guild):
    voice_channel = guild.voice_client
    if voice_channel is None:
        return "El bot no está conectado a un canal de voz."

    player = await YTDLSource.from_url(url, loop=bot.loop)
    voice_channel.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    return f'Reproduciendo: {player.title}'

async def pause_music(guild):
    voice_channel = guild.voice_client
    if voice_channel.is_playing():
        voice_channel.pause()
        return "Música pausada."
    return "No hay música reproduciéndose."

async def resume_music(guild):
    voice_channel = guild.voice_client
    if voice_channel.is_paused():
        voice_channel.resume()
        return "Música reanudada."
    return "La música no está pausada."

async def stop_music(guild):
    voice_channel = guild.voice_client
    if voice_channel.is_playing() or voice_channel.is_paused():
        voice_channel.stop()
        return "Música detenida."
    return "No hay música reproduciéndose."

app = Flask(__name__)

@app.route("/", methods=['GET'])
def on_router():
    return "200"

@app.route("/api/musica/", methods=['POST'])
def handle_music():
    data = request.json
    if 'type' in data and 'música' in data:
        if data['type'] == 'play':
            url = data['música']
            guild = bot.guilds[0]  # Aquí puedes mejorar para seleccionar el servidor correcto
            response_message = asyncio.run(play_music(url, guild))
            return response_message
    return "Solicitud no válida."

@app.route("/api/control", methods=['GET'])
def control_music():
    params = request.args
    if 'type' in params:
        action_type = params['type']
        guild = bot.guilds[0]  # Aquí puedes mejorar para seleccionar el servidor correcto

        if action_type == 'pause':
            response_message = asyncio.run(pause_music(guild))
        elif action_type == 'resume':
            response_message = asyncio.run(resume_music(guild))
        elif action_type == 'stop':
            response_message = asyncio.run(stop_music(guild))
        else:
            response_message = "Tipo de acción no válido."
        
        return response_message
    return "Solicitud no válida."

@bot.event
async def on_ready():
    print(f'{bot.user} se ha conectado a Discord!')

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    import threading
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.run('YOUR_TOKEN_HERE')
