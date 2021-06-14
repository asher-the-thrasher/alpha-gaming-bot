# A Discord bot that analyzes OBS log files for the Alpha Gaming discord
# Contributors: Asher_The_Thrasher, Goldeneyes, Awkward Potato, Spartichaos

import os

from aiohttp import ClientTimeout
from discord.ext import commands
from dotenv import load_dotenv

from RateLimit import RateLimiter
from cogs.log_analyzer import LogAnalyzer

# from keep_alive import keep_alive

# secret bot token
load_dotenv()
token = os.environ['token']

bot = commands.Bot(command_prefix="!")

timeout = ClientTimeout(total=60)
limiter = RateLimiter(20.0)

bot.add_cog(LogAnalyzer(bot))

# keep_alive()
bot.run(token)
