import discord
from discord.ext import commands
import json, os, random
from datetime import datetime, timedelta

DATA_FILE = "data/economy.json"
SHOP_FILE = "data/shop.json"

CHAT_COINS_MIN = 1
CHAT_COINS_MAX = 5
DAILY_REWARD = 100
VOTE_REWARD = 50
CHAT_COOLDOWN_SECONDS = 60

def load_economy():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_economy(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_shop():
    if not os.path.exists(SHOP_FILE):
        return {}
    with open(SHOP_FILE) as f:
        return json.load(f)

def save_shop(data):
    with open(SHOP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(guild_id, user_id):
    data = load_economy()
    gid, uid = str(guild_id), str(user_id)
    if gid not in data:
        data[gid] = {}
    if uid not in data[gid]:
        data[gid][uid] = {"coins": 0, "last_daily": None, "last_chat_coin": None}
    return data, gid, uid

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        data, gid, uid = get_user(message.guild.id, message.author.id)
        now = datetime.utcnow().isoformat()
        last = data[gid][uid].get("last_chat_coin")
        if last:
            diff = (datetime.utcnow() - datetime.fromisoformat(last)).total_seconds()
            if diff < CHAT_COOLDOWN_SECONDS:
                return
        coins = random.randint(CHAT_COINS_MIN, CHAT_COINS_MAX)
        data[gid][uid]["coins"] += coins
        data[gid][uid]["last_chat_coin"] = now
        save_economy(data)

    @commands.hybrid_command(aliases=["bal", "coins"])
    async def balance(self, ctx, member: discord.Member = None):
        """Check your coin balance. Usage: !balance or !balance @user"""
        member = member or ctx.author
        data, gid, uid = get_user(ctx.guild.id, member.id)
        coins = data[gid][uid]["coins"]
        embed = discord.Embed(
            title=f"💰 {member.display_name}'s Balance",
            description=f"**{coins:,}** coins ⛏️",
            color=0xFFD700
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def daily(self, ctx):
        """Claim your daily coin reward. Usage: !daily"""
        data, gid, uid = get_user(ctx.guild.id, ctx.author.id)
        last = data[gid][uid].get("last_daily")
        if last:
            next_claim = datetime.fromisoformat(last) + timedelta(days=1)
            if datetime.utcnow() < next_claim:
                remaining = next_claim - datetime.utcnow()
                hours, rem = divmod(int(remaining.total_seconds()), 3600)
                minutes = rem // 60
                await ctx.send(f"⏰ You already claimed your daily! Come back in **{hours}h {minutes}m**.")
                return
        data[gid][uid]["coins"] += DAILY_REWARD
        data[gid][uid]["last_daily"] = datetime.utcnow().isoformat()
        save_economy(data)
        await ctx.send(f"✅ {ctx.author.mention} claimed their daily reward of **{DAILY_REWARD} coins**! 💰")

    @commands.hybrid_command()
    async def vote(self, ctx):
        """Claim vote coins (for when you vote on server listing sites). Usage: !vote"""
        data, gid, uid = get_user(ctx.guild.id, ctx.author.id)
        data[gid][uid]["coins"] += VOTE_REWARD
        save_economy(data)
        await ctx.send(f"✅ {ctx.author.mention} received **{VOTE_REWARD} coins** for voting! 💰\nMake sure to actually vote at your server listing site!")

    @commands.hybrid_command()
    async def transfer(self, ctx, member: discord.Member, amount: int):
        """Transfer coins to another player. Usage: !transfer @user 50"""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.")
            return
        if member == ctx.author:
            await ctx.send("❌ You can't transfer to yourself.")
            return
        data, gid, uid = get_user(ctx.guild.id, ctx.author.id)
        if data[gid][uid]["coins"] < amount:
            await ctx.send(f"❌ You don't have enough coins. You have **{data[gid][uid]['coins']:,}**.")
            return
        _, _, target_uid = get_user(ctx.guild.id, member.id)
        data[gid][uid]["coins"] -= amount
        data[gid][target_uid]["coins"] += amount
        save_economy(data)
        await ctx.send(f"✅ Transferred **{amount:,} coins** to {member.mention}!")

    @commands.hybrid_command()
    async def richest(self, ctx):
        """Show the richest members. Usage: !richest"""
        data = load_economy()
        gid = str(ctx.guild.id)
        if gid not in data:
            await ctx.send("No economy data yet!")
            return
        sorted_users = sorted(data[gid].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
        embed = discord.Embed(title="💰 Richest Members", color=0xFFD700)
        medals = ["🥇", "🥈", "🥉"] + ["💰"] * 7
        lines = []
        for i, (uid, udata) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown"
            lines.append(f"{medals[i]} **{name}** — {udata['coins']:,} coins")
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def shop(self, ctx):
        """Browse the shop. Usage: !shop"""
        data = load_shop()
        gid = str(ctx.guild.id)
        items = data.get(gid, {})
        if not items:
            await ctx.send("🛒 The shop is empty! Admins can add items with `!additem`.")
            return
        embed = discord.Embed(title="🛒 Shop", color=0x4CAF50)
        for item_id, item in items.items():
            role_info = ""
            if item.get("role_id"):
                role = ctx.guild.get_role(item["role_id"])
                role_info = f" → gives {role.mention}" if role else ""
            embed.add_field(
                name=f"`{item_id}` — {item['name']} — {item['price']:,} coins",
                value=item.get("description", "No description") + role_info,
                inline=False
            )
        embed.set_footer(text="Use !buy <item_id> to purchase")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def buy(self, ctx, item_id: str):
        """Buy an item from the shop. Usage: !buy vip"""
        shop = load_shop()
        gid = str(ctx.guild.id)
        items = shop.get(gid, {})
        item_id = item_id.lower()
        if item_id not in items:
            await ctx.send(f"❌ Item `{item_id}` not found. Use `!shop` to see available items.")
            return
        item = items[item_id]
        data, _, uid = get_user(ctx.guild.id, ctx.author.id)
        user_coins = data[gid][uid]["coins"]
        if user_coins < item["price"]:
            await ctx.send(f"❌ Not enough coins! You have **{user_coins:,}** but need **{item['price']:,}**.")
            return
        data[gid][uid]["coins"] -= item["price"]
        save_economy(data)
        # Give role if attached
        if item.get("role_id"):
            role = ctx.guild.get_role(item["role_id"])
            if role:
                try:
                    await ctx.author.add_roles(role, reason=f"Shop purchase: {item['name']}")
                except discord.Forbidden:
                    pass
        await ctx.send(f"✅ You bought **{item['name']}** for **{item['price']:,} coins**! 🛒")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def additem(self, ctx, item_id: str, price: int, *, name: str):
        """Add an item to the shop. Usage: !additem vip 500 VIP Role"""
        shop = load_shop()
        gid = str(ctx.guild.id)
        if gid not in shop:
            shop[gid] = {}
        shop[gid][item_id.lower()] = {
            "name": name,
            "price": price,
            "description": "A shop item.",
            "role_id": None
        }
        save_shop(shop)
        await ctx.send(f"✅ Added **{name}** to the shop for **{price:,} coins** (ID: `{item_id}`).\nUse `!linkrole {item_id} @Role` to attach a role to it.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def linkrole(self, ctx, item_id: str, role: discord.Role):
        """Link a role to a shop item. Usage: !linkrole vip @VIP"""
        shop = load_shop()
        gid = str(ctx.guild.id)
        item_id = item_id.lower()
        if gid not in shop or item_id not in shop[gid]:
            await ctx.send(f"❌ Item `{item_id}` not found.")
            return
        shop[gid][item_id]["role_id"] = role.id
        save_shop(shop)
        await ctx.send(f"✅ Linked `{role.name}` to shop item `{item_id}`.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def removeitem(self, ctx, item_id: str):
        """Remove an item from the shop. Usage: !removeitem vip"""
        shop = load_shop()
        gid = str(ctx.guild.id)
        item_id = item_id.lower()
        if gid in shop and item_id in shop[gid]:
            del shop[gid][item_id]
            save_shop(shop)
            await ctx.send(f"✅ Removed `{item_id}` from the shop.")
        else:
            await ctx.send(f"❌ Item `{item_id}` not found.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def givecoins(self, ctx, member: discord.Member, amount: int):
        """Give coins to a member. Usage: !givecoins @user 500"""
        data, gid, uid = get_user(ctx.guild.id, member.id)
        data[gid][uid]["coins"] += amount
        save_economy(data)
        await ctx.send(f"✅ Gave **{amount:,} coins** to {member.mention}.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def takecoins(self, ctx, member: discord.Member, amount: int):
        """Take coins from a member. Usage: !takecoins @user 100"""
        data, gid, uid = get_user(ctx.guild.id, member.id)
        data[gid][uid]["coins"] = max(0, data[gid][uid]["coins"] - amount)
        save_economy(data)
        await ctx.send(f"✅ Took **{amount:,} coins** from {member.mention}.")

async def setup(bot):
    await bot.add_cog(Economy(bot))