import asyncio
import discord
import psycopg2

from cogs.utility import thingInList, sqlEXE, Owner_id, hashFunction, twitchGet
from discord.ext import commands
from discord.ext.commands import Cog
from os import environ

class Credits(Cog):
    def __init__(self, client):
        self.client = client

    # Command to register a password
    @commands.command(name = "register",
                    description = "Register on the database with a password",
                    brief = "Register a password",
                    aliases = ["Register"])
    async def register(self, ctx):

        if ' ' not in str(ctx.message.channel):
            await ctx.send("That's not a good idea; Try this command in a private message")
            return

        if thingInList(str(ctx.message.author.id), "credits_list"):
            await ctx.send("This Discord account is already registered. If you want to link your Twitch account, private message me with the command `c!login [password]` on Twitch")
            return

        await ctx.send("Please input your password")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        stuff = await self.client.wait_for("message", check=pred)
        
        hash = hashFunction(stuff.content)
        sqlEXE(f"INSERT INTO credits_list(discordID, passwordHash, user_credits, game_voted) VALUES('{ctx.message.author.id}', '{hash}', 0, FALSE)")
        await ctx.send("Success! You have started with 0 credits. I recommend deleting the message with your password, now.")

    # Command to login to a registered account
    @commands.command(name = "login",
                    description = "Login to an account registered on the opposite platform",
                    brief = "Login to existing account",
                    aliases = ["Login"])
    async def login(self, ctx):

        if ' ' not in str(ctx.message.channel):
            await ctx.send("That's not a good idea; Try this command in a private message")
            return

        if thingInList(str(ctx.message.author.id), "credits_list"):
            await ctx.send("This Discord account is already in the database. If you mean to link your Twitch account, do the same command on Twitch")
            return

        await ctx.send("Please input your password")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        stuff = await self.client.wait_for("message", check=pred)

        password = stuff.content
        password = hashFunction(password)

        if not thingInList(str(password), 'credits_list'):
            await ctx.send("This password is incorrect.")
            return

        twitchID = sqlEXE(f"SELECT twitchID FROM credits_list WHERE passwordHash = '{password}';")

        twitchID = str(twitchID)[3:-4]
        twitchContent = await twitchGet(f"users?id={int(twitchID)}")
        twitchUsername = twitchContent["data"][0]["login"]
        await ctx.send(f"Link this Discord account with Twitch account '{twitchUsername}' with ID '{twitchID}'? Y/N")
        
        sure = await self.client.wait_for("message", check=pred)

        if sure.content.title() == 'Y':
            sqlEXE(f"UPDATE credits_list SET discordID = '{ctx.message.author.id}' WHERE twitchID = '{twitchID}';")
            await ctx.send("Success! I recommend you now delete the message containing your password")
        else:
            return

    # Command to give a user credits
    @commands.command(name = "Award",
                    description = "Award a member x credits",
                    brief = "Award credits",
                    aliases = ["award", "reward", "givecredits", "Givecredits", "Reward"]
                    )
    async def award(self, ctx, member : discord.Member, credits):
        try:
            credits = int(credits)
            if credits < 1:
                raise ValueError
        except ValueError:
            await ctx.send("That's not a valid argument (Must be an integer above 0).")
            return

        if ctx.message.author.id in Owner_id:
            if not thingInList(str(member.id), 'credits_list'):
                await ctx.send("User is not in the database! Maybe they need to do `c!login` to link their Twitch account.")
                return
            sqlEXE(f"UPDATE credits_list SET user_credits = user_credits + {credits} WHERE discordID = '{str(member.id)}'")     
            await ctx.send(f"{member.display_name} has been awarded {credits} credit(s).")
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to take away credits
    @commands.command(name = "Punish",
                    description = "Take x credits away from a member",
                    brief = "Take credits",
                    aliases = ["punish", "take", "takecredits", "Takecredits", "Take"]
                    )
    async def punish(self, ctx, member : discord.Member, credits):
        try:
            credits = int(credits)
            if credits < 1:
                raise ValueError
        except ValueError:
            await ctx.send("That's not a valid argument (Must be an integer above 0).")
            return

        if ctx.message.author.id in Owner_id:
            if not thingInList(str(member.id), 'credits_list'):
                await ctx.send("User is not in the database! Maybe they need to do `c!login` to link their Twitch account.")
                return
            sqlEXE(f"UPDATE credits_list SET user_credits = user_credits - {credits} WHERE discordID = '{str(member.id)}'")     
            await ctx.send(f"{member.display_name} has had {credits} credit(s) taken.")
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to check user's credits
    @commands.command(name = "credits",
                    description = "Check how many credits a user has",
                    brief = "Check credits",
                    aliases =["credit", 'check', 'Check']
                    )
    async def credits(self, ctx, member : discord.Member = None):
        if member:
            if not thingInList(str(member.id), 'credits_list'):
                await ctx.send("User is not in the database! Maybe they need to do `c!login` to link their Twitch account.")
                return
            data = sqlEXE(f"SELECT user_credits FROM credits_list WHERE discordID = '{str(member.id)}'")
            await ctx.send(f"{member.display_name} has {str(data)[2:-3]} credits(s).")

        else:
            if not thingInList(str(ctx.message.author.id), 'credits_list'):
                await ctx.send("You're not in the database! Do `c!register` to register your Discord account, or do `c!login` to link to an existing Twitch account")
                return
            data = sqlEXE(f"SELECT user_credits FROM credits_list WHERE discordID = '{str(ctx.message.author.id)}'")
            await ctx.send(f"<@{ctx.message.author.id}>, you have {str(data)[2:-3]} credits(s).")

    # Command to reset all users' credits
    @commands.command(name = "Resetcredits",
                    description = "Sets all users' credits to 0",
                    brief = "Reset all credits",
                    aliases = ["resetcredits"]
                    )
    async def resetcredits(self, ctx):
        if ctx.message.author.id in Owner_id:
            await ctx.send("This will set all users' credits to 0. Are you sure? (y/n)")
            def pred(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel
            sure = await self.client.wait_for("message", check=pred)

            if sure.content == 'y':
                sqlEXE("UPDATE credits_list SET user_credits = 0")
                await ctx.send("Successfully reset all credits.")

            elif sure.content == "n":
                await ctx.send("Then why did you invoke this command? smh")

            else:
                return
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to claim daily credits
    @commands.command(name = "daily",
                    description = "Collect your daily credits",
                    brief = "Daily credits",
                    aliases = ["Daily"])
    @commands.cooldown(1, 60*60*24, commands.BucketType.user)
    async def daily(self, ctx):

        if not thingInList(str(ctx.message.author.id), "credits_list"):
            await ctx.send("You're not in the database! Do `c!register` to register your Discord account, or do `c!login` to link to an existing Twitch account")

        sqlEXE(f"UPDATE credits_list SET user_credits = user_credits + 100 WHERE discordID = '{str(ctx.message.author.id)}';")
        user_credits = sqlEXE(f"SELECT user_credits FROM credits_list WHERE discordID = '{ctx.message.author.id}'")
        user_credits = int(str(user_credits)[2:-3])

        await ctx.send(f"Success! Your new balance is {user_credits}.")


def setup(bot):
    bot.add_cog(credits(bot))
