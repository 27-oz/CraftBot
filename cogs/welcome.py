import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/welcome.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = load_data()
        guild_id = str(member.guild.id)
        if guild_id not in data:
            return
        cfg = data[guild_id]
        if "welcome_channel" not in cfg:
            return
        channel = member.guild.get_channel(cfg["welcome_channel"])
        if not channel:
            return
        msg = cfg.get("welcome_message", "Welcome to the server, {user}! ⛏️").replace("{user}", member.mention)
        embed = discord.Embed(
            title="⛏️ A new miner has joined!",
            description=msg,
            color=0x4CAF50
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        data = load_data()
        guild_id = str(member.guild.id)
        if guild_id not in data:
            return
        cfg = data[guild_id]
        if "goodbye_channel" not in cfg:
            return
        channel = member.guild.get_channel(cfg["goodbye_channel"])
        if not channel:
            return
        msg = cfg.get("goodbye_message", "{user} has left the server. 😢").replace("{user}", str(member))
        embed = discord.Embed(
            title="👋 A miner has left the server",
            description=msg,
            color=0xF44336
        )
        embed.set_footer(text=f"{member.guild.name} • Now {member.guild.member_count} members")
        await channel.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """Set the welcome channel (and optionally a custom message). Use {user} as a placeholder."""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {}
        data[guild_id]["welcome_channel"] = channel.id
        if message:
            data[guild_id]["welcome_message"] = message
        save_data(data)
        await ctx.send(f"✅ Welcome channel set to {channel.mention}!")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setgoodbye(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """Set the goodbye channel (and optionally a custom message). Use {user} as a placeholder."""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {}
        data[guild_id]["goodbye_channel"] = channel.id
        if message:
            data[guild_id]["goodbye_message"] = message
        save_data(data)
        await ctx.send(f"✅ Goodbye channel set to {channel.mention}!")

async def setup(bot):
    await bot.add_cog(Welcome(bot))