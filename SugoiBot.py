import random
import asyncio
import discord
import re
import psycopg2

from discord.ext.commands import Bot
from discord import Game
from os import environ

# The command prefix & bot token (KEEP TOKEN SECRET)
commandPrefix, TOKEN = "c!", environ["TOKEN"]
helpCommand = f'{commandPrefix}help'
Owner_id = 142485371987427328

# Initialise the client
client = Bot(command_prefix=commandPrefix)
client.remove_command("help")

@client.command(name="help")
async def Help(ctx):
    await ctx.send(  """```help        Shows this message.
id          
AddUser     Add <member> to doc
DelUser     Delete <member> from doc
Award       Award points
Punish      Take points
Points      Check points
ResetPoints Reset all points
NewReward   Add new reward
DelReward   Delete a reward
Rewards     List all rewards
Nominate    Nominate a game
Accept      Accept a game suggestion
Reject      Reject a game suggestion
Games       List all games in the list
ResetGames  Delete all games in the lists
Vote        Vote for a game
Top         Show top games
Redeem      Redeem a reward

Type c!help command for more info on a command.
You can also type c!help category for more info on a category.```""")

# When executing sql statements
def sqlEXE(statement):
    con = None
    try:
        # Connect to the database
        DATABASE_URL = environ["DATABASE_URL"]
        con = psycopg2.connect(DATABASE_URL, sslmode="require")
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

# Command to send raw sql statements
@client.command()
async def sql(ctx, *args):
    if ctx.message.author.id == 237585716836696065 or ctx.message.author.id == Owner_id:
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

# Check if a thing is in the database
def thingInList(thing, table):
    if str(sqlEXE(f"SELECT * FROM {table}")) != "[]":
        for item in sqlEXE(f"SELECT * FROM {table}"):
            if item[0] == thing:
                return True
    return False

# Returns a user's ID
@client.command()
async def id(ctx, member : discord.Member = ''):
    try:
        await ctx.send(f"{member.display_name}'s ID is {member.id}.")
    except AttributeError:
        await ctx.send("You did not specify a user!")

# Add a user to the points list
def initUser(member : discord.Member):
    if thingInList(str(member.id), 'points_list') == False: # Add member to list with 0 points
        sqlEXE(f"INSERT INTO points_list(user_id, user_points) VALUES('{str(member.id)}', 0)")
        return True
    else:
        return False

# Deletes a user from the points lists
def delUser(memberID):
    if thingInList(str(memberID), 'points_list'):
        sqlEXE(f"DELETE FROM points_list WHERE user_id = '{str(memberID)}'")
        return True
    else:
        return False

#Adds a game to the list or suggestion
def addGame(game, userID, param):
    if len(game) == 0:
        return "You can't add a game with no name."

    if thingInList(game.title(), 'games_list'):
        return "That game is already in the list! use c!games"
    if param == False and thingInList(game.title(), 'games_pending'):
        return "That game has already been suggested!"


    if userID == str(Owner_id):
        sqlEXE(f"INSERT INTO games_list(game_name, votes) VALUES('{game.title()}', 0)")
        return f"Added {game.title()} to the list of games. Vote for it with 'c!vote <game>'."
    else:
        sqlEXE(f"INSERT INTO games_pending(game_name, suggestor, status) VALUES('{game.title()}', '{userID}', 'Pending')")
        return f"Added {game.title()} to the pending list, now just gotta wait for Sugoi Boy to deal with it."

# Command to add user to points list
@client.command(name = "AddUser",
                description = "Adds a user to the points document",
                brief = "Add <member> to doc",
                aliases = ["UserAdd", "InitUser", "adduser", "useradd", "inituser", "auser", "aUser"]
                )
async def AddUser(ctx, member : discord.Member):
    if ctx.message.author.id == Owner_id:
        if initUser(member):
            await ctx.send(f"<@{member.id}> has been added to the list")
            await ctx.send("They have started with 0 points.")
        else:
            await ctx.send("Member is already in the list.")
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to delete user from points list
@client.command(name = "DelUser",
                description = "Deletes a user to the points document",
                brief = "Delete <member> from doc",
                aliases = ["UserDel", "deluser", "userdel", "duser", "dUser"]
                )
async def DelUser(ctx, member : discord.Member):
    if ctx.message.author.id == Owner_id:
        if delUser(str(member.id)):
            await ctx.send(f"{member.name} has been deleted from the database")
        else:
            await ctx.send("Member is not in the list.")
    else:
        await ctx.send("You don't have permission to use that command.")    

# Command to give a user points
@client.command(name = "Award",
                description = "Award a member x points",
                brief = "Award points",
                aliases = ["award", "reward", "givepoints", "GivePoints", "Reward"]
                )
