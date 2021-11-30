import asyncio
import json
import os
import sys
import re
import requests
from collections import Counter

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json", encoding="cp866") as file:
        config = json.load(file)


# We will recieve the entire red team and blue team dictionaries with memberObjs

class Stats:
    lol_roles = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']

# make a method for fetching a member's match stats so we can add it to the database

    @staticmethod
    async def get_stats(red, blue):
        print('inside get_stats, stats.py')
        red_members = []
        blue_members = []
        for role in Stats.lol_roles:
            red_members.append(red[role])
            blue_members.append(blue[role])
        all_members = red_members + blue_members
        puuid_dict = {}
        for member in all_members:
            response = await Stats.fetch_puuid(member)
            if response:
                puuid_dict[response] = member

        matchIdlst = []
        for puuid in puuid_dict:
            response = await Stats.fetch_match_ids(puuid)
            if response:
                matchIdlst.append(response[0])

        # Getting most common match id
        matchId = Stats.Most_Common(matchIdlst)
        print('\nmatchId: ', matchId)
        response = await Stats.fetch_match_data(matchId)
        metadata_participants = response.json()['metadata']['participants']
        print('\nmetadata_participants: ', metadata_participants)
        info_participants = response.json()['info']['participants']

        # {discordid: [Champion_name, win, kills, deaths, assists, CreepScore????, doublekills, triplekills,
        # quadrakills, pentakills, totalDamageDealt, totalDamageTaken]}

        stats = {}
        for index in range(len(info_participants)):
            print('inside get_stats, for loop')
            participant = info_participants[index]
            puuid = metadata_participants[index]
            discord_id = puuid_dict[puuid].id        # discord_id

            # win, kills, deaths, assists, doubleKills, tripleKills, quadraKills, pentaKills
            try:
                creepScorePerMin = participant["totalMinionsKilled"] / (participant["timePlayed"] / 60)
            except ZeroDivisionError:
                creepScorePerMin = 0
            statslst = {"win": participant["win"], "kills": participant["kills"], "deaths": participant["deaths"],
                        "assists": participant["assists"], 'creepScore': creepScorePerMin,
                        "totalMinionsKilled": participant["totalMinionsKilled"], "timePlayed":(participant["timePlayed"]/60),
                        "tripleKills": participant["tripleKills"],"quadraKills": participant["quadraKills"],
                        "pentaKills": participant["pentaKills"], "totalDamageDealt": participant["totalDamageDealt"],
                        "totalDamageTaken": participant["totalDamageTaken"]}
            stats[discord_id] = statslst
        print('stats list: ', stats)
        return stats

    @staticmethod
    def Most_Common(lst):
        data = Counter(lst)
        return data.most_common(1)[0][0]

    @staticmethod
    def most_common(lst):
        data = Counter(lst)
        return max(lst, key=data.get)

    @staticmethod
    async def fetch_match_data(matchId):
        API_KEY = config['RIOT_API_KEY']
        region = "americas"
        for i in range(3):
            response = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}?api_key={API_KEY}")
            if response.status_code == 200:
                return response

    @staticmethod
    async def fetch_match_ids(puuid):
        API_KEY = config['RIOT_API_KEY']
        region = "americas"
        no_of_matches = 1
        for i in range(3):
            response = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={no_of_matches}&api_key={API_KEY}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code != 200:
                return False

    @staticmethod
    async def fetch_puuid(member):
        API_KEY = config['RIOT_API_KEY']
        league_id = re.split("[\[\] ]+", member.display_name)

        if len(league_id) > 2:
            league_id.pop(0)
            league_id.pop(0)
            league_id = ' '.join(league_id)
        elif len(league_id) == 2:
            league_id = league_id[1]

        league_region = 'na1'  # hardcoded
        for i in range(3):
            response = requests.get(
                f"https://{league_region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{league_id}?api_key={API_KEY}")
            if response.status_code == 200:
                return response.json()['puuid']
            elif response.status_code == 404:
                return False
            elif response.status_code == 429 or response.status_code == 503 or response.status_code == 504:
                print("Rate limit exceeded, retrying....")
                await asyncio.sleep(1)

            elif response.status_code in [400, 401, 403, 405, 500, 502]:
                print('API Error')
                break

