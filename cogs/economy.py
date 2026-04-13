import discord
from discord.ext import commands
from discord import app_commands
import json, os, random
from datetime import datetime, timedelta

DATA_FILE = "data/economy.json"
SHOP_FILE = "data/shop.json"
CHAT_COINS_MIN, CHAT_COINS_MAX = 1, 5
DAILY_REWARD = 100
VOTE_REWARD = 50
CHAT_COOLDOWN_SECONDS = 60

def load_economy():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE) as f: return json.load(f)
def save_economy(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)
def load_shop():
    if not os.path.exists(SHOP_FILE): return {}
    with open(SHOP_FILE) as f: return json.load(f)
def save_shop(data):
    with open(SHOP_FILE, "w") as f: json.dump(data, f, indent=2)

def get_user(guild_id, user_id):
    data = load_economy()
    gid, uid = str(guild_id), str(user_id)
    if gid not in data: data[gid] = {}
    if uid not in data[gid]: data[gid][uid] = {"coins": 0, "last_daily": None, "last_chat_coin": None}
    return data, gid, uid

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        data, gid, uid = get_user(message.guild.id, message.author.id)
        now = datetime.utcnow().isoformat()
        last = data[gid][uid].get("last_chat_coin")
        if last and (datetime.utcnow() - datetime.fromisoformat(last)).total_seconds() < CHAT_COOLDOWN_SECONDS: return
        data[gid][uid]["coins"] += random.randint(CHAT_COINS_MIN, CHAT_COINS_MAX)
        data[gid][uid]["last_chat_coin"] = now
        save_economy(data)

    async def _balance(self, send, guild, member):
        data, gid, uid = get_user(guild.id, member.id)
        embed = discord.Embed(title=f"{member.display_name}'s Balance", description=f"**{data[gid][uid]['coins']:,}** coins", color=0xFFD700)
        await send(embed=embed)

    @app_commands.command(name="balance", description="Check your coin balance")
    @app_commands.describe(member="The member to check (defaults to you)")
    async def balance_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._balance(interaction.response.send_message, interaction.guild, member or interaction.user)

    @commands.hybrid_command(name="balance", aliases=["bal", "coins"])
    async def balance_prefix(self, ctx, member: discord.Member = None):
        await self._balance(ctx.send, ctx.guild, member or ctx.author)

    async def _daily(self, send, guild, user):
        data, gid, uid = get_user(guild.id, user.id)
        last = data[gid][uid].get("last_daily")
        if last:
            next_claim = datetime.fromisoformat(last) + timedelta(days=1)
            if datetime.utcnow() < next_claim:
                remaining = next_claim - datetime.utcnow()
                hours, rem = divmod(int(remaining.total_seconds()), 3600)
                await send(f"You already claimed your daily! Come back in **{hours}h {rem//60}m**."); return
        data[gid][uid]["coins"] += DAILY_REWARD
        data[gid][uid]["last_daily"] = datetime.utcnow().isoformat()
        save_economy(data)
        await send(f"{user.mention} claimed their daily reward of **{DAILY_REWARD} coins**!")

    @app_commands.command(name="daily", description="Claim your daily coin reward")
    async def daily_slash(self, interaction: discord.Interaction):
        await self._daily(interaction.response.send_message, interaction.guild, interaction.user)

    @commands.hybrid_command(name="daily")
    async def daily_prefix(self, ctx):
        await self._daily(ctx.send, ctx.guild, ctx.author)

    async def _vote(self, send, guild, user):
        data, gid, uid = get_user(guild.id, user.id)
        data[gid][uid]["coins"] += VOTE_REWARD
        save_economy(data)
        await send(f"{user.mention} received **{VOTE_REWARD} coins** for voting!")

    @app_commands.command(name="vote", description="Claim vote coins")
    async def vote_slash(self, interaction: discord.Interaction):
        await self._vote(interaction.response.send_message, interaction.guild, interaction.user)

    @commands.hybrid_command(name="vote")
    async def vote_prefix(self, ctx):
        await self._vote(ctx.send, ctx.guild, ctx.author)

    async def _transfer(self, send, guild, author, member, amount):
        if amount <= 0: await send("Amount must be positive."); return
        if member == author: await send("You can't transfer to yourself."); return
        data, gid, uid = get_user(guild.id, author.id)
        if data[gid][uid]["coins"] < amount: await send(f"Not enough coins. You have **{data[gid][uid]['coins']:,}**."); return
        _, _, tuid = get_user(guild.id, member.id)
        data[gid][uid]["coins"] -= amount
        data[gid][tuid]["coins"] += amount
        save_economy(data)
        await send(f"Transferred **{amount:,} coins** to {member.mention}!")

    @app_commands.command(name="transfer", description="Transfer coins to another player")
    @app_commands.describe(member="The recipient", amount="Amount to transfer")
    async def transfer_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await self._transfer(interaction.response.send_message, interaction.guild, interaction.user, member, amount)

    @commands.hybrid_command(name="transfer")
    async def transfer_prefix(self, ctx, member: discord.Member, amount: int):
        await self._transfer(ctx.send, ctx.guild, ctx.author, member, amount)

    async def _richest(self, send, guild):
        data = load_economy()
        gid = str(guild.id)
        if gid not in data: await send("No economy data yet!"); return
        sorted_users = sorted(data[gid].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
        embed = discord.Embed(title="Richest Members", color=0xFFD700)
        lines = []
        for i, (uid, udata) in enumerate(sorted_users, 1):
            m = guild.get_member(int(uid))
            lines.append(f"{i}. **{m.display_name if m else 'Unknown'}** — {udata['coins']:,} coins")
        embed.description = "\n".join(lines)
        await send(embed=embed)

    @app_commands.command(name="richest", description="Show the richest members")
    async def richest_slash(self, interaction: discord.Interaction):
        await self._richest(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="richest")
    async def richest_prefix(self, ctx):
        await self._richest(ctx.send, ctx.guild)

    async def _shop(self, send, guild):
        data = load_shop()
        gid = str(guild.id)
        items = data.get(gid, {})
        if not items: await send("The shop is empty! Admins can add items with `/additem`."); return
        embed = discord.Embed(title="Shop", color=0x4CAF50)
        for item_id, item in items.items():
            embed.add_field(name=f"`{item_id}` — {item['name']} — {item['price']:,} coins", value=item.get("description", "No description"), inline=False)
        embed.set_footer(text="Use /buy <item_id> to purchase")
        await send(embed=embed)

    @app_commands.command(name="shop", description="Browse the shop")
    async def shop_slash(self, interaction: discord.Interaction):
        await self._shop(interaction.response.send_message, interaction.guild)

    @commands.hybrid_command(name="shop")
    async def shop_prefix(self, ctx):
        await self._shop(ctx.send, ctx.guild)

    async def _buy(self, send, guild, user, item_id):
        shop = load_shop()
        gid = str(guild.id)
        items = shop.get(gid, {})
        item_id = item_id.lower()
        if item_id not in items: await send(f"Item `{item_id}` not found."); return
        item = items[item_id]
        data, _, uid = get_user(guild.id, user.id)
        if data[gid][uid]["coins"] < item["price"]: await send(f"Not enough coins! You need **{item['price']:,}**."); return
        data[gid][uid]["coins"] -= item["price"]
        save_economy(data)
        if item.get("role_id"):
            role = guild.get_role(item["role_id"])
            if role:
                member = guild.get_member(user.id)
                if member:
                    try: await member.add_roles(role)
                    except discord.Forbidden: pass
        await send(f"You bought **{item['name']}** for **{item['price']:,} coins**!")

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item_id="The item ID from /shop")
    async def buy_slash(self, interaction: discord.Interaction, item_id: str):
        await self._buy(interaction.response.send_message, interaction.guild, interaction.user, item_id)

    @commands.hybrid_command(name="buy")
    async def buy_prefix(self, ctx, item_id: str):
        await self._buy(ctx.send, ctx.guild, ctx.author, item_id)

    @app_commands.command(name="additem", description="Add an item to the shop")
    @app_commands.describe(item_id="Short ID (e.g. vip)", price="Coin price", name="Display name")
    async def additem_slash(self, interaction: discord.Interaction, item_id: str, price: int, name: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        shop = load_shop()
        gid = str(interaction.guild.id)
        if gid not in shop: shop[gid] = {}
        shop[gid][item_id.lower()] = {"name": name, "price": price, "description": "A shop item.", "role_id": None}
        save_shop(shop)
        await interaction.response.send_message(f"Added **{name}** to the shop for **{price:,} coins**!")

    @commands.hybrid_command(name="additem")
    @commands.has_permissions(manage_guild=True)
    async def additem_prefix(self, ctx, item_id: str, price: int, *, name: str):
        shop = load_shop()
        gid = str(ctx.guild.id)
        if gid not in shop: shop[gid] = {}
        shop[gid][item_id.lower()] = {"name": name, "price": price, "description": "A shop item.", "role_id": None}
        save_shop(shop)
        await ctx.send(f"Added **{name}** to the shop for **{price:,} coins**!")

    @app_commands.command(name="givecoins", description="Give coins to a member")
    @app_commands.describe(member="The member", amount="Amount to give")
    async def givecoins_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data, gid, uid = get_user(interaction.guild.id, member.id)
        data[gid][uid]["coins"] += amount
        save_economy(data)
        await interaction.response.send_message(f"Gave **{amount:,} coins** to {member.mention}.")

    @commands.hybrid_command(name="givecoins")
    @commands.has_permissions(manage_guild=True)
    async def givecoins_prefix(self, ctx, member: discord.Member, amount: int):
        data, gid, uid = get_user(ctx.guild.id, member.id)
        data[gid][uid]["coins"] += amount
        save_economy(data)
        await ctx.send(f"Gave **{amount:,} coins** to {member.mention}.")

    @app_commands.command(name="takecoins", description="Take coins from a member")
    @app_commands.describe(member="The member", amount="Amount to take")
    async def takecoins_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You don't have permission.", ephemeral=True); return
        data, gid, uid = get_user(interaction.guild.id, member.id)
        data[gid][uid]["coins"] = max(0, data[gid][uid]["coins"] - amount)
        save_economy(data)
        await interaction.response.send_message(f"Took **{amount:,} coins** from {member.mention}.")

    @commands.hybrid_command(name="takecoins")
    @commands.has_permissions(manage_guild=True)
    async def takecoins_prefix(self, ctx, member: discord.Member, amount: int):
        data, gid, uid = get_user(ctx.guild.id, member.id)
        data[gid][uid]["coins"] = max(0, data[gid][uid]["coins"] - amount)
        save_economy(data)
        await ctx.send(f"Took **{amount:,} coins** from {member.mention}.")

async def setup(bot):
    await bot.add_cog(Economy(bot))
