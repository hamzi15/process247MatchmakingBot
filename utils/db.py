import codecs
import pickle
from apscheduler.schedulers.background import BlockingScheduler
import psycopg2


class dbAction:
    scheduler = BlockingScheduler()
    def __init__(self):
        self.db = psycopg2.connect(host="ec2-23-22-243-103.compute-1.amazonaws.com",
                                   database="d3fvi6kbgm35kg", user="tlwdfftatkjcnt",
                                   port=5432, password="81aa0b82170b336db25efdb1b4af241c3925239e0d5adfbe43e5f4a752b938ea")

    async def write_to_db(self, lobby_name, red, blue, captain):
        cur = self.db.cursor()
        cur.execute(f"INSERT INTO team_db (match_name, red_team, blue_team, captain) values ({lobby_name}, {self.pickled(red)}, {self.pickled(blue)}, {self.pickled(captain)});")
        self.db.commit()
        cur.close()

    def check_user(self,discord_id,table):
        cur = self.db.cursor()
        cur.execute(f"SELECT discord_id FROM {table};")
        list_of_discord_ids = cur.fetchall()
        print(list_of_discord_ids)
        if discord_id in list_of_discord_ids:
            return True
        return False

    async def pre_write_stats(self,stats):
        await self.write_stats(stats, "overall_stats")

        #Implement time logic for these ones.
        await self.write_stats(stats, "weekly_stats")
        await self.write_stats(stats, "monthly_stats")
        await self.write_stats(stats, "yearly_stats")

    async def write_stats(self,stats,table):
        cur = self.db.cursor()
        for discord_id in stats:
            no_of_matches = 1
            win = 0
            lose = 0
            kills = stats[discord_id]["kills"]
            deaths = stats[discord_id]["deaths"]
            assists = stats[discord_id]["assists"]
            totalMinionsKilled = stats[discord_id]["totalMinionsKilled"]
            timeplayed = stats[discord_id]["timePlayed"]
            tkills = stats[discord_id]["tripleKills"]
            qkills = stats[discord_id]["quadraKills"]
            pkills = stats[discord_id]["pentaKills"]
            tDamageDealt = stats[discord_id]["totalDamageDealt"]
            tDamageTaken = stats[discord_id]["totalDamageTaken"]
            if stats[discord_id]['win']:
                win = 1
            else:
                lose = 1
            if not self.check_user(discord_id,table):
                cur.execute(f"INSERT INTO {table} (discord_id,no_of_matches,wins,loses,kills,deaths,assists,totalMinionsKilled,timeplayed,tripleKills,quadraKills,pentaKills,totalDamageDealt,totalDamageTaken,highestKillGame,highestDeathGame) values ({discord_id},{no_of_matches},{win},{lose},{kills},{deaths},{assists},{totalMinionsKilled},{timeplayed},{tkills},{qkills},{pkills},{tDamageTaken},{tDamageDealt},{kills},{deaths});")
            else:
                cur.execute(f"SELECT * FROM {table} WHERE discord_id={discord_id};")
                old_stats = cur.fetchone()
                new_stats = [no_of_matches,win,lose,kills,deaths,assists,totalMinionsKilled,timeplayed,tkills,qkills,pkills,tDamageDealt,tDamageTaken]
                new_stats = dbAction.update_old_stats(old_stats,new_stats)
                cur.execute(f"UPDATE {table} SET (discord_id = discord_id,no_of_matches = new_stats[0], wins = new_stats[1],loses = new_stats[2],kills=new_stats[3],deaths=new_stats[4],assists=new_stats[5],totalMinionsKilled=new_stats[6],timeplayed=new_stats[7],tripleKills=new_stats[8],quadraKills=new_stats[9],pentaKills=new_stats[10],totalDamageDealt=new_stats[11],totalDamageTaken=new_stats[12],highestKillGame=new_stats[13],highestDeathGame=new_stats[14]) WHERE discord_id = {discord_id};")

    async def get_stats(self,table):
        cur = self.db.cursor()
        cur.execute(f"SELECT discord_id FROM {table};")
        list_of_discord_ids = cur.fetchall()

        stats = {} #a dictionary will be returned
        for discord_id in list_of_discord_ids:
            cur.execute(f"SELECT * FROM {table} WHERE discord_id={discord_id};")
            unproccessed_stats = cur.fetchone()

            #Proccessing stats
            winLoseRatio = unproccessed_stats[2]/unproccessed_stats[3]
            killDeathRatio = unproccessed_stats[4]/unproccessed_stats[5]
            assists = unproccessed_stats[6]
            creepScore = unproccessed_stats[7]/unproccessed_stats[8]
            averageDamageDealt = unproccessed_stats[12]/unproccessed_stats[1]
            averageDamageTaken = unproccessed_stats[13]/unproccessed_stats[1]

            stats[discord_id] = {"winLoseRatio": winLoseRatio, "killDeathRatio": killDeathRatio,
                                 "assists" : assists, "creepScore" : creepScore, "tripleKills": unproccessed_stats[9],
                                 "quadraKills" : unproccessed_stats[10], "pentaKills" : unproccessed_stats[11],
                                 "totalDamageDealt" : unproccessed_stats[12], "totalDamageTaken" : unproccessed_stats[13],
                                 "averageDamageDealt" : averageDamageDealt, "averageDamageTaken" : averageDamageTaken,
                                 "highestKillGame" : unproccessed_stats[14], "highestDeathGame" : unproccessed_stats[15]
                }
        return stats



    @staticmethod
    def update_old_stats(old_stats,new_stats):
        index = 1 #start from 1 to skip discord_id
        for stat in new_stats:
            stat = stat + old_stats[index]
            index+=1
        #highest kill and death check
        if new_stats[3] > old_stats[-2]:
            new_stats.append(new_stats[3])
        else:
            new_stats.append(old_stats[-2])
        if new_stats[4] > old_stats[-1]:
            new_stats.append(new_stats[4])
        else:
            new_stats.append(old_stats[-1])
        return new_stats


    @staticmethod
    def pickled(obj):
        return codecs.encode(pickle.dumps(obj), "base64").decode()

    @staticmethod
    def unpickled(pickled):
        return pickle.loads(codecs.decode(pickled.encode(), "base64"))

    async def get_teams(self, lobby_name):
        cur = self.db.cursor()
        cur.execute(f"SELECT * FROM team_db WHERE match_name={lobby_name};")
        print(cur.fetchone())
        cur.close()

    # def delete_match(self, lobby_name):