import discord
from discord.ext import commands
from discord import app_commands
import json, os
from datetime import datetime

DATA_FILE = "data/afk.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        data = load_data()
        gid, uid = str(message.guild.id), str(message.author.id)
        if gid in data and uid in data[gid]:
            afk_info = data[gid][uid]
            del data[gid][uid]
            save_data(data)
            duration = datetime.utcnow() - datetime.fromisoformat(afk_info["since"])
            hours, rem = divmod(int(duration.total_seconds()), 3600)
            time_str = f"{hours}h {rem//60}m" if hours else f"{rem//60}m"
            await message.channel.send(f"Welcome back {message.author.mention}! You were AFK for **{time_str}**.", delete_after=8)
            return
        for mentioned in message.mentions:
            muid = str(mentioned.id)
            if gid in data and muid in data[gid]:
                afk_info = data[gid][muid]
                reason = afk_info.get("reason", "AFK")
                duration = datetime.utcnow() - datetime.fromisoformat(afk_info["since"])
                hours, rem = divmod(int(duration.total_seconds()), 3600)
                time_str = f"{hours}h {rem//60}m" if hours else f"{rem//60}m"
                await message.channel.send(f"**{mentioned.display_name}** is AFK: *{reason}* (for {time_str})", delete_after=10)

    async def _afk(self, send, guild_id, user_id, mention, reason):
        data = load_data()
        gid, uid = str(guild_id), str(user_id)
        if gid not in data: data[gid] = {}
        data[gid][uid] = {"reason": reason, "since": datetime.utcnow().isoformat()}
        save_data(data)
        await send(f"{mention} is now AFK: *{reason}*")

    @app_commands.command(name="afk", description="Set yourself as AFK")
    @app_commands.describe(reason="Why you're AFK")
    async def afk_slash(self, interaction: discord.Interaction, reason: str = "AFK"):
        await self._afk(interaction.response.send_message, interaction.guild.id, interaction.user.id, interaction.user.mention, reason)

    @commands.hybrid_command(name="afk")
    async def afk_prefix(self, ctx, *, reason: str = "AFK"):
        await self._afk(ctx.send, ctx.guild.id, ctx.author.id, ctx.author.mention, reason)

async def setup(bot):
    await bot.add_cog(AFK(bot))
