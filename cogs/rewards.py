import asyncio
import discord
import psycopg2

from cogs.utility import thingInList, sqlEXE, initUser
from discord.ext import commands
from discord.ext.commands import Cog
from string import capwords

Owner_id = 142485371987427328

class Rewards(Cog):
    def __init__(self, client):
        self.client = client

    # Command to add a reward to the list
    @commands.command(name = "NewReward",
                    description = "Adds a new reward that user's can redeem",
                    brief = "Add new reward",
                    aliases = ["AddR", "addreward", "AddReward", "newreward", "addr"]
                    )
    async def NewReward(self, ctx, *args):
        if ctx.message.author.id == Owner_id:
            
            if len(args) == 0:
                await ctx.send("You can't have a reward with no name.")
                return

            rewardName = " ".join(args)

            if thingInList(rewardName, 'rewards_list'):
                await ctx.send(f"'{rewardName}' is already in the list.")
                return

            await ctx.send("Please write a short description of the reward. (Type '#cancel# to cancel this reward)")
            def pred(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel
            rewardDesc = await self.client.wait_for("message", check=pred)

            if rewardDesc.content == "#cancel#":
                await ctx.send("Cancelled the reward-creator.")
                return

            rewardDesc = rewardDesc.content

            await ctx.send("And how many points will it take to redeem this reward? (Type '#cancel#' to cancel this reward)")
            rewardCost = await self.client.wait_for("message", check=pred)

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

            sqlEXE(f"INSERT INTO rewards_list(reward_name, reward_desc, price) VALUES($${capwords(rewardName)}$$, $${rewardDesc}$$, {rewardCost})")

            await ctx.send(f"Reward '{capwords(rewardName)}' succesfully added to list.")
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to delete a reward
    @commands.command(name = "DelReward",
                    description = "Deletes a redeemable reward from the list",
                    brief = "Delete a reward",
                    aliases = ["DelR", "delr", "delreward"]
                    )
    async def DeleteReward(self, ctx, *args):
        if ctx.message.author.id == Owner_id:
            if len(args) == 0:
                await ctx.send("You have to specify a reward to delete.")
            else:
                reward = " ".join(args)
                if thingInList(capwords(reward), 'rewards_list'):
                    sqlEXE(f"DELETE FROM rewards_list WHERE reward_name = '{capwords(reward)}'")
                    await ctx.send("Reward deleted")
                else:
                    await ctx.send("There is no reward by that name")

        else:
            await ctx.send("You don't have permission to use that command.")

    # Command that lists all rewards
    @commands.command(name = "Rewards",
                    description = "List all the redeemable rewards",
                    brief = "List all rewards",
                    aliases = ["rewards"]
                    )
    async def rewards(self, ctx):
        em = discord.Embed(title="Rewards", colour=0xA366FF)
        for record in sqlEXE("SELECT * FROM rewards_list"):
            em.add_field(name=f"{record[0]} | Price: {record[2]}", value=record[1], inline=False)
        
        em.add_field(name="Pick next stream game | Price: 300", value="Use c!games to view the list of games you can vote for.", inline=False)
        em.add_field(name="To redeem", value="Use c!redeem <reward>", inline=False)
        await ctx.send(embed=em)

    # Command to redeem custom rewards
    @commands.command(name = "Redeem",
                    description = "Redeem a reward from the custom list",
                    brief = "Redeem a reward",
                    aliases = ["redeem", "buy", "Buy"]
                    )
    async def redeem(self, ctx, *args):
        initUser(ctx.message.author)
        reward = " ".join(args)

        if not thingInList(reward.title(), 'rewards_list'):
            await ctx.send(f"'{reward.title()}' is not in the list. Use c!rewards to see the list of available rewards.")
            return

        user_points = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{ctx.message.author.id}'")
        user_points = int(str(user_points)[2:-3])

        reward_cost = sqlEXE(f"SELECT price FROM rewards_list WHERE reward_name = '{reward.title()}'")
        reward_cost = int(str(reward_cost)[2:-3])

        if user_points >= reward_cost:
            await ctx.send(f"Are you sure you want to redeem {reward.title()}? (y/n)")
            def pred(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel
            sure = await self.client.wait_for("message", check=pred)

            if sure.content.title() == 'Y':

                sqlEXE(f"UPDATE points_list SET user_points = user_points - {reward_cost}")
                
                await ctx.send(f"Success! Your new balance is {user_points - reward_cost}.")

                Sugoi_Boy = self.client.get_user(Owner_id)
                await Sugoi_Boy.send(f"{ctx.message.author.name} has redeemed {reward.title()}.")
            elif sure.content.title() == 'N':
                await ctx.send("Well why did you invoke this command then? smh")
            else:
                await ctx.send("???")

        else:
            ctx.send("You don't have enough points.")


def setup(bot):
    bot.add_cog(Rewards(bot))