import discord
from discord.ext import commands
import asyncio
import yt_dlp

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("webpage_url")
        self.duration = data.get("duration", 0)
        self.thumbnail = data.get("thumbnail")

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if "entries" in data:
            data = data["entries"][0]
        filename = data["url"]
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # guild_id -> list of (url, title)
        self.current = {}  # guild_id -> YTDLSource

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.voice_client.disconnect()
            return
        url, title = queue.pop(0)
        try:
            source = await YTDLSource.from_url(url, loop=self.bot.loop)
            self.current[ctx.guild.id] = source
            ctx.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
            )
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"[{source.title}]({source.url})",
                color=0xFF0000
            )
            if source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            mins, secs = divmod(source.duration, 60)
            embed.add_field(name="Duration", value=f"{mins}:{secs:02d}", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Error playing track: {e}")
            await self.play_next(ctx)

    @commands.hybrid_command()
    async def join(self, ctx):
        """Join your voice channel. Usage: !join"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
        if ctx.voice_client:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()
        await ctx.send(f"✅ Joined **{ctx.author.voice.channel.name}**!")

    @commands.hybrid_command()
    async def play(self, ctx, *, query: str):
        """Play a song from YouTube. Usage: !play never gonna give you up"""
        if not ctx.author.voice:
            await ctx.send("❌ Join a voice channel first!")
            return
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                source = await YTDLSource.from_url(query, loop=self.bot.loop)
            except Exception as e:
                await ctx.send(f"⚠️ Couldn't find that song: {e}")
                return

        if ctx.voice_client.is_playing():
            self.get_queue(ctx.guild.id).append((query, source.title))
            await ctx.send(f"➕ Added to queue: **{source.title}**")
        else:
            self.get_queue(ctx.guild.id).append((query, source.title))
            await self.play_next(ctx)

    @commands.hybrid_command()
    async def skip(self, ctx):
        """Skip the current song. Usage: !skip"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped!")
        else:
            await ctx.send("❌ Nothing is playing.")

    @commands.hybrid_command()
    async def queue(self, ctx):
        """Show the music queue. Usage: !queue"""
        q = self.get_queue(ctx.guild.id)
        current = self.current.get(ctx.guild.id)
        if not current and not q:
            await ctx.send("📭 The queue is empty.")
            return
        embed = discord.Embed(title="🎵 Music Queue", color=0xFF0000)
        if current:
            embed.add_field(name="Now Playing", value=f"🎵 {current.title}", inline=False)
        if q:
            lines = [f"{i+1}. {title}" for i, (_, title) in enumerate(q[:10])]
            embed.add_field(name="Up Next", value="\n".join(lines), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def pause(self, ctx):
        """Pause the music. Usage: !pause"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.send("❌ Nothing is playing.")

    @commands.hybrid_command()
    async def resume(self, ctx):
        """Resume the music. Usage: !resume"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.send("❌ Nothing is paused.")

    @commands.hybrid_command()
    async def stop(self, ctx):
        """Stop music and clear the queue. Usage: !stop"""
        if ctx.voice_client:
            self.queues[ctx.guild.id] = []
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Stopped and disconnected.")
        else:
            await ctx.send("❌ Not in a voice channel.")

    @commands.hybrid_command()
    async def volume(self, ctx, vol: int):
        """Set volume (0-100). Usage: !volume 50"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("❌ Nothing is playing.")
            return
        if not 0 <= vol <= 100:
            await ctx.send("❌ Volume must be between 0 and 100.")
            return
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"🔊 Volume set to **{vol}%**.")

    @commands.hybrid_command()
    async def nowplaying(self, ctx):
        """Show what's currently playing. Usage: !nowplaying"""
        current = self.current.get(ctx.guild.id)
        if not current or not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("❌ Nothing is playing.")
            return
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{current.title}]({current.url})",
            color=0xFF0000
        )
        if current.thumbnail:
            embed.set_thumbnail(url=current.thumbnail)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))