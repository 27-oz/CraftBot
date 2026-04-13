import discord
from discord.ext import commands
from collections import defaultdict
from datetime import datetime, timedelta

# Config
SPAM_THRESHOLD = 5       # messages
SPAM_WINDOW = 5          # seconds
MUTE_DURATION = 5        # minutes

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_log = defaultdict(list)  # user_id -> [timestamps]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if message.author.guild_permissions.manage_messages:
            return

        uid = message.author.id
        now = datetime.utcnow()

        # Clean old entries
        self.message_log[uid] = [
            t for t in self.message_log[uid]
            if now - t < timedelta(seconds=SPAM_WINDOW)
        ]
        self.message_log[uid].append(now)

        if len(self.message_log[uid]) >= SPAM_THRESHOLD:
            self.message_log[uid] = []

            # Delete recent messages
            def is_spam(m):
                return m.author == message.author

            try:
                await message.channel.purge(limit=SPAM_THRESHOLD + 2, check=is_spam)
            except discord.Forbidden:
                pass

            # Mute
            try:
                await message.author.timeout(
                    timedelta(minutes=MUTE_DURATION),
                    reason="Auto-mod: Spam detected"
                )
            except discord.Forbidden:
                pass

            embed = discord.Embed(
                title="🛡️ Anti-Spam",
                description=f"{message.author.mention} was muted for **{MUTE_DURATION} minutes** for spamming.",
                color=0xF44336
            )
            await message.channel.send(embed=embed, delete_after=10)

            try:
                await message.author.send(
                    f"⚠️ You were muted in **{message.guild.name}** for {MUTE_DURATION} minutes for spamming."
                )
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
