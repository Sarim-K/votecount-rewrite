import db

def validate(card_type, dark_light):
    if card_type != "karma" and card_type != "given":
        message_text = "Incorrect card type."
        return
    elif dark_light != "dark" and dark_light != "light":
        message_text = "Incorrect colour type."
    else:
        raise Exception("Validation passed.")

    return message_text

def set_card_type(author_id, karma_template_name, karma_dark_light, given_template_name, given_dark_light):
    sql_query = f"""INSERT OR REPLACE INTO user_data
                (USER_ID, KARMA_TEMPLATE, KARMA_COLOUR, GIVEN_TEMPLATE, GIVEN_COLOUR)
                VALUES ({author_id}, "{karma_template_name}", "{karma_dark_light}", "{given_template_name}", "{given_dark_light}"
                );"""
    db.c.execute(sql_query)
    db.conn.commit()

def update_card_type(author_id, template_name, dark_light, karma_given):
    sql_query = f"""UPDATE user_data
                SET {karma_given}_TEMPLATE = "{template_name}",
                    {karma_given}_COLOUR = "{dark_light}"
                WHERE USER_ID = {author_id}
    """
    db.c.execute(sql_query)
    db.conn.commit()