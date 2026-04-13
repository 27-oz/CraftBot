import discord
from discord.ext import commands, tasks
import json, os
import feedparser
from datetime import datetime

DATA_FILE = "data/tiktok.json"

# We use an RSS bridge to monitor TikTok public profiles.
# Set RSSHUB_URL in your .env to your own RSSHub instance (free: https://rsshub.app)
# or leave default. Format: https://rsshub.app/tiktok/user/@username
RSSHUB_BASE = os.getenv("RSSHUB_URL", "https://rsshub.app")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class TikTok(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_tiktok.start()

    def cog_unload(self):
        self.check_tiktok.cancel()

    @tasks.loop(minutes=10)
    async def check_tiktok(self):
        data = load_data()
        for guild_id, cfg in data.items():
            for username, info in cfg.get("accounts", {}).items():
                channel = self.bot.get_channel(info["channel_id"])
                if not channel:
                    continue
                feed_url = f"{RSSHUB_BASE}/tiktok/user/@{username}"
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    continue
                latest = feed.entries[0]
                latest_id = latest.get("id", latest.get("link", ""))
                if latest_id == info.get("last_id"):
                    continue
                # New post detected
                data[guild_id]["accounts"][username]["last_id"] = latest_id
                save_data(data)
                embed = discord.Embed(
                    title=f"🎵 {username} posted on TikTok!",
                    description=latest.get("summary", "")[:300],
                    url=latest.get("link", ""),
                    color=0x010101
                )
                embed.set_footer(text="TikTok • " + latest.get("published", ""))
                role_ping = info.get("ping_role")
                content = f"<@&{role_ping}>" if role_ping else ""
                await channel.send(content=content, embed=embed)

    @check_tiktok.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def addtiktok(self, ctx, username: str, channel: discord.TextChannel, ping_role: discord.Role = None):
        """Track a TikTok account and post alerts in a channel.
        Usage: !addtiktok username #channel @Role(optional)"""
        username = username.lstrip("@")
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"accounts": {}}
        data[guild_id]["accounts"][username] = {
            "channel_id": channel.id,
            "last_id": None,
            "ping_role": ping_role.id if ping_role else None
        }
        save_data(data)
        await ctx.send(f"✅ Now tracking TikTok `@{username}` → {channel.mention}")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def removetiktok(self, ctx, username: str):
        """Stop tracking a TikTok account. Usage: !removetiktok username"""
        username = username.lstrip("@")
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id in data and username in data[guild_id].get("accounts", {}):
            del data[guild_id]["accounts"][username]
            save_data(data)
            await ctx.send(f"✅ No longer tracking `@{username}`.")
        else:
            await ctx.send("⚠️ That account wasn't being tracked.")

    @commands.hybrid_command()
    async def tiktoks(self, ctx):
        """List tracked TikTok accounts."""
        data = load_data()
        guild_id = str(ctx.guild.id)
        accounts = data.get(guild_id, {}).get("accounts", {})
        if not accounts:
            await ctx.send("No TikTok accounts are being tracked.")
            return
        lines = []
        for username, info in accounts.items():
            ch = ctx.guild.get_channel(info["channel_id"])
            lines.append(f"`@{username}` → {ch.mention if ch else 'unknown channel'}")
        embed = discord.Embed(title="🎵 Tracked TikTok Accounts", description="\n".join(lines), color=0x010101)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TikTok(bot))