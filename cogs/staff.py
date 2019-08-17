from discord.ext import commands
from datetime import datetime as d

# Error response strings.
INSUFFICIENT_PRIVILEGES  = "You do not have sufficient privileges for this command."
INCORRECT_SYNTAX         = "You have used the incorrect syntax for this command."
INCORRECT_NUMBER_OF_ARGS = "You have specified an invalid number of arguments for this command."

class Staff(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name        = "prune",
        description = "Prune messages from the current channel.",
        aliases     = ['p'],
        usage       = "<message-count> (Max 1000)"
    )
    async def prune_command(self, ctx):
        if not ctx.message.author.guild_permissions.manage_messages:
            await ctx.send(content=INSUFFICIENT_PRIVILEGES)
            return

        text = ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with) + 1:]

        if text == '':
            await ctx.send(content=INCORRECT_NUMBER_OF_ARGS)
        else:
            message_count = text.split(' ')[0]

            if not message_count.isdigit():
                await ctx.send(content=INCORRECT_SYNTAX)
            else:
                message_count = int(message_count)

                if message_count <= 1000 and message_count >= 1:
                    deleted = await ctx.channel.purge(limit=message_count + 1 if message_count != 1000 else message_count)

                    await ctx.send(content=f"Successfully pruned {len(deleted) - 1} message{'s' if len(deleted) - 1 > 1 else ''}.")
                else:
                    await ctx.send(content=INCORRECT_SYNTAX)

        return


def setup(bot):
    bot.add_cog(Staff(bot))