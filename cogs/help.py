import discord
from discord.ext import commands
from discord import app_commands

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=cog_name, description=f"Commands for {cog_name}")
            for cog_name in bot.cogs if bot.get_cog(cog_name).get_commands()
        ]
        super().__init__(placeholder="Choose a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cog = self.bot.get_cog(self.values[0])
        cmds = cog.get_commands()
        
        help_text = "\n".join([f"**/{c.name}** - {c.description or 'No description'}" for c in cmds])
        
        embed = discord.Embed(title=f"{self.values[0]} Commands", description=help_text, color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.add_item(HelpDropdown(bot))

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command = None # Remove default help

    @commands.hybrid_command(name="help", description="List all my categories and commands")
    async def help(self, ctx):
        embed = discord.Embed(
            title="Bot Help Menu", 
            description="Select a category from the dropdown below to see available commands.",
            color=discord.Color.green()
        )
        view = HelpView(self.bot)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Help(bot))
    
