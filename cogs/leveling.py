import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
import json, os, random
from datetime import datetime, timedelta

DATA_FILE = "data/levels.json"
CONFIG_FILE = "data/levels_config.json"
LEVEL_THRESHOLDS = [10, 25, 50, 75, 100]
PERKS = {
    10:  {"name": "Settler",  "perk": "Access to suggestions"},
    25:  {"name": "Villager", "perk": "Access to staff applications"},
    50:  {"name": "Knight",   "perk": "Access to admin applications"},
    75:  {"name": "Elder",    "perk": "Special Elder role"},
    100: {"name": "Legend",   "perk": "Legend role — the highest honor"},
}

def xp_for_level(level): return 100 * (level ** 2)
def get_level(xp):
    level = 0
    while xp >= xp_for_level(level + 1): level += 1
    return level

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)
def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE) as f: return json.load(f)
def save_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=2)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def get_user(self, guild_id, user_id):
        data = load_data()
        gid, uid = str(guild_id), str(user_id)
        if gid not in data: data[gid] = {}
        if uid not in data[gid]: data[gid][uid] = {"xp": 0, "level": 0}
        return data, gid, uid

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        try:
            from cogs.xpconfig import is_xp_blacklisted
            if is_xp_blacklisted(message.guild.id, message.channel.id): return
        except Exception: pass
        uid = message.author.id
        now = datetime.utcnow()
        if uid in self.cooldowns and now - self.cooldowns[uid] < timedelta(seconds=60): return
        self.cooldowns[uid] = now
        base_xp = random.randint(10, 25)
        try:
            from cogs.xpconfig import get_xp_multiplier
            multiplier = get_xp_multiplier(message.guild.id)
        except Exception: multiplier = 1.0
        xp_gain = int(base_xp * multiplier)
        data, gid, uid_str = self.get_user(message.guild.id, uid)
        old_level = data[gid][uid_str]["level"]
        data[gid][uid_str]["xp"] += xp_gain
        new_level = get_level(data[gid][uid_str]["xp"])
        data[gid][uid_str]["level"] = new_level
        save_data(data)
        if new_level > old_level:
            await self.on_level_up(message, new_level)

    async def on_level_up(self, message, new_level):
        config = load_config()
        gid = str(message.guild.id)
        level_channel_id = config.get(gid, {}).get("level_channel")
        channel = message.guild.get_channel(level_channel_id) if level_channel_id else message.channel
        embed = discord.Embed(title="Level Up!", description=f"{message.author.mention} reached **Level {new_level}**!", color=0xFFD700)
        if new_level in PERKS:
            perk = PERKS[new_level]
            embed.add_field(name="Perk Unlocked", value=perk["perk"], inline=False)
            role_id = config.get(gid, {}).get("level_roles", {}).get(str(new_level))
            if role_id:
                role = message.guild.get_role(int(role_id))
                if role:
                    try: await message.author.add_roles(role, reason=f"Reached level {new_level}")
                    except discord.Forbidden: pass
        await channel.send(embed=embed)

    async def _rank(self, send, guild, member):
        data, gid, uid = self.get_user(guild.id, member.id)
        user_data = data[gid][uid]
        xp, level = user_data["xp"], user_data["level"]
        next_xp = xp_for_level(level + 1)
        progress = int((xp / next_xp) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        embed = discord.Embed(title=f"{member.display_name}'s Rank", color=member.top_role.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp} / {next_xp}", inline=True)
        embed.add_field(name="Progress", value=f"`{bar}`", inline=False)
        next_perk = next((l for l in LEVEL_THRESHOLDS if l > level), None)
        if next_perk:
            embed.add_field(name=f"Next perk at Level {next_perk}", value=PERKS[next_perk]["perk"], inline=False)
        await send(embed=embed)

    @app_commands.command(name="rank", description="Check your level and XP")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def rank_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._rank(interaction.response.send_message, interaction.guild, member or interaction.user)

    @commands.hybrid_command(name="rank")
    async def rank_prefix(self, ctx, member: discord.Member = None):
        await self._rank(ctx.send, ctx.guild, member or ctx.author)

    async def _leaderboard(self, send, guild):
        data = load_data()
        gid = str(guild.id)
        if gid not in data:
            await send("No XP data yet!"); return
        sorted_users = sorted(data[gid].items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
        embed = discord.Embed(title="XP Leaderboard", color=0xFFD700)
        medals = ["1.", "2.", "3."] + [f"{i}." for i in range(4, 11)]
        desc = []
        for i, (uid, udata) in enumerate(sorted_users):
            m = guild.get_member(int(uid))
            name = m.display_name if m else "Unknown"
            desc.append(f"{medals[i]} **{name}** — Level {udata['level']} ({udata['xp']} XP)")
        embed.description = "\n".join(desc)
        await send(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the top 10 most active members")
    async def leaderboard_slash(self, interaction: discord.Interaction):
        await self._leaderboard(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="leaderboard")
    async def leaderboard_prefix(self, ctx):
        await self._leaderboard(ctx.send, ctx.guild)

    async def _perks(self, send):
        embed = discord.Embed(title="Level Perks", color=0x4CAF50)
        for level, info in PERKS.items():
            embed.add_field(name=f"Level {level} — {info['name']}", value=info["perk"], inline=False)
        await send(embed=embed)

    @app_commands.command(name="perks", description="Show all level perks")
    async def perks_slash(self, interaction: discord.Interaction):
        await self._perks(interaction.response.send_message)

    @commands.hybrid_command(name="perks")
    async def perks_prefix(self, ctx):
        await self._perks(ctx.send)

    @app_commands.command(name="setlevelchannel", description="Set the level-up announcement channel")
    @app_commands.describe(channel="The channel for level-up announcements")
    async def setlevelchannel_slash(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission to do that.", ephemeral=True); return
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["level_channel"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"Level-up announcements will go to {channel.mention}!")

    @commands.hybrid_command(name="setlevelchannel")
    @commands.has_permissions(manage_guild=True)
    async def setlevelchannel_prefix(self, ctx, channel: discord.TextChannel):
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["level_channel"] = channel.id
        save_config(config)
        await ctx.send(f"Level-up announcements will go to {channel.mention}!")

    @app_commands.command(name="setlevelrole", description="Assign a role to be given at a specific level")
    @app_commands.describe(level="The level threshold", role="The role to assign")
    async def setlevelrole_slash(self, interaction: discord.Interaction, level: int, role: discord.Role):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        if level not in LEVEL_THRESHOLDS:
            await interaction.response.send_message(f"Valid levels: {', '.join(map(str, LEVEL_THRESHOLDS))}", ephemeral=True); return
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        if "level_roles" not in config[gid]: config[gid]["level_roles"] = {}
        config[gid]["level_roles"][str(level)] = role.id
        save_config(config)
        await interaction.response.send_message(f"`{role.name}` will be given at Level {level}!")

    @commands.hybrid_command(name="setlevelrole")
    @commands.has_permissions(manage_guild=True)
    async def setlevelrole_prefix(self, ctx, level: int, role: discord.Role):
        if level not in LEVEL_THRESHOLDS:
            await ctx.send(f"Valid levels: {', '.join(map(str, LEVEL_THRESHOLDS))}"); return
        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config: config[gid] = {}
        if "level_roles" not in config[gid]: config[gid]["level_roles"] = {}
        config[gid]["level_roles"][str(level)] = role.id
        save_config(config)
        await ctx.send(f"`{role.name}` will be given at Level {level}!")

    @app_commands.command(name="setxp", description="Set a member's XP directly")
    @app_commands.describe(member="The member", amount="The XP amount")
    async def setxp_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data, gid, uid = self.get_user(interaction.guild.id, member.id)
        data[gid][uid]["xp"] = max(0, amount)
        data[gid][uid]["level"] = get_level(max(0, amount))
        save_data(data)
        await interaction.response.send_message(f"Set {member.mention}'s XP to `{amount}` (Level {data[gid][uid]['level']}).")

    @commands.hybrid_command(name="setxp")
    @commands.has_permissions(manage_guild=True)
    async def setxp_prefix(self, ctx, member: discord.Member, amount: int):
        data, gid, uid = self.get_user(ctx.guild.id, member.id)
        data[gid][uid]["xp"] = max(0, amount)
        data[gid][uid]["level"] = get_level(max(0, amount))
        save_data(data)
        await ctx.send(f"Set {member.mention}'s XP to `{amount}` (Level {data[gid][uid]['level']}).")

    @app_commands.command(name="addxp", description="Add or subtract XP from a member")
    @app_commands.describe(member="The member", amount="Amount to add (negative to subtract)")
    async def addxp_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data, gid, uid = self.get_user(interaction.guild.id, member.id)
        data[gid][uid]["xp"] = max(0, data[gid][uid]["xp"] + amount)
        data[gid][uid]["level"] = get_level(data[gid][uid]["xp"])
        save_data(data)
        action = "Added" if amount >= 0 else "Removed"
        await interaction.response.send_message(f"{action} `{abs(amount)}` XP {'to' if amount >= 0 else 'from'} {member.mention}. Now Level {data[gid][uid]['level']}.")

    @commands.hybrid_command(name="addxp")
    @commands.has_permissions(manage_guild=True)
    async def addxp_prefix(self, ctx, member: discord.Member, amount: int):
        data, gid, uid = self.get_user(ctx.guild.id, member.id)
        data[gid][uid]["xp"] = max(0, data[gid][uid]["xp"] + amount)
        data[gid][uid]["level"] = get_level(data[gid][uid]["xp"])
        save_data(data)
        action = "Added" if amount >= 0 else "Removed"
        await ctx.send(f"{action} `{abs(amount)}` XP {'to' if amount >= 0 else 'from'} {member.mention}. Now Level {data[gid][uid]['level']}.")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
