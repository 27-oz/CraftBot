import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
import json, os, re
from datetime import datetime, timedelta

DATA_FILE = "data/reminders.json"

def load_data():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def parse_time(time_str):
    match = re.fullmatch(r"(\d+)(s|m|h|d)", time_str.lower())
    if not match: return None
    value, unit = int(match.group(1)), match.group(2)
    return value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]

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
        for r in data:
            if now >= r["due"]:
                channel = self.bot.get_channel(r["channel_id"])
                if channel:
                    embed = discord.Embed(title="Reminder!", description=r["message"], color=0xFF9800)
                    await channel.send(f"<@{r['user_id']}>", embed=embed)
            else:
                remaining.append(r)
        save_data(remaining)

    @check_reminders.before_loop
    async def before_check(self): await self.bot.wait_until_ready()

    async def _remind(self, send, channel_id, user_id, time_str, message):
        seconds = parse_time(time_str)
        if not seconds: await send("Invalid time format. Use `10s`, `5m`, `2h`, or `1d`."); return
        due = (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()
        data = load_data()
        data.append({"user_id": user_id, "channel_id": channel_id, "message": message, "due": due})
        save_data(data)
        await send(f"Reminder set! I'll remind you in `{time_str}`.")

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(time="Duration e.g. 10m, 2h, 1d", message="What to remind you about")
    async def remind_slash(self, interaction: discord.Interaction, time: str, message: str):
        await self._remind(interaction.response.send_message, interaction.channel.id, interaction.user.id, time, message)

    @commands.hybrid_command(name="remind")
    async def remind_prefix(self, ctx, time_str: str, *, message: str):
        await self._remind(ctx.send, ctx.channel.id, ctx.author.id, time_str, message)

    async def _reminders(self, send, user_id):
        data = load_data()
        user_reminders = [r for r in data if r["user_id"] == user_id]
        if not user_reminders: await send("You have no pending reminders."); return
        embed = discord.Embed(title="Your Reminders", color=0xFF9800)
        for i, r in enumerate(user_reminders, 1):
            due_time = datetime.utcfromtimestamp(r["due"]).strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(name=f"#{i} — {due_time}", value=r["message"], inline=False)
        await send(embed=embed)

    @app_commands.command(name="reminders", description="View your pending reminders")
    async def reminders_slash(self, interaction: discord.Interaction):
        await self._reminders(interaction.response.send_message, interaction.user.id)

    @commands.hybrid_command(name="reminders")
    async def reminders_prefix(self, ctx):
        await self._reminders(ctx.send, ctx.author.id)

async def setup(bot):
    await bot.add_cog(Reminders(bot))
