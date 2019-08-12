import asyncio
import discord
import re
import psycopg2
import cogs.utility
import aiohttp

from cogs.utility import thingInList, sqlEXE, initUser, delUser, Utility, KeywordInMessage
from cogs.points import Points
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
        client.add_cog(Points(client))
        client.add_cog(Rewards(client))
        client.add_cog(Games(client))
        client.add_cog(Fun(client))

streaming = False
async def twitchget(streaming):
    channel = client.get_channel(502233377965867010)
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://api.twitch.tv/helix/streams?user_login=cornben',
                headers={"Client-ID": "q5hm7ld6pl5azmlauqd5mxml4wdklj"}) as s:
                s = await s.json()

            if s["data"] == []:
                if streaming == True:
                    print("Stopped streaming")
                    streaming = False
                else:
                    print("Still not streaming")
                
            if s["data"] != []:  
                async with session.get(
                    'https://api.twitch.tv/helix/users?login=cornben',
                    headers={"Client-ID": "q5hm7ld6pl5azmlauqd5mxml4wdklj"}) as u:
                    u = await u.json()
                async with session.get(
                    'https://api.twitch.tv/helix/games?id={}'.format(s["data"][0]["game_id"]),
                    headers={"Client-ID": "q5hm7ld6pl5azmlauqd5mxml4wdklj"}) as g:
                    g = await g.json()

                if s["data"][0]["type"] == 'live':
                    if streaming == False:
                        s = s["data"][0]
                        u = u["data"][0]
                        g = g["data"][0]

                        print("Started streaming")
                        streaming = True
                        Turl = "https://twitch.tv/{}".format(u["login"])
                        e = discord.Embed(color=discord.Color(0x800080), description='[{0}]({1})'.format(s["title"], Turl))
                        e.set_author(icon_url=u["profile_image_url"], name=u["display_name"], url=Turl)
                        e.set_thumbnail(url=u["profile_image_url"])
                        e.add_field(name="Game", value=g["name"], inline=True)
                        e.add_field(name="Viewers", value=s["viewer_count"], inline=True)
                        e.set_image(url=s["thumbnail_url"].format(width=320, height=180))
                        await channel.send("Hey "+"@everyone"+"! {0} is streaming {1} on {2}! Go check it out!".format(u["display_name"], g["name"], Turl), embed=e)
                    else:
                        print("Still streaming")

            await asyncio.sleep(5)

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

    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'points_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE points_list(user_id TEXT PRIMARY KEY, user_points INTEGER, game_voted BOOLEAN)")
        print("init points_list")
    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'rewards_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE rewards_list(reward_name TEXT PRIMARY KEY, reward_desc TEXT, price INTEGER)")
        print("init rewards_list")
    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'games_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE games_list(game_name TEXT PRIMARY KEY, votes INTEGER)")
        print("init games_list")
    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'games_pending');")) == "[(False,)]":
        sqlEXE("CREATE TABLE games_pending(game_name TEXT PRIMARY KEY, suggestor TEXT, status TEXT)")
        print("init games_pending")

        loop = asyncio.get_running_loop()
        asyncio.create_task(twitchget(streaming))
        print(loop)
        loop.run_forever()

# Actually run the damn thing
client.run(TOKEN)
