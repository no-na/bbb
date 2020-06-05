import discord
import os
import mysql.conenctor

client = discord.Client()

@client.event
async def on_ready():
    connect()
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    splitMessage = message.content.split()

    if message.content.startswith('/personality'):
        await message.channel.send(question_personality())

@client.event
async def on_member_join(member):
    print('{0} has joined server.'.format(member))

def question_personality():
    out_message = "";

    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personalities")
        rows = cursor.fetchall()

        print('Total Row(s):', cursor.rowcount)
        for row in rows:
            print(row)
            out_message ="{0}\n".format(row)

    except Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()
    return outmessage

def connect_to_database():
    """ Connect to MySQL database """
    conn = None
    try:
        conn = mysql.connector.connect(host='localhost',
                                       database='BBB',
                                       user='root',
                                       password=os.environ['SQL_PASS'])
        if conn.is_connected():
            print('Connected to MySQL database')
            return conn

    except Error as e:
        print(e)

    finally:
        if conn is not None and conn.is_connected():
            conn.close()


client.run(os.environ['BBB_TOK'])