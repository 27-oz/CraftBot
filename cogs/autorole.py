import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/autorole.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = load_data()
        guild_id = str(member.guild.id)
        if guild_id not in data:
            return
        for role_id in data[guild_id]:
            role = member.guild.get_role(int(role_id))
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    pass

    @commands.hybrid_command()
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx, action: str, role: discord.Role):
        """Add or remove an auto-role. Usage: !autorole add @Role / !autorole remove @Role"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = []
        if action.lower() == "add":
            if str(role.id) not in data[guild_id]:
                data[guild_id].append(str(role.id))
                save_data(data)
                await ctx.send(f"✅ `{role.name}` will now be given to new members automatically.")
            else:
                await ctx.send(f"⚠️ `{role.name}` is already an auto-role.")
        elif action.lower() == "remove":
            if str(role.id) in data[guild_id]:
                data[guild_id].remove(str(role.id))
                save_data(data)
                await ctx.send(f"✅ `{role.name}` removed from auto-roles.")
            else:
                await ctx.send(f"⚠️ `{role.name}` is not an auto-role.")
        else:
            await ctx.send("❌ Usage: `!autorole add @Role` or `!autorole remove @Role`")

    @commands.hybrid_command()
    async def autoroles(self, ctx):
        """List all current auto-roles for this server."""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data or not data[guild_id]:
            await ctx.send("No auto-roles configured.")
            return
        roles = [ctx.guild.get_role(int(r)) for r in data[guild_id]]
        roles = [r.mention for r in roles if r]
        embed = discord.Embed(title="⚙️ Auto-Roles", description="\n".join(roles), color=0x2196F3)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))