import discord
from discord.ext import commands
import json, os
from datetime import datetime

DATA_FILE = "data/afk.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        gid = str(message.guild.id)
        uid = str(message.author.id)

        # If the author was AFK, remove them
        if gid in data and uid in data[gid]:
            afk_info = data[gid][uid]
            del data[gid][uid]
            save_data(data)
            since = datetime.fromisoformat(afk_info["since"])
            duration = datetime.utcnow() - since
            hours, rem = divmod(int(duration.total_seconds()), 3600)
            minutes = rem // 60
            time_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            msg = await message.channel.send(
                f"👋 Welcome back {message.author.mention}! You were AFK for **{time_str}**.",
                delete_after=8
            )
            return

        # Check if anyone mentioned is AFK
        for mentioned in message.mentions:
            muid = str(mentioned.id)
            if gid in data and muid in data[gid]:
                afk_info = data[gid][muid]
                reason = afk_info.get("reason", "No reason given")
                since = datetime.fromisoformat(afk_info["since"])
                duration = datetime.utcnow() - since
                hours, rem = divmod(int(duration.total_seconds()), 3600)
                minutes = rem // 60
                time_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
                await message.channel.send(
                    f"💤 **{mentioned.display_name}** is AFK: *{reason}* (for {time_str})",
                    delete_after=10
                )

    @commands.hybrid_command()
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set yourself as AFK. Usage: !afk or !afk Eating dinner"""
        data = load_data()
        gid = str(ctx.guild.id)
        uid = str(ctx.author.id)
        if gid not in data:
            data[gid] = {}
        data[gid][uid] = {
            "reason": reason,
            "since": datetime.utcnow().isoformat()
        }
        save_data(data)
        await ctx.send(f"💤 {ctx.author.mention} is now AFK: *{reason}*")

async def setup(bot):
    await bot.add_cog(AFK(bot))