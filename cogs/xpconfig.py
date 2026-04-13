import discord
from discord.ext import commands
from discord import app_commands
import json, os, re
from datetime import datetime, timedelta

CONFIG_FILE = "data/xp_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE) as f: return json.load(f)
def save_config(data):
    with open(CONFIG_FILE, "w") as f: json.dump(data, f, indent=2)

def parse_duration(s):
    match = re.fullmatch(r"(\d+)(m|h|d)", s.lower())
    if not match: return None
    v, u = int(match.group(1)), match.group(2)
    return v * {"m":60,"h":3600,"d":86400}[u]

def get_xp_multiplier(guild_id):
    config = load_config()
    boost = config.get(str(guild_id), {}).get("boost")
    if not boost or datetime.utcnow().timestamp() > boost["expires"]: return 1.0
    return boost["multiplier"]

def is_xp_blacklisted(guild_id, channel_id):
    config = load_config()
    return str(channel_id) in config.get(str(guild_id), {}).get("blacklist", [])

class XPConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xpboost", description="Start an XP multiplier event")
    @app_commands.describe(multiplier="XP multiplier (e.g. 2 for double XP)", duration="Duration e.g. 1h, 30m")
    async def xpboost_slash(self, interaction: discord.Interaction, multiplier: float, duration: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        if not 1 <= multiplier <= 10: await interaction.response.send_message("Multiplier must be between 1 and 10.", ephemeral=True); return
        seconds = parse_duration(duration)
        if not seconds: await interaction.response.send_message("Invalid duration. Use: `30m`, `2h`, `1d`", ephemeral=True); return
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["boost"] = {"multiplier": multiplier, "expires": (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()}
        save_config(config)
        embed = discord.Embed(title="XP Boost Active!", description=f"**{multiplier}x XP** for the next **{duration}**!", color=0xFFD700)
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="xpboost")
    @commands.has_permissions(manage_guild=True)
    async def xpboost_prefix(self, ctx, multiplier: float, duration: str):
        seconds = parse_duration(duration)
        if not seconds: await ctx.send("Invalid duration."); return
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["boost"] = {"multiplier": multiplier, "expires": (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()}
        save_config(config)
        await ctx.send(f"**{multiplier}x XP boost** active for **{duration}**!")

    @app_commands.command(name="xpboostend", description="End the current XP boost early")
    async def xpboostend_slash(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        config = load_config()
        gid = str(interaction.guild.id)
        if gid in config and "boost" in config[gid]:
            del config[gid]["boost"]; save_config(config)
            await interaction.response.send_message("XP boost ended.")
        else: await interaction.response.send_message("No active XP boost.", ephemeral=True)

    @commands.hybrid_command(name="xpboostend")
    @commands.has_permissions(manage_guild=True)
    async def xpboostend_prefix(self, ctx):
        config = load_config()
        gid = str(ctx.guild.id)
        if gid in config and "boost" in config[gid]:
            del config[gid]["boost"]; save_config(config)
            await ctx.send("XP boost ended.")
        else: await ctx.send("No active XP boost.")

    @app_commands.command(name="xpboostcheck", description="Check if an XP boost is active")
    async def xpboostcheck_slash(self, interaction: discord.Interaction):
        await self._xpboostcheck(interaction.response.send_message, interaction.guild.id)

    @commands.hybrid_command(name="xpboostcheck")
    async def xpboostcheck_prefix(self, ctx):
        await self._xpboostcheck(ctx.send, ctx.guild.id)

    async def _xpboostcheck(self, send, guild_id):
        config = load_config()
        boost = config.get(str(guild_id), {}).get("boost")
        if not boost or datetime.utcnow().timestamp() > boost["expires"]:
            await send("No XP boost is currently active."); return
        expires = datetime.utcfromtimestamp(boost["expires"])
        remaining = expires - datetime.utcnow()
        hours, rem = divmod(int(remaining.total_seconds()), 3600)
        await send(f"**{boost['multiplier']}x XP boost** active! Expires in **{hours}h {rem//60}m**.")

    @app_commands.command(name="xpblacklist", description="Stop XP being earned in a channel")
    @app_commands.describe(channel="The channel to blacklist")
    async def xpblacklist_slash(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        if "blacklist" not in config[gid]: config[gid]["blacklist"] = []
        cid = str(channel.id)
        if cid in config[gid]["blacklist"]: await interaction.response.send_message(f"{channel.mention} is already blacklisted.", ephemeral=True); return
        config[gid]["blacklist"].append(cid)
        save_config(config)
        await interaction.response.send_message(f"{channel.mention} is now blacklisted from XP.")

    @commands.hybrid_command(name="xpblacklist")
    @commands.has_permissions(manage_guild=True)
    async def xpblacklist_prefix(self, ctx, channel: discord.TextChannel):
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config: config[gid] = {}
        if "blacklist" not in config[gid]: config[gid]["blacklist"] = []
        config[gid]["blacklist"].append(str(channel.id))
        save_config(config)
        await ctx.send(f"{channel.mention} is now blacklisted from XP.")

    @app_commands.command(name="xpunblacklist", description="Remove a channel from the XP blacklist")
    @app_commands.describe(channel="The channel to unblacklist")
    async def xpunblacklist_slash(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        config = load_config()
        gid = str(interaction.guild.id)
        blacklist = config.get(gid, {}).get("blacklist", [])
        cid = str(channel.id)
        if cid not in blacklist: await interaction.response.send_message(f"{channel.mention} isn't blacklisted.", ephemeral=True); return
        blacklist.remove(cid)
        config[gid]["blacklist"] = blacklist
        save_config(config)
        await interaction.response.send_message(f"{channel.mention} removed from XP blacklist.")

    @commands.hybrid_command(name="xpunblacklist")
    @commands.has_permissions(manage_guild=True)
    async def xpunblacklist_prefix(self, ctx, channel: discord.TextChannel):
        config = load_config()
        gid = str(ctx.guild.id)
        blacklist = config.get(gid, {}).get("blacklist", [])
        if str(channel.id) in blacklist: blacklist.remove(str(channel.id))
        config[gid]["blacklist"] = blacklist
        save_config(config)
        await ctx.send(f"{channel.mention} removed from XP blacklist.")

    @app_commands.command(name="xpblacklisted", description="List all XP-blacklisted channels")
    async def xpblacklisted_slash(self, interaction: discord.Interaction):
        await self._xpblacklisted(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="xpblacklisted")
    async def xpblacklisted_prefix(self, ctx):
        await self._xpblacklisted(ctx.send, ctx.guild)

    async def _xpblacklisted(self, send, guild):
        config = load_config()
        blacklist = config.get(str(guild.id), {}).get("blacklist", [])
        if not blacklist: await send("No channels are XP-blacklisted."); return
        channels = [guild.get_channel(int(cid)) for cid in blacklist]
        mentions = [c.mention for c in channels if c]
        embed = discord.Embed(title="XP Blacklisted Channels", description="\n".join(mentions), color=0xF44336)
        await send(embed=embed)

async def setup(bot):
    await bot.add_cog(XPConfig(bot))
