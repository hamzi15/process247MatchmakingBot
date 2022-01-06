import asyncio
import json
import os
import random
import re
import sys
import requests

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json", encoding="cp866") as file:
        config = json.load(file)


class MatchMaking:
    def __init__(self):
        self.dict_of_players = {}
        self.ranks = ['challenger', 'grandmaster', 'master', 'plat', 'platinum', 'gold', 'silver', 'bronze', 'iron']

    def matchmaker(self, lst_of_memberObjs):
        self.bubbleSort(lst_of_memberObjs)
        # matchmaking starts here then make two lists of players
        # also put a check if a player has no rank then give them diamond rank
        red = []
        blue = []
        redQueue = ['top', 'jungle', 'mid', 'adc', 'support']
        blueQueue = ['top', 'jungle', 'mid', 'adc', 'support']
        red_sum = 0
        blue_sum = 0
        # MATCHMAKING
        for member in lst_of_memberObjs:
            if len(blue) == 5:
                # self.assign_role(redQueue, member, red)
                red.append(member)
            elif len(red) == 5:
                # self.assign_role(blueQueue, member, blue)
                blue.append(member)
            elif red_sum == blue_sum:
                choice = random.randint(0, 1)
                if choice == 0:
                    red.append(member)
                else:
                    blue.append(member)
            elif red_sum < blue_sum:
                red.append(member)
            elif red_sum > blue_sum:
                blue.append(member)
            for member in red:
                red_sum += self.dict_of_players[member][0]
            for member in blue:
                blue_sum += self.dict_of_players[member][0]

        red = self.assign_role(redQueue, red)
        blue = self.assign_role(blueQueue, blue)

        return red, blue

    def assign_role(self, list_of_roles, members):
        dict = {}
        not_assigned = []
        for member in members:
            member_roles = self.dict_of_players[member][1:]
            if member_roles[0].lower() in list_of_roles:  # assign all possible primary roles
                dict[member_roles[0]] = member
                list_of_roles.remove(member_roles[0])
            else:  # else appedn to not assigned list
                not_assigned.append(member)
        still_not_assigned = []

        for member in not_assigned:
            member_roles = self.dict_of_players[member][1:]
            if member_roles[1].lower() in list_of_roles:  # now check if secondary role is available
                dict[member_roles[1]] = member
                list_of_roles.remove(member_roles[1])
            elif member_roles[0] != 'primary' and (self.dict_of_players[dict[member_roles[0]]][
                2]).lower() in list_of_roles:  # check if the previous main holder has a secondary which they can switch to
                prev_role_holder = dict[member_roles[0]]
                dict[member_roles[0]] = member  # assign the primary to this one
                dict[self.dict_of_players[prev_role_holder][2]] = prev_role_holder  # assign the secondary to this one
                list_of_roles.remove(self.dict_of_players[prev_role_holder][2])
            elif member_roles[1] != 'secondary' and (self.dict_of_players[dict[member_roles[1]]][
                2]).lower() in list_of_roles:  # check if the previous main holder has a secondary which they can switch to
                prev_role_holder = dict[member_roles[1]]
                dict[member_roles[1]] = member  # assign the primary to this one
                dict[self.dict_of_players[prev_role_holder][2]] = prev_role_holder  # assign the secondary to this one
                list_of_roles.remove(self.dict_of_players[prev_role_holder][2])
            else:
                still_not_assigned.append(member)
        for member in still_not_assigned:
            member_roles = self.dict_of_players[member][1:]
            if member_roles[0].lower() in list_of_roles:  # assign all possible primary roles
                dict[member_roles[0]] = member
                list_of_roles.remove(member_roles[0])
            elif member_roles[1].lower() in list_of_roles:  # now check if secondary role is available
                dict[member_roles[1]] = member
                list_of_roles.remove(member_roles[1])
            else:
                dict[list_of_roles.pop()] = member

        return dict

    ''''
    def assign_role(self, queue, member, dict):  # (red or blue queue, member from lst[index], and red or blue dict)
        member_roles = self.dict_of_players[member][
                       1:]  # Now the function can go through more roles or have none and still assign
        print('inside assign role')
        role_assigned = False
        for role in member_roles:
            if role in queue:
                dict[role] = member
                role_assigned = True
                queue.remove(role)
                break
        if not role_assigned:
            dict[queue.pop()] = member'''

    @staticmethod
    async def fetch_rank(member):
        print("inside fetch_rank")
        # API action here
        API_KEY = config["RIOT_API_KEY"]

        # If display name [ADC] P247 Paint then we need to remove [ADC]
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
                f'https://{league_region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{league_id}?api_key={API_KEY}')
            print('fetch_rank status code: ', response.status_code)
            if response.status_code == 200:
                summoner_id = response.json()['id']
                summoner_stats = requests.get(
                    f'https://{league_region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={API_KEY}').json()
                return summoner_stats
            elif response.status_code == 404:
                return False
            elif response.status_code == 429 or response.status_code == 503 or response.status_code == 504:
                print("Rate limit exceeded retrying....")
                await asyncio.sleep(1)

            elif response.status_code in [400, 401, 403, 405, 500, 502]:
                print('API Error')
                break

    @staticmethod
    def player_valuation(tier, rank, wins, loses, lp):
        totalMatches = wins + loses
        WinRate = (wins / totalMatches) * 100  # Percentage winrate
        mmr = int
        print('inside rank_value')
        tier = tier.lower()
        rank_precedence = ["iron IV", "iron III", "iron II", "iron I",
                           "bronze IV", "bronze III", "bronze II", "bronze I",
                           "silver IV", "silver III", "silver II", "silver I",
                           "gold IV", "gold III", "gold II", "gold I",
                           "platinum IV", "platinum III", "platinum II", "platinum I",
                           "diamond IV", "diamond III", "diamond II", "diamond I", "master I"]
        tier_rank = f"{tier} {rank}"
        if WinRate >= 55:
            if tier_rank in rank_precedence and rank_precedence.index(tier_rank) < 22:
                index = 0
                for prec in rank_precedence:
                    if tier_rank == prec:
                        index = rank_precedence.index(prec)
                if WinRate < 65:
                    tier_rank = rank_precedence[index + 1]
                elif WinRate < 75:
                    tier_rank = rank_precedence[index + 2]
                else:
                    tier_rank = rank_precedence[index + 3]

        tier, rank = tier_rank.split()[0], tier_rank.split()[1]
        if tier == "iron":
            if rank == "III":
                mmr = 1.25
            elif rank == "II":
                mmr = 1.5
            elif rank == "I":
                mmr = 2
            else:
                mmr = 1
        elif tier == "bronze":
            if rank == "III":
                mmr = 2.25
            elif rank == "II":
                mmr = 2.5
            elif rank == "I":
                mmr = 3
            else:
                mmr = 2
        elif tier == "silver":
            if rank == "III":
                mmr = 4.25
            elif rank == "II":
                mmr = 4.5
            elif rank == "I":
                mmr = 5
            else:
                mmr = 4
        elif tier == "gold":
            if rank == "III":
                mmr = 5.5
            elif rank == "II":
                mmr = 6
            elif rank == "I":
                mmr = 7
            else:
                mmr = 5
        elif tier == "platinum":
            if rank == "III":
                mmr = 9
            elif rank == "II":
                mmr = 10
            elif rank == "I":
                mmr = 12
            else:
                mmr = 8
        elif tier == "diamond":
            if rank == "III":
                mmr = 15
            elif rank == "II":
                mmr = 17
            elif rank == "I":
                mmr = 21
            else:
                mmr = 13
        elif tier == "master" or tier == "grandmaster" or tier == "challenger":
            mmr = 22
            lpValue = (int(lp / 100)) * 2
            mmr += lpValue

        return mmr

    def bubbleSort(self, arr):
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if self.dict_of_players[arr[j]][0] < self.dict_of_players[arr[j + 1]][0]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
