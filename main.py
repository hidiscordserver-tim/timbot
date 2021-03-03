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
debates_status = False # 0: None, 1: Warning, 2: Slowmode

@client.event
async def on_ready():
    print("bot online")

@client.event
async def on_message(msg):
    if msg.channel.name == 'debates' and not msg.author.bot:
        global debates_message_history
        global debates_status

        debates_message_history = debates_message_history.append({'Time':msg.created_at, 'User':msg.author}, ignore_index=True)
        debates_message_history = debates_message_history.shift(-1).reset_index(drop=True).dropna()

        num_users = len(debates_message_history.loc[~(debates_message_history['User']=='None'), 'User'].drop_duplicates())
        mean_time = (debates_message_history.loc[~(debates_message_history['Time']==datetime(2000,1,1)), 'Time'].shift(-1) - debates_message_history.loc[~(debates_message_history['Time']==datetime(2000,1,1)), 'Time']).dropna().mean().total_seconds()

        if num_users == 2 and mean_time < 5:
            if debates_status != 1:
                await msg.channel.edit(slowmode_delay=0)
                await msg.channel.send('Users: ' + str(num_users) + '\nMean Message Gap: ' + str(mean_time) + ' s\nStatus 1 (monitoring)')
                debates_status = 1
        elif num_users >= 3 and mean_time < 5:
            if debates_status != 2:
                await msg.channel.edit(slowmode_delay=15)
                await msg.channel.send('Users: ' + str(num_users) + '\nMean Message Gap: ' + str(mean_time) + ' s\nStatus 2 (slow-mode)')
                debates_status = 2
        else:
            if debates_status != 0:
                await msg.channel.edit(slowmode_delay=0)
                await msg.channel.send('Users: ' + str(num_users) + '\nMean Message Gap: ' + str(mean_time) + ' s\nStatus 0 (normal)')
                debates_status = 0

client.run(os.getenv("TOKEN"))
