import discord
from discord.ext import commands
import json, os

CONFIG_FILE = "data/applications_config.json"

SUGGEST_LEVEL = 10
STAFF_LEVEL = 25
ADMIN_LEVEL = 50

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_user_level(guild_id, user_id):
    path = "data/levels.json"
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        data = json.load(f)
    return data.get(str(guild_id), {}).get(str(user_id), {}).get("level", 0)

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_staff_channel(self, guild):
        config = load_config()
        gid = str(guild.id)
        channel_id = config.get(gid, {}).get("staff_channel")
        return guild.get_channel(channel_id) if channel_id else None

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setstaffchannel(self, ctx, channel: discord.TextChannel):
        """Set where applications get posted. Usage: !setstaffchannel #staff-apps"""
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["staff_channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Applications will be posted to {channel.mention}.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setsuggestchannel(self, ctx, channel: discord.TextChannel):
        """Set where suggestions get posted. Usage: !setsuggestchannel #suggestions"""
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["suggest_channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Suggestions will be posted to {channel.mention}.")

    @commands.hybrid_command()
    async def suggest(self, ctx, *, suggestion: str):
        """Submit a suggestion. Requires Level 10. Usage: !suggest Add a PvP arena"""
        level = get_user_level(ctx.guild.id, ctx.author.id)
        if level < SUGGEST_LEVEL:
            await ctx.send(f"❌ You need to be **Level {SUGGEST_LEVEL}** to suggest. You're Level {level}. Keep chatting!")
            return

        config = load_config()
        gid = str(ctx.guild.id)
        channel_id = config.get(gid, {}).get("suggest_channel")
        channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel

        embed = discord.Embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=0x2196F3
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Level {level} member")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        if channel != ctx.channel:
            await ctx.send("✅ Your suggestion has been submitted!")

    @commands.hybrid_command()
    async def staffapp(self, ctx):
        """Apply for staff. Requires Level 25. Usage: !staffapp"""
        level = get_user_level(ctx.guild.id, ctx.author.id)
        if level < STAFF_LEVEL:
            await ctx.send(f"❌ You need to be **Level {STAFF_LEVEL}** to apply for staff. You're Level {level}. Keep chatting!")
            return

        await ctx.send("📝 I'll DM you the staff application form!")

        questions = [
            "What is your age?",
            "How long have you been in the server?",
            "What timezone are you in?",
            "How many hours per week can you dedicate to moderation?",
            "Why do you want to be staff?",
            "Do you have any previous moderation experience?",
            "Anything else you'd like us to know?"
        ]

        answers = []
        try:
            dm = await ctx.author.create_dm()
            await dm.send("📋 **Staff Application**\nAnswer each question. You have 5 minutes per question.\nType `cancel` to cancel.\n\u200b")

            for q in questions:
                await dm.send(f"**{q}**")

                def check(m):
                    return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=300)
                    if msg.content.lower() == "cancel":
                        await dm.send("❌ Application cancelled.")
                        return
                    answers.append(msg.content)
                except Exception:
                    await dm.send("⏰ Timed out. Application cancelled.")
                    return

            await dm.send("✅ Application submitted! You'll hear back soon.")

        except discord.Forbidden:
            await ctx.send("❌ I couldn't DM you! Please enable DMs from server members.")
            return

        # Post to staff channel
        staff_channel = await self.get_staff_channel(ctx.guild)
        if staff_channel:
            embed = discord.Embed(title="📋 New Staff Application", color=0x4CAF50)
            embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            embed.add_field(name="Member", value=ctx.author.mention, inline=True)
            embed.add_field(name="Level", value=str(level), inline=True)
            for i, (q, a) in enumerate(zip(questions, answers)):
                embed.add_field(name=q, value=a[:1024], inline=False)
            await staff_channel.send(embed=embed)

    @commands.hybrid_command()
    async def adminapp(self, ctx):
        """Apply for admin. Requires Level 50. Usage: !adminapp"""
        level = get_user_level(ctx.guild.id, ctx.author.id)
        if level < ADMIN_LEVEL:
            await ctx.send(f"❌ You need to be **Level {ADMIN_LEVEL}** to apply for admin. You're Level {level}. Keep chatting!")
            return

        await ctx.send("📝 I'll DM you the admin application form!")

        questions = [
            "What is your age?",
            "How long have you been in the server / community?",
            "What timezone are you in?",
            "Are you currently or have you previously been staff here?",
            "How many hours per week can you commit to admin duties?",
            "Why do you want to be admin specifically (not just staff)?",
            "Describe a situation where you had to make a difficult moderation decision.",
            "What would you improve about the server?",
            "Any additional comments?"
        ]

        answers = []
        try:
            dm = await ctx.author.create_dm()
            await dm.send("📋 **Admin Application**\nAnswer each question. You have 5 minutes per question.\nType `cancel` to cancel.\n\u200b")

            for q in questions:
                await dm.send(f"**{q}**")

                def check(m):
                    return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=300)
                    if msg.content.lower() == "cancel":
                        await dm.send("❌ Application cancelled.")
                        return
                    answers.append(msg.content)
                except Exception:
                    await dm.send("⏰ Timed out. Application cancelled.")
                    return

            await dm.send("✅ Admin application submitted! You'll hear back soon.")

        except discord.Forbidden:
            await ctx.send("❌ I couldn't DM you! Please enable DMs from server members.")
            return

        staff_channel = await self.get_staff_channel(ctx.guild)
        if staff_channel:
            embed = discord.Embed(title="⭐ New Admin Application", color=0xFFD700)
            embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            embed.add_field(name="Member", value=ctx.author.mention, inline=True)
            embed.add_field(name="Level", value=str(level), inline=True)
            for i, (q, a) in enumerate(zip(questions, answers)):
                embed.add_field(name=q, value=a[:1024], inline=False)
            await staff_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Applications(bot))
