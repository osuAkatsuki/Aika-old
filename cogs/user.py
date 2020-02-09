from typing import Dict, List, Optional, Union
import discord
from discord.ext import commands
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime as d
from requests import get
from random import randint
from json import loads
from time import time
from hashlib import md5, sha1, sha224, sha256, sha384, sha512

from constants import mods
from objects import glob
from helpers import osuHelper

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name        = 'recent',
        description = "Displays information about a user's most recent score.",
        aliases     = ['recentscore'],
        usage       = '<username (default: linked osu!Akatsuki account)> <-rx>',
    )
    async def recent_score_command(self, ctx) -> None:
        messages: List[str] = ctx.message.content.split(' ')[1:]
        username_safe: Optional[str] = None
        rx: bool = False

        if len(messages) > 2: # Should never have more than a username and possibly -rx flag.
            await ctx.send('Invalid syntax. Please use the following syntax:\n> `!recent <username (default: linked osu!Akatsuki account)> <-rx>`')
            return

        for m in messages:
            if m == '-rx': rx = True
            else: username_safe = m

        if not username_safe: # User didn't specify a username; use their connected osu!Akatsuki account if their Discord is linked..
            res: Optional[Dict[str, Union[str, int]]] = glob.db.fetch(
                'SELECT users.username, users.username_safe, users.id FROM discord LEFT JOIN users ON discord.userid = users.id WHERE discord.discordid = %s',
                [ctx.author.id]
            )
            if not res or not res['id']:
                await ctx.send('Please either specify a username, or connect your osu!Akatsuki account with the !linkosu command.\n\n> `!recent <username (default: linked osu!Akatsuki account)> <-rx>`')
                return
        else:
            res = glob.db.fetch('SELECT username, id FROM users WHERE username_safe = %s', [username_safe])
            if not res:
                await ctx.send(f'Sorry, but I could not find a user by that name.\nIf you believe this is a bug, please report it to cmyui(#0425).')
                return

        # Do API request to akatsuki-api.
        r = get(f'http://akatsuki.pw/api/v1/users/scores/recent?id={res["id"]}&l=1&rx={"1" if rx else "0"}', timeout=1.50).json()
        if not r or int(r['code']) != 200:
            await ctx.send('An error occured while attempting to fetch data from the API.\n\nPlease try again later.')
            return

        if not r['scores']:
            await ctx.send("That user doesn't seem to have any scores!")
            return

        score = r['scores'][0] # sanity > a few bytes

        embed = discord.Embed(
            title = score['beatmap']['song_name'],
            description = f'** **', # bad idea to strptime?
            url = f"https://akatsuki.pw/b/{score['beatmap']['beatmap_id']}") \
        .set_image(url = f"https://assets.ppy.sh/beatmaps/{score['beatmap']['beatmapset_id']}/covers/cover.jpg?1522396856") \
        .set_footer(text = f'Score submitted on {"Relax" if score["mods"] & mods.RELAX else "Vanilla"} @ {d.strptime(score["time"], "%Y-%m-%dT%H:%M:%SZ").strftime("%-I:%M%p %b %d %Y")}.') \
        .set_thumbnail(url = glob.config['akatsuki_logo']) \
        .set_author(
            url      = f'https://akatsuki.pw/u/{res["id"]}',
            name     = res['username'],
            icon_url = f'https://a.akatsuki.pw/{res["id"]}') \
        .add_field(
            name  = 'Play Information',
            value = '\n'.join((
                f'**PP**: {score["pp"]:,.2f}pp' if score['pp'] else '**Map completion**: TBA', # TODO: add map completion % to db on score submit so we can use it here!
                f'**Accuracy**: {score["accuracy"]:.2f}%',
                f'**Combo**: {score["max_combo"]}x',
                f'**Mods**: {osuHelper.mods_to_readable(score["mods"])}',
                f'**Passed**: {"True" if score["completed"] > 1 else "False"}'
            )), inline = True) \
        .add_field(
            name  = 'Beatmap Information',
            value = '\n'.join((
                f'**AR**: {score["beatmap"]["ar"]} | **OD**: {score["beatmap"]["od"]}',
                f'**Status**: {osuHelper.ranked_status_to_readable(score["beatmap"]["ranked"])}',
                f'**Max combo**: {score["beatmap"]["max_combo"]}x' if score["beatmap"]["max_combo"] else '**Max combo**: ok so the api literally sent the max combo for the map as "0" idk what u expect me to do',
                f'**Length**: {osuHelper.hitlength_to_readable(score["beatmap"]["hit_length"])}'
                )), inline = True)
        await ctx.send(embed=embed)
        return

    @commands.command(
        name        = 'faq',
        description = 'Frequently asked questions.',
        aliases     = ['info', 'information'],
        usage       = '<callback>'
    )
    async def faq_command(self, ctx) -> None:
        _faq: bool = not ctx.invoked_with.startswith('info')
        callback = ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with) + 1:]

        async def fail() -> None: # Send the available FAQ topics.
            embed = discord.Embed(
                title = f"Available FAQ topics",
                description = 'The following are the currently available FAQ topics.',
                color = 0x00ff00)

            embed.set_footer(
                icon_url = glob.config['akatsuki_logo'],
                text = "For any additional help required, please use the #help channel.")

            for i, v in enumerate(glob.db.fetchall('SELECT topic, title FROM discord_faq WHERE type = %s', [int(_faq)])):
                embed.add_field(name=f'{i + 1}) {v["topic"]}', value=v["title"], inline=False)

            await ctx.send(embed=embed)
            return

        if len(ctx.message.content.split(' ')) == 1:
            await fail()
            return

        res: Optional[Dict[str, Union[str, int, bool]]] = glob.db.fetch(
            'SELECT id, title, content, footer, inline FROM discord_faq WHERE topic = %s AND type = %s',
            [callback, int(_faq)]
        )

        if not res:
            await fail()
            return

        content_len = len(res['content'])
        if content_len > 1024:
            await ctx.send(f'An error occurred while trying to print the faq.\n\n<@285190493703503872> `faq [{res["id"]}] content {content_len - 1024} too long`.')
            return

        embed = discord.Embed(
            title = res['title'],
            description = '** **',
            color = 0x00ff00
        ).add_field(
            name = '** **',
            value = res['content'].format(
                        AKATSUKI_IP    = glob.config['akatsuki_ip'],
                        COMMAND_PREFIX = ctx.prefix
                    ),
            inline = res['inline']
        ).set_thumbnail(url=glob.config['akatsuki_logo'])

        if res['footer']:
            embed.set_footer(icon_url='', text=res['footer'])

        await ctx.send(embed=embed)
        return


    @commands.command(
        name        = 'rewrite',
        description = "Aika's rewrite information.",
        aliases     = ['stats', 'botinfo', 'aika', 'cmyui', 'apply', 'akatsuki']
    )
    async def rewrite_info(self, ctx) -> None:
        await ctx.send(f'**Aika is currently undergoing a rewrite, and the {ctx.invoked_with} command has not yet been implemented.**\n'
                        '\n'
                        'Repository: https://github.com/osuAkatsuki/Aika.\n'
                        'Sorry for the inconvenience!')
        return


    @commands.command(
        name        = 'nsfw',
        description = 'Grants access to the NSFW channels of Akatsuki.',
        aliases     = ['nsfwaccess']
    )
    async def nsfw_access(self, ctx) -> None: # TODO: toggle or check if already has access
        # Check if user already has NSFW Access.
        if any(i.name == 'NSFW Access' for i in ctx.author.roles):
            return

        # Story time!
        # We had the NSFW channel public for a long time, and with that came a lot
        # of issues, even some resulting in emails from the discord team warning us
        # that we had to delete specific images or the server itself would be deleted
        # within 24 hours. Our solution was to make the NSFW channels a donation perk,
        # not only to reduce the amount of members or possible offenders who may break
        # discord TOS, but also because the server grew to an extent that I personally
        # don't think we should have a public NSFW channel; it seems quite unprofessional.
        if not any(r.name in ('Supporter', 'Premium') for r in ctx.author.roles):
            return

        await ctx.author.add_roles(discord.utils.get(ctx.message.guild.roles, name='NSFW Access'))
        await ctx.message.delete()
        return


    @commands.command(
        name        = 'time',
        description = 'Returns the current UNIX time.',
        aliases     = ['unix', 'unixtime']
    )
    async def current_unixtime(self, ctx) -> None:
        await ctx.send(f'Current UNIX timestamp: `{int(time.time())}`') # int cast to round lol
        return


    @commands.command(
        name        = 'ftcm',
        description = 'Feet & inches > cm. So all our Americans can understand us metric boys.',
        aliases     = ['fttocm', 'america']
    )
    async def ft_to_cm(self, ctx) -> None: # TODO both inches and ft alone
        ft_in = ctx.message.content.split(' ')[1]

        if any(i not in "1234567890'" for i in ft_in):
            await ctx.send("Invalid characters.\nValid: `1234567890'`")
            return

        if "'" in ft_in:
            if len(ft_in.split("'")) != 2:
                await ctx.send('Invalid format.')
                return

            feet, inches = [int(i) for i in ft_in.split("'")]

            await ctx.send(f'`{feet}ft {inches}in` -> `{((feet * 12) + inches) * 2.54:.2f}cm`')

        else:
            await ctx.send(f'`{int(ft_in)}ft` -> `{int(ft_in) * 30.48:.2f}cm`')

        return

    @commands.command(
        name        = 'hash',
        description = 'Returns the current MD5 of the input string.',
        aliases     = ['encrypt']
    )
    async def hash_string(self, ctx) -> None:
        hash_type = ctx.message.content.split(' ')[1].lower()
        if hash_type not in ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'):
            await ctx.send(f'{hash_type} is not a supported algorithm.')
            return

        string = ' '.join(ctx.message.content.split(' ')[2:]).encode('utf-8')

        if   hash_type == 'md5':    r = md5   (string)
        elif hash_type == 'sha1':   r = sha1  (string)
        elif hash_type == 'sha224': r = sha224(string)
        elif hash_type == 'sha256': r = sha256(string)
        elif hash_type == 'sha384': r = sha384(string)
        elif hash_type == 'sha512': r = sha512(string)

        await ctx.send(f'{hash_type.upper()}: `{r.hexdigest()}`')
        return


    @commands.command(
        name        = 'roll',
        description = 'Rolls a random number between 1-100.'
    )
    async def roll(self, ctx) -> None:
        await ctx.send(f'{ctx.author} rolled a {randint(1, 100)}!')
        return


    @commands.command(
        name        = 'linkosu',
        description = 'Links your discord account to your osu!Akatsuki account.',
        aliases     = ['linkdiscord']
    )
    async def link_osu_account(self, ctx) -> None:
        res = glob.db.fetch('SELECT userid FROM discord WHERE discordid = %s', [ctx.author.id])
        if res and res['userid']:
            await ctx.send(f"Your account is already linked to https://akatsuki.pw/u/{res['userid']}.\nIf you'd like to link your Discord to another account, please contact <@{glob.config['discord_owner_userid']}>.")
            return
        elif res:
            s = "It seems as if you've already initiated the linking process."
        else:
            glob.db.execute('INSERT INTO discord (id, userid, discordid) VALUES (NULL, 0, %s)', [ctx.author.id])
            s = 'Linking process initiated.'

        await ctx.send(f'{s}\nPlease enter the following command on the osu!Akatsuki server to `Aika`, or in #osu to complete verification.\n> `!linkdiscord {ctx.author.id}`')
        return


    @commands.command(
        name        = 'syncroles',
        description = 'Syncs your roles from the osu!Akatsuki server to the Discord.'
    )
    async def sync_osu_roles(self, ctx) -> None:
        res = glob.db.fetch('SELECT privileges FROM users LEFT JOIN discord ON users.id = discord.userid WHERE discordid = %s', [ctx.author.id]) # broke?
        if not res:
            await ctx.send("It doesn't seem like your Discord is linked to an osu!Akatsuki account.\nYou can link one by using the `!linkosu` command.")
            return

        if res['privileges'] & 8388608: role = discord.utils.get(ctx.message.guild.roles, name='Premium') # Premium
        elif res['privileges'] & 4: role = discord.utils.get(ctx.message.guild.roles, name='Supporter') # Supporter
        else:
            await ctx.send("I couldn't find any roles to sync!\n\nIf you have recently donated and are trying to claim your discord perks, please contact <@285190493703503872> directly.")
            return

        await ctx.author.add_roles(role)
        await ctx.send('Your roles have been synced.')
        return


    @commands.command(
        name        = 'rawfrom',
        description = 'Returns the amount of raw PP you would get for a specific amount of PP.',
        aliases = ('ppfrom',)
    )
    async def rawfrom_command(self, ctx) -> None:
        messages: List[str] = ctx.message.content.split(' ')[1:]
        username_safe: Optional[str] = None
        pp: float = 0.
        rx: bool = False

        if len(messages) > 3: # Should never have more than a username and possibly -rx flag.
            await ctx.send('Invalid syntax. Please use the following syntax:\n> `!ppfrom <username (default: linked osu!Akatsuki account)> <-rx>`')
            return

        for m in messages:
            if m == '-rx': rx = True
            else:
                try: pp = float(m)
                except:
                    if username_safe:
                        await ctx.send('Invalid syntax. Please use the following syntax:\n> `!ppfrom <username (default: linked osu!Akatsuki account)> <-rx>`')
                        return
                    username_safe = m
                    pp = 0.

        if not pp or pp < 0 or pp > 3000:
            await ctx.send('HUH')
            return

        if not username_safe: # User didn't specify a username; use their connected osu!Akatsuki account if their Discord is linked..
            res: Optional[Dict[str, Union[str, int]]] = glob.db.fetch(
                'SELECT users.id FROM discord LEFT JOIN users ON discord.userid = users.id WHERE discord.discordid = %s',
                [ctx.author.id]
            )
            if not res or not res['id']:
                await ctx.send('Please either specify a username, or connect your osu!Akatsuki account with the !linkosu command.\n\n> `!recent <username (default: linked osu!Akatsuki account)> <-rx>`')
                return
        else:
            res = glob.db.fetch('SELECT id FROM users WHERE username_safe = %s', [username_safe])
            if not res:
                await ctx.send(f'Sorry, but I could not find a user by that name.\nIf you believe this is a bug, please report it to cmyui(#0425).')
                return

        scores = [row['pp'] for row in glob.db.fetchall(
            f'SELECT pp FROM scores{"_relax" if rx else ""} LEFT JOIN(beatmaps) USING(beatmap_md5) '
            'WHERE userid = %s AND play_mode = %s AND completed = 3 AND ranked >= 2 AND disable_pp = 0 AND pp IS NOT NULL '
            'ORDER BY pp DESC LIMIT 125',
            (res['id'], 0)) # TODO: allow for other modes
        ]

        total: List[int] = [0, 0]

        # Current total pp
        total[0] = sum(round(round(_pp) * 0.95 ** i) for i, _pp in enumerate(scores))

        # Add the new score and re-sort the List.
        scores.append(pp)
        scores.sort(reverse=True)

        # New total pp after getting that amount of pp.
        total[1] = sum(round(round(_pp) * 0.95 ** i) for i, _pp in enumerate(scores))

        # Return our answer.
        await ctx.send(f'<@{ctx.author.id}> - A **{pp}pp** score would give {username_safe if username_safe else "you"} **{total[1] - total[0]}pp** raw.')
        return


    @commands.command(
        name        = 'ar',
        description = 'Returns AR with the specified AR and mods.'
    )
    async def calculate_ar(self, ctx) -> None:
        def check(m: discord.Message) -> bool:
            return m.channel == ctx.channel and m.author == ctx.author

        def ApplyModsToDifficulty(difficulty: float, hardRockFactor: float, mods: int) -> float:
            if 'EZ' in mods: difficulty = max(0, difficulty / 2)
            if 'HR' in mods: difficulty = min(10, difficulty * hardRockFactor)
            return difficulty

        def MapDifficultyRange(difficulty: float, min: float, mid: float, max: float, mods: int) -> float:
            difficulty = ApplyModsToDifficulty(difficulty, 1.4, mods)

            if difficulty > 5: return mid + (max - mid) * (difficulty - 5) / 5
            if difficulty < 5: return mid - (mid - min) * (5 - difficulty) / 5
            return mid

        await ctx.send('What AR would you like to calculate?')
        ar: Union[discord.Message, float, str] = await self.bot.wait_for('message', check=check)

        try:
            ar = float(ar.content)
            if ar > 10.0 or ar < 0.0: raise ValueError # Check for invalid ARs.
        except ValueError:
            await ctx.send('Please use a valid AR.')
            return

        await ctx.send('What mod(s) would you like to calculate with? (None is fine!)')
        _mods: Union[discord.Message, str] = await self.bot.wait_for('message', check=check)
        _mods = _mods.content.lower()

        if ('ht' in _mods and 'dt' in _mods) or ('hr' in _mods and 'ez' in _mods):
            await ctx.send('Please use valid mods (EZ/HR/DT/HT).')
            return

        mods: List[str] = []

        if 'ez' in _mods: mods.append('EZ') # Add EZ to mods.
        if 'hr' in _mods: mods.append('HR') # Add HR to mods.
        if 'dt' in _mods: mods.append('DT') # Add DT to mods.
        if 'ht' in _mods: mods.append('HT') # Add HT to mods.

        # Calculate the ms of the AR.
        ar_ms = round(MapDifficultyRange(ar, 1800.0, 1200.0, 450.0, mods))

        # Calculate ms with speed changing mods.
        ar_ms /= 1.5 if 'DT' in mods else 0.75

        # Calculate AR. Round to 3 decimal places.
        ar = f'{round(-(ar_ms - 1800.0) / 120.0 if ar_ms > 1200.0 else -(ar_ms - 1200.0) / 150.0 + 5.0, 3):.3f}'
        await ctx.send(f'AR{ar} ({ar_ms}ms) | Mods: {", ".join(mods) if mods else "None"}')
        return


def setup(bot: commands.Bot):
    bot.add_cog(User(bot))
