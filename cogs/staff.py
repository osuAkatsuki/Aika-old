from typing import List, Union
from discord.ext import commands
from datetime import datetime as d

class Staff(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name        = 'prune',
        description = 'Prune messages from the current channel.',
        aliases     = ['p'],
        usage       = '<message-count> (Max 1000)'
    )
    async def prune_command(self, ctx) -> None:
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(content='You do not have sufficient privileges for this command.')
            return

        text: List[str] = ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with) + 1:]

        if text == '':
            await ctx.send(content='You have specified an invalid number of arguments for this command.')
        else:
            message_count: Union[str, int] = text.split(' ')[0]

            if not message_count.isdigit():
                await ctx.send(content='You have used the incorrect syntax for this command.')
            else:
                message_count = int(message_count)

                if message_count <= 1000 and message_count >= 1:
                    deleted: List[discord.Message] = await ctx.channel.purge(limit=message_count + 1 if message_count != 1000 else message_count)

                    await ctx.send(content=f'Successfully pruned {len(deleted) - 1} message{"s" if len(deleted) - 1 > 1 else ""}.')
                else:
                    await ctx.send(content='You have used the incorrect syntax for this command.')

        return


def setup(bot: commands.Bot):
    bot.add_cog(Staff(bot))