async def award(ctx, member : discord.Member, points):
    try:
        points = int(points)
        if points < 1:
            raise ValueError
    except ValueError:
        await ctx.send("That's not a valid argument (Must be an integer above 0).")
        return

    if ctx.message.author.id == Owner_id:
        initUser(member)
        sqlEXE(f"UPDATE points_list SET user_points = user_points + {points} WHERE user_id = '{str(member.id)} ' ")    
        await ctx.send(f"{member.display_name} has been awarded {points} point(s).")
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to take away points
@client.command(name = "Punish",
                description = "Take x points away from a member",
                brief = "Take points",
                aliases = ["punish", "take", "takepoints", "TakePoints", "Take"]
                )
async def punish(ctx, member : discord.Member, points):
    try:
        points = int(points)
        if points < 1:
            raise ValueError
    except ValueError:
        await ctx.send("That's not a valid argument (Must be an integer above 0).")
        return

    if ctx.message.author.id == Owner_id:
        initUser(member)
        sqlEXE(f"UPDATE points_list SET user_points = user_points - {points}")    
        await ctx.send(f"{member.display_name} has had {points} point(s) taken.")
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to check user's points
@client.command(name = "Points",
                description = "Check how many points a user has",
                brief = "Check points",
                aliases =["points", 'check', 'Check']
                )
async def points(ctx, member : discord.Member = None):
    if member:
        initUser(member)
        data = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{str(member.id)}'")
        await ctx.send(f"{member.display_name} has {str(data)[2:-3]} points(s).")

    else:
        initUser(ctx.message.author)
        data = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{str(ctx.message.author.id)}'")
        await ctx.send(f"<@{ctx.message.author.id}>, you have {str(data)[2:-3]} points(s).")

# Command to reset all users' points
@client.command(name = "ResetPoints",
                description = "Sets all users' points to 0",
                brief = "Reset all points",
                aliases = ["resetpoints"]
                )
