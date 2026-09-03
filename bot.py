import os
import glob
import tempfile
import discord
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# can never be too sure of quality 
user_quality = "128"
# I tried removing this once. and whole code decided to destroy itself. never removed the 13th line ever since
class FuckingStupidClanker(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = FuckingStupidClanker()

@bot.event
async def on_ready():
    print(f"\nI'm alive, unfortunately, and I'm {bot.user}")

def resolve_quality(s: str) -> str:
    match s.lower().strip():
        case "good" | "h": return "128"
        case "bad" | "m": return "96"
        case "earrape" | "l": return "48"
        case "ihatemylife" | "z": return "24"
        case _: return "128"

@bot.tree.command(name="quality", description="What u want the quality of ur song to be")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def preferredquality(interaction: discord.Interaction, user_input: str):
    global user_quality 
    user_quality = resolve_quality(user_input)
    await interaction.response.send_message(f"Quality is {user_quality} kbps")

def run_download(url, work_dir, current_quality: str):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get('duration')      
        if duration is None:
            raise ValueError("WTF I can't install a live stream")
        if duration > 600:
            raise ValueError("Video too long (max 10 minutes) unless owner buys me nitro")

    ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(work_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio', 
                    'preferredcodec': 'mp3',
                    'preferredquality': current_quality
                    },
                {'key': 'EmbedThumbnail'},
                ],
            'writethumbnail': True,
            'extractor_args': {
                'youtube': {'player_client': ['android']}
                },
            }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@bot.tree.command(name="download", description="Download audio from YouTube")
@app_commands.allowed_installs(guilds=True, users=True)
# too much constructors for my liking 
# TODO: Fix this shit
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download(interaction: discord.Interaction, url: str):
    global user_quality
    await interaction.response.defer(thinking=True)
    try:
        with tempfile.TemporaryDirectory() as work_dir:
            await bot.loop.run_in_executor(None, run_download, url, work_dir, user_quality)

            files = glob.glob(os.path.join(work_dir, '*.mp3'))
            if files:
                await interaction.followup.send(f"Your music taste sucks ", file=discord.File(files[0])) # this one isn't scripted yet
            else:
                await interaction.followup.send("Shiiii: File could not be generated")
    except Exception as error:
        print(f"Error: {error}")
        await interaction.followup.send(f"Download failed: {str(error)[:100]}")

if __name__ == "__main__":
    bot.run(TOKEN)
