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

    @staticmethod
    def matchmaker(self, lst_of_player_memberObjs):
        red, blue = self.distribute_equally(lst_of_player_memberObjs)
        return (red, blue)

    def distribute_equally(self, lst):
        for member in lst:
            self.dict_of_players[member] = []
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
            rank = self.fetch_rank(league_id, league_region) # fetching rank and adding it to the player's creds list
            self.dict_of_players[member].append(self.rank_value(rank))
        self.bubbleSort(lst)

        for member in lst:
            lol_roles = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
            for role in member.roles:
                if role.startswith('Main '):
                    role = role[5:]
                if role in lol_roles:
                    self.dict_of_players[member].append(role)
                    #add check that atleast one role has been assigned
        # matchmaking starts here then make two lists of players
        # also put a check if a player has no rank then give them diamond rank
        red = {}
        blue = {}
        redQueue = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
        blueQueue = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
        red_sum = 0
        blue_sum = 0
        #MATCHMAKING
        index = 0
        for member in lst:
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
                #red.append(member)
            elif red_sum > blue_sum:
                self.assign_role(blueQueue,member,blue)
                #blue.append(member)
            for role in red:
                member = red[role]
                red_sum += self.dict_of_players[member][0]
            for role in blue:
                member = blue[role]
                blue_sum += self.dict_of_players[member][0]

        return red, blue

    def assign_role(self,queue,member,dict): #(red or blue queue, member from lst[index], and red or blue dict)
        try:
            member_role = (self.dict_of_players[member][1],self.dict_of_players[member][2])
        except:
            member_role = (self.dict_of_players[member][1],None)
        if member_role[0] in queue:
            dict[member_role[0]] = member
        elif member_role[1] and member_role[1] in queue:
            dict[member_role[1]] = member
        else:
            dict[queue.pop()] = member

    @staticmethod
    def fetch_rank(league_id, league_region):
        #API action here
        API_KEY = config["RIOT_API_KEY"]
        watcher = LolWatcher(API_KEY)

        try:
            me = watcher.summoner.by_name(league_region,league_id)
            rank_stats = watcher.league.by_summoner(league_region,me['id'])
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
                return 'Unranked' #RECHECK THIS

    def rank_value(self,rank):
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