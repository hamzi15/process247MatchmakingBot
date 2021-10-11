import os
import sys
import json
import discord
from riotwatcher import LolWatcher,ApiError
import random

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


class MatchMaking:
    def __init__(self):
        self.dict_of_players = {}
        self.ranks = ['challenger', 'grandmaster', 'master', 'plat', 'platinum', 'gold', 'silver', 'bronze', 'iron']

    def prepare_roles_ranks(self,lst_of_memberObjs):
        norank_members = []
        for member in lst_of_memberObjs:
            lol_roles = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
            no_of_roles = 2  # some people have more than two roles so we ignore the extra roles
            found_rank_flag = False
            self.dict_of_players[member] = ['Rank_goes_here','Primary_role','Secondary role']
            for role in member.roles:
                if no_of_roles:
                    if role.name.startswith('Mains '):
                        # 'Mains' is the primary role
                        primary_role = (role.name.split())[1]
                        if primary_role in lol_roles:
                            self.dict_of_players[member].append(primary_role)
                            no_of_roles -= 1

                    ########### this is the secondary role. consider this in matchmaking too #########
                    if role.name.lower() in lol_roles:
                        secondary_role = role.name
                        no_of_roles -= 1

                if role.name.lower() in self.ranks:  # searching for rank in member roles
                    rank = role.name.lower()
                    found_rank_flag = True
                    self.dict_of_players[member][0] = MatchMaking.rank_value(rank)

            if not found_rank_flag:  # if rank not found in roles THEN fetch from API endpoint
                    norank_members.append(member)
        return norank_members


    def matchmaker(self,lst_of_memberObjs):
        self.bubbleSort(lst_of_memberObjs)
        # matchmaking starts here then make two lists of players
        # also put a check if a player has no rank then give them diamond rank
        red = {}
        blue = {}
        redQueue = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
        blueQueue = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
        red_sum = 0
        blue_sum = 0
        #MATCHMAKING
        for member in lst_of_memberObjs:
            if len(blue) == 5:
                self.assign_role(redQueue,member,red)
            elif len(red) == 5:
                self.assign_role(blueQueue,member,blue)
            elif red_sum == blue_sum:
                choice = random.randint(0,1)
                if choice == 0:
                    self.assign_role(redQueue,member,red)
                else:
                    self.assign_role(blueQueue,member,blue)
            elif red_sum < blue_sum:
                self.assign_role(redQueue,member,red)
            elif red_sum > blue_sum:
                self.assign_role(blueQueue,member,blue)
            for role in red:
                member = red[role]
                red_sum += self.dict_of_players[member][0]
            for role in blue:
                member = blue[role]
                blue_sum += self.dict_of_players[member][0]

        return red, blue

    def assign_role(self,queue,member,dict): #(red or blue queue, member from lst[index], and red or blue dict)
        member_roles = self.dict_of_players[member][1:]  #Now the function can go through more roles or have none and still assign
        role_assigned = False
        for role in member_roles:
            if role in queue:
                dict[role] = member
                role_assigned = True
                queue.remove(role)
                break
        if role_assigned == False:
            dict[queue.pop()] = member

    @staticmethod
    def fetch_rank(member):
        #API action here
        API_KEY = config["RIOT_API_KEY"]
        watcher = LolWatcher(API_KEY)

        league_id = member.display_name
        #If display name [ADC] P247 Paint then we need to remove [ADC]
        if league_id.startswith('['):
            removal = ""
            for char in league_id:
                if char == "]":
                    removal +="] "
                    break
                else:
                    removal+=char
            league_id = league_id[len(removal):]
        league_region = 'na1' #hardcoded

        try:
            summonerID = watcher.summoner.by_name(league_id,league_region)
            rank_stats = watcher.league.by_summoner(summonerID['id'])
            rank = rank_stats[0]['tier']
            return rank

        except ApiError as err:
            if err.response.status_code == 429:
                print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
                print('this retry-after is handled by default by the RiotWatcher library')
                print('future requests wait until the retry-after time passes')
            elif err.response.status_code == 404:
                print('Summoner with that ridiculous name not found.')
            elif err.response.status_code == 403:
                print("API Key is invalid.")
            else:
                return [{'tier':'Unranked'}] #RECHECK THIS

    @staticmethod
    def rank_value(rank):
        rank = rank.lower()
        if rank == 'challenger':
            return 9
        elif rank == 'grandmaster':
            return 8
        elif rank == 'master':
            return 7
        elif rank =='plat':
            return 5
        elif rank == 'gold':
            return 4
        elif rank == 'silver':
            return 3
        elif rank == 'bronze':
            return 2
        elif rank == 'iron':
            return 1
        else: # diamond or unranked
            return 6

    def bubbleSort(self,arr):
        n = len(arr)
        for i in range(n):
            for j in range(0, n-i-1):
                if self.dict_of_players[arr[j]][0] < self.dict_of_players[arr[j+1]][0]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
