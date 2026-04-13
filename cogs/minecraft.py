import discord
from discord.ext import commands
import aiohttp, urllib.parse

WHITELIST_ROLE_NAME = "Whitelist"  # Change this to match your exact role name

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def wiki(self, ctx, *, term: str):
        """Look up a term on the Minecraft Wiki. Usage: !wiki creeper"""
        encoded = urllib.parse.quote(term.replace(" ", "_"))
        url = f"https://minecraft.wiki/w/{encoded}"
        api_url = f"https://minecraft.wiki/api.php?action=query&titles={urllib.parse.quote(term)}&prop=extracts&exintro=true&explaintext=true&format=json"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    page = next(iter(pages.values()))

                    if "missing" in page:
                        await ctx.send(f"❌ Couldn't find `{term}` on the Minecraft Wiki. Try a different spelling?")
                        return

                    extract = page.get("extract", "")
                    # Trim to first 2 paragraphs
                    paragraphs = [p for p in extract.split("\n") if p.strip()]
                    summary = "\n\n".join(paragraphs[:2])[:500]
                    if len(summary) == 500:
                        summary += "..."

                    embed = discord.Embed(
                        title=f"📖 {page.get('title', term)}",
                        description=summary,
                        url=url,
                        color=0x4CAF50
                    )
                    embed.set_footer(text="Minecraft Wiki • Click title for full article")
                    await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"⚠️ Couldn't reach the Minecraft Wiki right now. Try: {url}")

    @commands.hybrid_command()
    async def whitelist(self, ctx):
        """Show all members with the Whitelist role."""
        role = discord.utils.find(
            lambda r: r.name.lower() == WHITELIST_ROLE_NAME.lower(),
            ctx.guild.roles
        )
        if not role:
            await ctx.send(f"⚠️ No role named `{WHITELIST_ROLE_NAME}` found. Use `!setwhitelistrole @Role` to configure it.")
            return

        members = [m for m in role.members if not m.bot]
        if not members:
            await ctx.send(f"No members have the `{role.name}` role yet.")
            return

        names = [f"⛏️ {m.display_name}" for m in sorted(members, key=lambda m: m.display_name.lower())]
        # Split into chunks of 20
        chunks = [names[i:i+20] for i in range(0, len(names), 20)]

        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"📋 Whitelisted Members ({len(members)} total)" if i == 0 else "📋 Continued...",
                description="\n".join(chunk),
                color=0x4CAF50
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setwhitelistrole(self, ctx, role: discord.Role):
        """Set which role counts as the whitelist role. Usage: !setwhitelistrole @Whitelisted"""
        # Save to config
        import json, os
        config_file = "data/minecraft_config.json"
        config = {}
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
        config[str(ctx.guild.id)] = {"whitelist_role": role.id}
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        await ctx.send(f"✅ Whitelist role set to `{role.name}`.")

    @commands.hybrid_command()
    async def mcstatus(self, ctx, address: str = None):
        """Check if a Minecraft server is online. Usage: !mcstatus play.example.net"""
        if not address:
            # Try to load saved IP from custom commands
            await ctx.send("Usage: `!mcstatus play.example.net` or `!mcstatus play.example.net:25565`")
            return

        host = address
        port = 25565
        if ":" in address:
            host, port = address.rsplit(":", 1)
            port = int(port)

        api_url = f"https://api.mcsrvstat.us/3/{host}:{port}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()

                    if not data.get("online"):
                        embed = discord.Embed(
                            title=f"🔴 {host} is OFFLINE",
                            color=0xF44336
                        )
                        await ctx.send(embed=embed)
                        return

                    players = data.get("players", {})
                    online = players.get("online", 0)
                    max_p = players.get("max", 0)
                    version = data.get("version", "Unknown")
                    motd = data.get("motd", {}).get("clean", [""])[0] if data.get("motd") else ""
                    player_list = players.get("list", [])

                    embed = discord.Embed(
                        title=f"🟢 {host} is ONLINE",
                        description=motd,
                        color=0x4CAF50
                    )
                    embed.add_field(name="👥 Players", value=f"{online}/{max_p}", inline=True)
                    embed.add_field(name="🎮 Version", value=version, inline=True)
                    if player_list:
                        names = ", ".join([p.get("name", p) if isinstance(p, dict) else p for p in player_list[:10]])
                        embed.add_field(name="Online Now", value=names, inline=False)
                    embed.set_footer(text=f"IP: {host}:{port}")
                    await ctx.send(embed=embed)
            except Exception:
                await ctx.send(f"⚠️ Couldn't check server status. Is the IP correct?")

async def setup(bot):
    await bot.add_cog(Minecraft(bot))