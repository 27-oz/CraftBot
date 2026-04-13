import discord
from discord.ext import commands
from discord import app_commands

NUMBER_EMOJIS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll. Separate question and options with |")
    @app_commands.describe(content="Question | Option1 | Option2 | ...")
    async def poll_slash(self, interaction: discord.Interaction, content: str):
        await self._poll(interaction.response.send_message, interaction.channel, content, interaction.user)

    @commands.hybrid_command(name="poll")
    async def poll_prefix(self, ctx, *, content: str):
        await ctx.message.delete()
        await self._poll(ctx.send, ctx.channel, content, ctx.author)

    async def _poll(self, send, channel, content, author):
        parts = [p.strip() for p in content.split("|")]
        if len(parts) < 2: await send("Usage: `question | option1 | option2`"); return
        if len(parts) > 11: await send("Max 10 options."); return
        question, options = parts[0], parts[1:]
        description = "\n".join(f"{NUMBER_EMOJIS[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(title=question, description=description, color=0x3F51B5)
        embed.set_footer(text=f"Poll by {author.display_name}")
        msg = await channel.send(embed=embed)
        for i in range(len(options)): await msg.add_reaction(NUMBER_EMOJIS[i])

    @app_commands.command(name="yesno", description="Create a yes/no poll")
    @app_commands.describe(question="The question to ask")
    async def yesno_slash(self, interaction: discord.Interaction, question: str):
        await self._yesno(interaction.response.send_message, interaction.channel, question, interaction.user)

    @commands.hybrid_command(name="yesno")
    async def yesno_prefix(self, ctx, *, question: str):
        await ctx.message.delete()
        await self._yesno(ctx.send, ctx.channel, question, ctx.author)

    async def _yesno(self, send, channel, question, author):
        embed = discord.Embed(title=question, description="Yes  |  No", color=0xFF5722)
        embed.set_footer(text=f"Poll by {author.display_name}")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

async def setup(bot):
    await bot.add_cog(Polls(bot))
