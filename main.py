import discord
from discord import NotFound
from discord.ext import commands

from karma_card.createcard import create_card
import topcmds as top
import onreaction as react
import customise as cus
import helpcmds
import db

from tabulate import tabulate

import sqlite3
import operator
import datetime

KEY = open("keys.txt", "r").readline().split("=")[1]

debug_mode = False
bot = commands.Bot(command_prefix="$")
bot.remove_command("help")

conn = sqlite3.connect("votecount.db")
c = db.conn.cursor()
print("Database initialised")

sql_query = f"""
CREATE TABLE IF NOT EXISTS user_data (
USER_ID         INTEGER (0, 18),
KARMA_TEMPLATE  TEXT    (0, 20),
KARMA_COLOUR    TEXT    (0, 5),
GIVEN_TEMPLATE  TEXT    (0, 20),
GIVEN_COLOUR    TEXT    (0, 5)
);"""
db.c.execute(sql_query)


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@bot.event
async def on_guild_join(guild):
    sql_query = f"""
    CREATE TABLE IF NOT EXISTS data_{guild.id} (
    USER_ID   INTEGER (0, 18),
    UPVOTES   INTEGER (0, 8),
    DOWNVOTES INTEGER (0, 8),
    UPVOTES_GIVEN   INTEGER (0, 8),
    DOWNVOTES_GIVEN INTEGER (0, 8),
    BLACKLISTED INTEGER (0, 1)
    );"""
    db.c.execute(sql_query)

    sql_query = f"""
    CREATE TABLE IF NOT EXISTS settings_{guild.id} (
    UPVOTE_ID   STRING (0, 56),
    RT_ID   STRING (0, 56),
    DOWNVOTE_ID STRING (0, 56),
    TIMELIMIT INTEGER
    );"""
    db.c.execute(sql_query)

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send("Hello! To get started, type out your desired reaction emotes as such:\n$setup <:upvote:452121917462151169> <:downvote:451890347761467402> <:rt:451882250884218881>\nIf you don't have an RT emote, just replace it with 'NONE'")
            break


@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
@bot.command()
async def debug(ctx):
    global debug_mode
    try:
        status = ctx.message.content.split(" ")[1]
    except IndexError:
        await ctx.message.channel.send(f"Debug mode is {debug_mode}")
    if status == "0":
        debug_mode = False
        await ctx.message.channel.send("Debug mode disabled")
    elif status == "1":
        debug_mode = True
        await ctx.message.channel.send("Debug mode enabled")


@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
@bot.command()
async def setup(ctx):
    upvote_id = ctx.message.content.split(" ")[1]
    downvote_id = ctx.message.content.split(" ")[2]
    rt_id = ctx.message.content.split(" ")[3]

    sql_query = f"DELETE FROM settings_{ctx.guild.id}"
    db.c.execute(sql_query)
    db.conn.commit()

    sql_query = f"""
    INSERT OR REPLACE INTO settings_{ctx.guild.id}
    VALUES('{upvote_id}', '{rt_id}', '{downvote_id}', "NONE"
    );"""
    db.c.execute(sql_query)
    db.conn.commit()

    await ctx.message.channel.send("Your reaction emotes have successfully been set!")


@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
@bot.command()
async def blacklist_add(ctx):
    if len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        sql_query = f"""
        UPDATE data_{ctx.message.guild.id}
        SET BLACKLISTED = 1
        WHERE USER_ID = {user_id}
        """
        db.c.execute(sql_query)
        db.conn.commit()
        await ctx.message.channel.send("User has been added to the blacklist.")


@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
@bot.command()
async def blacklist_remove(ctx):
    if len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        sql_query = f"""
        UPDATE data_{ctx.message.guild.id}
        SET BLACKLISTED = 0
        WHERE USER_ID = {user_id}
        """
        db.c.execute(sql_query)
        db.conn.commit()
        await ctx.message.channel.send("User has been removed from the blacklist.")


