import discord
from discord.ext import commands, tasks
import json, os, aiohttp

DATA_FILE = "data/twitch.json"

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.access_token = None
        self.check_twitch.start()

    def cog_unload(self):
        self.check_twitch.cancel()

    async def get_token(self):
        if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
            return None
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": TWITCH_CLIENT_ID,
                    "client_secret": TWITCH_CLIENT_SECRET,
                    "grant_type": "client_credentials"
                }
            ) as resp:
                data = await resp.json()
                return data.get("access_token")

    async def is_live(self, username):
        if not self.access_token:
            self.access_token = await self.get_token()
        if not self.access_token:
            return None
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.twitch.tv/helix/streams?user_login={username}",
                headers={
                    "Client-ID": TWITCH_CLIENT_ID,
                    "Authorization": f"Bearer {self.access_token}"
                }
            ) as resp:
                data = await resp.json()
                streams = data.get("data", [])
                return streams[0] if streams else None

    @tasks.loop(minutes=5)
    async def check_twitch(self):
        if not TWITCH_CLIENT_ID:
            return
        data = load_data()
        for guild_id, cfg in data.items():
            for username, info in cfg.get("accounts", {}).items():
                channel = self.bot.get_channel(info["channel_id"])
                if not channel:
                    continue
                stream = await self.is_live(username)
                was_live = info.get("live", False)
                if stream and not was_live:
                    # Just went live!
                    data[guild_id]["accounts"][username]["live"] = True
                    save_data(data)
                    embed = discord.Embed(
                        title=f"🔴 {username} is LIVE on Twitch!",
                        description=stream.get("title", ""),
                        url=f"https://twitch.tv/{username}",
                        color=0x9146FF
                    )
                    embed.add_field(name="🎮 Game", value=stream.get("game_name", "Unknown"), inline=True)
                    embed.add_field(name="👥 Viewers", value=str(stream.get("viewer_count", 0)), inline=True)
                    if stream.get("thumbnail_url"):
                        thumb = stream["thumbnail_url"].replace("{width}", "320").replace("{height}", "180")
                        embed.set_image(url=thumb)
                    role_ping = info.get("ping_role")
                    content = f"<@&{role_ping}>" if role_ping else ""
                    await channel.send(content=content, embed=embed)
                elif not stream and was_live:
                    data[guild_id]["accounts"][username]["live"] = False
                    save_data(data)

    @check_twitch.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def addtwitch(self, ctx, username: str, channel: discord.TextChannel, ping_role: discord.Role = None):
        """Track a Twitch streamer. Usage: !addtwitch username #channel @Role(optional)"""
        if not TWITCH_CLIENT_ID:
            await ctx.send("⚠️ Twitch credentials not configured. Add `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` to your `.env`.")
            return
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"accounts": {}}
        data[guild_id]["accounts"][username.lower()] = {
            "channel_id": channel.id,
            "live": False,
            "ping_role": ping_role.id if ping_role else None
        }
        save_data(data)
        await ctx.send(f"✅ Now tracking Twitch `{username}` → {channel.mention}")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def removetwitch(self, ctx, username: str):
        """Stop tracking a Twitch streamer. Usage: !removetwitch username"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id in data and username.lower() in data[guild_id].get("accounts", {}):
            del data[guild_id]["accounts"][username.lower()]
            save_data(data)
            await ctx.send(f"✅ No longer tracking `{username}`.")
        else:
            await ctx.send("⚠️ That streamer wasn't being tracked.")

async def setup(bot):
    await bot.add_cog(Twitch(bot))