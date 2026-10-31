import asyncio
import email.utils
import glob
import logging
import os
import tempfile
import time

import aiohttp
import discord
import yt_dlp
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

log = logging.getLogger("clanker")

# Discord will not let a normal (non-boosted) server upload bigger than this
MAX_UPLOAD_MB = 10

# can never be too sure of quality
DEFAULT_QUALITY = "128"
# quality is per user now so one person setting it doesn't ruin it for everyone
user_quality: dict[int, str] = {}


KEEP_WARM_SECONDS = 10


async def probe_network() -> None:
    # connection screwing around
    url = "https://discord.com/api/v10/gateway"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=40)) as session:
            for label in ("cold", "warm"):
                started = time.monotonic()
                async with session.get(url) as response:
                    date_header = response.headers.get("Date")
                    await response.read()
                elapsed = time.monotonic() - started
                log.info("%s Discord request: %.2fs", label.capitalize(), elapsed)

                if label == "warm" and date_header:
                    server_time = email.utils.parsedate_to_datetime(date_header).timestamp()
                    skew = time.time() - server_time - elapsed / 2
                    log.info("Local clock vs Discord: %+.1fs (about +/- 1s)", skew)
    except Exception as error:
        log.warning("Could not probe Discord latency: %s", error)


class ClankerTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        age = time.time() - interaction.created_at.timestamp()
        if age > 1.0:
            name = (interaction.data or {}).get("name", "unknown")
            log.warning(
                "Interaction %s for /%s reached  %.1fs ",
                interaction.id,
                name,
                age,
            )
        return True


class FuckingStupidClanker(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = ClankerTree(self)
        self._keep_warm_task: asyncio.Task | None = None

    async def setup_hook(self):
        await self.tree.sync()
        await probe_network()
        self._keep_warm_task = asyncio.create_task(self._keep_warm())

    async def _keep_warm(self) -> None:
        while not self.is_closed():
            await asyncio.sleep(KEEP_WARM_SECONDS)
            try:
                await self.http.get_bot_gateway()
            except Exception:
                pass

    async def close(self) -> None:
        if self._keep_warm_task is not None:
            self._keep_warm_task.cancel()
        await super().close()


bot = FuckingStupidClanker()


@bot.event
async def on_ready():
    print(f"\nI'm alive, unfortunately, and I'm {bot.user}")


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    original = getattr(error, "original", error)

    if isinstance(original, discord.NotFound) and original.code == 10062:
        age = time.time() - interaction.created_at.timestamp()
        log.warning(
            "Discord said nuh-uh to /%s with 10062 after %.1fs (3s max). "
            "The interaction had already expired.",
            getattr(interaction.command, "name", "unknown"),
            age,
        )
        return

    log.error(
        "Command /%s failed",
        getattr(interaction.command, "name", "unknown"),
        exc_info=original,
    )

    message = f"Something broke: {str(original)[:200]}"
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        # if even the error message fails there is nothing left to do
        pass


def resolve_quality(s: str) -> str:
    match s.lower().strip():
        case "good" | "h": return "128"
        case "bad" | "m": return "96"
        case "earrape" | "l": return "48"
        case "ihatemylife" | "z": return "24"
        case _: return DEFAULT_QUALITY


@bot.tree.command(name="quality", description="What u want the quality of ur song to be")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def preferredquality(interaction: discord.Interaction, user_input: str):
    quality = resolve_quality(user_input)
    user_quality[interaction.user.id] = quality
    await interaction.response.send_message(f"Quality is {quality} kbps")


def run_download(url, work_dir, current_quality: str):
    with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
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
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download(interaction: discord.Interaction, url: str):
    quality = user_quality.get(interaction.user.id, DEFAULT_QUALITY)
    await interaction.response.defer(thinking=True)
    try:
        with tempfile.TemporaryDirectory() as work_dir:
            await asyncio.get_running_loop().run_in_executor(
                None, run_download, url, work_dir, quality
            )

            files = glob.glob(os.path.join(work_dir, '*.mp3'))
            if not files:
                await interaction.followup.send("Shiiii: File could not be generated")
                return

            path = files[0]
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb > MAX_UPLOAD_MB:
                await interaction.followup.send(
                    f"That file is {size_mb:.1f} MB and Discord only lets me upload "
                    f"{MAX_UPLOAD_MB} MB. Try a worse quality."
                )
                return

            await interaction.followup.send("Your music taste sucks ", file=discord.File(path))  # this one isn't scripted yet
    except Exception as error:
        print(f"Error: {error}")
        try:
            await interaction.followup.send(f"Download failed: {str(error)[:100]}")
        except discord.HTTPException:
            pass


if __name__ == "__main__":
    discord.utils.setup_logging(level=logging.INFO)
    bot.run(TOKEN)
