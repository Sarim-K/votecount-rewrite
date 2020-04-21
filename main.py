import discord
import sqlite3
import os
from karma_card.createcard import create_card
from discord.ext import commands


key = open("keys.txt", "r").readline().split("=")[1]


bot = commands.Bot(command_prefix='$')
@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@commands.has_permissions(administrator=True)
@bot.command()
async def setup(message):
    await message.channel.send("yurp")


bot.run(key)
