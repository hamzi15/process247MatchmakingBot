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
    with open("config.json") as file:
        config = json.load(file)


# We will recieve the entire red team and blue team dictionaries with memberObjs

class Stats:
    lol_roles = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']

# make a method for fetching a member's match stats so we can add it to the database

    @staticmethod
    def get_stats(red, blue):
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
            response = Stats.fetch_match_ids(puuid)
            if response:
                matchIdlst.append(response[0])

        # Getting most common match id
        matchId = Stats.Most_Common(matchIdlst)

        response = Stats.fetch_match_data(matchId)
        metadata_participants = response.json()['metadata']['participants']
        info_participants = response.json()['info']['participants']
        # {discordid: [Champion_name,win,kills,deaths,assists,CreepScore????,doublekills,triplekills,quadrakills,pentakills,totalDamageDealt,totalDamageTaken]}
        stats = {}
        for index in range(len(info_participants)):
            participant = info_participants[index]
            puuid = metadata_participants[index]
            discordid = puuid_dict[puuid].id        # discordid

            # win, kills, deaths, assists, doubleKills, tripleKills, quadraKills, pentaKills
            creepScorePerMin = participant["totalMinionsKilled"] / (participant["timePlayed"] / 60)
            statslst = {"win": participant["win"], "kills": participant["kills"], "deaths": participant["deaths"],
                        "assists": participant["assists"], 'creepScore': creepScorePerMin,
                        "totalMinionsKilled": participant["totalMinionsKilled"], "timePlayed":(participant["timePlayed"]/60),
                        "tripleKills": participant["tripleKills"],"quadraKills": participant["quadraKills"],
                        "pentaKills": participant["pentaKills"], "totalDamageDealt": participant["totalDamageDealt"],
                        "totalDamageTaken": participant["totalDamageTaken"]}
            stats[discordid] = statslst
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
    def fetch_match_data(matchId):
        API_KEY = config['RIOT_API_KEY']
        region = "americas"
        for i in range(3):
            response = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}?api_key={API_KEY}")
            if response.status_code == 200:
                return response

    @staticmethod
    def fetch_match_ids(puuid):
        API_KEY = config['RIOT_API_KEY']
        region = "americas"
        no_of_matches = 1
        for i in range(3):
            response = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={no_of_matches}&api_key={API_KEY}")
            if response.status_code == 200:
                return response.json()

    @staticmethod
    def fetch_puuid(member):
        API_KEY = config['RIOT_API_KEY']
        league_id = re.split('[ ]', member.display_name)
        if len(league_id) > 1:
            league_id = f"{league_id[1]} {league_id[2]}"
        else:
            league_id = league_id[0]

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

