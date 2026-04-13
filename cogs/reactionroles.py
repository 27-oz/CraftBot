import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/reactionroles.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_key(self, message_id, emoji):
        return f"{message_id}:{str(emoji)}"

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        data = load_data()
        key = self.get_key(payload.message_id, payload.emoji)
        if key not in data:
            return
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(data[key])
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.add_roles(role, reason="Reaction role")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        data = load_data()
        key = self.get_key(payload.message_id, payload.emoji)
        if key not in data:
            return
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(data[key])
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.remove_roles(role, reason="Reaction role removed")

    @commands.hybrid_command()
    @commands.has_permissions(manage_roles=True)
    async def rradd(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Bind an emoji reaction on a message to a role.
        Usage: !rradd <message_id> <emoji> @Role"""
        data = load_data()
        key = self.get_key(message_id, emoji)
        data[key] = role.id
        save_data(data)
        await ctx.send(f"✅ Reacting with {emoji} on message `{message_id}` will now give `{role.name}`.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_roles=True)
    async def rrremove(self, ctx, message_id: int, emoji: str):
        """Remove a reaction role binding.
        Usage: !rrremove <message_id> <emoji>"""
        data = load_data()
        key = self.get_key(message_id, emoji)
        if key in data:
            del data[key]
            save_data(data)
            await ctx.send(f"✅ Reaction role removed.")
        else:
            await ctx.send("⚠️ No reaction role found for that message/emoji combo.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_roles=True)
    async def rrpanel(self, ctx, *, description: str):
        """Post a reaction role panel in the current channel.
        Usage: !rrpanel Pick your roles below!"""
        embed = discord.Embed(
            title="🎭 Role Selection",
            description=description,
            color=0x9C27B0
        )
        embed.set_footer(text="React to get your role!")
        msg = await ctx.send(embed=embed)
        await ctx.send(f"✅ Panel posted! Message ID: `{msg.id}` — use `!rradd {msg.id} <emoji> @Role` to bind roles.")

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
