import discord
from discord.ext import commands
from datetime import datetime

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def stats(self, ctx):
        """Show server statistics."""
        guild = ctx.guild
        total = guild.member_count
        bots = sum(1 for m in guild.members if m.bot)
        humans = total - bots
        online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles) - 1  # exclude @everyone
        created = guild.created_at.strftime("%b %d, %Y")

        embed = discord.Embed(
            title=f"📊 {guild.name} — Server Stats",
            color=0x4CAF50
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👥 Members", value=f"{humans} humans\n{bots} bots", inline=True)
        embed.add_field(name="🟢 Online", value=str(online), inline=True)
        embed.add_field(name="📅 Created", value=created, inline=True)
        embed.add_field(name="💬 Text Channels", value=str(text_channels), inline=True)
        embed.add_field(name="🔊 Voice Channels", value=str(voice_channels), inline=True)
        embed.add_field(name="🏷️ Roles", value=str(roles), inline=True)
        embed.set_footer(text=f"Server ID: {guild.id}")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show info about a user. Usage: !userinfo @User (defaults to yourself)"""
        member = member or ctx.author
        roles = [r.mention for r in member.roles[1:]]  # skip @everyone
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.top_role.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "None", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def membercount(self, ctx):
        """Quick member count."""
        guild = ctx.guild
        humans = sum(1 for m in guild.members if not m.bot)
        await ctx.send(f"⛏️ **{guild.name}** has `{humans}` miners ({guild.member_count} total including bots).")

async def setup(bot):
    await bot.add_cog(ServerStats(bot))