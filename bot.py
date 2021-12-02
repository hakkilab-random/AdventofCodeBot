import os
import json
import datetime
import requests
import dotenv
import discord
from discord.ext import commands, tasks

dotenv.load_dotenv("secret.env")
TOKEN = os.getenv("DISCORD_TOKEN")
SESSION = os.getenv("SESSION_KEY")
TEST_GUILD_ID = int(os.getenv("TEST_SERVER"))
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL"))
ACM_CHANNEL_ID = int(os.getenv("ACM_CHANNEL"))
CHURCH_CHANNEL_ID = int(os.getenv("CHURCH_OF_EVAN_CHANNEL"))
OSU_LEADERBOARD_JSON_URL = "https://adventofcode.com/2021/leaderboard/private/view/129530.json"
AOC_BOT_CHANNEL = "advent-of-code-bot"
DEBUG = False

bot = commands.Bot(command_prefix='!')
bot.remove_command("help")
CHANNEL_IDS = [ACM_CHANNEL_ID, CHURCH_CHANNEL_ID]
if DEBUG:
    CHANNEL_IDS.append(TEST_CHANNEL_ID)

def get_leaderboard():
    leaderboard_json = requests.get(OSU_LEADERBOARD_JSON_URL, cookies={"session": SESSION}).json()
    del leaderboard_json["members"]["1544109"]
    leaderboard_arr = list(leaderboard_json["members"].values())
    leaderboard_arr.sort(key=lambda x: (x["local_score"], x["global_score"], x["stars"], -float(x["last_star_ts"]), -int(x["id"])), reverse=True)
    
    return leaderboard_arr

@bot.event
async def on_ready():
    print(f"{bot.user} is connected to the server.")

@bot.event
async def on_message(message):
    if DEBUG and message.guild.id != TEST_GUILD_ID:
        return
    if message.author == bot.user or not (message.channel.id in CHANNEL_IDS or message.channel.name == AOC_BOT_CHANNEL):
        return
    await bot.process_commands(message)

@bot.command(name="help", help="Shows the current list of valid bot commands")
async def on_help(ctx):
    await ctx.send("Available commands:\n!leaderboard")

@bot.command(name="leaderboard", help="Shows the current OSU Advent of Code leaderboard")
async def on_leaderboard(ctx, leaderboard=None):
    if leaderboard is None:
        leaderboard = get_leaderboard()
    for player in leaderboard:
        if player["name"] is None:
            player["name"] = f"(anonymous user #{player['id']})"

    leaderboard_str = "`" + ("NAME").ljust(25) + ("LOCAL SCORE").rjust(10) + ("STARS").rjust(10) + "\n"
    for player in leaderboard:
        leaderboard_str += player["name"].ljust(25) + str(player["local_score"]).rjust(10) + str(player["stars"]).rjust(10) + " \n"
    leaderboard_str = leaderboard_str[:-1]+"`"
    await ctx.send(leaderboard_str)

async def multi_leaderboard(channels, final=False):
    leaderboard = get_leaderboard()
    for c in channels:
        if not final:
            await c.send("Daily Leaderboard")
        else:
            await c.send("Advent of Code 2021 is over! Here is the final leaderboard.")
        await on_leaderboard(c, leaderboard=leaderboard)

@tasks.loop(hours=24)
async def daily_leaderboard():
    if DEBUG:
        return
    channels = []
    for cid in CHANNEL_IDS:
        channel = bot.get_channel(cid)
        if channel is not None:
            channels.append(channel)
    if datetime.datetime.now() < datetime.datetime(2021, 12, 27):
        await multi_leaderboard(channels)
    else:
        await multi_leaderboard(channels, final=True)
        quit()

@daily_leaderboard.before_loop
async def before():
    await bot.wait_until_ready()

daily_leaderboard.start()
bot.run(TOKEN)
