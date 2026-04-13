import discord
from discord.ext import commands
import aiohttp, random, json, os
from datetime import datetime

EVENTS_FILE = "data/mc_events.json"

MINECRAFT_TIPS = [
    "⛏️ Torches prevent mob spawning! Place them every 12 blocks in your mines.",
    "🌙 Phantoms spawn if you haven't slept in 3+ in-game nights. Sleep regularly!",
    "🔥 Netherite is found below Y=15 in the Nether. Use beds to find it fast (carefully!).",
    "🐑 Name a sheep 'jeb_' to make it cycle through all wool colors!",
    "🍎 Apples + gold nuggets = Golden Apples. Great for early-game healing.",
    "🗺️ Holding a map in your off-hand lets you see it while walking around.",
    "🏃 Sprint-jumping uses less hunger than regular sprinting.",
    "🔦 F3 shows your coordinates! Note your base coords to find it again.",
    "🧲 Lodestone + Compass = a compass that always points to the Lodestone.",
    "🪣 Carrying a water bucket lets you safely fall from any height by placing it!",
    "🌊 Dolphins lead you to underwater ruins and shipwrecks if you feed them fish.",
    "🦅 Elytra + Fireworks = infinite flight. Stock up on rockets!",
    "🌿 Bone meal on grass creates flowers. Great for dyes!",
    "🕯️ You can stack up to 4 candles in one block for more light.",
    "🏔️ Ancient cities are found deep underground in deep dark biomes. Watch for wardens!",
    "🧊 Blue ice is slippery and makes boat highways much faster.",
    "🐐 Goat horns drop when goats ram into solid blocks. Collect them all!",
    "🪵 Scaffolding lets you build up and down quickly. Break the bottom to clear it all.",
    "🎣 Fishing during rain increases your chances of catching something!",
    "🪨 You can mine faster underwater with Aqua Affinity on your helmet.",
]

def load_events():
    if not os.path.exists(EVENTS_FILE):
        return {}
    with open(EVENTS_FILE) as f:
        return json.load(f)

def save_events(data):
    with open(EVENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class MinecraftExtras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def skin(self, ctx, username: str):
        """View a Minecraft player's skin. Usage: !skin Notch"""
        async with aiohttp.ClientSession() as session:
            # Get UUID first
            async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as resp:
                if resp.status == 404:
                    await ctx.send(f"❌ Player `{username}` not found.")
                    return
                if resp.status != 200:
                    await ctx.send("⚠️ Couldn't reach Mojang API right now.")
                    return
                profile = await resp.json()
                uuid = profile["id"]
                name = profile["name"]

        skin_url = f"https://visage.surgeplay.com/full/256/{uuid}"
        face_url = f"https://visage.surgeplay.com/face/128/{uuid}"

        embed = discord.Embed(
            title=f"🎮 {name}'s Skin",
            color=0x4CAF50
        )
        embed.set_image(url=skin_url)
        embed.set_thumbnail(url=face_url)
        embed.add_field(name="Username", value=name, inline=True)
        embed.add_field(name="UUID", value=uuid, inline=True)
        embed.set_footer(text="Skin via visage.surgeplay.com")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def uuid(self, ctx, username: str):
        """Look up a Minecraft player's UUID. Usage: !uuid Notch"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as resp:
                if resp.status == 404:
                    await ctx.send(f"❌ Player `{username}` not found.")
                    return
                if resp.status != 200:
                    await ctx.send("⚠️ Couldn't reach Mojang API right now.")
                    return
                profile = await resp.json()

        uuid = profile["id"]
        formatted = f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"
        embed = discord.Embed(title=f"🔍 UUID Lookup: {profile['name']}", color=0x2196F3)
        embed.add_field(name="Username", value=profile["name"], inline=True)
        embed.add_field(name="UUID (raw)", value=uuid, inline=False)
        embed.add_field(name="UUID (formatted)", value=formatted, inline=False)
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/face/64/{uuid}")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def tip(self, ctx):
        """Get a random Minecraft tip. Usage: !tip"""
        tip = random.choice(MINECRAFT_TIPS)
        embed = discord.Embed(
            title="💡 Minecraft Tip",
            description=tip,
            color=0xFFEB3B
        )
        embed.set_footer(text="Use !tip again for another tip!")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def events(self, ctx):
        """Show upcoming server events. Usage: !events"""
        data = load_events()
        gid = str(ctx.guild.id)
        events = data.get(gid, [])
        now = datetime.utcnow().timestamp()
        upcoming = [e for e in events if e["timestamp"] > now]
        upcoming.sort(key=lambda e: e["timestamp"])

        if not upcoming:
            await ctx.send("📅 No upcoming events! Admins can add events with `!addevent`.")
            return

        embed = discord.Embed(title="📅 Upcoming Server Events", color=0x9C27B0)
        for event in upcoming[:10]:
            dt = datetime.utcfromtimestamp(event["timestamp"])
            time_str = dt.strftime("%b %d, %Y at %H:%M UTC")
            diff = event["timestamp"] - now
            days = int(diff // 86400)
            hours = int((diff % 86400) // 3600)
            countdown = f"in {days}d {hours}h" if days else f"in {hours}h"
            embed.add_field(
                name=f"🎮 {event['name']} — {countdown}",
                value=f"{event.get('description', 'No description')}\n📅 {time_str}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def addevent(self, ctx, date: str, time: str, *, name_and_desc: str):
        """Add a server event. Usage: !addevent 2026-05-01 20:00 SMP Opening | Join us for the grand opening!
        Date format: YYYY-MM-DD, Time format: HH:MM (UTC)"""
        try:
            dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            await ctx.send("❌ Invalid date/time format. Use: `YYYY-MM-DD HH:MM`")
            return

        parts = name_and_desc.split("|", 1)
        name = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""

        data = load_events()
        gid = str(ctx.guild.id)
        if gid not in data:
            data[gid] = []

        data[gid].append({
            "name": name,
            "description": description,
            "timestamp": dt.timestamp()
        })
        save_events(data)
        await ctx.send(f"✅ Event **{name}** added for {dt.strftime('%b %d, %Y at %H:%M UTC')}!")

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def removeevent(self, ctx, *, name: str):
        """Remove an event by name. Usage: !removeevent SMP Opening"""
        data = load_events()
        gid = str(ctx.guild.id)
        events = data.get(gid, [])
        new_events = [e for e in events if e["name"].lower() != name.lower()]
        if len(new_events) == len(events):
            await ctx.send(f"❌ No event named `{name}` found.")
            return
        data[gid] = new_events
        save_events(data)
        await ctx.send(f"✅ Removed event `{name}`.")

async def setup(bot):
    await bot.add_cog(MinecraftExtras(bot))
