import discord
from discord.ext import commands
from datetime import datetime as d
import mysql.connector
from mysql.connector import errorcode
import time
import hashlib
import re

# Error response strings.
INSUFFICIENT_PRIVILEGES  = "You do not have sufficient privileges for this command."
INCORRECT_SYNTAX         = "You have used the incorrect syntax for this command."
INCORRECT_NUMBER_OF_ARGS = "You have specified an invalid number of arguments for this command."

# For FAQ
AKATSUKI_IP_ADDRESS      = "51.79.17.191"     # Akatsuki's osu! server IP.

# Akatsuki's logo.
# To be used mostly for embed thumbnails.
AKATSUKI_LOGO            = "https://akatsuki.pw/static/logos/logo.png"

# Initalize values as Nonetype for now.
SQL_HOST, SQL_USER, SQL_PASS, SQL_DB = [None] * 4

# Config
config = open('config.ini', 'r')
config_contents = config.read().split("\n")
for line in config_contents:
    line = line.split("=")
    if line[0].strip() == "SQL_HOST": # IP Address for SQL.
        SQL_HOST = line[1].strip()
    elif line[0].strip() == "SQL_USER": # Username for SQL.
        SQL_USER = line[1].strip()
    elif line[0].strip() == "SQL_PASS": # Password for SQL.
        SQL_PASS = line[1].strip()
    elif line[0].strip() == "SQL_DB": # DB name for SQL.
        SQL_DB = line[1].strip()
    else: # Config value is unknown. continue iterating anyways.
        continue

# MySQL
try:
    cnx = mysql.connector.connect(
        user       = SQL_USER,
        password   = SQL_PASS,
        host       = SQL_HOST,
        database   = SQL_DB,
        autocommit = True)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your username or password.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist.")
    else:
        print(err)
else:
    SQL = cnx.cursor()

