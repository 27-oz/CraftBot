import discord
from discord.ext import commands
from discord import app_commands
import json, os
from datetime import datetime, timedelta

DATA_FILE = "data/moderation.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def add_warn(guild_id, user_id, reason, mod_id):
    data = load_data()
    gid, uid = str(guild_id), str(user_id)
    if gid not in data: data[gid] = {}
    if uid not in data[gid]: data[gid][uid] = []
    data[gid][uid].append({"reason": reason, "mod": str(mod_id), "time": datetime.utcnow().isoformat()})
    save_data(data)
    return len(data[gid][uid])

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- warn ---
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        count = add_warn(interaction.guild.id, member.id, reason, interaction.user.id)
        embed = discord.Embed(title="Member Warned", color=0xFF9800)
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Warned by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Total warnings: {count}")
        await interaction.response.send_message(embed=embed)
        try: await member.send(f"You were warned in **{interaction.guild.name}**\nReason: {reason}\nTotal warnings: {count}")
        except discord.Forbidden: pass

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        count = add_warn(ctx.guild.id, member.id, reason, ctx.author.id)
        embed = discord.Embed(title="Member Warned", color=0xFF9800)
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Warned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Total warnings: {count}")
        await ctx.send(embed=embed)

    # --- warnings ---
    @app_commands.command(name="warnings", description="Check warnings for a member")
    @app_commands.describe(member="The member to check")
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        data = load_data()
        warns = data.get(str(interaction.guild.id), {}).get(str(member.id), [])
        if not warns: await interaction.response.send_message(f"{member.mention} has no warnings."); return
        embed = discord.Embed(title=f"Warnings for {member.display_name}", color=0xFF9800)
        for i, w in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i} — {w['time'][:10]}", value=f"**Reason:** {w['reason']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="warnings")
    async def warnings_prefix(self, ctx, member: discord.Member):
        data = load_data()
        warns = data.get(str(ctx.guild.id), {}).get(str(member.id), [])
        if not warns: await ctx.send(f"{member.mention} has no warnings."); return
        embed = discord.Embed(title=f"Warnings for {member.display_name}", color=0xFF9800)
        for i, w in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i}", value=w['reason'], inline=False)
        await ctx.send(embed=embed)

    # --- clearwarnings ---
    @app_commands.command(name="clearwarnings", description="Clear all warnings for a member")
    @app_commands.describe(member="The member to clear")
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data = load_data()
        gid, uid = str(interaction.guild.id), str(member.id)
        if gid in data and uid in data[gid]: data[gid][uid] = []; save_data(data)
        await interaction.response.send_message(f"Cleared all warnings for {member.mention}.")

    @commands.hybrid_command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings_prefix(self, ctx, member: discord.Member):
        data = load_data()
        gid, uid = str(ctx.guild.id), str(member.id)
        if gid in data and uid in data[gid]: data[gid][uid] = []; save_data(data)
        await ctx.send(f"Cleared all warnings for {member.mention}.")

    # --- kick ---
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.describe(member="The member to kick", reason="Reason")
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        try: await member.send(f"You were kicked from **{interaction.guild.name}**\nReason: {reason}")
        except discord.Forbidden: pass
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked {member} — {reason}")

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member} — {reason}")

    # --- ban ---
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.describe(member="The member to ban", reason="Reason")
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        try: await member.send(f"You were banned from **{interaction.guild.name}**\nReason: {reason}")
        except discord.Forbidden: pass
        await member.ban(reason=reason)
        await interaction.response.send_message(f"Banned {member} — {reason}")

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member} — {reason}")

    # --- unban ---
    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.describe(user_id="The user's ID")
    async def unban_slash(self, interaction: discord.Interaction, user_id: str):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"Unbanned {user}.")
        except Exception: await interaction.response.send_message("User not found or not banned.", ephemeral=True)

    @commands.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban_prefix(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"Unbanned {user}.")
        except Exception: await ctx.send("User not found or not banned.")

    # --- mute ---
    @app_commands.command(name="mute", description="Mute a member for 10 minutes")
    @app_commands.describe(member="The member to mute", reason="Reason")
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        await member.timeout(timedelta(minutes=10), reason=reason)
        await interaction.response.send_message(f"Muted {member.mention} for 10 minutes — {reason}")

    @commands.hybrid_command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.timeout(timedelta(minutes=10), reason=reason)
        await ctx.send(f"Muted {member.mention} for 10 minutes.")

    # --- unmute ---
    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.describe(member="The member to unmute")
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        await member.timeout(None)
        await interaction.response.send_message(f"Unmuted {member.mention}.")

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute_prefix(self, ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f"Unmuted {member.mention}.")

    # --- purge ---
    @app_commands.command(name="purge", description="Delete a number of messages")
    @app_commands.describe(amount="Number of messages to delete (max 100)")
    async def purge_slash(self, interaction: discord.Interaction, amount: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        if amount > 100: await interaction.response.send_message("Max 100 messages.", ephemeral=True); return
        await interaction.response.send_message(f"Deleting {amount} messages...", ephemeral=True)
        await interaction.channel.purge(limit=amount)

    @commands.hybrid_command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge_prefix(self, ctx, amount: int):
        if amount > 100: await ctx.send("Max 100 messages."); return
        await ctx.channel.purge(limit=amount + 1)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
