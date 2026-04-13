import discord
from discord.ext import commands
from discord import app_commands
import random, aiohttp

EIGHT_BALL_RESPONSES = [
    "It is certain.", "Without a doubt.", "Yes, definitely.",
    "You may rely on it.", "As I see it, yes.", "Most likely.",
    "Outlook good.", "Signs point to yes.", "Reply hazy, try again.",
    "Ask again later.", "Better not tell you now.", "Cannot predict now.",
    "Don't count on it.", "My reply is no.", "My sources say no.",
    "Outlook not so good.", "Very doubtful.",
]

JOKES = [
    ("Why did the Creeper go to therapy?", "Because it had too many explosive emotions."),
    ("What do you call a Minecraft player who works at a bakery?", "A bread miner."),
    ("Why don't Endermen use umbrellas?", "Because they'd teleport away the moment it rained."),
    ("What did Steve say to the diamond?", "I dig you."),
    ("Why is Minecraft so calming?", "Because everything is in blocks — even your feelings."),
    ("What do you call a skeleton who won't fight?", "Bone idle."),
    ("Why did the zombie break up with the skeleton?", "He had no guts."),
    ("What's a Creeper's favourite subject?", "Hiss-tory."),
    ("How do Minecraft players stay cool?", "They stand next to a fan."),
    ("Why can't you trust atoms in Minecraft?", "Because they make up everything."),
]

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 8ball ---
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question")
    async def eight_ball_slash(self, interaction: discord.Interaction, question: str):
        await self._eight_ball(interaction.response.send_message, question)

    @commands.hybrid_command(name="8ball")
    async def eight_ball_prefix(self, ctx, *, question: str):
        await self._eight_ball(ctx.send, question)

    async def _eight_ball(self, send, question):
        response = random.choice(EIGHT_BALL_RESPONSES)
        embed = discord.Embed(color=0x1A237E)
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        await send(embed=embed)

    # --- coinflip ---
    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip_slash(self, interaction: discord.Interaction):
        await self._coinflip(interaction.response.send_message)

    @commands.hybrid_command(name="coinflip")
    async def coinflip_prefix(self, ctx):
        await self._coinflip(ctx.send)

    async def _coinflip(self, send):
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(title="Coin Flip", description=f"It landed on **{result}**!", color=0xFFD700)
        await send(embed=embed)

    # --- dice ---
    @app_commands.command(name="dice", description="Roll a dice")
    @app_commands.describe(sides="Number of sides (default 6)")
    async def dice_slash(self, interaction: discord.Interaction, sides: int = 6):
        await self._dice(interaction.response.send_message, sides)

    @commands.hybrid_command(name="dice")
    async def dice_prefix(self, ctx, sides: int = 6):
        await self._dice(ctx.send, sides)

    async def _dice(self, send, sides):
        if sides < 2 or sides > 1000:
            await send("Dice must have between 2 and 1000 sides.")
            return
        result = random.randint(1, sides)
        embed = discord.Embed(title=f"D{sides} Roll", description=f"You rolled a **{result}**!", color=0xFF5722)
        await send(embed=embed)

    # --- rps ---
    @app_commands.command(name="rps", description="Play rock paper scissors vs the bot")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    async def rps_slash(self, interaction: discord.Interaction, choice: str):
        await self._rps(interaction.response.send_message, choice)

    @commands.hybrid_command(name="rps")
    async def rps_prefix(self, ctx, choice: str):
        await self._rps(ctx.send, choice)

    async def _rps(self, send, choice):
        choice = choice.lower()
        options = ["rock", "paper", "scissors"]
        if choice not in options:
            await send("Choose `rock`, `paper`, or `scissors`.")
            return
        bot_choice = random.choice(options)
        if choice == bot_choice:
            result, color = "It's a tie!", 0x9E9E9E
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result, color = "You win!", 0x4CAF50
        else:
            result, color = "Bot wins!", 0xF44336
        embed = discord.Embed(title="Rock Paper Scissors", color=color)
        embed.add_field(name="Your choice", value=choice.capitalize(), inline=True)
        embed.add_field(name="Bot's choice", value=bot_choice.capitalize(), inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        await send(embed=embed)

    # --- joke ---
    @app_commands.command(name="joke", description="Get a random Minecraft joke")
    async def joke_slash(self, interaction: discord.Interaction):
        await self._joke(interaction.response.send_message)

    @commands.hybrid_command(name="joke")
    async def joke_prefix(self, ctx):
        await self._joke(ctx.send)

    async def _joke(self, send):
        setup, punchline = random.choice(JOKES)
        embed = discord.Embed(title="Minecraft Joke", color=0x4CAF50)
        embed.add_field(name=setup, value=f"||{punchline}||", inline=False)
        embed.set_footer(text="Click the spoiler to reveal the punchline!")
        await send(embed=embed)

    # --- meme ---
    @app_commands.command(name="meme", description="Get a random Minecraft meme")
    async def meme_slash(self, interaction: discord.Interaction):
        await self._meme(interaction.response.send_message)

    @commands.hybrid_command(name="meme")
    async def meme_prefix(self, ctx):
        await self._meme(ctx.send)

    async def _meme(self, send):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://meme-api.com/gimme/Minecraft", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = discord.Embed(title=data.get("title", "Minecraft Meme"), color=0x4CAF50)
                        embed.set_image(url=data.get("url"))
                        embed.set_footer(text=f"{data.get('ups', 0)} upvotes on r/Minecraft")
                        await send(embed=embed)
                        return
        except Exception:
            pass
        await send("Couldn't fetch a meme right now. Try again!")

async def setup(bot):
    await bot.add_cog(Fun(bot))
