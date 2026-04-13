import discord
from discord.ext import commands
from discord import app_commands

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _stats(self, send, guild):
        humans = sum(1 for m in guild.members if not m.bot)
        bots = guild.member_count - humans
        online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
        embed = discord.Embed(title=f"{guild.name} — Server Stats", color=0x4CAF50)
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=f"{humans} humans\n{bots} bots", inline=True)
        embed.add_field(name="Online", value=str(online), inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name="Text Channels", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="Voice Channels", value=str(len(guild.voice_channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles) - 1), inline=True)
        await send(embed=embed)

    @app_commands.command(name="stats", description="Show server statistics")
    async def stats_slash(self, interaction: discord.Interaction):
        await self._stats(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="stats")
    async def stats_prefix(self, ctx):
        await self._stats(ctx.send, ctx.guild)

    async def _userinfo(self, send, member):
        roles = [r.mention for r in member.roles[1:]]
        embed = discord.Embed(title=f"{member.display_name}", color=member.top_role.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "None", inline=False)
        await send(embed=embed)

    @app_commands.command(name="userinfo", description="Show info about a user")
    @app_commands.describe(member="The member to look up (defaults to you)")
    async def userinfo_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._userinfo(interaction.response.send_message, member or interaction.user)

    @commands.hybrid_command(name="userinfo")
    async def userinfo_prefix(self, ctx, member: discord.Member = None):
        await self._userinfo(ctx.send, member or ctx.author)

    async def _membercount(self, send, guild):
        humans = sum(1 for m in guild.members if not m.bot)
        await send(f"**{guild.name}** has `{humans}` members ({guild.member_count} total including bots).")

    @app_commands.command(name="membercount", description="Quick member count")
    async def membercount_slash(self, interaction: discord.Interaction):
        await self._membercount(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="membercount")
    async def membercount_prefix(self, ctx):
        await self._membercount(ctx.send, ctx.guild)

async def setup(bot):
    await bot.add_cog(ServerStats(bot))
