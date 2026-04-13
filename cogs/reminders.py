import discord
from discord.ext import commands
from discord.ext import tasks
import json, os, asyncio
from datetime import datetime, timedelta
import re

DATA_FILE = "data/reminders.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_time(time_str):
    """Parse a time string like 10m, 2h, 1d into seconds."""
    match = re.fullmatch(r"(\d+)(s|m|h|d)", time_str.lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers[unit]

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        data = load_data()
        now = datetime.utcnow().timestamp()
        remaining = []
        for reminder in data:
            if now >= reminder["due"]:
                channel = self.bot.get_channel(reminder["channel_id"])
                if channel:
                    user = self.bot.get_user(reminder["user_id"])
                    mention = user.mention if user else f"<@{reminder['user_id']}>"
                    embed = discord.Embed(
                        title="⏰ Reminder!",
                        description=reminder["message"],
                        color=0xFF9800
                    )
                    await channel.send(f"{mention}", embed=embed)
            else:
                remaining.append(reminder)
        save_data(remaining)

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command()
    async def remind(self, ctx, time_str: str, *, message: str):
        """Set a reminder. Usage: !remind 10m Do the thing / !remind 2h Check server"""
        seconds = parse_time(time_str)
        if not seconds:
            await ctx.send("❌ Invalid time format. Use `10s`, `5m`, `2h`, or `1d`.")
            return
        due = (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()
        data = load_data()
        data.append({
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "message": message,
            "due": due
        })
        save_data(data)
        await ctx.send(f"✅ Reminder set! I'll remind you in `{time_str}`. ⏰")

    @commands.hybrid_command()
    async def reminders(self, ctx):
        """List your pending reminders."""
        data = load_data()
        user_reminders = [r for r in data if r["user_id"] == ctx.author.id]
        if not user_reminders:
            await ctx.send("You have no pending reminders.")
            return
        embed = discord.Embed(title="⏰ Your Reminders", color=0xFF9800)
        for i, r in enumerate(user_reminders, 1):
            due_time = datetime.utcfromtimestamp(r["due"]).strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(name=f"#{i} — {due_time}", value=r["message"], inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Reminders(bot))