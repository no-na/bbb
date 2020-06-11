import discord
import os
import mysql.connector

client = discord.Client()


def connect():
    conn = mysql.connector.connect(database='bbb',
                                   user='root',
                                   password=os.environ['SQL_PASS'])
    return conn


def checkJoin(member):
    conn = connect()
    cursor = conn.cursor
    cursor.execute(
        "SELECT EXISTS(SELECT * FROM users WHERE user_id = {0})".format(member.id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if(row == 1):
        return True
    return False


def join(message):
    if(checkJoin(message.author) is False):
        conn = connect()
        cursor = conn.cursor
        cursor.execute("INSERT INTO users (user_id) VALUES ({0})".format(message.author.id))
        cursor.close()
        conn.close()
        return "You joined."
    else:
        return "You already joined."


def personality(message):
    split_message = message.content.split()
    out_message = ""
    conn = connect()
    cursor = conn.cursor
    if split_message.len() >= 2:
        personality_id = split_message[1]
        cursor.execute("SELECT EXISTS(SELECT * FROM personalities WHERE personality_id = {0})".format(personality_id))
        row = cursor.fetchone()
        if(row == 1):
            cursor.execute("UPDATE users SET user_personality = {0} WHERE user_id = {1}".format(personality_id, message.author.id))
            out_message += "Personality has been changed.."
        else:
            out_message += "That personality doesn't exist. Nothing has been changed."
    else:
        out_message += "To select a new personality, enter `!personality _`, replacing the underscore with the number of the personality.\n"
        cursor.execute("SELECT * FROM personalities")
        rows = cursor.fetchall()
        for row in rows:
            out_message += "{0}. **{1}:** {2}\n".format(row[0], row[1], row[2])
    cursor.close()
    conn.close()
    return out_message


response_options = {
    "!personality": personality
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
        if checkJoin(message.author):
            await message.channel.send(response_options[split_message[0]](message))
        else:
            await message.channel.send("Please subscribe to bot first by typing \"!join\"")
    elif split_message[0][0] == '!':
        await message.channel.send("Unrecognized command.")


@client.event
async def on_member_join(member):
    print('{0} has joined server.'.format(member))


client.run(os.environ['BBB_TOK'])
