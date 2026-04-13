import discord
from discord.ext import commands
from discord import app_commands
import json, os

DATA_FILE = "data/rules.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _rules(self, send, guild):
        data = load_data()
        rules_list = data.get(str(guild.id), {}).get("rules", [])
        if not rules_list: await send("No rules set yet! Admins can use `/setrules` to add them."); return
        embed = discord.Embed(title=f"{guild.name} — Rules", color=0x4CAF50)
        for i, rule in enumerate(rules_list, 1):
            embed.add_field(name=f"Rule {i}", value=rule, inline=False)
        embed.set_footer(text="Breaking rules may result in a warning, mute, or ban.")
        await send(embed=embed)

    @app_commands.command(name="rules", description="Show server rules")
    async def rules_slash(self, interaction: discord.Interaction):
        await self._rules(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="rules")
    async def rules_prefix(self, ctx):
        await self._rules(ctx.send, ctx.guild)

    @app_commands.command(name="setrules", description="Set server rules, separated by |")
    @app_commands.describe(rules_text="Rule 1 | Rule 2 | Rule 3")
    async def setrules_slash(self, interaction: discord.Interaction, rules_text: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        rules_list = [r.strip() for r in rules_text.split("|") if r.strip()]
        data = load_data()
        gid = str(interaction.guild.id)
        if gid not in data: data[gid] = {}
        data[gid]["rules"] = rules_list
        save_data(data)
        await interaction.response.send_message(f"Set {len(rules_list)} rules!")

    @commands.hybrid_command(name="setrules")
    @commands.has_permissions(manage_guild=True)
    async def setrules_prefix(self, ctx, *, rules_text: str):
        rules_list = [r.strip() for r in rules_text.split("|") if r.strip()]
        data = load_data()
        gid = str(ctx.guild.id)
        if gid not in data: data[gid] = {}
        data[gid]["rules"] = rules_list
        save_data(data)
        await ctx.send(f"Set {len(rules_list)} rules!")

    @app_commands.command(name="addrule", description="Add a single rule")
    @app_commands.describe(rule="The rule to add")
    async def addrule_slash(self, interaction: discord.Interaction, rule: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data = load_data()
        gid = str(interaction.guild.id)
        if gid not in data: data[gid] = {}
        if "rules" not in data[gid]: data[gid]["rules"] = []
        data[gid]["rules"].append(rule)
        save_data(data)
        await interaction.response.send_message(f"Rule added: *{rule}*")

    @commands.hybrid_command(name="addrule")
    @commands.has_permissions(manage_guild=True)
    async def addrule_prefix(self, ctx, *, rule: str):
        data = load_data()
        gid = str(ctx.guild.id)
        if gid not in data: data[gid] = {}
        if "rules" not in data[gid]: data[gid]["rules"] = []
        data[gid]["rules"].append(rule)
        save_data(data)
        await ctx.send(f"Rule added: *{rule}*")

    @app_commands.command(name="removerule", description="Remove a rule by number")
    @app_commands.describe(number="The rule number to remove")
    async def removerule_slash(self, interaction: discord.Interaction, number: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data = load_data()
        gid = str(interaction.guild.id)
        rules = data.get(gid, {}).get("rules", [])
        if number < 1 or number > len(rules): await interaction.response.send_message(f"Invalid rule number.", ephemeral=True); return
        removed = rules.pop(number - 1)
        data[gid]["rules"] = rules
        save_data(data)
        await interaction.response.send_message(f"Removed rule {number}: *{removed}*")

    @commands.hybrid_command(name="removerule")
    @commands.has_permissions(manage_guild=True)
    async def removerule_prefix(self, ctx, number: int):
        data = load_data()
        gid = str(ctx.guild.id)
        rules = data.get(gid, {}).get("rules", [])
        if number < 1 or number > len(rules): await ctx.send("Invalid rule number."); return
        removed = rules.pop(number - 1)
        data[gid]["rules"] = rules
        save_data(data)
        await ctx.send(f"Removed rule {number}: *{removed}*")

async def setup(bot):
    await bot.add_cog(Rules(bot))
