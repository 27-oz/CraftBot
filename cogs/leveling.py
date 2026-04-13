import discord
from discord.ext import commands
import json, os, random, asyncio
from datetime import datetime, timedelta

DATA_FILE = "data/levels.json"
CONFIG_FILE = "data/levels_config.json"

LEVEL_THRESHOLDS = [10, 25, 50, 75, 100]

PERKS = {
    10:  {"name": "Settler",      "perk": "Access to #suggestions"},
    25:  {"name": "Villager",     "perk": "Access to staff applications"},
    50:  {"name": "Knight",       "perk": "Access to admin applications"},
    75:  {"name": "Elder",        "perk": "Special Elder role & bragging rights"},
    100: {"name": "Legend",       "perk": "Legend role — the highest honor"},
}

def xp_for_level(level):
    return 100 * (level ** 2)

def get_level(xp):
    level = 0
    while xp >= xp_for_level(level + 1):
        level += 1
    return level

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # user_id -> last xp time

    def get_user(self, guild_id, user_id):
        data = load_data()
        gid = str(guild_id)
        uid = str(user_id)
        if gid not in data:
            data[gid] = {}
        if uid not in data[gid]:
            data[gid][uid] = {"xp": 0, "level": 0}
        return data, gid, uid

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        uid = message.author.id
        now = datetime.utcnow()

        # 60 second XP cooldown per user
        if uid in self.cooldowns:
            if now - self.cooldowns[uid] < timedelta(seconds=60):
                return

        self.cooldowns[uid] = now
        xp_gain = random.randint(10, 25)

        data, gid, user_id = self.get_user(message.guild.id, uid)
        old_level = data[gid][user_id]["level"]
        data[gid][user_id]["xp"] += xp_gain
        new_level = get_level(data[gid][user_id]["xp"])
        data[gid][user_id]["level"] = new_level
        save_data(data)

        if new_level > old_level:
            await self.on_level_up(message, new_level)

    async def on_level_up(self, message, new_level):
        config = load_config()
        gid = str(message.guild.id)

        # Send level up message
        level_channel_id = config.get(gid, {}).get("level_channel")
        channel = message.guild.get_channel(level_channel_id) if level_channel_id else message.channel

        embed = discord.Embed(
            title="⬆️ Level Up!",
            description=f"{message.author.mention} reached **Level {new_level}**! ⛏️",
            color=0xFFD700
        )

        if new_level in PERKS:
            perk = PERKS[new_level]
            embed.add_field(name="🎉 Perk Unlocked!", value=perk["perk"], inline=False)
            embed.set_footer(text=f"Role unlocked: {perk['name']}")

            # Assign level role if configured
            role_id = config.get(gid, {}).get("level_roles", {}).get(str(new_level))
            if role_id:
                role = message.guild.get_role(int(role_id))
                if role:
                    try:
                        await message.author.add_roles(role, reason=f"Reached level {new_level}")
                    except discord.Forbidden:
                        pass

        await channel.send(embed=embed)

    @commands.hybrid_command()
    async def rank(self, ctx, member: discord.Member = None):
        """Check your level and XP. Usage: !rank or !rank @user"""
        member = member or ctx.author
        data, gid, uid = self.get_user(ctx.guild.id, member.id)
        user_data = data[gid][uid]
        xp = user_data["xp"]
        level = user_data["level"]
        next_level_xp = xp_for_level(level + 1)
        progress = int((xp / next_level_xp) * 20)
        bar = "█" * progress + "░" * (20 - progress)

        embed = discord.Embed(
            title=f"⛏️ {member.display_name}'s Rank",
            color=member.top_role.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp} / {next_level_xp}", inline=True)
        embed.add_field(name="Progress", value=f"`{bar}`", inline=False)

        # Show next perk
        next_perk_level = next((l for l in LEVEL_THRESHOLDS if l > level), None)
        if next_perk_level:
            embed.add_field(
                name=f"🎯 Next perk at Level {next_perk_level}",
                value=PERKS[next_perk_level]["perk"],
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def leaderboard(self, ctx):
        """Show the top 10 most active members."""
        data = load_data()
        gid = str(ctx.guild.id)
        if gid not in data:
            await ctx.send("No XP data yet!")
            return

        sorted_users = sorted(data[gid].items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
        embed = discord.Embed(title="🏆 XP Leaderboard", color=0xFFD700)
        medals = ["🥇", "🥈", "🥉"] + ["⛏️"] * 7

        desc = []
        for i, (uid, udata) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown ({uid})"
            desc.append(f"{medals[i]} **{name}** — Level {udata['level']} ({udata['xp']} XP)")

        embed.description = "\n".join(desc)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setlevelchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for level-up announcements. Usage: !setlevelchannel #channel"""
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["level_channel"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Level-up announcements will go to {channel.mention}!")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setlevelrole(self, ctx, level: int, role: discord.Role):
        """Assign a role to be given at a specific level. Usage: !setlevelrole 10 @Settler"""
        if level not in LEVEL_THRESHOLDS:
            await ctx.send(f"⚠️ Valid levels are: {', '.join(map(str, LEVEL_THRESHOLDS))}")
            return
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        if "level_roles" not in config[gid]:
            config[gid]["level_roles"] = {}
        config[gid]["level_roles"][str(level)] = role.id
        save_config(config)
        await ctx.send(f"✅ `{role.name}` will be given at Level {level} ({PERKS[level]['name']})!")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setxp(self, ctx, member: discord.Member, amount: int):
        """Set a member's XP directly. Usage: !setxp @user 500"""
        data, gid, uid = self.get_user(ctx.guild.id, member.id)
        old_level = data[gid][uid]["level"]
        data[gid][uid]["xp"] = max(0, amount)
        new_level = get_level(data[gid][uid]["xp"])
        data[gid][uid]["level"] = new_level
        save_data(data)
        await ctx.send(f"✅ Set {member.mention}'s XP to `{amount}` (Level {new_level}).")
        if new_level > old_level:
            class FakeMsg:
                author = member
                guild = ctx.guild
                channel = ctx.channel
            await self.on_level_up(FakeMsg(), new_level)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def addxp(self, ctx, member: discord.Member, amount: int):
        """Add or subtract XP from a member. Usage: !addxp @user 100 or !addxp @user -50"""
        data, gid, uid = self.get_user(ctx.guild.id, member.id)
        old_level = data[gid][uid]["level"]
        data[gid][uid]["xp"] = max(0, data[gid][uid]["xp"] + amount)
        new_level = get_level(data[gid][uid]["xp"])
        data[gid][uid]["level"] = new_level
        save_data(data)
        action = "Added" if amount >= 0 else "Removed"
        await ctx.send(f"✅ {action} `{abs(amount)}` XP {'to' if amount >= 0 else 'from'} {member.mention}. Now Level {new_level} ({data[gid][uid]['xp']} XP).")
        if new_level > old_level:
            class FakeMsg:
                author = member
                guild = ctx.guild
                channel = ctx.channel
            await self.on_level_up(FakeMsg(), new_level)

    @commands.hybrid_command()
    async def perks(self, ctx):
        """Show all level perks."""
        embed = discord.Embed(title="🎯 Level Perks", color=0x4CAF50)
        for level, info in PERKS.items():
            embed.add_field(
                name=f"Level {level} — {info['name']}",
                value=info["perk"],
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))