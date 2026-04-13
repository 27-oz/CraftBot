import discord
from discord.ext import commands
import json, os
from datetime import datetime

DATA_FILE = "data/moderation.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def add_warn(self, guild_id, user_id, reason, mod_id):
        data = load_data()
        gid, uid = str(guild_id), str(user_id)
        if gid not in data:
            data[gid] = {}
        if uid not in data[gid]:
            data[gid][uid] = []
        data[gid][uid].append({
            "reason": reason,
            "mod": str(mod_id),
            "time": datetime.utcnow().isoformat()
        })
        save_data(data)
        return len(data[gid][uid])

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member. Usage: !warn @user Spamming"""
        count = self.add_warn(ctx.guild.id, member.id, reason, ctx.author.id)
        embed = discord.Embed(title="⚠️ Member Warned", color=0xFF9800)
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Warned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Total warnings: {count}")
        await ctx.send(embed=embed)

        try:
            await member.send(f"⚠️ You were warned in **{ctx.guild.name}**\nReason: {reason}\nTotal warnings: {count}")
        except discord.Forbidden:
            pass

    @commands.hybrid_command()
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member. Usage: !warnings @user"""
        data = load_data()
        gid, uid = str(ctx.guild.id), str(member.id)
        warns = data.get(gid, {}).get(uid, [])
        if not warns:
            await ctx.send(f"✅ {member.mention} has no warnings.")
            return
        embed = discord.Embed(title=f"⚠️ Warnings for {member.display_name}", color=0xFF9800)
        for i, w in enumerate(warns, 1):
            mod = ctx.guild.get_member(int(w["mod"]))
            mod_name = mod.display_name if mod else "Unknown"
            embed.add_field(
                name=f"Warning #{i} — {w['time'][:10]}",
                value=f"**Reason:** {w['reason']}\n**By:** {mod_name}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        """Clear all warnings for a member. Usage: !clearwarnings @user"""
        data = load_data()
        gid, uid = str(ctx.guild.id), str(member.id)
        if gid in data and uid in data[gid]:
            data[gid][uid] = []
            save_data(data)
        await ctx.send(f"✅ Cleared all warnings for {member.mention}.")

    @commands.hybrid_command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member. Usage: !kick @user Breaking rules"""
        try:
            await member.send(f"👢 You were kicked from **{ctx.guild.name}**\nReason: {reason}")
        except discord.Forbidden:
            pass
        await member.kick(reason=reason)
        embed = discord.Embed(title="👢 Member Kicked", color=0xF44336)
        embed.add_field(name="Member", value=str(member), inline=True)
        embed.add_field(name="By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member. Usage: !ban @user Griefing"""
        try:
            await member.send(f"🔨 You were banned from **{ctx.guild.name}**\nReason: {reason}")
        except discord.Forbidden:
            pass
        await member.ban(reason=reason)
        embed = discord.Embed(title="🔨 Member Banned", color=0xB71C1C)
        embed.add_field(name="Member", value=str(member), inline=True)
        embed.add_field(name="By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Unban a user by ID. Usage: !unban 123456789"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned {user}.")
        except discord.NotFound:
            await ctx.send("❌ User not found or not banned.")

    @commands.hybrid_command()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Mute a member using Discord timeout (10 minutes). Usage: !mute @user Spamming"""
        from datetime import timedelta
        duration = timedelta(minutes=10)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="🔇 Member Muted (10 min)", color=0x607D8B)
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member. Usage: !unmute @user"""
        await member.timeout(None)
        await ctx.send(f"✅ {member.mention} has been unmuted.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Delete a number of messages. Usage: !purge 10"""
        if amount > 100:
            await ctx.send("❌ Max 100 messages at a time.")
            return
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🗑️ Deleted {amount} messages.")
        await msg.delete(delay=3)

async def setup(bot):
    await bot.add_cog(Moderation(bot))