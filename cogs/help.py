import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def help(self, ctx, category: str = None):
        """Show all commands. Usage: !help or !help welcome"""
        categories = {
            "welcome": {
                "emoji": "👋",
                "title": "Welcome & Goodbye",
                "commands": [
                    ("!setwelcome #channel [msg]", "Set welcome channel. Use {user} in message."),
                    ("!setgoodbye #channel [msg]", "Set goodbye channel. Use {user} in message."),
                ]
            },
            "roles": {
                "emoji": "🎭",
                "title": "Roles",
                "commands": [
                    ("!autorole add/remove @Role", "Auto-assign a role to new members."),
                    ("!autoroles", "List all auto-roles."),
                    ("!rradd <msg_id> <emoji> @Role", "Bind reaction to role."),
                    ("!rrremove <msg_id> <emoji>", "Remove reaction role binding."),
                    ("!rrpanel <description>", "Post a reaction role panel."),
                ]
            },
            "reminders": {
                "emoji": "⏰",
                "title": "Reminders",
                "commands": [
                    ("!remind <time> <message>", "Set a reminder. Time: 10m, 2h, 1d"),
                    ("!reminders", "View your pending reminders."),
                ]
            },
            "commands": {
                "emoji": "📋",
                "title": "Custom Commands",
                "commands": [
                    ("!addcmd <trigger> <response>", "Add a custom command. Use {user} for mention."),
                    ("!delcmd <trigger>", "Delete a custom command."),
                    ("!listcmds", "List all custom commands."),
                ]
            },
            "stats": {
                "emoji": "📊",
                "title": "Server Stats",
                "commands": [
                    ("!stats", "Show server statistics."),
                    ("!userinfo [@User]", "Show user information."),
                    ("!membercount", "Quick member count."),
                ]
            },
            "polls": {
                "emoji": "📊",
                "title": "Polls",
                "commands": [
                    ("!poll Q | Opt1 | Opt2 | ...", "Create a multi-option poll."),
                    ("!yesno <question>", "Create a yes/no poll."),
                ]
            },
            "feeds": {
                "emoji": "📡",
                "title": "Social Feeds",
                "commands": [
                    ("!addtiktok <user> #ch [@role]", "Track a TikTok account."),
                    ("!removetiktok <user>", "Stop tracking a TikTok account."),
                    ("!tiktoks", "List tracked TikTok accounts."),
                    ("!addtwitch <user> #ch [@role]", "Track a Twitch streamer (needs API keys)."),
                    ("!removetwitch <user>", "Stop tracking a Twitch streamer."),
                ]
            }
        }

        if category and category.lower() in categories:
            cat = categories[category.lower()]
            embed = discord.Embed(
                title=f"{cat['emoji']} {cat['title']} Commands",
                color=0x4CAF50
            )
            for cmd, desc in cat["commands"]:
                embed.add_field(name=f"`{cmd}`", value=desc, inline=False)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="⛏️ CraftBot — Command Categories",
            description="Use `!help <category>` for details.\nAll commands use the `!` prefix.",
            color=0x4CAF50
        )
        for key, cat in categories.items():
            embed.add_field(
                name=f"{cat['emoji']} `!help {key}` — {cat['title']}",
                value=f"{len(cat['commands'])} commands",
                inline=False
            )
        embed.set_footer(text="⛏️ Built for Minecraft communities")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))