import discord
from discord.ext import commands
import json, os

DATA_FILE = "data/starboard.json"
STAR_THRESHOLD = 5
STAR_EMOJI = "⭐"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != STAR_EMOJI:
            return
        data = load_data()
        gid = str(payload.guild_id)
        if gid not in data or "channel" not in data[gid]:
            return

        starboard_channel = self.bot.get_channel(data[gid]["channel"])
        if not starboard_channel:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        if channel.id == starboard_channel.id:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        star_reaction = discord.utils.get(message.reactions, emoji=STAR_EMOJI)
        star_count = star_reaction.count if star_reaction else 0

        if star_count < STAR_THRESHOLD:
            return

        msg_id = str(payload.message_id)
        already_posted = data[gid].get("posted", {})

        if msg_id in already_posted:
            # Update existing starboard message
            try:
                sb_msg = await starboard_channel.fetch_message(already_posted[msg_id])
                await sb_msg.edit(content=f"{STAR_EMOJI} **{star_count}** | {channel.mention}")
            except discord.NotFound:
                pass
            return

        # Build starboard embed
        embed = discord.Embed(description=message.content or "", color=0xFFD700)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to message]({message.jump_url})", inline=False)
        embed.set_footer(text=f"#{channel.name} • {message.created_at.strftime('%b %d, %Y')}")

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        sb_msg = await starboard_channel.send(
            content=f"{STAR_EMOJI} **{star_count}** | {channel.mention}",
            embed=embed
        )

        if "posted" not in data[gid]:
            data[gid]["posted"] = {}
        data[gid]["posted"][msg_id] = sb_msg.id
        save_data(data)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def setstarboard(self, ctx, channel: discord.TextChannel):
        """Set the starboard channel. Usage: !setstarboard #starboard"""
        data = load_data()
        gid = str(ctx.guild.id)
        if gid not in data:
            data[gid] = {}
        data[gid]["channel"] = channel.id
        save_data(data)
        await ctx.send(f"⭐ Starboard set to {channel.mention}! Messages with {STAR_THRESHOLD}+ ⭐ will be pinned there.")

async def setup(bot):
    await bot.add_cog(Starboard(bot))
