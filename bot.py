import discord
import os
import mysql.connector

client = discord.Client()

response_options = {}


def connect():
    conn = mysql.connector.connect(database='bbb',
                                   user='root',
                                   password=os.environ['SQL_PASS'])
    return conn


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
    if(checkJoin(message.author) is False):
        conn = connect()
        cursor = conn.cursor()
        query = (
            "INSERT INTO users(user_id)"
            "VALUES (%s)"
        )
        data = (message.author.id, )
        cursor.execute(query, data)
        conn.commit()
        cursor.close()
        conn.close()
        return "You joined."
    else:
        return "You already joined."


def helpp(message):
    out_message = "```stan\n"
    conn = connect()
    cursor = conn.cursor()
    query = (
        "SELECT user_personality FROM users WHERE user_id = %s"
    )
    data = (message.author.id, )
    cursor.execute(query, data)
    row = cursor.fetchone()
    personality_id = row[0]
    query = (
        "SELECT response_text FROM responses WHERE response_name = 'help' AND response_personality = %s"
    )
    data = (personality_id, )
    cursor.execute(query, data)
    row = cursor.fetchone()
    out_message += "{0}\n".format(row[0])
    for key in response_options:
        out_message += "{0:<20} {1:>20}\n".format(key, response_options[key][0])

    cursor.close()
    conn.close()
    out_message += "```"
    return out_message


def personality(message):
    split_message = message.content.split()
    out_message = "```stan\n"
    conn = connect()
    cursor = conn.cursor()
    if len(split_message) >= 2:
        personality_id = split_message[1]
        query = (
            "SELECT EXISTS(SELECT * FROM personalities WHERE personality_id = %s)"
        )
        data = (personality_id, )
        cursor.execute(query, data)
        row = cursor.fetchone()
        if(row[0] == 1):
            query = (
                "UPDATE users SET user_personality = %s WHERE user_id = %s"
            )
            data = (personality_id, message.author.id)
            cursor.execute(query, data)
            conn.commit()
            out_message += "Personality has been changed."
        else:
            out_message += "That personality doesn't exist. Nothing has been changed."
    else:
        out_message += "To select a new personality, enter !personality _, replacing the underscore with the number of the personality."
        out_message += "\n{0}".format("# personality [NUMBER]")
        query = ("SELECT * FROM personalities")
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            out_message += "{0:<20} {1:>20}\n".format("{0} {1}".format(row[0], row[1]), row[2])
    cursor.close()
    conn.close()
    out_message += "```"
    return out_message


response_options = {
    "!help": ("List commands.", helpp),
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
        await message.channel.send(join(message))
    elif split_message[0] in response_options:
        if checkJoin(message.author) is True:
            await message.channel.send(response_options[split_message[0]][1](message))
        else:
            await message.channel.send("Please subscribe to bot first by typing \"!join\"")
    elif split_message[0][0] == '!':
        await message.channel.send("Unrecognized command.")


@client.event
async def on_member_join(member):
    print('{0} has joined server.'.format(member))


client.run(os.environ['BBB_TOK'])