@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
@bot.command()
async def blacklist_view(ctx):
    message_string = ""
    sql_query = f"""
    SELECT USER_ID
    FROM data_{ctx.message.guild.id}
    WHERE BLACKLISTED = 1
    """
    db.c.execute(sql_query)
    user_data = db.c.execute(sql_query).fetchall()
    if debug_mode is True: print(user_data)

    for user_id in user_data:
        user = await bot.fetch_user(user_id[0])
        message_string += f"{user.name}#{user.discriminator}\n"

    try:
        await ctx.message.channel.send(message_string)
    except discord.errors.HTTPException:
        await ctx.message.channel.send("Blacklist is empty!")


@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
@bot.command()
async def set_timelimit(ctx):
    time_limit = ctx.message.content.split(" ")[1]
    sql_query = f"""UPDATE settings_{ctx.message.guild.id}
                    SET TIMELIMIT = "{time_limit}"
                """
    db.c.execute(sql_query)
    db.conn.commit()
    await ctx.message.channel.send(f"The bot will now only count reactions for messages that are {time_limit} seconds old or less.")


@bot.command()
async def customise(ctx):
    if len(ctx.message.content.split(" ")) == 4:
        card_type = ctx.message.content.split(" ")[1].lower()
        template_name = ctx.message.content.split(" ")[2].lower()
        dark_light = ctx.message.content.split(" ")[3].lower()

        try:
            await ctx.message.channel.send(cus.validate(card_type, dark_light))
        except Exception:
            pass

    else:
        embed = helpcmds.help("$help customise", ctx.message)
        await ctx.message.channel.send(embed=embed)
        return

    sql_query = f"SELECT * FROM user_data WHERE USER_ID = {ctx.message.author.id}"
    user_data = db.c.execute(sql_query).fetchone()

    if user_data is None:   # blacksea dark & space light are defaults
        if card_type == "karma":
            cus.set_card_type(ctx.message.author.id, template_name, dark_light, "space", "light")
        elif card_type == "given":
            cus.set_card_type(ctx.message.author.id, "blacksea", "dark", template_name, dark_light)

    else:
        if card_type == "karma":
            cus.update_card_type(ctx.message.author.id, template_name, dark_light, "KARMA")
        elif card_type == "given":
            cus.update_card_type(ctx.message.author.id, template_name, dark_light, "GIVEN")

    await ctx.message.channel.send(f"Your {card_type} card now has the '{template_name}' image with {dark_light} text.")


@bot.command()
async def help(ctx):
    try:
        embed, img = helpcmds.help(ctx.message.content.lower(), ctx.message, img=None)
    except Exception:
        embed = helpcmds.help(ctx.message.content.lower(), ctx.message, img=None)
        img = None

    if img is None:
        await ctx.message.channel.send(embed=embed)
    else:
        await ctx.message.channel.send(embed=embed, file=img)
    return


@bot.command()
async def karma(ctx):
    if len(ctx.message.content.split(" ")) == 1:
        user_id = ctx.message.author.id
        username = ctx.message.author.name
        avatar = ctx.message.author.avatar_url
    elif len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        user = ctx.message.guild.get_member(user_id)
        username = user.name
        avatar = user.avatar_url

    sql_query = f"SELECT KARMA_TEMPLATE, KARMA_COLOUR FROM user_data WHERE USER_ID = {user_id}"
    try:
        karma_template, karma_colour = db.c.execute(sql_query).fetchone()
    except TypeError:
        karma_template, karma_colour = "space", "light"
    sql_query = f"SELECT * FROM data_{ctx.message.guild.id} WHERE USER_ID = {user_id}"
    user_data = db.c.execute(sql_query).fetchone()
    if user_data is None:
        user_data = [0, 0, 0]

    create_card(user_data[1], user_data[2], username, avatar, karma_template, karma_colour)
    await ctx.message.channel.send(file=discord.File("card.png"))


