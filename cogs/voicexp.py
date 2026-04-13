import discord
from discord.ext import commands
from discord.ext import tasks
import json, os, random
from datetime import datetime

DATA_FILE = "data/levels.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_level(xp):
    level = 0
    while xp >= 100 * ((level + 1) ** 2):
        level += 1
    return level

class VoiceXP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_xp_loop.start()

    def cog_unload(self):
        self.voice_xp_loop.cancel()

    @tasks.loop(minutes=5)
    async def voice_xp_loop(self):
        """Give XP to members in voice channels every 5 minutes."""
        data = load_data()
        for guild in self.bot.guilds:
            gid = str(guild.id)
            if gid not in data:
                data[gid] = {}
            for vc in guild.voice_channels:
                for member in vc.members:
                    if member.bot:
                        continue
                    # Skip muted/deafened members
                    if member.voice and (member.voice.self_deaf or member.voice.afk):
                        continue
                    uid = str(member.id)
                    if uid not in data[gid]:
                        data[gid][uid] = {"xp": 0, "level": 0}
                    xp_gain = random.randint(5, 15)
                    old_level = data[gid][uid]["level"]
                    data[gid][uid]["xp"] += xp_gain
                    new_level = get_level(data[gid][uid]["xp"])
                    data[gid][uid]["level"] = new_level
        save_data(data)

    @voice_xp_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(VoiceXP(bot))
