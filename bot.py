import discord
import os
import mysql.connector
import json
from datetime import datetime, timedelta

client = discord.Client()

response_options = {}

claimee_point_increment = 2
bounty_owner_point_increment = 1


def connect():
    conn = mysql.connector.connect(database='bbb',
                                   user='root',
                                   password=os.environ['SQL_PASS'])
    return conn


# Boilerplate code that runs at the start of every response function.
def setup_response(user_id=None):
    out_message = "```stan\n"
    personality_id = None
    conn = connect()
    cursor = conn.cursor()
    if(user_id is not None):
        query = (
            "SELECT user_personality FROM users WHERE user_id = %s"
        )
        data = (user_id, )
        cursor.execute(query, data)
        row = cursor.fetchone()
        if row is not None:
            personality_id = row[0]
        else:
            personality_id = 1
    return (out_message, conn, cursor, personality_id)


# Boilerplate code that runs at the end of every response function.
def end_response(out_message, conn, cursor):
    cursor.close()
    conn.close()
    out_message += "```"
    return out_message


# Returns string of requested response with personality.
def get_response(cursor, response_name, personality_id):
    query = (
        "SELECT response_text FROM responses WHERE response_name = %s AND response_personality = %s"
    )
    data = (response_name, personality_id)
    cursor.execute(query, data)
    row = cursor.fetchone()
    return row[0]


def checkJoin(member):
    conn = connect()
    cursor = conn.cursor()
    query = (
        "SELECT EXISTS(SELECT * FROM users WHERE user_id = %s)"
    )
    data = (member.id, )
    cursor.execute(query, data)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if(row[0] == 1):
        return True
    return False


def join(message):
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]

    if(checkJoin(message.author) is False):
        query = (
            "INSERT INTO users(user_id,user_personality)"
            "VALUES (%s,%s)"
        )
        data = (message.author.id, 1)
        cursor.execute(query, data)
        conn.commit()
        out_message += "User joined.\n"
    else:
        query = (
            "SELECT user_personality FROM users WHERE user_id = %s"
        )
        data = (message.author.id, )
        cursor.execute(query, data)
        row = cursor.fetchone()
        personality_id = row[0]
        out_message += "{0}\n".format(get_response(cursor, "joined_true", personality_id))
    return (end_response(out_message, conn, cursor), )


def command_bad(message):
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    out_message += "{0}\n".format(get_response(cursor, "command_invalid", personality_id))

    return (end_response(out_message, conn, cursor), )


def helpp(message):
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    out_message += "{0}\n".format(get_response(cursor, "help", personality_id))
    for key in response_options:
        out_message += "{0:<20} {1}\n".format(key, response_options[key][0])

    return (end_response(out_message, conn, cursor), )


