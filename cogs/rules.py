import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/rules.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def rules(self, ctx):
        """Show server rules. Usage: !rules"""
        data = load_data()
        gid = str(ctx.guild.id)
        rules_list = data.get(gid, {}).get("rules", [])

        if not rules_list:
            await ctx.send("No rules set yet! Admins can use `!setrules` to add them.")
            return

        embed = discord.Embed(
            title=f"📜 {ctx.guild.name} — Rules",
            color=0x4CAF50
        )
        for i, rule in enumerate(rules_list, 1):
            embed.add_field(name=f"Rule {i}", value=rule, inline=False)
        embed.set_footer(text="Breaking rules may result in a warning, mute, or ban.")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setrules(self, ctx, *, rules_text: str):
        """Set server rules. Separate each rule with a | symbol.
        Usage: !setrules Be respectful | No spamming | No griefing"""
        rules_list = [r.strip() for r in rules_text.split("|") if r.strip()]
        data = load_data()
        gid = str(ctx.guild.id)
        if gid not in data:
            data[gid] = {}
        data[gid]["rules"] = rules_list
        save_data(data)
        await ctx.send(f"✅ Set {len(rules_list)} rules! Use `!rules` to preview.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def addrule(self, ctx, *, rule: str):
        """Add a single rule. Usage: !addrule No hacking"""
        data = load_data()
        gid = str(ctx.guild.id)
        if gid not in data:
            data[gid] = {}
        if "rules" not in data[gid]:
            data[gid]["rules"] = []
        data[gid]["rules"].append(rule)
        save_data(data)
        await ctx.send(f"✅ Rule added: *{rule}*")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def removerule(self, ctx, number: int):
        """Remove a rule by number. Usage: !removerule 3"""
        data = load_data()
        gid = str(ctx.guild.id)
        rules = data.get(gid, {}).get("rules", [])
        if number < 1 or number > len(rules):
            await ctx.send(f"❌ Invalid rule number. There are {len(rules)} rules.")
            return
        removed = rules.pop(number - 1)
        data[gid]["rules"] = rules
        save_data(data)
        await ctx.send(f"✅ Removed rule {number}: *{removed}*")

async def setup(bot):
    await bot.add_cog(Rules(bot))