import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

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
    "cogs.help",
]

@bot.event
async def on_ready():
    await bot.tree.sync()
    print('Tree Synced')
    print(f"⛏️  {bot.user} is online and mining!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Minecraft | !help"
        )
    )
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"  ✅ Loaded {cog}")
        except Exception as e:
            print(f"  ❌ Failed to load {cog}: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You don't have permission to do that!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❓ Unknown command. Try `!help` for a list of commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`. Use `!help {ctx.command}` for usage.")
    else:
        await ctx.send(f"⚠️ An error occurred: {error}")

bot.run(os.getenv('DISCORD_TOKEN'))

import os

