import discord
import os
import mysql.connector
from datetime import datetime, timedelta

client = discord.Client()

response_options = {}


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
        personality_id = row[0]
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
            out_message += "{0:<20} {1}\n".format("{0} {1} Expires {2} UTC".format(row[0], client.get_user(row[4]).name), row[3], row[2])

    return (end_response(out_message, conn, cursor), )


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
                "SELECT EXISTS(SELECT * FROM bounties WHERE bounty_creator != %s AND bounty_id = %s AND JSON_CONTAINS(bounty_accepted,%s) = 0 AND bounty_expiration > NOW())"
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
                query = (
                    "INSERT INTO claims(claim_bounty_id, claim_creation, claim_expiration, claim_claimee, claim_bounty_creator)"
                    "VALUES (%s,%s,%s,%s,%s)"
                )
                now = datetime.utcnow()
                data = (split_message[2], now.strftime('%Y-%m-%d %H:%M:%S'), bounty_info[0], message.author.id, bounty_info[1])
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
        else:
            out_message += "{0}\n".format(get_response(cursor, "claim_invalid", personality_id))

    else:
        # Display help and existing claims that the user has authority over, or made.
        out_message += "{0}\n".format(get_response(cursor, "claim", personality_id))
        out_message += "{0}".format("# !claim -new [BOUNTY ID]\n")
        out_message += "{0}".format("# !claim -new [BOUNTY ID] [PILLAR NAME]\n")
        out_message += "{0}".format("# !claim -new [BOUNTY ID] [PILLAR NAME] [PILLAR NAME] ...\n")
        out_message += "{0}".format("# !claim -delete [CLAIM ID]\n")

        query = ("SELECT * FROM claims WHERE claim_bounty_creator = %s")
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("CLAIMS SUBMITTED TO YOU\n")
        for row in rows:
            out_message += "{0:<20} {1}\n".format("{0} {1}".format(row[0], row[5]), row[4])

        query = ("SELECT * FROM claims WHERE claim_claimee = %s")
        data = (message.author.id, )
        cursor.execute(query, data)
        rows = cursor.fetchall()
        out_message += "\n{0}".format("CLAIMS SUBMITTED BY YOU\n")
        for row in rows:
            out_message += "{0:<20} {1}\n".format("{0} {1}".format(row[0], row[5]), row[4])

    return (end_response(out_message, conn, cursor), dms)


def accept(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 2:
        # Attempt to accept a claim.
        pass
    else:
        # Display help.
        pass

    return (end_response(out_message, conn, cursor), )


def refuse(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 2:
        # Attempt to refuse a claim.
        pass
    else:
        # Display help.
        pass

    return (end_response(out_message, conn, cursor), )


def pillar(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    if len(split_message) >= 3:
        if split_message[1] == "-new":
            pass
        elif split_message[1] == "-rename":
            pass
        elif split_message[1] == "-delete":
            pass
        elif split_message[1] == "-favorite":
            pass
        else:
            pass
    else:
        # Display help and the user's existing pillars.
        pass

    return (end_response(out_message, conn, cursor), )


def leaderboard(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    # Display leaderboard.

    return (end_response(out_message, conn, cursor), )


def stats(message):
    split_message = message.content.split()
    setup = setup_response(message.author.id)
    out_message = setup[0]
    conn = setup[1]
    cursor = setup[2]
    personality_id = setup[3]

    # Display personal statistics.

    return (end_response(out_message, conn, cursor), )


response_options = {
    "!help": ("List commands.", helpp),
    "!bounty": ("Create or view bounties.", bounty),
    "!claim": ("Create or view claims on bounties.", claim),
    "!accept": ("Accept a claim on a bounty you made.", accept),
    "!reject": ("Reject a claim on a bounty you made.", refuse),
    "!pillar": ("Edit or view your pillars.", pillar),
    "!leaderboard": ("View leaderboard.", leaderboard),
    "!stats": ("View your personal stats.", stats),
    "!personality": ("Change bot personality.", personality)
}


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    split_message = message.content.split()
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
