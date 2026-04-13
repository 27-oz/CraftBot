import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/channel_locks.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_level(guild_id, user_id):
    path = "data/levels.json"
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        data = json.load(f)
    return data.get(str(guild_id), {}).get(str(user_id), {}).get("level", 0)

class ChannelLocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Pre-load your channel locks on startup
        self._preload_defaults()

    def _preload_defaults(self):
        data = load_data()
        defaults = {
            "1490371885635076117": 50,
            "1490206001192767748": 50,
            "1489639648954159175": 30,
        }
        changed = False
        for channel_id, level in defaults.items():
            if channel_id not in data:
                data[channel_id] = level
                changed = True
        if changed:
            save_data(data)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        # Ignore admins/mods
        if message.author.guild_permissions.manage_messages:
            return

        data = load_data()
        channel_id = str(message.channel.id)
        if channel_id not in data:
            return

        required_level = data[channel_id]
        user_level = get_user_level(message.guild.id, message.author.id)

        if user_level < required_level:
            await message.delete()
            try:
                await message.author.send(
                    f"🔒 **#{message.channel.name}** requires **Level {required_level}** to send messages.\n"
                    f"You're Level {user_level}. Keep chatting to level up! Use `!rank` to check your progress."
                )
            except discord.Forbidden:
                pass

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def lockchannel(self, ctx, channel: discord.TextChannel, level: int):
        """Lock a channel to a minimum level. Usage: !lockchannel #channel 25"""
        data = load_data()
        data[str(channel.id)] = level
        save_data(data)
        await ctx.send(f"🔒 {channel.mention} is now view-only for members below **Level {level}**.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def unlockchannel(self, ctx, channel: discord.TextChannel):
        """Remove a level lock from a channel. Usage: !unlockchannel #channel"""
        data = load_data()
        cid = str(channel.id)
        if cid in data:
            del data[cid]
            save_data(data)
            await ctx.send(f"🔓 {channel.mention} is now unlocked for everyone.")
        else:
            await ctx.send(f"⚠️ {channel.mention} wasn't locked.")

    @commands.hybrid_command()
    async def lockedchannels(self, ctx):
        """List all level-locked channels."""
        data = load_data()
        if not data:
            await ctx.send("No channels are level-locked.")
            return
        embed = discord.Embed(title="🔒 Level-Locked Channels", color=0x607D8B)
        lines = []
        for channel_id, level in data.items():
            channel = ctx.guild.get_channel(int(channel_id))
            name = channel.mention if channel else f"Unknown ({channel_id})"
            lines.append(f"{name} → Level {level}+")
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChannelLocks(bot))
