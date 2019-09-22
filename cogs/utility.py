import asyncio
import discord
import psycopg2
import re
import aiohttp

from discord.ext import commands
from discord.ext.commands import Cog
from os import environ

Owner_id = [332505589701935104, 237585716836696065, 554760937245245460]

def sqlEXE(statement):
    con = None
    try:
        # Connect to the database
        con = psycopg2.connect(environ['DATABASE_URL'], sslmode="require")
        con.autocommit = True
        cur = con.cursor()

        cur.execute(statement)
        if statement[:6] == 'SELECT':
            data = cur.fetchall()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if con is not None:
            con.close()
            if statement[:6] == 'SELECT':
                return data

# Check if a thing is in the database
def thingInList(thing, table):
    if str(sqlEXE(f"SELECT * FROM {table}")) != "[]":
        for item in sqlEXE(f"SELECT * FROM {table}"):
            for data in item:
                if data == thing:
                    return True
    return False

# Add a user to the credits list
def initUser(twitchID = None, discordID = None):
    if twitchID and discordID:
        if thingInList(discordID, 'credits_list') == False: # Add member to list with 0 credits
            if thingInList(twitchID, 'credits_list') == False:
                
                sqlEXE(f"INSERT INTO credits_list(discordID, twitchID, user_credits, game_voted) VALUES('{discordID}', '{twitchID}', 0, FALSE)")
                
                return True
        return False

    if discordID and not twitchID:
        if thingInList(discordID, 'credits_list') == False:
            sqlEXE(f"INSERT INTO credits_list(discordID, user_credits, game_voted) VALUES('{discordID}', 0, FALSE)")
            return True
        return False

    if twitchID and not discordID:
        if thingInList(twitchID, 'credits_list') == False:
            sqlEXE(f"INSERT INTO credits_list(twitchID, user_credits, game_voted) VALUES('{twitchID}', 0, FALSE)")
            return True
        return False

# Deletes a user from the credits lists
def delUser(memberID):
    if thingInList(str(memberID), 'credits_list'):
        sqlEXE(f"DELETE FROM credits_list WHERE discordID = '{str(memberID)}'")
        return True
    else:
        return False

# CHECK IF KEYWORD IN MESSAGE
def KeywordInMessage(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search

async def twitchGet(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'https://api.twitch.tv/helix/{endpoint}',
            headers={"Client-ID": "q5hm7ld6pl5azmlauqd5mxml4wdklj"}) as r:
            r = await r.json()
            return r

class Utility(Cog) :
    def __init__(self, client):
        self.client = client

    # Command to send raw sql statements
    @commands.command(hidden=True)
    async def sql(self, ctx, *args):
        if ctx.message.author.id in Owner_id:
            statement = " ".join(args)

            if args[0] == 'SELECT':
                if str(sqlEXE(statement)) != "[]":
                    await ctx.send(sqlEXE(statement))
                else:
                    await ctx.send("No matching records found.")
            else:
                sqlEXE(statement)
                await ctx.message.add_reaction("\U0001F44D")
        else:
            await ctx.send("You don't have permission to use this command")

    # Returns a user's ID
    @commands.command(hidden=True)
    async def id(self, ctx, member : discord.Member = ''):
        try:
            await ctx.send(f"{member.display_name}'s ID is {member.id}.")
        except AttributeError:
            await ctx.send("You did not specify a user!")

    # Command to add user to credits list
    @commands.command(name = "AddUser",
                    description = "Adds a user to the credits document",
                    brief = "Add <member> to doc",
                    aliases = ["UserAdd", "InitUser", "adduser", "useradd", "inituser", "auser", "aUser"]
                    )
    async def AddUser(self, ctx, member : discord.Member):
        if ctx.message.author.id in Owner_id:

            if initUser(None, str(member.id)):
                await ctx.send(f"{member.display_name} has been added to the database. They have started with 0 credits")
                await ctx.send("User should use `c!addTwitch [Twitch username]` to link their Twitch account.")
            else:
                await ctx.send("That user is already in the list!")

        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to delete user from credits list
    @commands.command(name = "DelUser",
                    description = "Deletes a user from the credits document",
                    brief = "Delete <member> from doc",
                    aliases = ["UserDel", "deluser", "userdel", "duser", "dUser"]
                    )
    async def DelUser(self, ctx, member : discord.Member):
        if ctx.message.author.id in Owner_id:
            if delUser(str(member.id)):
                await ctx.send(f"{member.name} has been deleted from the database")
            else:
                await ctx.send("Member is not in the list.")
        else:
            await ctx.send("You don't have permission to use that command.")    

    # Command to link Twitch account
    @commands.command(name = 'addTwitch',
                    description = 'Links a user\'s Twitch account. Use if your Discord is in the database, but not your Twitch.',
                    brief = 'Link a Twitch account',
                    aliases = ['addtwitch', 'Addtwitch', 'AddTwitch']
                    )
    async def AddTwitch(self, ctx, username):

        initUser(None, str(ctx.message.author.id)) # init user

        twitchID = await twitchGet(f'users?login={username}')
        twitchName = twitchID['data'][0]['display_name']
        twitchID = twitchID['data'][0]['id']

        if thingInList(twitchID, 'credits_list'):
            linked_user = sqlEXE(f"SELECT discordID FROM credits_list WHERE twitchID = '{twitchID}';")
            linked_user = linked_user[3:-4]
            linked_user = await self.client.get_user(int(linked_user))

            await ctx.send(f"That Twitch account is already linked to {linked_user.display_name}.")
            return

        sqlEXE(f"UPDATE credits_list SET twitchID = '{twitchID}' WHERE discordID = '{ctx.message.author.id}';")
        await ctx.send(f"{ctx.message.author.display_name} linked to {twitchName} successfully!")

    # Command to link Discord account
    @commands.command(name = 'addDiscord',
                    description = 'Links a user\'s Discord account. Use if your Twitch is in the database, but not your Discord.',
                    brief = 'Link a Discord account',
                    aliases = ['adddiscord', 'Adddiscord', 'AddDiscord']
                    )
    async def AddDiscord(self, ctx, TwitchUsername):

        twitchID = await twitchGet(f'users?login={TwitchUsername}')
        twitchName = twitchID['data'][0]['display_name']
        twitchID = twitchID['data'][0]['id']
        discordID = str(ctx.message.author.id)

        if thingInList(discordID, 'credits_list'):
            await ctx.send(f"This Discord account is already in the database.\nYou should use c!addTwitch [username] to link your Twitch account to this Discord account.")
            return

        sqlEXE(f"UPDATE credits_list SET discordID = '{discordID}' WHERE twitchID = '{twitchID}';")
        await ctx.send(f"{twitchName} linked to {ctx.message.author.display_name} successfully!")

def setup(bot):
    bot.add_cog(Utility(bot))
