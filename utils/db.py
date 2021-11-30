import codecs
import pickle

import json
import os
import sys

import psycopg2

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json", encoding="cp866") as file:
        config = json.load(file)


class dbAction:
    def __init__(self):
        self.db = psycopg2.connect(host=config["database_creds"]["host"], database=config["database_creds"]["database"],
                                   user=config["database_creds"]["user"], port=config["database_creds"]["port"],
                                   password=config["database_creds"]["password"])

    def check_user(self, discord_id, table):
        cur = self.db.cursor()
        cur.execute(f"SELECT discord_id FROM {table};")
        list_of_discord_ids = cur.fetchall()
        if discord_id in list_of_discord_ids:
            return True
        return False

    async def write_stats(self, stats, table):
        cur = self.db.cursor()
        for discord_id in stats:
            if stats[discord_id]['win']:
                stats[discord_id]['win'] = 1
                stats[discord_id]['lose'] = 0
            else:
                stats[discord_id]['lose'] = 1
                stats[discord_id]['win'] = 0
            if not self.check_user(discord_id, table):
                cur.execute(
                    f"""INSERT INTO {table} (discord_id, no_of_matches, wins, loses, kills, deaths, assists, "totalMinionsKilled", "timePlayed", "doubleKills", "tripleKills", "quadraKills", "pentaKills", "totalDamageDealt", "totalDamageTaken", "highestKillGame", "highestDeathGame") values ({discord_id},{1},{stats[discord_id]['win']},{stats[discord_id]['lose']},{stats[discord_id]['kills']},{stats[discord_id]['deaths']},{stats[discord_id]['assists']},{stats[discord_id]['totalMinionsKilled']},{stats[discord_id]['timePlayed']}, {stats[discord_id]['doubleKills']}, {stats[discord_id]['tripleKills']}, {stats[discord_id]['quadraKills']}, {stats[discord_id]['pentaKills']}, {stats[discord_id]['totalDamageTaken']}, {stats[discord_id]['totalDamageDealt']}, {stats[discord_id]['kills']}, {stats[discord_id]['deaths']});""")
                cur.close()
                return
            cur.execute(f"SELECT * FROM {table} WHERE discord_id={int(discord_id)};")
            old_stats = list(cur.fetchone())
            # returns tuple (123, 1, 1, 0, 23, 23, 23, 2, 12, 0, 0, 123, 123, 132, 123, 123, 2)
            no_of_matches = old_stats[1] + 1
            wins = old_stats[2] + stats[discord_id]['win']
            loses = old_stats[3] + stats[discord_id]['lose']
            kills = old_stats[4] + stats[discord_id]["kills"]
            deaths = old_stats[5] + stats[discord_id]["deaths"]
            assists = old_stats[6] + stats[discord_id]["assists"]
            totalMinionsKilled = old_stats[7] + stats[discord_id]["totalMinionsKilled"]
            timePlayed = old_stats[8] + stats[discord_id]["timePlayed"]
            dkills = old_stats[16] + stats[discord_id]['doubleKills']
            tkills = old_stats[9] + stats[discord_id]["tripleKills"]
            qkills = old_stats[10] + stats[discord_id]["quadraKills"]
            pkills = old_stats[11] + stats[discord_id]["pentaKills"]
            tDamageDealt = old_stats[12] + stats[discord_id]["totalDamageDealt"]
            tDamageTaken = old_stats[13] + stats[discord_id]["totalDamageTaken"]

            if old_stats[14] < stats[discord_id]['kills']:          # check this
                highestKillGame = stats[discord_id]['kills']
            else:
                highestKillGame = old_stats[14]

            if old_stats[15] < stats[discord_id]['deaths']:
                highestDeathGame = stats[discord_id]['deaths']
            else:
                highestDeathGame = old_stats[15]

            cur.execute(f"""UPDATE {table}
             SET (no_of_matches = {no_of_matches}, wins = {wins},loses = {loses},kills={kills},deaths={deaths},assists={assists},"totalMinionsKilled"={totalMinionsKilled},"timePlayed"={timePlayed},"doubleKills"={dkills}, "tripleKills"={tkills}, "quadraKills"={qkills}, "pentaKills"={pkills},"totalDamageDealt"={tDamageDealt},"totalDamageTaken"={tDamageTaken},"highestKillGame"={highestKillGame},"highestDeathGame"={highestDeathGame})
              WHERE discord_id = {int(discord_id)};""")
            cur.close()
            return

    # async def get_stats(self, table):
    #     cur = self.db.cursor()
    #     cur.execute(f"SELECT discord_id FROM {table};")
    #     list_of_discord_ids = cur.fetchall()
    #     cur.close()
    #
    #     stats = {}  # a dictionary will be returned
    #     for discord_id in list_of_discord_ids:
    #         cur.execute(f"SELECT * FROM {table} WHERE discord_id={discord_id};")
    #         unprocessed_stats = cur.fetchone()
    #
    #         # Proccessing stats
    #         winLoseRatio = unprocessed_stats[2] / unprocessed_stats[3]
    #         killDeathRatio = unprocessed_stats[4] / unprocessed_stats[5]
    #         assists = unprocessed_stats[6]
    #         creepScore = unprocessed_stats[7] / unprocessed_stats[8]
    #         averageDamageDealt = unprocessed_stats[12] / unprocessed_stats[1]
    #         averageDamageTaken = unprocessed_stats[13] / unprocessed_stats[1]
    #
    #         stats[discord_id] = {'no_of_matches': unprocessed_stats[1], 'wins': unprocessed_stats[2], 'losses': unprocessed_stats[3], "winLoseRatio": winLoseRatio, "killDeathRatio": killDeathRatio,
    #                              'kills': unprocessed_stats[4], 'deaths': unprocessed_stats[5], 'doubleKills': unprocessed_stats[16],
    #                              "assists": assists, "creepScore": creepScore, "tripleKills": unprocessed_stats[9],
    #                              "quadraKills": unprocessed_stats[10], "pentaKills": unprocessed_stats[11],
    #                              "totalDamageDealt": unprocessed_stats[12], "totalDamageTaken": unprocessed_stats[13],
    #                              "averageDamageDealt": averageDamageDealt, "averageDamageTaken": averageDamageTaken,
    #                              "highestKillGame": unprocessed_stats[14], "highestDeathGame": unprocessed_stats[15]
    #                              }
    #     return stats

    @staticmethod
    def remove_member_objs(team):
        dict = {}
        for key in team:
            dict[key] = team[key].id
        return dict

    async def write_to_db(self, lobby_name, red, blue, captain):
        cur = self.db.cursor()
        red1 = self.remove_member_objs(red)
        blue1 = self.remove_member_objs(blue)
        cur.execute(f"INSERT INTO team_db (match_name, red_team, blue_team, captain) values ('{lobby_name}', '{self.pickled(red1)}', '{self.pickled(blue1)}', {captain});")
        self.db.commit()
        cur.close()

    @staticmethod
    def pickled(obj):
        return codecs.encode(pickle.dumps(obj), "base64").decode()

    @staticmethod
    def unpickled(pickled):
        return pickle.loads(codecs.decode(pickled.encode(), "base64"))

    async def get_teams(self, lobby_name):
        cur = self.db.cursor()
        cur.execute(f"SELECT * FROM team_db WHERE match_name='{lobby_name}';")
        lst = cur.fetchone()
        red = self.unpickled(lst[1])
        blue = self.unpickled(lst[-1])
        captain_id = int(lst[2])
        return red, blue, captain_id

    # def delete_match(self, lobby_name):
