import random
import asyncio
import discord
import csv
import re

from discord.ext.commands import Bot
from discord import Game
from operator import itemgetter
from os import environ

# The command prefix & bot token (KEEP TOKEN SECRET)
commandPrefix, TOKEN = "c!", environ["TOKEN"]
helpCommand = '{0}help'.format(commandPrefix)

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

# Check if a member is in the database
def userInList(member):
    with open("Points_List.txt", "r", newline="") as file:
        found = False
        for row in csv.reader(file):
            if row[1] == str(member):
                found = True
    return found

# Returns a user's ID
@client.command()
async def id(ctx, member : discord.Member = ''):
    try:
        await ctx.send("{0}'s ID is {1}.".format(member.display_name, member.id))
    except AttributeError:
        await ctx.send("You did not specify a user!")

# Add a user to the points list
def initUser(member : discord.Member):
    if userInList(member.id) == False: # Add member to list with 0 points
        with open("Points_List.txt", "a", newline='') as file:
            row = [member.name, member.id, 0]

            writer = csv.writer(file)
            writer.writerow(row)
            return True
    else:
        return False

# Deletes a user from the points lists
def delUser(member=''):
    with open("Points_List.txt", "r", newline='') as file:
        data = list(csv.reader(file))

    deleted = False

    with open("Points_List.txt", "w", newline='') as file:
        writer = csv.writer(file)
        for row in data:
            if row[1] == str(member.id):
                deleted = True
            else:
                writer.writerow(row)
    
    if deleted == False:
        return False
    else:
        return True

#Adds a game to the list or suggestion
def addGame(game, userID, userName):
    if len(game) == 0:
        return "You can't add a game with no name."

    found = False

    with open("Games_List.txt", "r", newline="") as file:
        for row in csv.reader(file):
            if row[0].capitalize() == game.capitalize():
                found = True

    if userID ==  142485371987427328:
        
        if found:
            return "'{0}' is already in the list".format(game)

        with open("Games_List.txt", "a", newline="") as file:
            writer = csv.writer(file)
            row = [game, 0]

            writer.writerow(row)

        with open("Games_Pending.txt", "r") as file:
            data = list(csv.reader(file))
        
        with open("Games_Pending.txt", "w", newline="") as file:
            writer = csv.writer(file)

            for row in data:
                if row[0].capitalize() == game.capitalize():
                    rowtowrite = row
                    rowtowrite.append("Accepted")
                    writer.writerow(rowtowrite)
                else:
                    writer.writerow(row)

        return "'{0}' has been added successfully.".format(game)

    else:
        if not found:
            suggestions = 0
            with open("Games_Pending.txt", "r", newline="") as file:
                for row in csv.reader(file):
                    if row[0].capitalize() == game.capitalize():
                        return "'{0}' has already been suggested.".format(game)

                    if row[1] == userName:
                        suggestions += 1
            if suggestions > 1:
                return "You only get two suggestions per wave."

        else:
            return "'{0}' is already in the list".format(game)

        with open("Games_Pending.txt", "a", newline="") as file:
            writer = csv.writer(file)

            rowToWrite = [game, userName]
            writer.writerow(rowToWrite)
        x = True                
        return ["'{0}' has been suggested successfully. Gotta wait for Cloutboy to approve it.".format(game), x]

# Command to add user to points list
@client.command(name = "AddUser",
                description = "Adds a user to the points document",
                brief = "Add <member> to doc",
                aliases = ["UserAdd", "InitUser", "adduser", "useradd", "inituser", "auser", "aUser"]
                )
