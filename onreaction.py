import discord
import db
import datetime

def check_time(msg, payload, debug_mode):
    # checks to see if the message fits the time constraint set by server owner
    message_time = msg.created_at.timestamp()
    current_time = datetime.datetime.utcnow().timestamp()

    sql_query = f"SELECT TIMELIMIT FROM settings_{payload.guild_id}"
    time_limit = db.c.execute(sql_query).fetchone()[0]
    if time_limit != int:
        if debug_mode is True: print("No time limit.")
        pass
    elif current_time - message_time > time_limit:
        if debug_mode is True: print("Exceeds time limit.")
        raise Exception("Exceeds time limit.")
    else:
        if debug_mode is True: print("Passed time limit checks.")
        pass

def check_self_react(payload, msg, debug_mode):
    # checks to see if it's a reaction on their own message
    if payload.user_id == msg.author.id:
        raise Exception("Self react.")
    if debug_mode is True: print("Not the same user.")

def check_blacklist(payload, msg, debug_mode):
    # checks to see if reactor (person who reacted) is in blacklist
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
    user_data = db.c.execute(sql_query).fetchone()
    try:
        if user_data[5] == 1:
            if debug_mode is True: print("USER IS BLACKLISTED.")
            raise Exception("Blacklisted")
    except TypeError:
        pass  # user doesnt exist in db, so cannot be in blacklist

def upvote_or_downvote(payload, debug_mode):
    upvoted, downvoted = 0, 0
    # gets server emotes and decides if it was an upvote or downvote
    sql_query = f"SELECT * FROM settings_{payload.guild_id}"
    server_emotes = db.c.execute(sql_query).fetchone()
    if str(payload.emoji) == server_emotes[0] or str(payload.emoji) == server_emotes[1]:
        upvoted = 1
        return upvoted, downvoted
    elif str(payload.emoji) == server_emotes[2]:
        downvoted = 1
        return upvoted, downvoted
    else:
        if debug_mode is True: print("SERVER EMOTES:", server_emotes, type(server_emotes[1]))
        if debug_mode is True: print("EMOTE USED:", str(payload.emoji), type(str(payload.emoji)))
        raise Exception("Incorrect emote.")

def get_author_data(msg, debug_mode):
    # gets user data for the author of msg
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
    user_data = db.c.execute(sql_query).fetchone()
    if debug_mode is True: print("USER DATA:", user_data)
    if debug_mode is True: print("IF NONE, SPOT WILL BE ADDED")
    return user_data

def create_tables_if_not_exist(msg, payload):
    # creates tables for both users if they dont already exist
    sql_query = f"""
    CREATE TABLE IF NOT EXISTS '{msg.guild.id}_{msg.author.id}' (
    USER_ID          INTEGER     PRIMARY KEY,
    UPVOTES          INTEGER     (1, 100),
    DOWNVOTES        INTEGER     (1, 100),
    UPVOTES_GIVEN    INTEGER   (1, 100),
    DOWNVOTES_GIVEN  INTEGER    (1, 100)
    );"""
    db.c.execute(sql_query)

    sql_query = f"""
    CREATE TABLE IF NOT EXISTS '{msg.guild.id}_{payload.user_id}' (
    USER_ID          INTEGER     PRIMARY KEY,
    UPVOTES          INTEGER    (1, 100),
    DOWNVOTES        INTEGER    (1, 100),
    UPVOTES_GIVEN    INTEGER    (1, 100),
    DOWNVOTES_GIVEN  INTEGER    (1, 100)
    );"""
    db.c.execute(sql_query)
    db.conn.commit()