@bot.command()
async def given(ctx):
    if len(ctx.message.content.split(" ")) == 1:
        user_id = ctx.message.author.id
        username = ctx.message.author.name
        avatar = ctx.message.author.avatar_url
    elif len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        user = ctx.message.guild.get_member(user_id)
        username = user.name
        avatar = user.avatar_url

    sql_query = f"SELECT GIVEN_TEMPLATE, GIVEN_COLOUR FROM user_data WHERE USER_ID = {user_id}"
    try:
        given_template, given_colour = db.c.execute(sql_query).fetchone()
    except TypeError:
        given_template, given_colour = "blacksea", "dark"

    sql_query = f"SELECT * FROM data_{ctx.message.guild.id} WHERE USER_ID = {user_id}"
    user_data = db.c.execute(sql_query).fetchone()
    if user_data is None:
        user_data = [0, 0, 0, 0, 0]

    create_card(user_data[3], user_data[4], username, avatar, given_template, given_colour)
    await ctx.message.channel.send(file=discord.File("card.png"))


@bot.command()
async def top_karma(ctx):
    final = []
    finalstring = ""
    count = 0

    message_content, total = top.get_total_and_message(str(ctx.message.content))

    try:
        guild_id = ctx.message.guild.id
        user_data = top.get_user_data(message_content, guild_id, "UPVOTES", "DOWNVOTES")
    except Exception as e:
        if debug_mode is True: print(e)
        return

    user_data = top.create_sorted_list(user_data, "top")

    for user in user_data:
        if count == total:
            break

        if user[2] == 0 and user[3] == 0:
            continue

        ratio = top.get_ratio(user[2], user[3])

        try:
            user_object = ctx.message.guild.get_member(user[0])
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", user_object.name, ratio])
        except AttributeError:
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", f"<@{user[0]}>", ratio])
        finally:
            count += 1

    finalstring = top.format_codeblock(tabulate(final))

    try:
        if total > 15:
            await ctx.message.author.send(finalstring)
        else:
            await ctx.message.channel.send(finalstring)
    except discord.HTTPException as e:
        await ctx.message.channel.send(f"`{e}`")


@bot.command()
async def bottom_karma(ctx):
    final = []
    finalstring = ""
    count = 0

    message_content, total = top.get_total_and_message(str(ctx.message.content))

    try:
        guild_id = ctx.message.guild.id
        user_data = top.get_user_data(message_content, guild_id, "UPVOTES", "DOWNVOTES")
    except Exception as e:
        if debug_mode is True: print(e)
        return

    user_data = top.create_sorted_list(user_data, "bottom")

    for user in user_data:
        if count == total:
            break

        if user[2] == 0 and user[3] == 0:
            continue

        ratio = top.get_ratio(user[2], user[3])

        try:
            user_object = ctx.message.guild.get_member(user[0])
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", user_object.name, ratio])
        except AttributeError:
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", f"<@{user[0]}>", ratio])
        finally:
            count += 1

    finalstring = top.format_codeblock(tabulate(final))

    try:
        if total > 15:
            await ctx.message.author.send(finalstring)
        else:
            await ctx.message.channel.send(finalstring)
    except discord.HTTPException as e:
        await ctx.message.channel.send(f"`{e}`")


@bot.command()
async def top_given(ctx):
    final = []
    finalstring = ""
    count = 0

    message_content, total = top.get_total_and_message(str(ctx.message.content))

    try:
        guild_id = ctx.message.guild.id
        user_data = top.get_user_data(message_content, guild_id, "UPVOTES_GIVEN", "DOWNVOTES_GIVEN")
    except Exception as e:
        if debug_mode is True: print(e)
        return

    user_data = top.create_sorted_list(user_data, "top")

    for user in user_data:
        if count == total:
            break

        if user[2] == 0 and user[3] == 0:
            continue

        ratio = top.get_ratio(user[2], user[3])

        try:
            user_object = ctx.message.guild.get_member(user[0])
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", user_object.name, ratio])
        except AttributeError:
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", f"<@{user[0]}>", ratio])
        finally:
            count += 1

    finalstring = top.format_codeblock(tabulate(final))

    try:
        if total > 15:
            await ctx.message.author.send(finalstring)
        else:
            await ctx.message.channel.send(finalstring)
    except discord.HTTPException as e:
        await ctx.message.channel.send(f"`{e}`")


