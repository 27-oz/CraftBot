import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/customcommands.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if not message.content.startswith("!"):
            return
        data = load_data()
        guild_id = str(message.guild.id)
        if guild_id not in data:
            return
        trigger = message.content[1:].split()[0].lower()
        if trigger in data[guild_id]:
            response = data[guild_id][trigger].replace("{user}", message.author.mention)
            await message.channel.send(response)

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def addcmd(self, ctx, trigger: str, *, response: str):
        """Add a custom command. Use {user} to mention the caller.
        Usage: !addcmd ip Our server IP is play.example.net"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {}
        trigger = trigger.lower()
        data[guild_id][trigger] = response
        save_data(data)
        await ctx.send(f"✅ Custom command `!{trigger}` created!")

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def delcmd(self, ctx, trigger: str):
        """Delete a custom command. Usage: !delcmd ip"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        trigger = trigger.lower()
        if guild_id in data and trigger in data[guild_id]:
            del data[guild_id][trigger]
            save_data(data)
            await ctx.send(f"✅ Custom command `!{trigger}` deleted.")
        else:
            await ctx.send(f"⚠️ No custom command `!{trigger}` found.")

    @commands.hybrid_command()
    async def listcmds(self, ctx):
        """List all custom commands for this server."""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data or not data[guild_id]:
            await ctx.send("No custom commands set up yet.")
            return
        cmds = [f"`!{k}` → {v}" for k, v in data[guild_id].items()]
        embed = discord.Embed(
            title="📋 Custom Commands",
            description="\n".join(cmds),
            color=0x00BCD4
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))