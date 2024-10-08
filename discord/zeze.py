from dotenv import load_dotenv
import os
import discord
from discord.ext import commands, tasks
import datetime
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Bot token for ZeZe from the environment file
TOKEN = os.getenv("DISCORD_TOKEN_ZEZE")

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN_ZEZE is not set in the environment.")

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Set the command prefix to #
bot = commands.Bot(command_prefix='#', intents=intents)

# Channel ID for the #announcement channel
ANNOUNCEMENT_CHANNEL_ID = 1288274033154199594

# In-memory store for scheduled announcements
scheduled_announcements = []

# In-memory log of past announcements (for simple backup/restore)
announcement_logs = []

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    activity = discord.Activity(type=discord.ActivityType.watching, name="over the server")
    await bot.change_presence(activity=activity)
    announcement_scheduler.start()  # Start the scheduled announcement task

# Simple ping command to check if the bot is running
@bot.command(name='ping')
async def ping(ctx):
    print("Ping command received")  # Debugging line
    await ctx.send("Pong!")

# Custom help command to show all available commands
@bot.command(name='bot_help')
@commands.has_permissions(administrator=True)
async def help_command(ctx):
    """Command to show the list of all available commands for admins."""
    help_message = (
        "**ZeZe Bot Commands:**\n"
        "\n**#ping** - Check if the bot is responsive."
        "\n**#announce message** - Send an immediate announcement."
        "\n**#schedule_announce HH:MM message** - Schedule an announcement at a specific time (24-hour format)."
        "\n**#urgent_announce message** - Send an urgent announcement with priority formatting."
        "\n**#view_log** - View the log of past announcements."
        "\n**#view_schedule** - View all upcoming scheduled announcements."
        "\n**#bot_help** - Display this help message."
    )
    await ctx.send(help_message)

# Command to announce a message immediately
@bot.command(name='announce')
@commands.has_permissions(administrator=True)
async def announce(ctx, *, message: str):
    """Command to send an announcement to the #announcement channel."""
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="Announcement", description=message, color=discord.Color.blue())
        embed.set_footer(text=f"Sent by {ctx.author}")
        await channel.send(embed=embed)
        log_announcement(message, ctx.author)
        await ctx.send(f'Announcement sent to {channel.mention}')
    else:
        await ctx.send('Announcement channel not found.')

# Command for urgent announcements
@bot.command(name='urgent_announce')
@commands.has_permissions(administrator=True)
async def urgent_announce(ctx, *, message: str):
    """Send an urgent announcement with priority formatting."""
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="🚨 URGENT ANNOUNCEMENT 🚨", description=message, color=discord.Color.red())
        embed.set_footer(text=f"Sent by {ctx.author}")
        await channel.send(embed=embed)
        log_announcement(message, ctx.author)
        await ctx.send(f'Urgent announcement sent to {channel.mention}')
    else:
        await ctx.send('Announcement channel not found.')

# Command to schedule an announcement
@bot.command(name='schedule_announce')
@commands.has_permissions(administrator=True)
async def schedule_announce(ctx, time: str, *, message: str):
    """Schedule an announcement at a specific time. Time format: HH:MM (24-hour format)."""
    try:
        scheduled_time = datetime.datetime.strptime(time, "%H:%M").time()
        scheduled_announcements.append((scheduled_time, message, ctx.author))
        await ctx.send(f"Scheduled announcement for {time}")
    except ValueError:
        await ctx.send("Invalid time format. Use HH:MM (24-hour format).")

# Background task to send scheduled announcements
@tasks.loop(minutes=1)
async def announcement_scheduler():
    now = datetime.datetime.now().time()
    to_remove = []
    for announcement in scheduled_announcements:
        scheduled_time, message, author = announcement
        if scheduled_time <= now:
            channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            if channel:
                embed = discord.Embed(title="Scheduled Announcement", description=message, color=discord.Color.green())
                embed.set_footer(text=f"Sent by {author}")
                await channel.send(embed=embed)
                log_announcement(message, author)
            to_remove.append(announcement)
    # Remove the sent announcements from the queue
    for announcement in to_remove:
        scheduled_announcements.remove(announcement)

# Command to view the upcoming scheduled announcements
@bot.command(name='view_schedule')
@commands.has_permissions(administrator=True)
async def view_schedule(ctx):
    """View upcoming scheduled announcements."""
    if not scheduled_announcements:
        await ctx.send("No scheduled announcements.")
    else:
        description = "\n".join([f"{time.strftime('%H:%M')} - {message}" for time, message, _ in scheduled_announcements])
        embed = discord.Embed(title="Scheduled Announcements", description=description, color=discord.Color.orange())
        await ctx.send(embed=embed)

# Log announcements
def log_announcement(message, author):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    announcement_logs.append({"message": message, "author": str(author), "timestamp": timestamp})

# Command to view the announcement log
@bot.command(name='view_log')
@commands.has_permissions(administrator=True)
async def view_log(ctx):
    """View the log of past announcements."""
    if not announcement_logs:
        await ctx.send("No announcements have been made yet.")
    else:
        description = "\n".join([f"{log['timestamp']} - {log['author']}: {log['message']}" for log in announcement_logs])
        embed = discord.Embed(title="Announcement Log", description=description, color=discord.Color.purple())
        await ctx.send(embed=embed)

# Start the bot
bot.run(TOKEN)
