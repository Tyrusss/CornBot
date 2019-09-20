import asyncio
import discord
import psycopg2
import re

from discord.ext import commands
from discord.ext.commands import Cog

Owner_id = [332505589701935104, 237585716836696065, 554760937245245460]

def sqlEXE(statement):
    con = None
    try:
        # Connect to the database
        con = psycopg2.connect("postgres://yjzwwijnjncubp:9c841c698f4b9b3dd09c2873e0af52ef9cb6868947d123b353d457584f344dfb@ec2-50-17-193-83.compute-1.amazonaws.com:5432/d5kopahi42g27b", sslmode="require")
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
def initUser(twitchID, member: discord.Member):
    if thingInList(str(member.id), 'credits_list') == False: # Add member to list with 0 credits
        if thingInList(twitchID, 'credits_list') == False:
            
            discordID = str(member.id)
            sqlEXE(f"INSERT INTO credits_list(discordID, twitchID, user_credits, game_voted) VALUES('{discordID}', '{twitchID}', '{str(member.id)}', 0, FALSE)")
            
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

async def twitchGet(endcredit):
    from aiohttp import ClientSession
    async with ClientSession() as session:
        async with session.get(
            f'https://api.twitch.tv/helix/{endcredit}',
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
            await ctx.send(f"What is {member.display_name}'s Twitch username?'")
            def pred(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel
            twitchID = await self.client.wait_for("message", check=pred)

            if initUser(twitchID, member.id):
                await ctx.send(f"{member.display_name} has been added to the database. They have started with 0 credits")
            else:
                await ctx.send("That user is already in the list!")

        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to delete user from credits list
    @commands.command(name = "DelUser",
                    description = "Deletes a user to the credits document",
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


def setup(bot):
    bot.add_cog(Utility(bot))
