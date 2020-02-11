import asyncio
import discord
import psycopg2

from cogs.utility import thingInList, sqlEXE
from discord.ext import commands
from discord.ext.commands import Cog


class Fun(Cog):
    def __init__(self, client):
        self.client = client

    # Command to hug people
    @commands.command(name = "Hug",
                    description = "Show your affection to someone",
                    brief = "Hug someone",
                    aliases = ["hug", "love", "Love"])
    async def hug(self, ctx, person=None):
        user = ctx.message.author.display_name
        
        if person:
            await ctx.send(f"{user} hugged {person}!")
        else:
            await ctx.send(f"{user} hugged themself!")

def setup(bot):
    bot.add_cog(Fun(bot))