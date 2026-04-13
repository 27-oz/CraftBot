import discord
from discord.ext import commands
import time
import platform

class About(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name="about", description="Technical info about CraftBot")
    async def about(self, ctx):
        # Calculate Uptime
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = discord.Embed(title="🤖 CraftBot V6", color=discord.Color.gold())
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        embed.add_field(name="Developer", value="**27-oz**", inline=True)
        embed.add_field(name="Library", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="Architecture", value=f"Python {platform.python_version()}", inline=True)
        
        embed.set_footer(text="Securely deployed on Render | Hybrid Mode Active")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(About(bot))
