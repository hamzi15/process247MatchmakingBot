import os
import sys
import json
from riotwatcher import LolWatcher,ApiError

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


class MatchMaking:
    def __init__(self):
        self.dict_of_players = {}

    def matchmaker(self, lst_of_player_ids):
        red, blue = self.distribute_equally(lst_of_player_ids)
        return (red, blue)

    def distribute_equally(self, lst):
        dict_LoL_id = config['dict_lol_ids']  # fetching league ids and regions
        # dictionary from database.
        # i.e. {'discord_id': ['league_id', 'league_region']}
        for i in lst:
            player_league_creds = dict_LoL_id.get(i)
            self.dict_of_players[i] = player_league_creds

        for discord_id_key in self.dict_of_players:
            league_id = self.dict_of_players[discord_id_key][0]
            league_region = self.dict_of_players[discord_id_key][1]

            rank = self.fetch_rank(league_id, league_region) # fetching rank and adding it to the player's creds list

            self.dict_of_players[discord_id_key].append(self.rank_value(rank))
            self.bubbleSort(lst)
        # matchmaking starts here then make two lists of players
        # also put a check if a player has no rank then give them diamond rank
        red = list()
        blue = list()
        red_sum = 0
        blue_sum = 0
        for id in lst:
            if red_sum == blue_sum:
                red.append(id)
            elif red_sum < blue_sum:
                red.append(id)
            elif red_sum > blue_sum:
                blue.append(id)
            for discord_id in red:
                red_sum += self.dict_of_players[discord_id][2]
            for discord_id in blue:
                blue_sum += self.dict_of_players[discord_id][2]
        return red, blue

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
                if self.dict_of_players[arr[j]][2] < self.dict_of_players[arr[j+1]][2]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]