class User(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name        = "faq",
        description = "Frequently asked questions.",
        aliases     = ['info', 'information'],
        usage       = "<callback>"
    )
    async def faq_command(self, ctx):
        text = ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with) + 1:]

        # 0 = info : 1 = faq
        command_type = 0 if ctx.invoked_with.startswith("info") else 1

        callback = text.split(" ")[0]

        SQL.execute("SELECT * FROM discord_faq WHERE topic = %s AND type = %s", [callback, command_type])
        result = SQL.fetchone()

        if callback == "" or result is None:
            SQL.execute("SELECT id, topic, title FROM discord_faq WHERE type = %s", [command_type])

            faq_db = SQL.fetchall()

            faq_list = ""
            for idx, val in enumerate(faq_db):
                faq_list += f"{idx + 1}. {val[1]}{' ' * (12 - len(val[1]))}|| {val[2]}\n"

            await ctx.send(f"{'I could not find a topic by that name.' if len(callback) else ''}\n```{faq_list.replace('`', '')}```")
        else:
            embed = discord.Embed(title=result[2], description='** **', color=0x00ff00)
            embed.set_thumbnail(url=AKATSUKI_LOGO)
            embed.add_field(
                name   = "** **",
                value  = result[3]
                            .replace("{AKATSUKI_IP}", AKATSUKI_IP_ADDRESS)
                            .replace("{COMMAND_PREFIX}", ctx.prefix),
                inline = result[5])

            if result[4] is not None:
                embed.set_footer(icon_url='', text=result[4])
            await ctx.send(embed=embed)
        return

    @commands.command(
        name        = "rewrite",
        description = "Aika's rewrite information.",
        aliases     = ['recent', 'stats', 'linkosu', 'botinfo', 'aika', 'cmyui', 'apply', 'akatsuki']
    )
    async def rewrite_info(self, ctx):
        await ctx.send(f"**Aika is currently undergoing a rewrite, and the {ctx.invoked_with} command has not yet been implemented.**\n"
                        "\n"
                        "Repository: https://github.com/osuAkatsuki/Aika.\n"
                        "Sorry for the inconvenience!")
        return

    @commands.command(
        name        = "nsfw",
        description = "Grants access to the NSFW channels of Akatsuki.",
        aliases     = ['nsfwaccess']
    )
    async def nsfw_access(self, ctx): # TODO: toggle or check if already has access
        def check(m):
            return m.channel == ctx.message.channel and m.author == ctx.message.author

        await ctx.send("Please type `Yes` to confirm you are over the age of 18.\n"
                       "If you falsely accept this, you will be permanently banned from the discord.")

        msg = await self.bot.wait_for("message", check=check)
        resp = msg.content.lower() == "yes"
        if resp:
            await ctx.author.add_roles(discord.utils.get(ctx.message.guild.roles, name="NSFW Access"))
            await ctx.send("You should now have access to the NSFW channels.")
        return

    @commands.command(
        name        = "time",
        description = "Returns the current UNIX time.",
        aliases     = ['unix', 'unixtime']
    )
    async def current_unixtime(self, ctx):
        await ctx.send(f"Current UNIX timestamp: `{int(time.time())}`") # int cast to round lol
        return

    @commands.command(
        name        = "hash",
        description = "Returns the current MD5 of the input string.",
        aliases     = ['encrypt']
    )
    async def hash_string(self, ctx):
        hash_type = ctx.message.content.split(' ')[1].lower()
        if hash_type not in ("md5", "sha1", "sha224", "sha256", "sha384", "sha512"):
            await ctx.send(f"{hash_type} is not a supported algorithm.")
            return

        string = ''.join(ctx.message.content.split(' ')[2:]).encode('utf-8')

        if hash_type == "md5":
            r = hashlib.md5(string)
        elif hash_type == "sha1":
            r = hashlib.sha1(string)
        elif hash_type == "sha224":
            r = hashlib.sha224(string)
        elif hash_type == "sha256":
            r = hashlib.sha256(string)
        elif hash_type == "sha384":
            r = hashlib.sha384(string)
        elif hash_type == "sha512":
            r = hashlib.sha512(string)

        await ctx.send(f"{hash_type.upper()}: `{r.hexdigest()}`")
        return

    @commands.command(
        name        = "round",
        description = "Returns arg0 rounded to arg1 decimal places."
    )
    async def round_number(self, ctx):
        fuckpy = None
        if re.match("^\d+?\.\d+?$", ctx.message.content.split(' ')[1]) is None:
            await ctx.send("Why are your trying to round that?")
            return

        if len(ctx.message.content.split(' ')[1].split(".")[1]) < int(ctx.message.content.split(' ')[2]): # User specified sig digits > actual amt of sig digits
            fuckpy = len(ctx.message.content.split(' ')[1].split(".")[1]) # use actual amt of sig digits

        await ctx.send(f"Rounded value (decimal places: {ctx.message.content.split(' ')[2] if not fuckpy else fuckpy}): `{round(float(ctx.message.content.split(' ')[1]), int(ctx.message.content.split(' ')[2]))}`")
        return

    @commands.command(
        name        = "ar",
        description = "Returns AR with the specified AR and mods."
    )
    async def calculate_ar(self, ctx):
        def check(m):
            return m.channel == ctx.message.channel and m.author == ctx.message.author

        def ApplyModsToDifficulty(difficulty, hardRockFactor, mods):
            if "EZ" in mods:
                difficulty = max(0, difficulty / 2)
            if "HR" in mods:
                difficulty = min(10, difficulty * hardRockFactor)
            return difficulty

        def MapDifficultyRange(difficulty, min, mid, max, mods):
            difficulty = ApplyModsToDifficulty(difficulty, 1.4, mods)

            if difficulty > 5:
                return mid + (max - mid) * (difficulty - 5) / 5
            if difficulty < 5:
                return mid - (mid - min) * (5 - difficulty) / 5
            return mid

        await ctx.send("What AR would you like to calculate?")
        ar = await self.bot.wait_for("message", check=check)

        try:
            ar = float(ar.content)
            if ar > 10 or ar < 0: raise ValueError
        except ValueError:
            await ctx.send("Please use a valid AR.")
            return

        await ctx.send("What mod(s) would you like to calculate with? (None is fine!)")
        _mods = await self.bot.wait_for("message", check=check)

        try:
            _mods = _mods.content.lower()
        except ValueError:
            await ctx.send("Please use valid mods (EZ/HR/DT/HT).")
            return

        mods = []

        if "ez" in _mods: mods.append("EZ") # Add EZ to mods.
        if "hr" in _mods: mods.append("HR") # Add HR to mods.
        if "dt" in _mods: mods.append("DT") # Add DT to mods.
        if "ht" in _mods: mods.append("HT") # Add HT to mods.

        ar_ms = round(MapDifficultyRange(ar, 1800, 1200, 450, mods))

        # Calculate ms with speed changing mods.
        if "DT" in mods: ar_ms /= 1.5
        if "HT" in mods: ar_ms *= 1.5

        # Calculate AR. Round to 3 decimal places.
        ar = round(-(ar_ms - 1800.0) / 120.0 if ar_ms > 1200.0 else -(ar_ms - 1200.0) / 150.0 + 5.0, 3)
        await ctx.send(f"AR{ar} ({ar_ms}ms){f' [Mods: {mods}]' if mods != [] else ''}")
        return

def setup(bot):
    bot.add_cog(User(bot))