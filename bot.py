import discord
from discord.ext import commands
from discord import app_commands
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

os.makedirs("data", exist_ok=True)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

COGS = [
    "cogs.welcome",
    "cogs.autorole",
    "cogs.reactionroles",
    "cogs.reminders",
    "cogs.customcommands",
    "cogs.serverstats",
    "cogs.polls",
    "cogs.tiktok",
    "cogs.twitch",
    "cogs.leveling",
    "cogs.moderation",
    "cogs.starboard",
    "cogs.applications",
    "cogs.minecraft",
    "cogs.channellocks",
    "cogs.economy",
    "cogs.tickets",
    "cogs.afk",
    "cogs.antispam",
    "cogs.rules",
    "cogs.mcextras",
    "cogs.voicexp",
    "cogs.music",
    "cogs.logging",
    "cogs.extramod",
    "cogs.fun",
    "cogs.xpconfig",
    "cogs.help",
]

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

threading.Thread(
    target=lambda: HTTPServer(("0.0.0.0", 8080), Health).serve_forever(),
    daemon=True
).start()

@bot.event
async def on_ready():
    print(f"CraftBot {bot.user} is online!")
    import itertools
    from discord.ext import tasks

    statuses = [
        (discord.ActivityType.playing,   "Minecraft | /help"),
        (discord.ActivityType.watching,  "over the server"),
        (discord.ActivityType.playing,   f"{sum(g.member_count for g in bot.guilds)} miners!"),
        (discord.ActivityType.listening, "/music"),
        (discord.ActivityType.watching,  "for rule breakers"),
    ]
    cycle = itertools.cycle(statuses)

    @tasks.loop(seconds=30)
    async def cycle_status():
        atype, text = next(cycle)
        await bot.change_presence(activity=discord.Activity(type=atype, name=text))

    cycle_status.start()

    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"  Loaded {cog}")
        except Exception as e:
            print(f"  Failed to load {cog}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"  Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"  Failed to sync slash commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to do that.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`. Use `/help` for usage.")
    else:
        await ctx.send(f"An error occurred: {error}")

bot.run(os.getenv("DISCORD_TOKEN"))