@bot.command()
async def bottom_given(ctx):
    final = []
    finalstring = ""
    count = 0

    message_content, total = top.get_total_and_message(str(ctx.message.content))

    try:
        guild_id = ctx.message.guild.id
        user_data = top.get_user_data(message_content, guild_id, "UPVOTES_GIVEN", "DOWNVOTES_GIVEN")
    except Exception as e:
        if debug_mode is True: print(e)
        return

    user_data = top.create_sorted_list(user_data, "bottom")

    for user in user_data:
        if count == total:
            break

        if user[2] == 0 and user[3] == 0:
            continue

        ratio = top.get_ratio(user[2], user[3])

        try:
            user_object = ctx.message.guild.get_member(user[0])
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", user_object.name, ratio])
        except AttributeError:
            final.append([f"{user[2]}|{user[3]}", f"({user[1]})", f"<@{user[0]}>", ratio])
        finally:
            count += 1

    finalstring = top.format_codeblock(tabulate(final))

    try:
        if total > 15:
            await ctx.message.author.send(finalstring)
        else:
            await ctx.message.channel.send(finalstring)
    except discord.HTTPException as e:
        await ctx.message.channel.send(f"`{e}`")


@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    try:
        msg = await channel.fetch_message(payload.message_id)
    except NotFound:
        if debug_mode is True: print("\n\nMessage not found.")
        return
    except Exception as e:
        if debug_mode is True: print(f"Unknown error.\n{e}")
        return
    if debug_mode is True: print("Message fetched.")

    try:
        react.check_time(msg, payload, debug_mode)
        react.check_self_react(payload, msg, debug_mode)
        react.check_blacklist(payload, msg, debug_mode)
        upvoted, downvoted = react.upvote_or_downvote(payload, debug_mode)

        user_data = react.get_author_data(msg, debug_mode)
        react.create_tables_if_not_exist(msg, payload)
        react.create_entry_if_not_exist(user_data, msg, payload, debug_mode)
        react.update_author_data(upvoted, downvoted, payload, msg, "+", debug_mode)

        user_data = react.get_reactor_data(msg, payload, debug_mode)
        react.create_reactor_entry_if_not_exist(user_data, msg, payload, debug_mode)
        react.update_reactor_data(upvoted, downvoted, payload, msg, "+", debug_mode)

        # debug
        if debug_mode is True:
            print("DATA UPDATED FOR MSG REACTOR")
            sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
            user_data = db.c.execute(sql_query).fetchone()
            print("AUTHOR DATA:", user_data)

            sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
            user_data = db.c.execute(sql_query).fetchone()
            print("REACTOR DATA:", user_data)

    except Exception as e:
        if debug_mode is True: print(e.message, e.args)
        return


@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(payload.channel_id)
    try:
        msg = await channel.fetch_message(payload.message_id)
    except NotFound:
        if debug_mode is True: print("\n\nMessage not found.")
        return
    except Exception as e:
        if debug_mode is True: print(f"Unknown error.\n{e}")
        return
    if debug_mode is True: print("Message fetched.")

    try:
        react.check_time(msg, payload, debug_mode)
        react.check_self_react(payload, msg, debug_mode)
        react.check_blacklist(payload, msg, debug_mode)
        upvoted, downvoted = react.upvote_or_downvote(payload, debug_mode)

        user_data = react.get_author_data(msg, debug_mode)
        react.create_tables_if_not_exist(msg, payload)
        react.create_entry_if_not_exist(user_data, msg, payload, debug_mode)
        react.update_author_data(upvoted, downvoted, payload, msg, "-", debug_mode)

        user_data = react.get_reactor_data(msg, payload, debug_mode)
        react.create_reactor_entry_if_not_exist(user_data, msg, payload, debug_mode)
        react.update_reactor_data(upvoted, downvoted, payload, msg, "-", debug_mode)

        # debug
        if debug_mode is True:
            print("DATA UPDATED FOR MSG REACTOR")
            sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
            user_data = db.c.execute(sql_query).fetchone()
            print("AUTHOR DATA:", user_data)

            sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
            user_data = db.c.execute(sql_query).fetchone()
            print("REACTOR DATA:", user_data)

    except Exception as e:
        print(e.message, e.args)
        return


bot.run(KEY)
