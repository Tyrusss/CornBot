import asyncio
import discord
import re
import psycopg2
import cogs.utility

from cogs.utility import thingInList, sqlEXE, initUser, delUser, Utility, KeywordInMessage, twitchGet
from cogs.credits import credits_handling
from cogs.rewards import Rewards
from cogs.games import Games
from cogs.fun import Fun

from discord.ext import commands
from discord.ext.commands import Bot
from discord import Game
from string import capwords
from os import environ

# The command prefix & bot token (KEEP TOKEN SECRET)
commandPrefix, TOKEN = "c!", environ["TOKEN"]
helpCommand = f'{commandPrefix}help'

# Initialise the client
client = Bot(command_prefix=commandPrefix)

if __name__ == '__main__':
        client.add_cog(Utility(client))
        client.add_cog(credits_handling(client))
        client.add_cog(Rewards(client))
        client.add_cog(Games(client))
        client.add_cog(Fun(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return # Don't reply to self

    if KeywordInMessage("daddy")(message.content):
        await message.channel.send("UwU")
        await asyncio.sleep(0.5)

    elif KeywordInMessage("UwU")(message.content):
        await message.channel.send("Daddy")
        await asyncio.sleep(0.5)

    elif KeywordInMessage("dinkster")(message.content):
        await message.channel.send("https://www.youtube.com/watch?v=bWE6Z3F-RwI")
        await asyncio.sleep(1)

    # Allow for commands to be processed while on_message occurs
    await client.process_commands(message)

# Error handling
@client.event
async def on_command_error(ctx, error):

    # Command on cooldown
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"You already collected today's daily!")

    # Command not found
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"'{ctx.message.content}' isn't a command.")

    # Member not found
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Member not found.")


    # If not accounted for, raise anyway so we can still see it
    else:
        raise error

# Stuff that happens on startup
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=Game(helpCommand))
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')

    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'credits_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE credits_list(user_id SERIAL PRIMARY KEY, discordID TEXT, twitchID TEXT, user_credits INTEGER, game_voted BOOLEAN)")
        print("init credits_list")
    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'rewards_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE rewards_list(reward_name TEXT PRIMARY KEY, reward_desc TEXT, price INTEGER)")
        print("init rewards_list")
    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'games_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE games_list(game_name TEXT PRIMARY KEY, votes INTEGER)")
        print("init games_list")
    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'games_pending');")) == "[(False,)]":
        sqlEXE("CREATE TABLE games_pending(game_name TEXT PRIMARY KEY, suggestor TEXT, status TEXT)")
        print("init games_pending")

# Actually run the damn thing
client.run(TOKEN)