def create_entry_if_not_exist(user_data, msg, payload, debug_mode):
    # if there is no user data for the author, add a spot for them in the database
    if user_data is None:   # from data_{guild.id}
        sql_query = f"""INSERT OR REPLACE INTO data_{msg.guild.id}
                    (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN, BLACKLISTED)
                    VALUES (?, 0, 0, 0, 0, 0
                    );"""
        db.c.execute(sql_query, (msg.author.id,))
        if debug_mode is True: print("EMPTY SPOT ADDED FOR MSG AUTHOR IN DATA_msg.guild.id")

    sql_query = f"SELECT * FROM '{msg.guild.id}_{msg.author.id}' WHERE USER_ID = {payload.user_id}"
    user_data = db.c.execute(sql_query).fetchone()
    if user_data is None:
        sql_query = f"""INSERT OR REPLACE INTO '{msg.guild.id}_{msg.author.id}'
                    (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN)
                    VALUES (?, 0, 0, 0, 0
                    );"""
        db.c.execute(sql_query, (payload.user_id,))
        db.conn.commit()
        if debug_mode is True: print("EMPTY SPOT ADDED FOR MSG AUTHOR")

def update_author_data(upvoted, downvoted, payload, msg, add_or_remove, debug_mode):
    # update author's data, now that it definitely exists
    sql_query = f"""
    UPDATE data_{payload.guild_id}
    SET UPVOTES = UPVOTES {add_or_remove} ?,
        DOWNVOTES = DOWNVOTES {add_or_remove} ?
    WHERE USER_ID = {msg.author.id}
    """
    db.c.execute(sql_query, (upvoted, downvoted))

    sql_query = f"""
    UPDATE '{msg.guild.id}_{msg.author.id}'
    SET UPVOTES = UPVOTES {add_or_remove} ?,
        DOWNVOTES = DOWNVOTES {add_or_remove} ?
    WHERE USER_ID = {payload.user_id}
    """
    db.c.execute(sql_query, (upvoted, downvoted))

    if debug_mode is True: print("DATA UPDATED FOR MSG AUTHOR")

def get_reactor_data(msg, payload, debug_mode):
    # gets user data for the user who reacted
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
    user_data = db.c.execute(sql_query).fetchone()
    if debug_mode is True: print("USER (REACTOR) DATA:", user_data)
    if debug_mode is True: print("IF NONE, SPOT WILL BE ADDED")
    return user_data

def create_reactor_entry_if_not_exist(user_data, msg, payload, debug_mode):
    # if there is no user data for reactor, add a spot for them in the database
    if user_data is None:   # from data_{guild.id}
        sql_query = f"""INSERT OR REPLACE INTO data_{msg.guild.id}
                    (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN, BLACKLISTED)
                    VALUES (?, 0, 0, 0, 0, 0
                    );"""
        db.c.execute(sql_query, (payload.user_id,))
        if debug_mode is True: print("EMPTY SPOT ADDED FOR MSG AUTHOR IN DATA_msg.guild.id")

    sql_query = f"SELECT * FROM '{msg.guild.id}_{payload.user_id}' WHERE USER_ID = {msg.author.id}"
    user_data = db.c.execute(sql_query).fetchone()
    if user_data is None:
        sql_query = f"""INSERT OR REPLACE INTO '{msg.guild.id}_{payload.user_id}'
                    (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN)
                    VALUES (?, 0, 0, 0, 0
                    );"""
        db.c.execute(sql_query, (msg.author.id,))
        if debug_mode is True: print("EMPTY SPOT ADDED FOR MSG AUTHOR")

def update_reactor_data(upvoted, downvoted, payload, msg, add_or_remove, debug_mode):
    # update reactor's data, now that it definitely exists
    sql_query = f"""
    UPDATE data_{msg.guild.id}
    SET UPVOTES_GIVEN = UPVOTES_GIVEN + ?,
        DOWNVOTES_GIVEN = DOWNVOTES_GIVEN + ?
    WHERE USER_ID = {payload.user_id}
    """
    db.c.execute(sql_query, (upvoted, downvoted))

    sql_query = f"""
    UPDATE '{msg.guild.id}_{payload.user_id}'
    SET UPVOTES_GIVEN = UPVOTES_GIVEN + ?,
        DOWNVOTES_GIVEN = DOWNVOTES_GIVEN + ?
    WHERE USER_ID = {msg.author.id}
    """
    db.c.execute(sql_query, (upvoted, downvoted))

def commit():
    db.conn.commit()