def personality(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 2:
        # Attempt to change personality.
        new_personality_id = split_message[1]
        query = (
            "SELECT EXISTS(SELECT * FROM personalities WHERE personality_id = %s)"
        )
        data = (new_personality_id, )
        cursor.execute(query, data)
        row = cursor.fetchone()
        if(row[0] == 1):
            query = (
                "UPDATE users SET user_personality = %s WHERE user_id = %s"
            )
            data = (new_personality_id, message.author.id)
            cursor.execute(query, data)
            conn.commit()
            out_message += "{0}\n".format(get_response(cursor, "personality_changed", new_personality_id))
        else:
            out_message += "{0}\n".format(get_response(cursor, "personality_invalid", personality_id))
    else:
        # Display help and available personalities.
        out_message += "{0}\n".format(get_response(cursor, "personality", personality_id))
        out_message += "\n{0}".format("# !personality [NUMBER]\n")
        query = ("SELECT * FROM personalities")
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            out_message += "{0:<20} {1}\n".format("{0} {1}".format(row[0], row[1]), row[2])

    return (end_response(out_message, conn, cursor), )


def bounty(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]
    dms = []

    if len(split_message) >= 2:
        # Create new bounty.
        if split_message[1] == "-new":
            query = (
                "INSERT INTO bounties(bounty_creation, bounty_expiration, bounty_text, bounty_creator, bounty_accepted)"
                "VALUES (%s,%s,%s,%s,JSON_ARRAY())"
            )
            now = datetime.utcnow()
            later = now + timedelta(days=7)
            description = " ".join(split_message[2:])
            data = (now.strftime('%Y-%m-%d %H:%M:%S'), later.strftime('%Y-%m-%d %H:%M:%S'), description, message.author.id)
            cursor.execute(query, data)
            conn.commit()
            out_message += "{0}\n".format(get_response(cursor, "bounty_new_valid", personality_id))
            out_message += "It expires on {0} UTC.\n".format(later.strftime('%Y-%m-%d %H:%M:%S'))
        elif split_message[1] == "-edit":
            # If the bounty exists under the user's id, replace description with new text.
            query = (
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator = %s AND bounty_id = %s)"
            )
            data = (message.author.id, split_message[2])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if(row[0] == 1):
                query = (
                    "UPDATE bounties SET bounty_text = %s WHERE bounty_id = %s"
                )
                description = " ".join(split_message[3:])
                data = (description, split_message[2])
                cursor.execute(query, data)
                conn.commit()
                out_message += "{0}\n".format(get_response(cursor, "bounty_edit_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "bounty_edit_invalid", personality_id))
        elif split_message[1] == "-delete":
            # If the bounty exists under the user's id, delete the bounty. Also delete any claims on it first.
            query = (
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator = %s AND bounty_id = %s)"
            )
            data = (message.author.id, split_message[2])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if(row[0] == 1):
                # Send DM to claimees.
                query = (
                    "SELECT * FROM claims WHERE claim_bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                rows = cursor.fetchall()
                for row in rows:
                    dms.append((row[4], "{0} deleted a bounty you had a claim on. Your claim has also been removed. The bounty was: {1}".format(row[5], "PUT DESCRIPTION HERE")))

                # Delete claims on bounty.
                query = (
                    "DELETE FROM claims WHERE claim_bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                conn.commit()

                # Delete bounty.
                query = (
                    "DELETE FROM bounties WHERE bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                conn.commit()

                out_message += "{0}\n".format(get_response(cursor, "bounty_delete_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "bounty_delete_invalid", personality_id))
        else:
            out_message += "{0}\n".format(get_response(cursor, "bounty_invalid", personality_id))
    else:
        # Display help and existing bounties.
        out_message += "{0}\n".format(get_response(cursor, "bounty", personality_id))
        out_message += "{0}".format("# !bounty -new [BOUNTY DESCRIPTION]\n")
        out_message += "{0}".format("# !bounty -edit [BOUNTY ID] [BOUNTY DESCRIPTION]\n")
        out_message += "{0}".format("# !bounty -delete [BOUNTY ID]\n")
        query = ("SELECT * FROM bounties WHERE bounty_active = TRUE")
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            out_message += "{0:<20} {1}\n".format("{0} {1} Expires {2} UTC".format(row[0], client.get_user(row[4]).name, row[2]), row[3])

    return (end_response(out_message, conn, cursor), dms)


def claim(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]
    dms = []

    if len(split_message) >= 2:
        if split_message[1] == "-new":
            # Create new claim if the bounty exists, the user is not the creator, and the bounty has not expired.
            # And the user hasn't already made a claim on this bounty, and the user hasn't already been accepted.
            query = (
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator != %s AND bounty_id = %s AND JSON_CONTAINS(bounty_accepted,'%s') = 0 AND bounty_expiration > NOW())"
            )
            data = (message.author.id, split_message[2], message.author.id)
            cursor.execute(query, data)
            row = cursor.fetchone()

            query = (
                "SELECT EXISTS(SELECT * FROM claims WHERE claim_bounty_id = %s AND claim_claimee = %s)"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            roww = cursor.fetchone()
            if(row[0] == 1 and roww[0] == 0):
                query = ("SELECT bounty_expiration, bounty_creator FROM bounties WHERE bounty_id = %s")
                data = (split_message[2], )
                cursor.execute(query, data)
                bounty_info = cursor.fetchone()

                # Get pillars if present.
                pillars = []
                for i, pillar in enumerate(split_message):
                    if i < 3:
                        pass
                    else:
                        query = (
                            "SELECT pillar_id FROM pillars WHERE pillar_name = %s and pillar_user = %s"
                        )
                        data = (pillar, message.author.id)
                        cursor.execute(query, data)
                        row_p = cursor.fetchone()
                        if row_p is not None:
                            pillars.append(row_p[0])
                        else:
                            out_message += "{0}\n".format(get_response(cursor, "claim_new_invalid_pillar", personality_id))
                            return (end_response(out_message, conn, cursor), dms)

                pillar_string = ""
                for pillar in pillars:
                    pillar_string += "{0}, ".format(pillar)
                pillar_string = pillar_string[:-2]
                query = (
                    "INSERT INTO claims(claim_bounty_id, claim_creation, claim_expiration, claim_claimee, claim_bounty_creator, claim_pillars)"
                    "VALUES (%s,%s,%s,%s,%s,JSON_ARRAY(%s))"
                )
                now = datetime.utcnow()
                data = (split_message[2], now.strftime('%Y-%m-%d %H:%M:%S'), bounty_info[0], message.author.id, bounty_info[1], pillar_string)
                cursor.execute(query, data)
                conn.commit()

                out_message += "{0}\n".format(get_response(cursor, "claim_new_valid", personality_id))

                # Send DM to bounty creator.
                dms.append((bounty_info[1], "{0} submitted a claim to a bounty you created. Please respond to it before the bounty period ends.".format(message.author.name)))
            else:
                out_message += "{0}\n".format(get_response(cursor, "claim_new_invalid", personality_id))
        elif split_message[1] == "-delete":
            # If the claim exists and is owned by the user, delete the claim.
            query = (
                "SELECT EXISTS(SELECT * FROM claims WHERE claim_id = %s AND claim_claimee = %s)"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            row = cursor.fetchone()
            if(row[0] == 1):
                query = (
                    "DELETE FROM claims WHERE claim_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                conn.commit()
                out_message += "{0}\n".format(get_response(cursor, "claim_delete_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "claim_delete_invalid", personality_id))
        elif split_message[1] == "-accept":
            # Attempt to accept a claim.

            # If bounty belongs to user, and the claim hasn't expired,
            # award 1 point to user, and 2 points to claimee.
            # Send DM to claimee.

            query = ("SELECT * FROM claims WHERE claim_bounty_creator = %s AND claim_id = %s AND claim_expiration > NOW()")
            data = (message.author.id, split_message[1])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if(row is not None):
                # Award point to claimee. Check for pillar bonus too.
                claimee_point_reward = claimee_point_increment
                query = ("SELECT claim_pillars FROM claims WHERE claim_claimee = %s")
                data = (message.author.id, row[4])
                cursor.execute(query, data)
                row_pi = cursor.fetchone()
                pillars = json.load(row_pi[0])

                for pillar in pillars:
                    query = (
                        "UPDATE pillars SET pillar_points = pillar_points+%s WHERE pillar_id = %s"
                    )
                    data = (1, pillar)
                    cursor.execute(query, data)
                    conn.commit()

                    query = ("SELECT * FROM pillars WHERE pillar_is_favorite = TRUE AND pillar_id = %s")
                    data = (pillar, )
                    cursor.execute(query, data)
                    row_pibo = cursor.fetchone()
                    if row_pibo is not None:
                        claimee_point_reward += 1

                query = (
                    "UPDATE users SET user_points = user_points+%s WHERE user_id = %s"
                )
                data = (claimee_point_reward, row[4])
                cursor.execute(query, data)
                conn.commit()

                # Send DM to claimee.
                query = (
                    "SELECT user_personality FROM users WHERE user_id = %s"
                )
                data = (row[4], )
                cursor.execute(query, data)
                row_p = cursor.fetchone()
                claimee_personality = row_p[0]
                dms.append((row[4], get_response(cursor, "accept_claimee_valid", claimee_personality).format(message.author.name, claimee_point_reward)))

                # Delete claim.
                query = (
                    "DELETE FROM claims WHERE claim_id = %s"
                )
                data = (row[0], )
                cursor.execute(query, data)
                conn.commit()

                # Add claimee to bounty's list of completed users.
                query = (
                    "UPDATE bounties SET bounty_accepted = JSON_ARRAY_APPEND(bounty_accepted, '$', %s) WHERE bounty_id = %s"
                )
                data = (row[4], row[1])
                cursor.execute(query, data)
                conn.commit()

                # If bounty creator hasn't received a bounty yet, award bonus to them.
                query = (
                    "SELECT * FROM bounties WHERE bounty_id = %s AND bounty_bonus_received = FALSE"
                )
                data = (row[1], )
                cursor.execute(query, data)
                row_br = cursor.fetchone()
                if row_br is not None:
                    query = (
                        "UPDATE users SET user_points = user_points+%s WHERE user_id = %s"
                    )
                    data = (bounty_owner_point_increment, row[5])
                    cursor.execute(query, data)
                    conn.commit()

                    query = (
                        "UPDATE bounties SET bounty_bonus_received = TRUE WHERE bounty_id = %s"
                    )
                    data = (row[1], )
                    cursor.execute(query, data)
                    conn.commit()

                    out_message += "{0}\n".format(get_response(cursor, "accept_valid", personality_id))
                else:
                    out_message += "{0}\n".format(get_response(cursor, "accept_valid_no_bonus", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "accept_invalid", personality_id))
        elif split_message[1] == "-reject":
            # Attempt to reject a claim.

            # If bounty belongs to user, and the claim hasn't expired,
            # delete claim.
            # Send DM to claimee.

            query = ("SELECT * FROM claims WHERE claim_bounty_creator = %s AND claim_id = %s AND claim_expiration > NOW()")
            data = (message.author.id, split_message[1])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if(row is not None):
                # Delete claim.
                query = (
                    "DELETE FROM claims WHERE claim_id = %s"
                )
                data = (row[0], )
                cursor.execute(query, data)
                conn.commit()

                # Send DM to bounty creator.
                query = (
                    "SELECT user_personality FROM users WHERE user_id = %s"
                )
                data = (row[4], )
                cursor.execute(query, data)
                row_p = cursor.fetchone()
                claimee_personality = row_p[0]
                dms.append((row[4], get_response(cursor, "reject_claimee_valid", claimee_personality).format(message.author.name)))

                out_message += "{0}\n".format(get_response(cursor, "reject_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "reject_invalid", personality_id))
        else:
            out_message += "{0}\n".format(get_response(cursor, "claim_invalid", personality_id))

    else:
        # Display help and existing claims that the user has authority over, or made.
        out_message += "{0}\n".format(get_response(cursor, "claim", personality_id))
        out_message += "{0}".format("# !claim -new [BOUNTY ID]\n")
        out_message += "{0}".format("# !claim -new [BOUNTY ID] [PILLAR NAME]\n")
        out_message += "{0}".format("# !claim -new [BOUNTY ID] [PILLAR NAME] [PILLAR NAME] ...\n")
        out_message += "{0}".format("# !claim -accept [CLAIM ID]\n")
        out_message += "{0}".format("# !claim -reject [CLAIM ID]\n")
        out_message += "{0}".format("# !claim -delete [CLAIM ID]\n")

        query = ("SELECT * FROM claims WHERE claim_bounty_creator = %s")
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("CLAIMS SUBMITTED TO YOU\n")
        for row in rows:
            out_message += "{0:<20} Expires {1} UTC\n".format("{0} {1}".format(row[0], client.get_user(row[4]).name), row[3])

        query = ("SELECT * FROM claims WHERE claim_claimee = %s")
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("CLAIMS SUBMITTED BY YOU\n")
        for row in rows:
            out_message += "{0:<20} Expires {1} UTC\n".format("{0} {1}".format(row[0], client.get_user(row[5]).name), row[3])

    return (end_response(out_message, conn, cursor), dms)


def pillar(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 2:
        if split_message[1] == "-new":
            # Ensure pillar name does not already exist.
            query = (
                "SELECT * FROM pillars WHERE pillar_name = %s AND pillar_user = %s"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            row_p = cursor.fetchone()
            if row_p is None:
                # Create new pillar.
                query = (
                    "INSERT INTO pillars(pillar_user, pillar_name, pillar_is_favorite, pillar_points)"
                    "VALUES (%s,%s,FALSE,0)"
                )
                data = (message.author.id, split_message[2])
                cursor.execute(query, data)
                conn.commit()
                out_message += "{0}\n".format(get_response(cursor, "pillar_new_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "pillar_new_invalid", personality_id))
        elif split_message[1] == "-rename":
            # Ensure old pillar exists.
            query = (
                "SELECT * FROM pillars WHERE pillar_name = %s AND pillar_user = %s"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            row_p1 = cursor.fetchone()

            # Ensure new pillar name does not already exist.
            query = (
                "SELECT * FROM pillars WHERE pillar_name = %s AND pillar_user = %s"
            )
            data = (split_message[3], message.author.id)
            cursor.execute(query, data)
            row_p2 = cursor.fetchone()

            if row_p1 is None:
                out_message += "{0}\n".format(get_response(cursor, "pillar_rename_invalid_old", personality_id))
            elif row_p2 is not None:
                out_message += "{0}\n".format(get_response(cursor, "pillar_rename_invalid_new", personality_id))
            else:
                # Rename pillar.
                query = (
                    "UPDATE pillars SET pillar_name = %s WHERE pillar_name = %s AND pillar_user = %s"
                )
                data = (split_message[3], split_message[2], message.author.id)
                cursor.execute(query, data)
                conn.commit()
                out_message += "{0}\n".format(get_response(cursor, "pillar_rename_valid", personality_id))

        elif split_message[1] == "-delete":
            # Ensure pillar exists.
            query = (
                "SELECT * FROM pillars WHERE pillar_name = %s AND pillar_user = %s"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            row_p = cursor.fetchone()
            if row_p is not None:
                # Delete the pillar.
                query = (
                    "DELETE FROM pillars WHERE pillar_name = %s AND pillar_user = %s"
                )
                data = (split_message[2], message.author.id)
                cursor.execute(query, data)
                conn.commit()
                out_message += "{0}\n".format(get_response(cursor, "pillar_delete_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "pillar_delete_invalid", personality_id))
        elif split_message[1] == "-favorite":
            # Ensure pillar exists.
            query = (
                "SELECT * FROM pillars WHERE pillar_name = %s AND pillar_user = %s"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            row_p = cursor.fetchone()
            if row_p is not None:
                # Unfavorite any favorited pillars owned by the user.
                query = (
                    "UPDATE pillars SET pillar_is_favorite = FALSE WHERE pillar_user = %s AND pillar_is_favorite = TRUE"
                )
                data = (message.author.id, )
                cursor.execute(query, data)
                conn.commit()

                # Favorite the pillar.
                query = (
                    "UPDATE pillars SET pillar_is_favorite = TRUE WHERE pillar_name = %s AND pillar_user = %s"
                )
                data = (split_message[2], message.author.id)
                cursor.execute(query, data)
                conn.commit()

                out_message += "{0}\n".format(get_response(cursor, "pillar_favorite_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "pillar_favorite_invalid", personality_id))
        else:
            out_message += "{0}\n".format(get_response(cursor, "pillar_invalid", personality_id))
    else:
        # Display help and the user's existing pillars.
        out_message += "{0}\n".format(get_response(cursor, "pillar", personality_id))
        out_message += "{0}".format("# !pillar -new [PILLAR NAME]\n")
        out_message += "{0}".format("# !pillar -rename [OLD PILLAR NAME] [NEW PILLAR NAME]\n")
        out_message += "{0}".format("# !pillar -delete [PILLAR NAME]\n")
        out_message += "{0}".format("# !pillar -favorite [PILLAR NAME]\n")

        query = ("SELECT * FROM pillars WHERE pillar_user = %s")
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("YOUR PILLARS\n")
        for row in rows:
            favorite_string = ""
            if row[3] == 1:
                favorite_string = "(FAVORITE)"
            out_message += "{0:<20} {1}\n".format(row[2], favorite_string)

    return (end_response(out_message, conn, cursor), )


def points(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    # Display leaderboard.

    out_message += "{0}\n".format(get_response(cursor, "points", personality_id))
    out_message += "{0}".format("# !points\n")

    points_user_message = ""
    points_pillars_message = ""
    points_board_message = ""

    query = ("SELECT * FROM users ORDER BY user_points DESC")
    cursor.execute(query)
    rows = cursor.fetchall()

    place = 0
    previous_points = -1
    for i, row in enumerate(rows):
        place_suffix = "th"
        if row[3] != previous_points:
            place = i + 1
        if place == 1:
            place_suffix = "st"
        elif place == 2:
            place_suffix = "nd"
        elif place == 3:
            place_suffix = "rd"
        previous_points = row[3]
        if row[0] == message.author.id:
            points_user_message += "{0:<20}{1:<20}{2:<20}\n".format("{0}{1}".format(place, place_suffix), client.get_user(row[0]).name, row[3])
        points_board_message += "{0:<20}{1:<20}{2:<20}\n".format("{0}{1}".format(place, place_suffix), client.get_user(row[0]).name, row[3])

    query = ("SELECT * FROM pillars WHERE pillar_user = %s ORDER BY pillar_points DESC")
    data = (message.author.id, )
    cursor.execute(query, data)
    rows = cursor.fetchall()
    for row in rows:
        points_pillars_message += "{0:<20}{1:<20}\n".format(row[2], row[4])

    out_message += "\n{0}\n".format(get_response(cursor, "points_user", personality_id))
    out_message += "{0:<20}{1:<20}{2:<20}\n".format("POSITION", "NAME", "POINTS")
    out_message += points_user_message
    out_message += "{0:<20}{1:<20}\n".format("PILLAR", "SUCCESSFUL CLAIMS")
    out_message += points_pillars_message
    out_message += "\n{0}\n".format(get_response(cursor, "points_leaderboard", personality_id))
    out_message += "{0:<20}{1:<20}{2:<20}\n".format("POSITION", "NAME", "POINTS")
    out_message += points_board_message
    return (end_response(out_message, conn, cursor), )


response_options = {
    "!help": ("List commands.", helpp),
    "!bounty": ("Create or view bounties.", bounty),
    "!claim": ("Create, accept, reject, or view claims on bounties.", claim),
    "!pillar": ("Edit or view your pillars.", pillar),
    "!points": ("View your points and the leaderboard.", points),
    "!personality": ("Change bot personality.", personality),
    #"!timezone": ("Change displayed timezone.",timezone)
}


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    split_message = message.content.split()
    if len(split_message) == 0:
        return
    if split_message[0] == "!join":
        await message.channel.send(join(message)[0])
    elif split_message[0] in response_options:
        if checkJoin(message.author) is True:
            response = response_options[split_message[0]][1](message)
            await message.channel.send(response[0])
            if len(response) >= 2:
                for dm in response[1]:
                    user = client.get_user(dm[0])
                    await user.send(dm[1])
        else:
            await message.channel.send("Please subscribe to bot first by typing \"!join\"")
    elif split_message[0][0] == '!':
        await message.channel.send(command_bad(message)[0])


@client.event
async def on_member_join(member):
    print('{0} has joined server.'.format(member))


client.run(os.environ['BBB_TOK'])
