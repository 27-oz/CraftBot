import discord
from discord.ext import commands
import json, os
from datetime import datetime

CONFIG_FILE = "data/logging_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_log_channel(bot, guild_id):
    config = load_config()
    channel_id = config.get(str(guild_id), {}).get("channel")
    if not channel_id:
        return None
    return bot.get_channel(channel_id)

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        """Set the logging channel. Usage: !setlog #logs"""
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Log channel set to {channel.mention}.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        channel = get_log_channel(self.bot, message.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=0xF44336,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Content", value=message.content[:1024] or "*empty*", inline=False)
        embed.set_footer(text=f"User ID: {message.author.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        channel = get_log_channel(self.bot, before.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=0xFF9800,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Author", value=before.author.mention, inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content[:512] or "*empty*", inline=False)
        embed.add_field(name="After", value=after.content[:512] or "*empty*", inline=False)
        embed.add_field(name="Jump", value=f"[View Message]({after.jump_url})", inline=False)
        embed.set_footer(text=f"User ID: {before.author.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = get_log_channel(self.bot, member.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="✅ Member Joined",
            color=0x4CAF50,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
        embed.set_footer(text=f"User ID: {member.id} • Member #{member.guild.member_count}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = get_log_channel(self.bot, member.guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="👋 Member Left",
            color=0x9E9E9E,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Member", value=str(member), inline=True)
        roles = [r.mention for r in member.roles[1:]]
        embed.add_field(name="Roles", value=" ".join(roles) if roles else "None", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = get_log_channel(self.bot, guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="🔨 Member Banned",
            color=0xB71C1C,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=str(user), inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = get_log_channel(self.bot, guild.id)
        if not channel:
            return
        embed = discord.Embed(
            title="✅ Member Unbanned",
            color=0x4CAF50,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=str(user), inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = get_log_channel(self.bot, before.guild.id)
        if not channel:
            return
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            if not added and not removed:
                return
            embed = discord.Embed(title="🎭 Roles Updated", color=0x9C27B0, timestamp=datetime.utcnow())
            embed.add_field(name="Member", value=after.mention, inline=True)
            if added:
                embed.add_field(name="Added", value=" ".join(r.mention for r in added), inline=True)
            if removed:
                embed.add_field(name="Removed", value=" ".join(r.mention for r in removed), inline=True)
            embed.set_footer(text=f"User ID: {after.id}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log = get_log_channel(self.bot, channel.guild.id)
        if not log:
            return
        embed = discord.Embed(title="📢 Channel Created", color=0x4CAF50, timestamp=datetime.utcnow())
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        await log.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log = get_log_channel(self.bot, channel.guild.id)
        if not log:
            return
        embed = discord.Embed(title="🗑️ Channel Deleted", color=0xF44336, timestamp=datetime.utcnow())
        embed.add_field(name="Channel", value=f"#{channel.name}", inline=True)
        await log.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
