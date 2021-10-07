import os
import sys
import json

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


class MatchMaking:
    def __init__(self, list_of_member_objs):
        self.list_of_players = list_of_member_objs

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

            self.dict_of_players[discord_id_key].append(rank)

        # matchmaking starts here then make two lists of players

        # also put a check if a player has no rank then give them diamond rank

        red = list()
        blue = list()
        return red, blue

    @staticmethod
    def fetch_rank(league_id, league_region):
        # API action here
        pass