async def AddUser(ctx, member : discord.Member):
    if ctx.message.author.id == 142485371987427328:
        if initUser(member):
            await ctx.send("<@{0}> has been added to the list".format(member.id))
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
    if ctx.message.author.id == 142485371987427328:
        if delUser(member):
            await ctx.send("{0} has been deleted from the database".format(member.name))
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
    if ctx.message.author.id == 142485371987427328:

        try:
            if int(points) < 1:
                raise ValueError

            initUser(member)
            with open("Points_List.txt", "r", newline='') as file:
                reader = csv.reader(file)
                lines = list(reader)

                for row in lines:
                    if row[1] == str(member.id):
                        newRow = row
                        temp = (int(row[2]) + (int(points)))
                        newRow[2] = temp
                        rowIndex = lines.index(row)

            lines[rowIndex] = newRow
            with open("Points_List.txt", "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerows(lines)
            
            single = 'points'
            if points == '1':
                single = 'point'

            await ctx.send("{0} has been awarded {1} {2}. They now have {3}".format(member.mention, points, single, temp))
    
        except ValueError:
            await ctx.send("That's not a valid argument (Must be an integer above 0).")
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to take away points
@client.command(name = "Punish",
                description = "Take x points away from a member",
                brief = "Take points",
                aliases = ["punish", "take", "takepoints", "TakePoints", "Take"]
                )
async def punish(ctx, member : discord.Member, points):
    if ctx.message.author.id == 142485371987427328:
        try:
            if int(points) < 1:
                raise ValueError

            initUser(member)
            with open("Points_List.txt", "r", newline='') as file:
                reader = csv.reader(file)
                lines = list(reader)

                for row in lines:
                    if row[1] == str(member.id):
                        newRow = row
                        temp = (int(row[2]) - (int(points)))
                        newRow[2] = temp
                        rowIndex = lines.index(row)

            lines[rowIndex] = newRow
            with open("Points_List.txt", "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerows(lines)
            
            single = 'points'
            if points == '1':
                single = 'point'

            await ctx.send("{0} has lost {1} {2}. They now have {3}".format(member.mention, points, single, temp))
    
        except ValueError:
            await ctx.send("That's not a valid number (Must be an integer above 0).")
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
        with open("Points_List.txt", "r", newline="") as file:
            for row in csv.reader(file):
                if row[1] == str(member.id):
                    points = row[2]

        single = 'points'
        if points == '1':
            single = 'point'
        await ctx.send("{0} has {1} {2}.".format(member.name, points, single))

    else:
        initUser(ctx.message.author)
        with open("Points_List.txt", "r", newline='') as file:
            for row in csv.reader(file):
                if row[0] == ctx.message.author.name:
                    points = row[2]

        single = 'points'
        if points == '1':
            single = 'point'
        await ctx.send("{0}, you have {1} {2}.".format(ctx.message.author.mention, points, single))

# Command to reset all users' points
@client.command(name = "ResetPoints",
                description = "Sets all users' points to 0",
                brief = "Reset all points",
                aliases = ["resetpoints"]
                )
async def resetPoints(ctx):
    if ctx.message.author.id == 142485371987427328:
        await ctx.send("This will set all users' points to 0. Are you sure? (y/n)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        sure = await client.wait_for("message", check=pred)

        if sure.content == 'y':
            with open("Points_List.txt", "r", newline="") as file:
                data = list(csv.reader(file))

            for row in data:
                data[data.index(row)][2] = 0

            with open("Points_List.txt", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(data)
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
    if ctx.message.author.id == 142485371987427328:
        
        if len(args) == 0:
            await ctx.send("You can't have a reward with no name.")
            return

        rewardName = " ".join(args)

        with open("Rewards_List.txt", "r", newline = "") as file:
            for row in csv.reader(file):
                if row[0] == rewardName:
                    await ctx.send("That reward is already on the list. If you wish to change it, you'll need to delete the existing one first.")
                    return

        await ctx.send("Please write a short description of the reward. (Type '#cancel# to cancel this reward)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        rewardDesc = await client.wait_for("message", check=pred)

        if rewardDesc.content == "#cancel#":
            await ctx.send("Cancelled the reward-creator.")
            return

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

        with open("Rewards_List.txt", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([rewardName, rewardCost, rewardDesc.content])

        await ctx.send("Reward '{0}' succesfully added to list.".format(rewardName))
    else:
        await ctx.send("You don't have permission to use that command.")

# Command to delete a reward
@client.command(name = "DelReward",
                description = "Deletes a redeemable reward from the list",
                brief = "Delete a reward",
                aliases = ["DelR", "delr", "delreward"]
                )
async def DeleteReward(ctx, *args):
    if ctx.message.author.id == 142485371987427328:
        if len(args) == 0:
            await ctx.send("You have to specify a reward to delete.")
        else:
            with open("Rewards_List.txt", "r", newline='') as file:
                data = list(csv.reader(file))

            deleted = False
            reward = " ".join(args)

            with open("Rewards_List.txt", "w", newline='') as file:
                writer = csv.writer(file)
                for row in data:
                    if row[0] == reward:
                        deleted = True
                    else:
                        writer.writerow(row)

            if deleted:
                await ctx.send("'{0}' has been successfully deleted.".format(" ".join(args)))
            else:
                await ctx.send("There is no reward by that name.")
    else:
        await ctx.send("You don't have permission to use that command.")

# Command that lists all rewards
@client.command(name = "Rewards",
                description = "List all the redeemable rewards",
                brief = "List all rewards",
                aliases = ["rewards"]
                )
async def rewards(ctx):
    initUser(ctx.message.author)
    with open("Rewards_List.txt", "r", newline="") as file:
        thingtosay = ""
        for row in csv.reader(file):
            thingtosay += f"------------------------------------------------\n{row[0]} | {row[2]}\n{row[1]} points\n"

    thingtosay += f"------------------------------------------------\nUse c!games to see the list of nominated games you can vote for.\n------------------------------------------------\nUse c!redeem <reward> to redeem a reward."
    await ctx.send(thingtosay)    

# Command to add/suggest a game to the list
@client.command(name = "Nominate",
                description = "Nominate a game to be voted for (Only two nominations per user)",
                brief = "Nominate a game",
                aliases = ["nominate"]
                )
async def nominate(ctx, *args):
    initUser(ctx.message.author)
    game = " ".join(args)
    result = addGame(game, ctx.message.author.id, ctx.message.author.name)

    if type(result) is list:
        await ctx.send(result[0])
        cloutboy = client.get_user(142485371987427328)
        await cloutboy.send("The game '{0}' has been suggested by {1}. Type 'c!Accept {0}' or c!Reject {0}'.".format(game, ctx.message.author.name))
    else:
        await ctx.send(result)

# Command to accept a suggestion
@client.command(name = "Accept",
                description = "Accept a game suggestion",
                brief = "Accept a game suggestion",
                aliases = ["accept"]
                )
async def Accept(ctx, *args):
    if ctx.message.author.id == 142485371987427328:
        game = " ".join(args)

        with open("Games_Pending.txt", "r", newline="") as file:
            found = False
            for row in csv.reader(file):
                if row[0].capitalize() == game.capitalize():
                    found = True

            if found == False:
                await ctx.send("'{0}' is not on the suggestions list.".format(game))
                return
            
        result = addGame(game, ctx.message.author.id, ctx.message.author.name)
        await ctx.send(result)
    else:
        await ctx.send("You don't have permisssion to use this command")

# Command to reject a suggestion/delete a game
@client.command(name = "Reject",
                description = "Reject a game suggestion",
                brief = "Reject a game suggestion",
                aliases = ["reject"]
                )
async def Reject(ctx, *args):
    game = " ".join(args)

    if ctx.message.author.id == 142485371987427328:
        with open("Games_Pending.txt", "r", newline="") as file:
            data = list(csv.reader(file))

        with open("Games_Pending.txt", "w", newline="") as file:
            writer = csv.writer(file)
            found = False
            for row in data:
                if row[0].capitalize() == game.capitalize():
                    found = True
                    rowtowrite = row
                    rowtowrite.append("Rejected")
                    writer.writerow(rowtowrite)
                else:
                    writer.writerow(row)

        with open("Games_List.txt", "r") as file:
            data = list(csv.reader(file))

        with open("Games_List.txt", "w", newline="") as file:
            writer = csv.writer(file)
            foundB = False
            for row in data:
                if row[0].capitalize() == game.capitalize():
                    foundB = True
                else:
                    writer.writerow(row)

        if found and (not foundB):
            await ctx.send("'{0}' has been rejected successfully.".format(game))
        elif foundB:
            with open("Games_Pending.txt", "a", newline="") as file:
                csv.writer(file).writerow([game, "Deleted"])

            await ctx.send("'{0}' has been deleted from the Games List".format(game))
        else:
            await ctx.send("'{0}' is not in the pending list.".format(game))

# Command to list all games in Games_List
@client.command(name = "Games",
                description = "Shows all the games that can be voted for",
                brief = "List all games in the list",
                aliases = ["games"]
                )
async def Games(ctx, votes=None):
    with open("Games_List.txt", "r") as file:
        reader = csv.reader(file)
    
        if ctx.message.author.id == 142485371987427328: 
            if votes == 'votes' or votes == 'Votes':

                rowToSay = ""
                for row in reader:
                    if row[1] == '1':
                        single = 'point'
                    else: 
                        single = 'points'

                    rowToSay += "------------------------------------------------\n{0} | {1} {2}\n".format(row[0], row[1], single)
                rowToSay += "------------------------------------------------\nUsers can type 'c!vote <game>' to vote. They can vote as many times as they wish."
                await ctx.send(rowToSay)
                return

        initUser(ctx.message.author)
        rowToSay = ""
        for row in reader:
            rowToSay += "------------------------------------------------\n{0}\n".format(row[0])
        rowToSay += "------------------------------------------------\nYou can vote for a game with 'c!vote <game>'. You can vote as many times as you wish."
        await ctx.send(rowToSay)

# Command to reset games
@client.command(name = "ResetGames",
                description = "Reset the Games list and the pending list",
                brief = "Delete all games in the lists",
                aliases = ["resetgames"]
                )
async def resetGames(ctx):
    if ctx.message.author.id == 142485371987427328:
        await ctx.send("This will delete all of the games in Games_List and Games_Pending, are you sure? (y/n)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        sure = await client.wait_for("message", check=pred)

        if sure.content == 'y' or sure.content == 'Y':
            with open("Games_List.txt", "w"):
                print("reset games_list")
            with open("Games_Pending.txt", "w"):
                print("reset games_pending")

            await ctx.send("Succesfully reset.")
        elif sure.content == 'n' or sure.content == 'N':
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
    with open("Games_List.txt", "r") as file:
        found = False
        for row in csv.reader(file):
            if row[0].capitalize() == game.capitalize():
                found = True
        
    if found:
        with open("Points_List.txt", "r") as file:
            reader = csv.reader(file)
            data = list(reader)
            for row in data:
                if row[0] == ctx.message.author.name:
                    points = int(row[2])

        if points == '1':
            single = 'point'
        else:
            single = 'points'
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        await ctx.send("{0}, how many points would you like to add to this game's pool? (You have {1} {2} left)".format(ctx.message.author.mention, points, single))
        vote = await client.wait_for("message", check=pred)

        try:
            vote = int(vote.content)
            if vote <= 0:
                raise ValueError
            
        except ValueError:
            await ctx.send("That's not a valid amount.")
            return

        if vote > points:
            await ctx.send("You don't have enough points.")
            return
        
        for row in data:
            if row[0] == ctx.message.author.name:
                newRow = row
                temp = (int(row[2]) - (int(vote)))
                newRow[2] = temp
                rowIndex = data.index(row)

        data[rowIndex] = newRow
        with open("Points_List.txt", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        

        with open("Games_List.txt", "r", newline='') as file:
            reader = csv.reader(file)
            lines = list(reader)

            for row in lines:
                if row[0] == game:
                    newRow = row
                    temp = (int(row[1]) + (int(vote)))
                    newRow[1] = temp
                    rowIndex = lines.index(row)

        lines[rowIndex] = newRow
        with open("Games_List.txt", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerows(lines)

        if vote == 1:
            single = 'point'
        else:
            single = 'points'

        await ctx.send("{0}, you have added {1} {2} to '{3}'".format(ctx.message.author.mention, vote, single, game))

    else:
        await ctx.send("'{0}' is not in the list.".format(game))

# Command to show top 3 games
@client.command(name = "Top",
                description = "Show the top voted-for games",
                brief = "Show top games",
                aliases = ["top"]
                )
async def top3(ctx):
    if ctx.message.author.id == 142485371987427328:
        with open("Games_List.txt", "r") as file:
            data = list(csv.reader(file))
            data.sort(key = itemgetter(1), reverse = True)
            try:
                top = [data[0], data[1], data[2]]
            except IndexError:
                try:
                    top = [data[0], data[1]]
                except IndexError:
                    try:
                        top = [data[0]]
                    except IndexError:
                        await ctx.send("There are no games in the list.")
                        return
        thingToSay = ''
        for row in top:
            if row[1] == '1':
                single = 'vote'
            else:
                single = 'votes'

            thingToSay += "------------------------------------------------\n{0} | {1} {2}\n".format(row[0], row[1], single)
        thingToSay += "------------------------------------------------"
        await ctx.send(thingToSay)

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

    with open("Rewards_List.txt", "r") as file:
        found = False
        for row in csv.reader(file):
            if row[0].capitalize() == reward.capitalize():
                found = True
                price = int(row[1])

    if not found:
        await ctx.send("That reward is not in the list.")
        return
    else:
        await ctx.send(f"Redeem '{reward}'' for {price}? (y/n)")
        def pred(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel
        sure = await client.wait_for("message", check=pred)
        if sure.content != "y" and sure.content != "Y":
            await ctx.send("Canceled redemption.")
            return

        with open("Points_List.txt", "r") as file:
            reader = csv.reader(file)
            lines = list(reader)

            for row in lines:
                if row[1] == str(ctx.message.author.id):
                    newRow = row
                    temp = int(row[2]) - price
                    if temp < 0:
                        await ctx.send("You don't have enough points.")
                        return

                    newRow[2] = temp
                    rowIndex = lines.index(row)

        lines[rowIndex] = newRow
        with open("Points_List.txt", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerows(lines)

        if price == 1:
            single = 'point'
        else:
            single = 'points'

        await ctx.send(f"{ctx.message.author.mention}, succesfully redeemed '{reward}' for {price} {single}. You now have {temp}.")

        cloutboy = client.get_user(142485371987427328)
        await cloutboy.send(f"{ctx.message.author.name} has redeemed '{reward}' for {price} {single}.")

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

# Actually run the damn thing
client.run(TOKEN)
