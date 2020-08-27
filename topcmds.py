import discord
import db
import operator

def get_total_and_message(message_content):
    try:
        total = int(message_content.split(" ")[-1])
        message_content = message_content[:-len(str(total))-1]
    except ValueError:
        message_content = message_content
        total = 10
    return message_content, total


def get_user_data(message_content, guild_id, upvote_type, downvote_type):
    if len(message_content.split(" ")) == 2:
        user_id = message_content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", "")
        sql_query = f"SELECT USER_ID, {upvote_type}, {downvote_type} FROM '{guild_id}_{user_id}'"
        user_data = db.c.execute(sql_query).fetchall()

    elif len(message_content.split(" ")) == 1:
        sql_query = f"SELECT USER_ID, {upvote_type}, {downvote_type} FROM data_{guild_id}"
        user_data = db.c.execute(sql_query).fetchall()
    else:
        raise Exception("Incorrect message length.")

    return user_data

def get_ratio(upvotes, downvotes):
    if downvotes < 1:
        return upvotes
    elif upvotes < 1:
        return 0
    else:
        return upvotes/downvotes

def create_sorted_list(user_data, top_bottom):
    newlist = []
    for user in user_data:
        newlist.append([user[0], user[1]-user[2], user[1], user[2]]) # id, karma, upvotes, downvotes
    user_data = sorted(newlist, key=operator.itemgetter(1))

    if top_bottom == "top":
        user_data.reverse()
    return user_data

def format_codeblock(finalstring):
    if len(finalstring) != 0:
        finalstring = "```glsl\n" + finalstring
        finalstring += "```"
    return finalstring
