import discord
import os
import mysql.connector
import json
import re
from datetime import datetime, timedelta
import visualizer

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

response_options = {}

CLAIMEE_POINT_INCREMENT = 2
BOUNTY_OWNER_POINT_INCREMENT = 1
OFFSET_MAX_HOUR = 14
OFFSET_MIN_HOUR = -12
OFFSET_MAX_MIN = 59
OFFSET_MIN_MIN = 0

oneEight = "\u258f"
twoEight = "\u258E"
threeEight = "\u258D"
fourEight = "\u258C"
fiveEight = "\u258B"
sixEight = "\u258A"
sevenEight = "\u2589"
eightEight = "\u2588"


class Response:
    text = None
    dms = None
    file = None

    def __init__(self, text=None, dms = None, file = None):
        self.text = text
        self.dms = dms
        self.file = file


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
    if user_id is not None:
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
    return out_message, conn, cursor, personality_id


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


def clean_cursor(cursor):
    try:
        cursor.fetchall()  # fetch (and discard) remaining rows
    except mysql.connector.errors.InterfaceError as ie:
        if ie.msg == 'No result set to fetch from.':
            # no problem, we were just at the end of the result set
            pass
        else:
            raise


def apply_time_offset(cursor, time, user_id):
    query = "SELECT user_time_offset FROM users WHERE user_id = %s"
    data = (user_id, )
    cursor.execute(query, data)
    row_ti = cursor.fetchone()
    hours = 0
    minutes = 0
    if row_ti is not None:
        hours = int(row_ti[0][:-2])
        minutes = int(row_ti[0][-2:])
    return time + timedelta(hours=hours, minutes=minutes), row_ti[0][:-2], row_ti[0][-2:]


def build_int_block(pp):
    full_blocks = pp // 8
    partial_block = pp % 8
    string_blocks = ""
    for i in range(0, full_blocks):
        string_blocks += eightEight
    if partial_block == 1:
        string_blocks += oneEight
    elif partial_block == 2:
        string_blocks += twoEight
    elif partial_block == 3:
        string_blocks += threeEight
    elif partial_block == 4:
        string_blocks += fourEight
    elif partial_block == 5:
        string_blocks += fiveEight
    elif partial_block == 6:
        string_blocks += sixEight
    elif partial_block == 7:
        string_blocks += sevenEight
    return string_blocks


def get_user_name(user_id):
    user = client.get_user(user_id)
    if user is None:
        return "UNKNOWN"
    else:
        return user.name


def format_command(command, description):
    return "{0:<60} {1}\n".format(command, description)


def check_join(member):
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
    if row[0] == 1:
        return True
    return False