async def resetPoints(ctx):
    if ctx.message.author.id == Owner_id:
        await ctx.send("This will set all users' points to 0. Are you sure? (y/n)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        sure = await client.wait_for("message", check=pred)

        if sure.content == 'y':
            sqlEXE("UPDATE points_list SET user_points = 0")
            await ctx.send("Successfully reset all points.")

        elif sure.content == "n":
            await ctx.send("Then why did you invoke this command? smh")

        else:
            return
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to add a reward to the list
@client.command(name = "NewReward",
                description = "Adds a new reward that user's can redeem",
                brief = "Add new reward",
                aliases = ["AddR", "addreward", "AddReward", "newreward", "addr"]
                )
async def NewReward(ctx, *args):
    if ctx.message.author.id == Owner_id:
        
        if len(args) == 0:
            await ctx.send("You can't have a reward with no name.")
            return

        rewardName = " ".join(args)
        if '"' in rewardName or "'" in rewardName or '’' in rewardName:
            rewardName = rewardName.replace("'", "")
            rewardName = rewardName.replace('"', "")
            rewardName = rewardName.replace('’', '')

        if thingInList(rewardName, 'rewards_list'):
            await ctx.send(f"'{rewardName}' is already in the list.")
            return

        await ctx.send("Please write a short description of the reward. (Type '#cancel# to cancel this reward)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        rewardDesc = await client.wait_for("message", check=pred)

        if rewardDesc.content == "#cancel#":
            await ctx.send("Cancelled the reward-creator.")
            return

        if '"' in rewardDesc.content or "'" in rewardDesc.content or '’' in rewardDesc.content:
            rewardDesc = rewardDesc.content.replace("'", "")
            rewardDesc = rewardDesc.content.replace('"', "")
            rewardDesc = rewardDesc.content.replace('’', '')
        else:
            rewardDesc = rewardDesc.content

        await ctx.send("And how many points will it take to redeem this reward? (Type '#cancel#' to cancel this reward)")
        rewardCost = await client.wait_for("message", check=pred)

        if rewardCost.content == "#cancel#":
            await ctx.send("Cancelled the reward-creator.")
            return

        try:
            rewardCost = int(rewardCost.content)
        except ValueError:
            await ctx.send("That's not a valid price (Must be an integer more than 0).")
            return
        if rewardCost < 1:
            await ctx.send("That's not a valid price (Must be an integer more than 0).")
            return

        sqlEXE(f"INSERT INTO rewards_list(reward_name, reward_desc, price) VALUES('{rewardName.title()}', '{rewardDesc}', {rewardCost})")

        await ctx.send(f"Reward '{rewardName.title()}' succesfully added to list.")
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to delete a reward
@client.command(name = "DelReward",
                description = "Deletes a redeemable reward from the list",
                brief = "Delete a reward",
                aliases = ["DelR", "delr", "delreward"]
                )
async def DeleteReward(ctx, *args):
    if ctx.message.author.id == Owner_id:
        if len(args) == 0:
            await ctx.send("You have to specify a reward to delete.")
        else:
            reward = " ".join(args)
            if thingInList(reward, 'rewards_list'):
                sqlEXE(f"DELETE FROM rewards_list WHERE reward_name = '{reward.title()}'")
            else:
                ctx.send("There is no reward by that name")

    else:
        await ctx.send("You don't have permission to use that command.")

# Command that lists all rewards
@client.command(name = "Rewards",
                description = "List all the redeemable rewards",
                brief = "List all rewards",
                aliases = ["rewards"]
                )
async def rewards(ctx):
    em = discord.Embed(title="Rewards", colour=0xA366FF)
    for record in sqlEXE("SELECT * FROM rewards_list"):
        em.add_field(name=f"{record[0]} | Price: {record[2]}", value=record[1], inline=False)
    
    em.add_field(name="Pick next stream game", value="Use c!games to view the list of games you can vote for.", inline=False)
    em.add_field(name="To redeem", value="Use c!redeem <reward>", inline=False)
    await ctx.send(embed=em)

# Command to add/suggest a game to the list
@client.command(name = "Nominate",
                description = "Nominate a game to be voted for (Only two nominations per user)",
                brief = "Nominate a game",
                aliases = ["nominate"]
                )
async def nominate(ctx, *args):
    initUser(ctx.message.author)
    game = " ".join(args)
    if "'" in game or '"' in game or '’' in game:
        game = game.replace('"', '')
        game = game.replace("'", '')
        game = game.replace('’', '')
    
    result = addGame(game, str(ctx.message.author.id), False)
    await ctx.send(result)
    if KeywordInMessage("pending")(result) and ctx.message.author.id != Owner_id:
        Sugoi_Boy = client.get_user(Owner_id)
        await Sugoi_Boy.send(f"{ctx.message.author.name} has nominated {game.title()}.\n\nUse c!accept {game.title()}\nor c!reject {game.title()}")

# Command to accept a suggestion
@client.command(name = "Accept",
                description = "Accept a game suggestion",
                brief = "Accept a game suggestion",
                aliases = ["accept"]
                )
async def Accept(ctx, *args):
    if ctx.message.author.id == Owner_id:
        game = " ".join(args)

        if thingInList(game.title(), 'games_pending'):
            addGame(str(game), str(Owner_id), True)
            sqlEXE(f"UPDATE games_pending SET status='Accepted' WHERE game_name = '{game.title()}'")
            await ctx.send(f"{game.title()} added to the list. View it with c!games")

            suggestor = int(str(sqlEXE(f"SELECT suggestor FROM games_pending WHERE game_name = '{game.title()}';"))[3:-4])
            suggestor = client.get_user(suggestor)
            await suggestor.send(f"Sugoi Boy has accepted your suggestion: {game.title()}")
        else:
            await ctx.send(f"{game.title()} is not pending. Use c!games pending")
    else:
        await ctx.send("You don't have permisssion to use this command")

# Command to reject a suggestion/delete a game
@client.command(name = "Reject",
                description = "Reject a game suggestion",
                brief = "Reject a game suggestion",
                aliases = ["reject"]
                )
async def Reject(ctx, *args):
    if ctx.message.author.id == Owner_id:
        game = " ".join(args)

        if thingInList(game.title(), 'games_list'):
            sqlEXE(f"DELETE FROM games_list WHERE game_name = '{game.title()}'")
            await ctx.send(f"{game.title()} has been deleted from the list.")
        if thingInList(game.title(), 'games_pending'):
            sqlEXE(f"UPDATE games_pending SET status='Rejected' WHERE game_name = '{game.title()}'")
            await ctx.send(f"Rejection of {game.title()} successful.")
        else:
            await ctx.send(f"{game.title()} is not in the list. Use c!games pending")
            return

        suggestor = int(str(sqlEXE(f"SELECT suggestor FROM games_pending WHERE game_name = '{game.title()}';"))[3:-4])
        suggestor = client.get_user(suggestor)
        await suggestor.send(f"Sugoi Boy has rejected your suggestion: {game.title()}")

# Command to list all games in Games_List
@client.command(name = "Games",
                description = "Shows all the games that can be voted for",
                brief = "List all games in the list",
                aliases = ["games"]
                )
async def Games(ctx, v_p = None):
    if v_p: v_p = v_p.title()

    if v_p == 'Pending' and ctx.message.author.id == Owner_id:
        em = discord.Embed(title="Pending games", colour=0xA366FF)
        
        for record in sqlEXE("SELECT * FROM games_pending"):
            user = client.get_user(int(record[1]))
            em.add_field(name=f"{record[0]} | {record[2]}", value=f"Suggested by {user.display_name}", inline=False)
    else:
        em = discord.Embed(title="Games", colour=0xA366FF)

        for record in sqlEXE("SELECT * FROM games_list"):
            if v_p == "Votes" and ctx.message.author.id == Owner_id:
                em.add_field(name=f"{record[0]} | Votes: {record[1]}", value=f"c!vote {record[0]}", inline=False)
            else:
                em.add_field(name=record[0], value=f"c!vote {record[0]}", inline=False)
    
    await ctx.send(embed=em)

# Command to reset games
@client.command(name = "ResetGames",
                description = "Reset the Games list and the pending list",
                brief = "Delete all games in the lists",
                aliases = ["resetgames"]
                )
async def resetGames(ctx):
    if ctx.message.author.id == Owner_id:
        await ctx.send("This will delete all of the games in both the pending & accepted tables. Are you sure? (y/n)")
        
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        sure = await client.wait_for("message", check=pred)

        if sure.content.title() == 'Y':
            sqlEXE("DELETE FROM games_list; DELETE FROM games_pending;")
            await ctx.send("Succesfully reset.")
        elif sure.content.title() == 'N':
            await ctx.send("Then why did you invoke this command? smh")
        else:
            await ctx.send("???")

# Command to add points to a game
@client.command(name = "Vote",
                description = "Vote for the game you want Cloutboy to play next",
                brief = "Vote for a game",
                aliases = ["vote"]
                )
async def Vote(ctx, *args):

    initUser(ctx.message.author)
        
    game = " ".join(args)
    
    if thingInList(game.title(), 'games_list'):
        user_points = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{str(ctx.message.author.id)}'")
        user_points = int(str(user_points)[2:-3])

        await ctx.send("How many points do you wish to put into the game's pool?")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        votes = await client.wait_for("message", check=pred)

        try:
            votes = int(votes.content)
            if votes < 1:
                raise ValueError
        except ValueError:
            await ctx.send("Invalid argument (Must be integer >0).")
            return

        if user_points >= votes:
            sqlEXE(f"UPDATE points_list SET user_points = user_points - {votes} WHERE user_id = '{ctx.message.author.id}'")
            sqlEXE(f"UPDATE games_list SET votes = votes + {votes} WHERE game_name = '{game.title()}'")
            await ctx.send(f"Success! You now have {user_points - votes}")

        else:
            await ctx.send("You don't have enough points.")
    else:
        await ctx.send(f"'{game.title()}' is not in the list. use c!games to see the list of available games to vote for.")

# Command to show top games
@client.command(name = "Top",
                description = "Show the top voted-for games",
                brief = "Show top games",
                aliases = ["top"]
                )
async def top3(ctx):
    if ctx.message.author.id == Owner_id:
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

# Command to redeem custom rewards
@client.command(name = "Redeem",
                description = "Redeem a reward from the custom list",
                brief = "Redeem a reward",
                aliases = ["redeem", "buy", "Buy"]
                )
async def redeem(ctx, *args):
    initUser(ctx.message.author)
    reward = " ".join(args)

    if not thingInList(reward.title(), 'rewards_list'):
        ctx.send(f"'{reward.title()}' is not in the list. Use c!rewards to see the list of available rewards.")
        return

    user_points = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{ctx.message.author.id}'")
    user_points = int(str(user_points)[2:-3])

    reward_cost = sqlEXE(f"SELECT price FROM rewards_list WHERE reward_name = '{reward.title()}'")
    reward_cost = int(str(reward_cost)[2:-3])

    if user_points >= reward_cost:
        await ctx.send(f"Are you sure you want to redeem {reward.title()}? (y/n)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        sure = await client.wait_for("message", check=pred)

        if sure.content.title() == 'Y':

            sqlEXE(f"UPDATE points_list SET user_points = user_points - {reward_cost}")
            
            await ctx.send(f"Success! Your new balance is {user_points - reward_cost}.")

            Sugoi_Boy = client.get_user(Owner_id)
            await Sugoi_Boy.send(f"{ctx.message.author.name} has redeemed {reward.title()}.")
        elif sure.content.title() == 'N':
            await ctx.send("Well why did you invoke this command then? smh")
        else:
            await ctx.send("???")

    else:
        ctx.send("You don't have enough points.")

# CHECK IF KEYWORD IN MESSAGE
def KeywordInMessage(word):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search

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

    # Allow for commands to be processed while on_message occurs
    await client.process_commands(message)


# Stuff that happens on startup
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=Game(helpCommand))
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')

    if str(sqlEXE("SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = 'points_list');")) == "[(False,)]":
        sqlEXE("CREATE TABLE points_list(user_id TEXT PRIMARY KEY, user_points INTEGER)")
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

# Actually run the damn thing
client.run(TOKEN)
