import discord
from discord.ext import commands
import json, os
from datetime import datetime

CONFIG_FILE = "data/tickets_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def ticket(self, ctx, *, issue: str):
        """Open a support ticket. Usage: !ticket I need help with my whitelist application"""
        config = load_config()
        gid = str(ctx.guild.id)
        cfg = config.get(gid, {})

        staff_channel_id = cfg.get("staff_channel")
        staff_role_id = cfg.get("staff_role")

        embed = discord.Embed(
            title="🎫 New Support Ticket",
            description=issue,
            color=0x2196F3,
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Member", value=ctx.author.mention, inline=True)
        embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        embed.add_field(name="User ID", value=str(ctx.author.id), inline=True)
        embed.set_footer(text=f"#{ctx.channel.name} • {ctx.guild.name}")

        if staff_channel_id:
            staff_channel = ctx.guild.get_channel(staff_channel_id)
            if staff_channel:
                ping = f"<@&{staff_role_id}>" if staff_role_id else ""
                await staff_channel.send(content=ping, embed=embed)

        if staff_role_id:
            staff_role = ctx.guild.get_role(staff_role_id)
            if staff_role:
                for member in staff_role.members:
                    if member.bot:
                        continue
                    try:
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        pass

        await ctx.author.send(
            f"✅ Your ticket has been submitted to the staff team of **{ctx.guild.name}**!\n"
            f"**Issue:** {issue}\n\nA staff member will reach out to you soon."
        )
        await ctx.message.delete()
        await ctx.send(f"✅ {ctx.author.mention} your ticket has been submitted! Check your DMs.", delete_after=10)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setticketstaff(self, ctx, role: discord.Role):
        """Set the staff role to receive tickets. Usage: !setticketstaff @Staff"""
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["staff_role"] = role.id
        save_config(config)
        await ctx.send(f"✅ Ticket alerts will be sent to all `{role.name}` members.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setticketstaffchannel(self, ctx, channel: discord.TextChannel):
        """Set a channel where all tickets are posted. Usage: !setticketstaffchannel #tickets"""
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["staff_channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Tickets will be posted to {channel.mention}.")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