def join(message):
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]

    if check_join(message.author) is False:
        query = (
            "INSERT INTO users(user_id, user_personality)"
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
    return Response(text=end_response(out_message, conn, cursor))


def command_bad(message):
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    out_message += "{0}\n".format(get_response(cursor, "command_invalid", personality_id))

    return Response(text=end_response(out_message, conn, cursor))


def helpp(message):
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    out_message += "{0}\n".format(get_response(cursor, "help", personality_id))
    for key in response_options:
        out_message += "{0:<20} {1}\n".format(key, response_options[key][0])

    return Response(text=end_response(out_message, conn, cursor))


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
        if row[0] == 1:
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
        out_message += format_command("# !personality [PERSONALITY ID]", "Sets your assistant's personality.")
        query = "SELECT * FROM personalities"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            out_message += "{0:<20} {1}\n".format("{0} {1}".format(row[0], row[1]), row[2])

    return Response(text=end_response(out_message, conn, cursor))


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
                "INSERT INTO bounties(bounty_creation, bounty_text, bounty_creator, bounty_accepted)"
                "VALUES (%s,%s,%s,JSON_ARRAY())"
            )
            now = datetime.utcnow()
            description = " ".join(split_message[2:])
            data = (now.strftime('%Y-%m-%d %H:%M:%S'), description, message.author.id)
            cursor.execute(query, data)
            conn.commit()
            out_message += "{0}\n".format(get_response(cursor, "bounty_new_valid", personality_id))
        elif split_message[1] == "-edit":
            # If the bounty exists under the user's id, replace description with new text.
            query = (
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator = %s AND bounty_id = %s)"
            )
            data = (message.author.id, split_message[2])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if row[0] == 1:
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
            if row[0] == 1:
                # Send DM to claimees.
                query = (
                    "SELECT * FROM claims WHERE claim_bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                rows = cursor.fetchall()
                for row in rows:
                    dms.append((row[3], "{0} deleted a bounty you had a claim on. Your claim has also been removed. "
                                        "The bounty was: {1}".format(row[4], "PUT DESCRIPTION HERE")))

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
        elif split_message[1] == "-close":
            # If the bounty exists under the user's id, close the bounty. Also delete any claims on it first.
            query = (
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator = %s AND bounty_id = %s)"
            )
            data = (message.author.id, split_message[2])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if row[0] == 1:
                # Send DM to claimees.
                query = (
                    "SELECT * FROM claims WHERE claim_bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                rows = cursor.fetchall()
                for row in rows:
                    dms.append((row[3], "{0} closed a bounty you had a claim on. Your claim has also been removed. "
                                        "The bounty was: {1}".format(row[4], "PUT DESCRIPTION HERE")))

                # Delete claims on bounty.
                query = (
                    "DELETE FROM claims WHERE claim_bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                conn.commit()

                # Close bounty.
                query = (
                    "UPDATE bounties SET bounty_active = 0 WHERE bounty_id = %s"
                )
                data = (split_message[2], )
                cursor.execute(query, data)
                conn.commit()

                out_message += "{0}\n".format(get_response(cursor, "bounty_close_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "bounty_close_invalid", personality_id))
        elif split_message[1] == "-v":
            query = "SELECT * FROM bounties ORDER BY bounty_creation DESC"
            cursor.execute(query)
            rows = cursor.fetchall()

            out_message += "{0:<20} {1:<30} {2}\n".format("{0} {1}".format("ID", "OWNER"), "CREATION DATE", "DESCRIPTION")
            for row in rows:
                offset_creation = apply_time_offset(cursor, row[1], message.author.id)
                is_inactive = ""
                if row[4] == 0:
                    is_inactive = " (INACTIVE)"
                out_message += "{0:<20} {1:<30} {2}{3}\n".format(
                    "{0} {1}".format(row[0], get_user_name(row[3])),
                    "{0}{1}:{2}".format(offset_creation[0], offset_creation[1], offset_creation[2]),
                    row[2],
                    is_inactive
                )
        else:
            out_message += "{0}\n".format(get_response(cursor, "bounty_invalid", personality_id))
    else:
        # Display help and existing bounties.
        out_message += "{0}\n".format(get_response(cursor, "bounty", personality_id))
        out_message += format_command("# !bounty -new [BOUNTY DESCRIPTION]", "Creates a new bounty.")
        out_message += format_command("# !bounty -close [BOUNTY ID]", "Rejects any pending claims on a bounty and "
                                                                      "removes it from the bounty list.")
        out_message += format_command("# !bounty -edit [BOUNTY ID] [BOUNTY DESCRIPTION]", "Rewrites the description "
                                                                                          "of a bounty.")
        out_message += format_command("# !bounty -delete [BOUNTY ID]", "Rejects any pending claims on a bounty and "
                                                                       "obliterates it from memory.")
        out_message += format_command("# !bounty -v", "\"Verbose\" bounty listing, displays bounties that have closed "
                                                      "too.")
        query = "SELECT * FROM bounties WHERE bounty_active = TRUE ORDER BY bounty_creation DESC"
        cursor.execute(query)
        rows = cursor.fetchall()

        out_message += "{0:<20} {1:<30} {2}\n".format("{0} {1}".format("ID", "OWNER"), "CREATION DATE", "DESCRIPTION")
        for row in rows:
            offset_creation = apply_time_offset(cursor, row[1], message.author.id)
            out_message += "{0:<20} {1:<30} {2}\n".format(
                "{0} {1}".format(row[0], get_user_name(row[3])),
                "{0}{1}:{2}".format(offset_creation[0], offset_creation[1], offset_creation[2]),
                row[2]
            )

    return Response(text=end_response(out_message, conn, cursor), dms=dms)


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
            # Create new claim if the bounty exists, the user is not the creator, and the bounty is active.
            # And the user hasn't already made a claim on this bounty, and the user hasn't already been accepted.
            query = (
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator != %s AND bounty_id = %s AND "
                "JSON_CONTAINS(bounty_accepted,'%s') = 0 AND bounty_active = 1) "
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
            if row[0] == 1 and roww[0] == 0:
                query = "SELECT bounty_creator FROM bounties WHERE bounty_id = %s"
                data = (split_message[2], )
                cursor.execute(query, data)
                bounty_creator = cursor.fetchone()[0]

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
                            return Response(text=end_response(out_message, conn, cursor), dms=dms)

                pillar_string = ""
                for pillar in pillars:
                    pillar_string += "{0}, ".format(pillar)
                pillar_string = pillar_string[:-2]
                query = (
                    "INSERT INTO claims(claim_bounty_id, claim_creation, claim_claimee, claim_bounty_creator, "
                    "claim_pillars) "
                    "VALUES (%s,%s,%s,%s,JSON_ARRAY({0}))".format(pillar_string)
                )
                now = datetime.utcnow()
                data = (split_message[2], now.strftime('%Y-%m-%d %H:%M:%S'), message.author.id, bounty_creator)
                cursor.execute(query, data)
                conn.commit()

                out_message += "{0}\n".format(get_response(cursor, "claim_new_valid", personality_id))

                # Send DM to bounty creator.
                dms.append((bounty_creator, "{0} submitted a claim to a bounty you created. Please respond to it "
                                            "before the bounty period ends.".format(message.author.name)))
            else:
                out_message += "{0}\n".format(get_response(cursor, "claim_new_invalid", personality_id))
        elif split_message[1] == "-cancel":
            # If the claim exists and is owned by the user, delete the claim.
            query = (
                "SELECT EXISTS(SELECT * FROM claims WHERE claim_id = %s AND claim_claimee = %s)"
            )
            data = (split_message[2], message.author.id)
            cursor.execute(query, data)
            row = cursor.fetchone()
            if row[0] == 1:
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

            # If bounty belongs to user,
            # award 1 point to user, and 2 points to claimee.
            # Send DM to claimee.

            query = "SELECT * FROM claims WHERE claim_bounty_creator = %s AND claim_id = %s"
            data = (message.author.id, split_message[2])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if row is not None:
                # Award point to claimee. Check for pillar bonus too.
                claimee_point_reward = CLAIMEE_POINT_INCREMENT
                query = "SELECT claim_pillars FROM claims WHERE claim_claimee = %s"
                data = (row[3], )
                cursor.execute(query, data)
                row_pi = cursor.fetchone()
                pillars = json.loads(row_pi[0])
                clean_cursor(cursor)

                for pillar in pillars:
                    query = (
                        "UPDATE pillars SET pillar_points = pillar_points+%s WHERE pillar_id = %s"
                    )
                    data = (1, pillar)
                    cursor.execute(query, data)
                    conn.commit()

                    query = "SELECT * FROM pillars WHERE pillar_is_favorite = TRUE AND pillar_id = %s"
                    data = (pillar, )
                    cursor.execute(query, data)
                    row_pibo = cursor.fetchone()
                    if row_pibo is not None:
                        claimee_point_reward += 1
                    clean_cursor(cursor)

                query = (
                    "UPDATE users SET user_points = user_points+%s WHERE user_id = %s"
                )
                data = (claimee_point_reward, row[3])
                cursor.execute(query, data)
                conn.commit()

                # Send DM to claimee.
                query = (
                    "SELECT user_personality FROM users WHERE user_id = %s"
                )
                data = (row[3], )
                cursor.execute(query, data)
                row_p = cursor.fetchone()
                claimee_personality = row_p[0]
                dms.append((row[3], get_response(cursor, "accept_claimee_valid", claimee_personality).format(message.author.name, claimee_point_reward)))

                # Delete claim.
                query = (
                    "DELETE FROM claims WHERE claim_id = %s"
                )
                data = (row[0], )
                cursor.execute(query, data)
                conn.commit()

                # Add claimee to bounty's list of completed users.
                query = (
                    "UPDATE bounties SET bounty_accepted = JSON_ARRAY_APPEND(bounty_accepted, '$', %s) WHERE "
                    "bounty_id = %s "
                )
                data = (row[3], row[1])
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
                    data = (BOUNTY_OWNER_POINT_INCREMENT, row[4])
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

            # If bounty belongs to user,
            # delete claim.
            # Send DM to claimee.

            query = "SELECT * FROM claims WHERE claim_bounty_creator = %s AND claim_id = %s"
            data = (message.author.id, split_message[2])
            cursor.execute(query, data)
            row = cursor.fetchone()
            if row is not None:
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
                data = (row[3], )
                cursor.execute(query, data)
                row_p = cursor.fetchone()
                claimee_personality = row_p[0]
                dms.append((row[3], get_response(cursor, "reject_claimee_valid", claimee_personality).format(message.author.name)))

                out_message += "{0}\n".format(get_response(cursor, "reject_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "reject_invalid", personality_id))
        else:
            out_message += "{0}\n".format(get_response(cursor, "claim_invalid", personality_id))

    else:
        # Display help and existing claims that the user has authority over, or made.
        out_message += "{0}\n".format(get_response(cursor, "claim", personality_id))
        out_message += "# BOUNTY HUNTER\n"
        out_message += format_command("# !claim -new [BOUNTY ID]", "Creates a new claim on a bounty.")
        out_message += format_command("# !claim -new [BOUNTY ID] [PILLAR NAME]", "Creates a new claim on a bounty, "
                                                                                 "with a pillar.")
        out_message += format_command("# !claim -new [BOUNTY ID] [PILLAR NAME] [PILLAR NAME] ...", "Creates a new "
                                                                                                   "claim on a "
                                                                                                   "bounty, "
                                                                                                   "with multiple "
                                                                                                   "pillars. Add as "
                                                                                                   "many pillars as "
                                                                                                   "appropriate.")
        out_message += format_command("# !claim -cancel [CLAIM ID]", "Rescinds a claim you've created.")
        out_message += "\n# BOUNTY CREATOR\n"
        out_message += format_command("# !claim -accept [CLAIM ID]", "Accepts a pending claim on a bounty you've "
                                                                     "created.")
        out_message += format_command("# !claim -reject [CLAIM ID]", "Rejects a pending claim on a bounty you've "
                                                                     "created.")

        query = "SELECT * FROM claims WHERE claim_bounty_creator = %s"
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("CLAIMS SUBMITTED TO YOU\n")
        out_message += "{0:<20} {1:<20}\n".format("{0} {1}".format("ID", "CLAIMANT"), "DESCRIPTION")
        for row in rows:
            query = "SELECT bounty_text FROM bounties WHERE bounty_id = %s"
            data = (row[1], )
            cursor.execute(query, data)
            row_bo = cursor.fetchone()
            desc = row_bo[0]
            desc = (desc[:18] + '..') if len(desc) > 20 else desc

            out_message += "{0:<20} {1:<20}\n".format("{0} {1}".format(row[0], get_user_name(row[3])), desc)

            query = "SELECT claim_pillars FROM claims WHERE claim_id = %s"
            data = (row[0], )
            cursor.execute(query, data)
            row_pi = cursor.fetchone()
            pillars = json.loads(row_pi[0])
            for pillar in pillars:
                query = (
                    "SELECT pillar_name FROM pillars where pillar_id = %s"
                )
                data = (pillar, )
                cursor.execute(query, data)
                row_pina = cursor.fetchone()
                out_message += "{0:<5}-{1}\n".format("", row_pina[0])

        query = "SELECT * FROM claims WHERE claim_claimee = %s"
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("CLAIMS SUBMITTED BY YOU\n")
        out_message += "{0:<20} {1:<20}\n".format("{0} {1}".format("ID", "OWNER"), "DESCRIPTION")
        for row in rows:
            query = "SELECT bounty_text FROM bounties WHERE bounty_id = %s"
            data = (row[1], )
            cursor.execute(query, data)
            row_bo = cursor.fetchone()
            desc = row_bo[0]
            desc = (desc[:18] + '..') if len(desc) > 20 else desc

            out_message += "{0:<20} {1:<20}\n".format("{0} {1}".format(row[0], get_user_name(row[4])), desc)

            query = "SELECT claim_pillars FROM claims WHERE claim_id = %s"
            data = (row[0], )
            cursor.execute(query, data)
            row_pi = cursor.fetchone()
            pillars = json.loads(row_pi[0])
            for pillar in pillars:
                query = (
                    "SELECT pillar_name FROM pillars where pillar_id = %s"
                )
                data = (pillar, )
                cursor.execute(query, data)
                row_pina = cursor.fetchone()
                out_message += "{0:<5}-{1}\n".format("", row_pina[0])

    return Response(text=end_response(out_message, conn, cursor), dms=dms)


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
        out_message += format_command("# !pillar -new [PILLAR NAME]", "Creates a new pillar.")
        out_message += format_command("# !pillar -rename [OLD PILLAR NAME] [NEW PILLAR NAME]", "Renames a pillar. The "
                                                                                               "pillar's height won't "
                                                                                               "change.")
        out_message += format_command("# !pillar -delete [PILLAR NAME]", "Deletes a pillar. Does not affect your "
                                                                         "points, but the pillar height will be lost "
                                                                         "forever.")
        out_message += format_command("# !pillar -favorite [PILLAR NAME]", "Favorites a pillar. Completing bounties "
                                                                           "using your favorite pillar will earn you "
                                                                           "extra points.")

        query = "SELECT * FROM pillars WHERE pillar_user = %s"
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("YOUR PILLARS\n")
        for row in rows:
            favorite_string = ""
            if row[3] == 1:
                favorite_string = "(FAVORITE)"
            out_message += "{0:<20} {1}\n".format(row[2], favorite_string)

    return Response(text=end_response(out_message, conn, cursor))


def points(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    # Display leaderboard.

    out_message += "{0}\n".format(get_response(cursor, "points", personality_id))
    out_message += format_command("# !points", "Displays your points, pillar heights, and leaderboard.")

    points_user_message = ""
    points_pillars_message = ""
    points_board_message = ""

    query = "SELECT * FROM users ORDER BY user_points DESC"
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
            points_user_message += "{0:<20}{1:<20}\n".format("{0}{1}".format(place, place_suffix), row[3])
        points_board_message += "{0:<20}{1:<20}{2:<4}{3}\n".format("{0}{1}".format(place, place_suffix), get_user_name(row[0]), row[3], build_int_block(int(row[3])))

    query = "SELECT * FROM pillars WHERE pillar_user = %s ORDER BY pillar_points DESC"
    data = (message.author.id, )
    cursor.execute(query, data)
    rows = cursor.fetchall()
    for row in rows:
        name = row[2]
        if row[3] == 1:
            name += " (*)"
        points_pillars_message += "{0:<20}{1:<4}{2}\n".format(name, row[4], build_int_block(int(row[4])))

    out_message += "\n{0}\n".format(get_response(cursor, "points_user", personality_id))
    out_message += "{0:<20}{1:<20}\n".format("POSITION", "POINTS")
    out_message += points_user_message
    out_message += "{0:<20}{1:<20}\n".format("PILLAR", "HEIGHT (Activity)")
    out_message += points_pillars_message
    out_message += "\n{0}\n".format(get_response(cursor, "points_leaderboard", personality_id))
    out_message += "{0:<20}{1:<20}{2:<20}\n".format("POSITION", "NAME", "POINTS")
    out_message += points_board_message
    return Response(text=end_response(out_message, conn, cursor))


def practice(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 2:
        # Get pillars if present.
        pillars = []
        for i, pillar in enumerate(split_message):
            if i < 1:
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
                    out_message += "{0}\n".format(get_response(cursor, "practice_invalid_pillar", personality_id))
                    return Response(text=end_response(out_message, conn, cursor))
        for pillar in pillars:
            query = (
                "UPDATE pillars SET pillar_points = pillar_points+%s WHERE pillar_id = %s"
            )
            data = (1, pillar)
            cursor.execute(query, data)
            conn.commit()
        out_message += "{0}\n".format(get_response(cursor, "practice_valid", personality_id))

    else:
        # Display help and the user's existing pillars.
        out_message += "{0}\n".format(get_response(cursor, "practice", personality_id))
        out_message += format_command("# !practice [PILLAR NAME]", "Increases the height of one pillar.")
        out_message += format_command("# !practice [PILLAR NAME] [PILLAR NAME] ...", "Increases the heights of "
                                                                                     "multiple pillars. Add as many "
                                                                                     "pillars as are pertinent.")

    return Response(text=end_response(out_message, conn, cursor))


def timeoffset(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 2:
        hours = 0
        minutes = 0
        rex = re.compile("(^[-+]\\d{1,2}$)|(^0$)|(^[-+]\\d{1,2}:\\d{2}$)|(^0{1,2}:0{2}$)")
        if rex.match(split_message[1]):
            split_time = split_message[1].split(":")
            hours = int(split_time[0])
            if len(split_time) == 2:
                minutes = int(split_time[1])
            if (OFFSET_MIN_HOUR <= hours <= OFFSET_MAX_HOUR) and (OFFSET_MIN_MIN <= minutes <= OFFSET_MAX_MIN):
                if hours < 0:
                    offset = "{:03d}".format(hours) + "{:02d}".format(minutes)
                else:
                    offset = "{:02d}".format(hours) + "{:02d}".format(minutes)
                query = (
                    "UPDATE users SET user_time_offset = %s WHERE user_id = %s"
                )
                data = (offset, message.author.id)
                cursor.execute(query, data)
                conn.commit()
                out_message += "{0}\n".format(get_response(cursor, "timezone_valid", personality_id))
            else:
                out_message += "{0}\n".format(get_response(cursor, "timezone_invalid_bounds", personality_id))
        else:
            out_message += "{0}\n".format(get_response(cursor, "timezone_invalid_syntax", personality_id))

    else:
        # Display help and the user's existing pillars.
        out_message += "{0}\n".format(get_response(cursor, "timezone", personality_id))
        out_message += format_command("# !timezone [NEW TIME ZONE OFFSET] (!timezone -9) (!timezone -09:00)", "Adjusts the UTC offset displayed for commands you write. Does not affect the UTC offset displayed for commands others write.")

        query = "SELECT user_time_offset FROM users WHERE user_id = %s"
        data = (message.author.id, )
        cursor.execute(query, data)
        row = cursor.fetchone()
        if row is not None:
            out_message += "YOUR OFFSET: {0}\n".format(row[0])

    return Response(text=end_response(out_message, conn, cursor))


def block_test(message):
    out_message = ""
    out_message += "\u2800\n\u2800\n⠀　⠀⠀⠀　:hatched_chick:\n⠀　⠀⠀ʙɪɢ cʜɪcκ ɪs\n⠀　𝗪𝗔𝗧𝗖𝗛𝗜𝗡𝗚 𝗬𝗢𝗨\n\u2800"
    return Response(text=out_message)


def dm_test(message):
    dms = []
    dms.append((message.author.id, "Hi."))
    return Response(text=":hatched_chick:", dms=dms)


def visualizer_overview(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]
    user_color = "[[C:199:255,133]]"

    query = "SELECT * FROM pillars WHERE pillar_user = %s ORDER BY pillar_points DESC"
    data = (message.author.id,)
    cursor.execute(query, data)
    rows = cursor.fetchall()
    graph_data = [[], []]
    for row in rows:
        graph_data[0].append(row[2])
        graph_data[1].append(int(row[4]))

    query = "SELECT * FROM users ORDER BY user_points DESC"
    cursor.execute(query)
    rows = cursor.fetchall()
    leaderboard_text = "LEADERBOARD\n\n"
    leaderboard_text_names = "\n\n"
    leaderboard_text_points = "\n\n"
    place = 0
    previous_points = -1
    for i, row in enumerate(rows):
        place_prefix = "[[C:84,189,167]]"
        place_suffix = "th[[c]]"
        if row[3] != previous_points:
            place = i + 1
        if place == 1:
            place_prefix = "[[C:255,206,0]]"
            place_suffix = "st[[c]]"
        elif place == 2:
            place_prefix = "[[C:204,204,204]]"
            place_suffix = "nd[[c]]"
        elif place == 3:
            place_prefix = "[[C:180,131,80]]"
            place_suffix = "rd[[c]]"
        elif place > 4:
            break
        previous_points = row[3]
        leaderboard_text += "{0}{1}{2}\n".format(place_prefix, place, place_suffix)
        if get_user_name(row[0]) == message.author.name:
            leaderboard_text_names += "{0}{1}{2}\n".format(user_color, get_user_name(row[0]), "[[c]]")
            leaderboard_text_points += "{0}{1}{2}\n".format(user_color, row[3], "[[c]]")
        else:
            leaderboard_text_names += "{0}\n".format(get_user_name(row[0]))
            leaderboard_text_points += "{0}\n".format(row[3])

    query = "SELECT * FROM claims WHERE claim_bounty_creator = %s"
    data = (message.author.id,)
    cursor.execute(query, data)
    rows = cursor.fetchall()
    claim_text = "OPEN CLAIMS\n\n"
    for row in rows:
        query = "SELECT bounty_text FROM bounties WHERE bounty_id = %s"
        data = (row[1],)
        cursor.execute(query, data)
        row_bo = cursor.fetchone()
        desc = row_bo[0]
        desc = (desc[:16-2] + '..') if len(desc) > 16 else desc
        claim_text += "{0:<3} {1:<20}\n".format("{0} {1}".format(row[0], get_user_name(row[3])), desc)
    if len(rows) == 0:
        claim_text += "[[C:255,255,0]]No open claims for now.[[c]]"

    v = visualizer.Visualizer()
    v.build_background()
    v.build_image('images/static/border.png', 0, 0, visualizer.WIDTH, visualizer.HEIGHT)
    v.build_text(visualizer.FONT_EIGHT, 232, 55, end_x=visualizer.WIDTH, end_y=visualizer.HEIGHT, string="hi " + message.author.name)
    v.build_text(visualizer.FONT_SIX, 17, 91, end_x=208, end_y=175, string=leaderboard_text)
    v.build_text(visualizer.FONT_SIX, 17 + 8*5, 91, end_x=208, end_y=175, string=leaderboard_text_names)
    v.build_text(visualizer.FONT_SIX, 17 + 8*20, 91, end_x=208, end_y=175, string=leaderboard_text_points)
    v.build_text(visualizer.FONT_SIX, 219, 91, end_x=420, end_y=175, string=claim_text)
    v.build_text(visualizer.FONT_SIX, 431, 91, end_x=622, end_y=175, string='COMMON COMMANDS')
    v.build_graph(start_x=41, start_y=212, end_x=302, end_y=365, data=graph_data)
    file = v.finish_image()
    cursor.close()
    conn.close()
    return Response(text="", file=file)


response_options = {
    "!help": ("List commands.", helpp),
    "!overview": ("Display things you should know.", visualizer_overview),
    "!bounty": ("Create and view bounties.", bounty),
    "!claim": ("Create, accept, reject, and view claims on bounties.", claim),
    "!practice": ("Record that you've practiced a pillar.", practice),
    "!pillar": ("Create and view your pillars.", pillar),
    "!points": ("View your points and the leaderboard.", points),
    "!personality": ("Change bot personality.", personality),
    "!timezone": ("Change displayed timezone.", timeoffset),
    "!big": ("BIG CHICK", block_test),
    "!dm_test": ("Bot will say 'hi' to you in a DM.", dm_test)
}


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    print("\nGUILDS")
    for guild in client.guilds:
        print("{0}".format(guild.name))
    print("\nUSERS")
    for user in client.users:
        print("{0}".format(user.name))


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
        if check_join(message.author) is True:
            response = response_options[split_message[0]][1](message)
            out_file = None
            if response.file is not None:
                out_file = discord.File(fp=response.file)
            await message.channel.send(response.text, file=out_file)
            if response.dms is not None:
                for dm in response.dms:
                    user = client.get_user(dm[0])
                    await user.send(dm[1])
        else:
            await message.channel.send("Please subscribe to bot first by typing \"!join\"")
    elif split_message[0][0] == '!':
        await message.channel.send(command_bad(message).text)


@client.event
async def on_member_join(member):
    print('{0} has joined server.'.format(member))


client.run(os.environ['BBB_TOK'])
