import discord
from discord.ext import commands

NUMBER_EMOJIS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def poll(self, ctx, *, content: str):
        """Create a poll. Separate question and options with | 
        Usage: !poll Best biome? | Forest | Desert | Ocean | Mountains"""
        parts = [p.strip() for p in content.split("|")]
        if len(parts) < 2:
            await ctx.send("❌ Usage: `!poll Question | Option 1 | Option 2 | ...`")
            return
        question = parts[0]
        options = parts[1:]
        if len(options) > 10:
            await ctx.send("❌ Maximum 10 options per poll.")
            return

        description = "\n".join(f"{NUMBER_EMOJIS[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=0x3F51B5
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        await ctx.message.delete()
        poll_msg = await ctx.send(embed=embed)

        for i in range(len(options)):
            await poll_msg.add_reaction(NUMBER_EMOJIS[i])

    @commands.hybrid_command()
    async def yesno(self, ctx, *, question: str):
        """Create a simple yes/no poll. Usage: !yesno Should we add a new gamemode?"""
        embed = discord.Embed(
            title=f"❓ {question}",
            description="✅ Yes  |  ❌ No",
            color=0xFF5722
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        await ctx.message.delete()
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

async def setup(bot):
    await bot.add_cog(Polls(bot))