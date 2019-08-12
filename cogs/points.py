import asyncio
import discord
import psycopg2

from cogs.utility import thingInList, sqlEXE, initUser, Owner_id
from discord.ext import commands
from discord.ext.commands import Cog

class Points(Cog):
    def __init__(self, client):
        self.client = client

    # Command to give a user points
    @commands.command(name = "Award",
                    description = "Award a member x points",
                    brief = "Award points",
                    aliases = ["award", "reward", "givepoints", "GivePoints", "Reward"]
                    )
    async def award(self, ctx, member : discord.Member, points):
        try:
            points = int(points)
            if points < 1:
                raise ValueError
        except ValueError:
            await ctx.send("That's not a valid argument (Must be an integer above 0).")
            return

        if ctx.message.author.id in Owner_id:
            initUser(member)
            sqlEXE(f"UPDATE points_list SET user_points = user_points + {points} WHERE user_id = '{str(member.id)}'")     
            await ctx.send(f"{member.display_name} has been awarded {points} point(s).")
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to take away points
    @commands.command(name = "Punish",
                    description = "Take x points away from a member",
                    brief = "Take points",
                    aliases = ["punish", "take", "takepoints", "TakePoints", "Take"]
                    )
    async def punish(self, ctx, member : discord.Member, points):
        try:
            points = int(points)
            if points < 1:
                raise ValueError
        except ValueError:
            await ctx.send("That's not a valid argument (Must be an integer above 0).")
            return

        if ctx.message.author.id in Owner_id:
            initUser(member)
            sqlEXE(f"UPDATE points_list SET user_points = user_points - {points} WHERE user_id = '{str(member.id)}'")     
            await ctx.send(f"{member.display_name} has had {points} point(s) taken.")
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to check user's points
    @commands.command(name = "Points",
                    description = "Check how many points a user has",
                    brief = "Check points",
                    aliases =["points", 'check', 'Check']
                    )
    async def points(self, ctx, member : discord.Member = None):
        if member:
            initUser(member)
            data = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{str(member.id)}'")
            await ctx.send(f"{member.display_name} has {str(data)[2:-3]} points(s).")

        else:
            initUser(ctx.message.author)
            data = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{str(ctx.message.author.id)}'")
            await ctx.send(f"<@{ctx.message.author.id}>, you have {str(data)[2:-3]} points(s).")

    # Command to reset all users' points
    @commands.command(name = "ResetPoints",
                    description = "Sets all users' points to 0",
                    brief = "Reset all points",
                    aliases = ["resetpoints"]
                    )
    async def resetPoints(self, ctx):
        if ctx.message.author.id in Owner_id:
            await ctx.send("This will set all users' points to 0. Are you sure? (y/n)")
            def pred(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel
            sure = await self.client.wait_for("message", check=pred)

            if sure.content == 'y':
                sqlEXE("UPDATE points_list SET user_points = 0")
                await ctx.send("Successfully reset all points.")

            elif sure.content == "n":
                await ctx.send("Then why did you invoke this command? smh")

            else:
                return
        else:
            await ctx.send("You don't have permission to use that command.")

    # Command to claim daily points
    @commands.command(name = "daily",
                    description = "Collect your daily points",
                    brief = "Daily points",
                    aliases = ["Daily"])
    @commands.cooldown(1, 60*60*24, commands.BucketType.user)
    async def daily(self, ctx):
        sqlEXE(f"UPDATE points_list SET user_points = user_points + 100 WHERE user_id = '{str(ctx.message.author.id)}';")
        user_points = sqlEXE(f"SELECT user_points FROM points_list WHERE user_id = '{ctx.message.author.id}'")
        user_points = int(str(user_points)[2:-3])

        await ctx.send(f"Success! Your new balance is {user_points}.")


def setup(bot):
    bot.add_cog(Points(bot))
