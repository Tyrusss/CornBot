import asyncio
import discord
import psycopg2

from cogs.utility import thingInList, sqlEXE, initUser, KeywordInMessage, Owner_id
from discord.ext import commands
from discord.ext.commands import Cog
from string import capwords

#Adds a game to the list or suggestion
def addGame(game, userID, param):
    if len(game) == 0:
        return "You can't add a game with no name."

    if thingInList(capwords(game), 'games_list'):
        return "That game is already in the list! use c!games"
    if param == False and thingInList(capwords(game), 'games_pending'):
        return "That game has already been suggested!"

    if int(userID) in Owner_id:
        sqlEXE(f"INSERT INTO games_list(game_name, votes) VALUES($${capwords(game)}$$, 0)")
        return f"Added {capwords(game)} to the list of games. Vote for it with 'c!vote <game>'."
    else:
        sqlEXE(f"INSERT INTO games_pending(game_name, suggestor, status) VALUES($${capwords(game)}$$, $${userID}$$, 'Pending')")
        return f"Added {capwords(game)} to the pending list, now just gotta wait for Corny Boy to deal with it."


class Games(Cog):
    def __init__(self, client):
        self.client = client

    # Command to add/suggest a game to the list
    @commands.command(name = "Nominate",
                    description = "Nominate a game to be voted for (Only two nominations per user)",
                    brief = "Nominate a game",
                    aliases = ["nominate"]
                    )
    async def nominate(self, ctx, *args):
        if not thingInList(str(ctx.author.id), 'credits_list'):
            await ctx.send("User must be added to the database with 'c!adduser [User]' first!")
            return
        game = " ".join(args)
        user_credits = sqlEXE(f"SELECT user_credits FROM credits_list WHERE discordID = '{ctx.message.author.id}'")
        user_credits = int(str(user_credits)[2:-3])

        if ctx.message.author.id not in Owner_id:
            if user_credits >= 300:
                result = addGame(game, str(ctx.message.author.id), False)
                await ctx.send(result)
                if KeywordInMessage("pending")(result):
                    Cornben = self.client.get_user(Owner_id[0])
                    await Cornben.send(f"{ctx.message.author.name} has nominated {capwords(game)}.\n\nUse c!accept {capwords(game)}\nor c!reject {capwords(game)}")
                sqlEXE(f"UPDATE credits_list SET user_credits = user_credits - 300 WHERE discordID = '{str(ctx.message.author.id)}';")
            else:
                await ctx.send("You don't have enough credits! You need 300 to nominate a game.")
        else:
            result = addGame(game, str(ctx.message.author.id), False)
            await ctx.send(result)

    # Command to accept a suggestion
    @commands.command(name = "Accept",
                    description = "Accept a game suggestion",
                    brief = "Accept a game suggestion",
                    aliases = ["accept"]
                    )
    async def Accept(self, ctx, *args):
        if ctx.message.author.id in Owner_id:
            game = " ".join(args)
            status = sqlEXE(f"SELECT status FROM games_pending WHERE game_name = '{capwords(game)}';")

            try:
                if str(status[0]) != "('Pending',)":
                    await ctx.send("You have already judged this game.")
                    return
            except IndexError:
                await ctx.send("That game is not in the list.")
                return

            addGame(str(game), str(ctx.message.author.id), True)
            sqlEXE(f"UPDATE games_pending SET status='Accepted' WHERE game_name = '{capwords(game)}'")
            await ctx.send(f"{capwords(game)} added to the list. View it with c!games")

            suggestor = int(str(sqlEXE(f"SELECT suggestor FROM games_pending WHERE game_name = '{capwords(game)}';"))[3:-4])
            suggestor = self.client.get_user(suggestor)
            await suggestor.send(f"Corny Boy has accepted your suggestion: {capwords(game)}")

        else:
            await ctx.send("You don't have permisssion to use this command")

    # Command to reject a suggestion
    @commands.command(name = "Reject",
                    description = "Reject a game suggestion",
                    brief = "Reject a game suggestion",
                    aliases = ["reject"]
                    )
    async def Reject(self, ctx, *args):
        if ctx.message.author.id in Owner_id:
            game = " ".join(args)
            status = sqlEXE(f"SELECT status FROM games_pending WHERE game_name = '{capwords(game)}';")

            try:
                if str(status[0]) != "('Pending',)":
                    await ctx.send("You have already judged this game.")
                    return
            except IndexError:
                await ctx.send("That game is not in the list.")
                return

            sqlEXE(f"UPDATE games_pending SET status='Rejected' WHERE game_name = '{capwords(game)}';")
            await ctx.send(f"Rejection of {capwords(game)} successful.")

            suggestor = int(str(sqlEXE(f"SELECT suggestor FROM games_pending WHERE game_name = '{capwords(game)}';"))[3:-4])
            suggestor = self.client.get_user(suggestor)
            sqlEXE(f"UPDATE credits_list SET user_credits = user_credits + 300 WHERE discordID = '{suggestor.id}';")

            await suggestor.send(f"Corny Boy has rejected your suggestion: {capwords(game)}\n300 credits have been refunded to your balance.")

    # Command to list all games in Games_List
    @commands.command(name = "Games",
                    description = "Shows all the games that can be voted for",
                    brief = "List all games in the list",
                    aliases = ["games"]
                    )
    async def Games(self, ctx, v_p = None):
        if v_p: v_p = v_p.title()

        if v_p == 'Pending' and ctx.message.author.id in Owner_id:
            em = discord.Embed(title="Pending games", colour=0xA366FF)
            
            for record in sqlEXE("SELECT * FROM games_pending"):
                user = self.client.get_user(int(record[1]))
                em.add_field(name=f"{record[0]} | {record[2]}", value=f"Suggested by {user.display_name}", inline=False)
        else:
            em = discord.Embed(title="Games", colour=0xA366FF)

            for record in sqlEXE("SELECT * FROM games_list"):
                if v_p == "Votes" and ctx.message.author.id in Owner_id:
                    em.add_field(name=f"{record[0]} | Votes: {record[1]}", value=f"c!vote {record[0]}", inline=False)
                else:
                    em.add_field(name=record[0], value=f"c!vote {record[0]}", inline=False)
        
        await ctx.send(embed=em)

    # Command to reset games
    @commands.command(name = "ResetGames",
                    description = "Reset the Games list and the pending list",
                    brief = "Delete all games in the lists",
                    aliases = ["resetgames"]
                    )
    async def resetGames(self, ctx):
        if ctx.message.author.id in Owner_id:
            await ctx.send("This will delete all of the games in both the pending & accepted tables. Are you sure? (y/n)")
            
            def pred(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel
            sure = await self.client.wait_for("message", check=pred)

            if sure.content.title() == 'Y':
                sqlEXE("DELETE FROM games_list; DELETE FROM games_pending WHERE status != 'Pending';")
                sqlEXE("UPDATE credits_list SET game_voted = FALSE;")
                await ctx.send("Succesfully reset.")
            elif sure.content.title() == 'N':
                await ctx.send("Then why did you invoke this command? smh")
            else:
                await ctx.send("???")

    # Command to add credits to a game
    @commands.command(name = "Vote",
                    description = "Vote for the game you want Cloutboy to play next",
                    brief = "Vote for a game",
                    aliases = ["vote"]
                    )
    async def Vote(self, ctx, *args):

        if not thingInList(str(ctx.author.id), 'credits_list'):
            await ctx.send("User must be added to the database with 'c!adduser [User]' first!")
            return
        voted = str(sqlEXE(f"SELECT game_voted FROM credits_list WHERE discordID = '{str(ctx.message.author.id)}' AND game_voted = 'yes';"))
        game = " ".join(args)
        
        if thingInList(capwords(game), 'games_list'):

            if len(voted) == 2:
                sqlEXE(f"UPDATE credits_list SET game_voted = TRUE WHERE discordID = '{str(ctx.message.author.id)}';")
                sqlEXE(f"UPDATE games_list SET votes = votes + 1 WHERE game_name = '{capwords(game)}'")
                await ctx.send(f"{ctx.message.author.mention}, successfully voted for {capwords(game)}.")

            elif len(voted) == 9:
                await ctx.send("You have already voted! Wait until the next set of nominations to vote again.")
                return
            else:
                await ctx.send("Something's gone wrong. Call Tyrus pls.")
                print(f"For some reason {str(ctx.message.author.display_name)}'s game_voted attribute is neither 2 nor 9 characters long")
                return
        else:
            await ctx.send("That game is not in the list. Use c!games to see the available games to vote for.")

    # Command to show top games
    @commands.command(name = "Top",
                    description = "Show the top voted-for games",
                    brief = "Show top games",
                    aliases = ["top"]
                    )
    async def top3(self, ctx):
        if ctx.message.author.id in Owner_id:
            em = discord.Embed(title="Top games", colour=0xA366FF)
            
            stop = 0
            for record in sqlEXE("SELECT * FROM games_list ORDER BY votes DESC;"):
                if stop == 3:
                    break
                
                em.add_field(name=f"{record[0]}", value=f"Votes: {record[1]}", inline=False)
                stop += 1

            await ctx.send(embed=em)
        else:
            await ctx.send("You don't have permission to use this command.")

def setup(bot):
    bot.add_cog(Games(bot))
