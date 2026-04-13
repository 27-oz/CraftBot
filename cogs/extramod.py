import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
import json, os, re
from datetime import datetime, timedelta

DATA_FILE = "data/tempbans.json"

def load_data():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def parse_duration(s):
    match = re.fullmatch(r"(\d+)(s|m|h|d|w)", s.lower())
    if not match: return None
    v, u = int(match.group(1)), match.group(2)
    return v * {"s":1,"m":60,"h":3600,"d":86400,"w":604800}[u]

class ExtraMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_tempbans.start()

    def cog_unload(self):
        self.check_tempbans.cancel()

    @tasks.loop(minutes=1)
    async def check_tempbans(self):
        data = load_data()
        now = datetime.utcnow().timestamp()
        remaining = []
        for ban in data:
            if now >= ban["expires"]:
                guild = self.bot.get_guild(ban["guild_id"])
                if guild:
                    try:
                        user = await self.bot.fetch_user(ban["user_id"])
                        await guild.unban(user, reason="Temp-ban expired")
                    except Exception: pass
            else: remaining.append(ban)
        save_data(remaining)

    @check_tempbans.before_loop
    async def before_check(self): await self.bot.wait_until_ready()

    @app_commands.command(name="tempban", description="Temporarily ban a member")
    @app_commands.describe(member="The member", duration="Duration e.g. 1d, 12h, 1w", reason="Reason")
    async def tempban_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        seconds = parse_duration(duration)
        if not seconds: await interaction.response.send_message("Invalid duration. Use: `30m`, `12h`, `1d`, `1w`", ephemeral=True); return
        expires = (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()
        try: await member.send(f"You were temp-banned from **{interaction.guild.name}**\nReason: {reason}\nDuration: {duration}")
        except discord.Forbidden: pass
        await member.ban(reason=f"[Temp-ban {duration}] {reason}")
        data = load_data()
        data.append({"guild_id": interaction.guild.id, "user_id": member.id, "expires": expires, "reason": reason})
        save_data(data)
        await interaction.response.send_message(f"Temp-banned {member} for {duration} — {reason}")

    @commands.hybrid_command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def tempban_prefix(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        seconds = parse_duration(duration)
        if not seconds: await ctx.send("Invalid duration."); return
        expires = (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()
        await member.ban(reason=f"[Temp-ban {duration}] {reason}")
        data = load_data()
        data.append({"guild_id": ctx.guild.id, "user_id": member.id, "expires": expires, "reason": reason})
        save_data(data)
        await ctx.send(f"Temp-banned {member} for {duration} — {reason}")

    @app_commands.command(name="lock", description="Lock a channel so only staff can talk")
    @app_commands.describe(channel="The channel to lock (defaults to current)")
    async def lock_slash(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"{channel.mention} has been locked.")

    @commands.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_prefix(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{channel.mention} has been locked.")

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(channel="The channel to unlock (defaults to current)")
    async def unlock_slash(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"{channel.mention} has been unlocked.")

    @commands.hybrid_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_prefix(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{channel.mention} has been unlocked.")

    @app_commands.command(name="slowmode", description="Set slowmode on the current channel")
    @app_commands.describe(seconds="Seconds between messages (0 to disable)")
    async def slowmode_slash(self, interaction: discord.Interaction, seconds: int = 0):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Slowmode set to **{seconds}s**." if seconds else "Slowmode disabled.")

    @commands.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode_prefix(self, ctx, seconds: int = 0):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Slowmode set to **{seconds}s**." if seconds else "Slowmode disabled.")

async def setup(bot):
    await bot.add_cog(ExtraMod(bot))
