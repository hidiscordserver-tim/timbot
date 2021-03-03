import discord
import os
import time
import discord.ext
from discord.utils import get
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, CheckFailure, check
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

intents = discord.Intents(messages=True)

load_dotenv()
client = discord.Client()
client = commands.Bot(command_prefix = '-T ')

debates_message_history = pd.DataFrame([['None',datetime(2000,1,1)]]*10)
debates_message_history.columns = ['User', 'Time']
debates_status = [0, 0.0] # [Num Users, Mean Time]
debates_status_code = 0 # 0: None, 1: Warning, 2: Slowmode
mod_update_channel = None

async def debates_update(num_users, mean_time, status):
    global mod_update_channel
    await mod_update_channel.send('#debates Update\nUsers: ' + str(num_users) + '\nMean Message Gap: ' + str(mean_time) + ' s\nStatus ' + str(status))

@client.event
async def on_ready():
    global mod_update_channel
    print("bot online")
    mod_update_channel = [x for x in client.get_all_channels() if x.name == os.getenv("MOD_UPDATE_CHANNEL")][0]
    await debates_update(0, 0, 10)

@client.event
async def on_message(msg):
    if msg.channel.name == 'debates' and not msg.author.bot:
        global debates_message_history
        global debates_status
        global debates_status_code

        debates_message_history = debates_message_history.append({'Time':msg.created_at, 'User':msg.author}, ignore_index=True)
        debates_message_history = debates_message_history.shift(-1).reset_index(drop=True).dropna()

        num_users = len(debates_message_history.loc[~(debates_message_history['User']=='None'), 'User'].drop_duplicates())
        mean_time = (debates_message_history.loc[~(debates_message_history['Time']==datetime(2000,1,1)), 'Time'].shift(-1) - debates_message_history.loc[~(debates_message_history['Time']==datetime(2000,1,1)), 'Time']).dropna().mean().total_seconds()

        debates_status_old = [x for x in debates_status] # Copy don't reference!
        debates_status = [num_users, mean_time]

        print(debates_status)

        update_posted = False

        if num_users == 2 and mean_time < 5:
            if debates_status_code != 1:
                debates_status_code = 1
                await msg.channel.edit(slowmode_delay=0)
                await debates_update(num_users, mean_time, 1)
                update_posted = True
        elif num_users >= 3 and mean_time < 5:
            if debates_status_code != 2:
                debates_status_code = 2
                await msg.channel.edit(slowmode_delay=15)
                await debates_update(num_users, mean_time, 2)
                update_posted = True
        else:
            if debates_status_code != 0:
                debates_status_code = 0
                await msg.channel.edit(slowmode_delay=0)
                await debates_update(num_users, mean_time, 0)
                update_posted = True

        if debates_status[0] != debates_status_old[0] or (debates_status[1] - debates_status_old[1]) > 5:
            # Post an update if it's newsworthy, even if the status code hasn't changed.
            if not update_posted:
                await debates_update(num_users, mean_time, debates_status_code)

@client.command()
async def debates(ctx):
    await debates_update(debates_status[0], debates_status[1], debates_status_code)

client.run(os.getenv("TOKEN"))
