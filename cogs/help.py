import discord
from discord.ext import commands
from discord import app_commands

BOT_VERSION = "v1.5.0"

CATEGORIES = {
    "welcome": {
        "title": "Welcome & Goodbye",
        "commands": [
            ("/setwelcome #channel [msg]", "Set welcome channel. Use {user} in message."),
            ("/setgoodbye #channel [msg]", "Set goodbye channel. Use {user} in message."),
        ]
    },
    "roles": {
        "title": "Roles",
        "commands": [
            ("/autorole add/remove @Role", "Auto-assign a role to new members."),
            ("/autoroles", "List all auto-roles."),
            ("/rradd msg_id emoji @Role", "Bind reaction to role."),
            ("/rrremove msg_id emoji", "Remove reaction role binding."),
            ("/rrpanel description", "Post a reaction role panel."),
        ]
    },
    "reminders": {
        "title": "Reminders",
        "commands": [
            ("/remind time message", "Set a reminder. Time: 10m, 2h, 1d"),
            ("/reminders", "View your pending reminders."),
        ]
    },
    "commands": {
        "title": "Custom Commands",
        "commands": [
            ("/addcmd trigger response", "Add a custom command."),
            ("/delcmd trigger", "Delete a custom command."),
            ("/listcmds", "List all custom commands."),
        ]
    },
    "stats": {
        "title": "Server Stats",
        "commands": [
            ("/stats", "Show server statistics."),
            ("/userinfo [@User]", "Show user information."),
            ("/membercount", "Quick member count."),
        ]
    },
    "polls": {
        "title": "Polls",
        "commands": [
            ("/poll question options", "Create a multi-option poll."),
            ("/yesno question", "Create a yes/no poll."),
        ]
    },
    "feeds": {
        "title": "Social Feeds",
        "commands": [
            ("/addtiktok user #ch [@role]", "Track a TikTok account."),
            ("/removetiktok user", "Stop tracking a TikTok account."),
            ("/tiktoks", "List tracked TikTok accounts."),
            ("/addtwitch user #ch [@role]", "Track a Twitch streamer."),
            ("/removetwitch user", "Stop tracking a Twitch streamer."),
        ]
    },
    "leveling": {
        "title": "Leveling & XP",
        "commands": [
            ("/rank [@User]", "Check your level and XP."),
            ("/leaderboard", "Show the top 10 most active members."),
            ("/perks", "Show all level perks."),
            ("/setlevelchannel #channel", "Set level-up announcement channel. (Admin)"),
            ("/setlevelrole level @Role", "Assign a role at a level. (Admin)"),
            ("/setxp @user amount", "Set a member's XP. (Admin)"),
            ("/addxp @user amount", "Add or subtract XP. (Admin)"),
            ("/xpboost multiplier duration", "Start an XP boost event. (Admin)"),
            ("/xpboostend", "End the current XP boost. (Admin)"),
            ("/xpboostcheck", "Check if an XP boost is active."),
            ("/xpblacklist #channel", "Stop XP in a channel. (Admin)"),
            ("/xpunblacklist #channel", "Remove XP blacklist. (Admin)"),
            ("/xpblacklisted", "List XP-blacklisted channels."),
        ]
    },
    "economy": {
        "title": "Economy",
        "commands": [
            ("/balance [@User]", "Check your coin balance."),
            ("/daily", "Claim your daily coin reward."),
            ("/vote", "Claim vote coins."),
            ("/transfer @user amount", "Transfer coins to another player."),
            ("/richest", "Show the richest members."),
            ("/shop", "Browse the shop."),
            ("/buy item_id", "Buy an item from the shop."),
            ("/additem id price name", "Add a shop item. (Admin)"),
            ("/linkrole item_id @Role", "Link a role to a shop item. (Admin)"),
            ("/removeitem item_id", "Remove a shop item. (Admin)"),
            ("/givecoins @user amount", "Give coins to a member. (Admin)"),
            ("/takecoins @user amount", "Take coins from a member. (Admin)"),
        ]
    },
    "moderation": {
        "title": "Moderation",
        "commands": [
            ("/warn @user [reason]", "Warn a member."),
            ("/warnings @user", "Check warnings for a member."),
            ("/clearwarnings @user", "Clear all warnings."),
            ("/kick @user [reason]", "Kick a member."),
            ("/ban @user [reason]", "Ban a member."),
            ("/unban user_id", "Unban a user by ID."),
            ("/tempban @user duration [reason]", "Temporarily ban a member."),
            ("/mute @user [reason]", "Mute a member for 10 minutes."),
            ("/unmute @user", "Unmute a member."),
            ("/purge amount", "Delete messages."),
            ("/lock [#channel]", "Lock a channel."),
            ("/unlock [#channel]", "Unlock a channel."),
            ("/slowmode seconds", "Set slowmode."),
            ("/setlog #channel", "Set the logging channel."),
        ]
    },
    "tickets": {
        "title": "Tickets",
        "commands": [
            ("/ticket issue", "Open a support ticket."),
            ("/setticketstaff @Role", "Set the staff role. (Admin)"),
            ("/setticketstaffchannel #channel", "Set the ticket channel. (Admin)"),
        ]
    },
    "applications": {
        "title": "Applications",
        "commands": [
            ("/suggest suggestion", "Submit a suggestion. Requires Level 30."),
            ("/staffapp", "Apply for staff. Requires Level 25."),
            ("/adminapp", "Apply for admin. Requires Level 50."),
            ("/setstaffchannel #channel", "Set applications channel. (Admin)"),
            ("/setsuggestchannel #channel", "Set suggestions channel. (Admin)"),
        ]
    },
    "minecraft": {
        "title": "Minecraft",
        "commands": [
            ("/mcstatus address", "Check if a Minecraft server is online."),
            ("/whitelist", "List all whitelisted members."),
            ("/wiki term", "Look up a term on the Minecraft Wiki."),
            ("/skin username", "View a Minecraft player's skin."),
            ("/uuid username", "Look up a Minecraft player's UUID."),
            ("/tip", "Get a random Minecraft tip."),
            ("/events", "Show upcoming server events."),
            ("/addevent date time name | desc", "Add a server event. (Admin)"),
            ("/removeevent name", "Remove a server event. (Admin)"),
        ]
    },
    "channellocks": {
        "title": "Channel Level Locks",
        "commands": [
            ("/lockchannel #channel level", "Lock a channel to a minimum level. (Admin)"),
            ("/unlockchannel #channel", "Remove a level lock. (Admin)"),
            ("/lockedchannels", "List all level-locked channels."),
        ]
    },
    "fun": {
        "title": "Fun",
        "commands": [
            ("/8ball question", "Ask the magic 8-ball a question."),
            ("/coinflip", "Flip a coin."),
            ("/dice [sides]", "Roll a dice."),
            ("/rps rock/paper/scissors", "Play rock paper scissors vs the bot."),
            ("/joke", "Get a random Minecraft joke."),
            ("/meme", "Get a random Minecraft meme."),
        ]
    },
    "misc": {
        "title": "Misc",
        "commands": [
            ("/afk [reason]", "Set yourself as AFK."),
            ("/rules", "Show server rules."),
            ("/setrules Rule 1 | Rule 2", "Set server rules. (Admin)"),
            ("/addrule rule", "Add a single rule. (Admin)"),
            ("/removerule number", "Remove a rule by number. (Admin)"),
            ("/setstarboard #channel", "Set the starboard channel. (Admin)"),
        ]
    },
}

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command
    @app_commands.command(name="help", description="Show all commands or a specific category")
    @app_commands.describe(category="The category to show commands for")
    async def help_slash(self, interaction: discord.Interaction, category: str = None):
        await self._send_help(interaction, category, slash=True)

    # Prefix fallback
    @commands.hybrid_command(name="help")
    async def help_prefix(self, ctx, category: str = None):
        await self._send_help(ctx, category, slash=False)

    async def _send_help(self, ctx_or_interaction, category, slash=True):
        send = ctx_or_interaction.response.send_message if slash else ctx_or_interaction.send

        if category and category.lower() in CATEGORIES:
            cat = CATEGORIES[category.lower()]
            embed = discord.Embed(title=f"{cat['title']} Commands", color=0x4CAF50)
            for cmd, desc in cat["commands"]:
                embed.add_field(name=f"`{cmd}`", value=desc, inline=False)
            embed.set_footer(text=f"CraftBot {BOT_VERSION}")
            await send(embed=embed)
            return

        embed = discord.Embed(
            title="CraftBot — Command Categories",
            description="Use `/help category` for details.",
            color=0x4CAF50
        )
        for key, cat in CATEGORIES.items():
            embed.add_field(
                name=f"`/help {key}` — {cat['title']}",
                value=f"{len(cat['commands'])} commands",
                inline=False
            )
        embed.set_footer(text=f"CraftBot {BOT_VERSION} — Built for Minecraft communities")
        await send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
