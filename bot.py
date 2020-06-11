import discord
import os
import mysql.connector

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    splitMessage = message.content.split()

    if message.content.startswith('!personality'):
        await message.channel.send(question_personality())


@client.event
async def on_member_join(member):
    print('{0} has joined server.'.format(member))


def question_personality():
    out_message = "To select a new personality, enter `!personality _`, replacing the underscore with the number of the personality.\n"
    conn = mysql.connector.connect(database='bbb',
                                   user='root',
                                   password=os.environ['SQL_PASS'])

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personalities")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        out_message += "{0}. **{1}:** {2}\n".format(row[0],row[1],row[2])
    cursor.close()
    conn.close()
    return out_message


client.run(os.environ['BBB_TOK'])
