import json
import requests
import time
import psycopg2
import config as cfg


api_url_base = 'https://la1.api.riotgames.com'
api_url1 = api_url_base+"/lol/spectator/v4/featured-games"
api_url2 = api_url_base+"/lol/summoner/v4/summoners/by-name/"

print(cfg.secondsPerRequest)

while True:
    try:
        time.sleep(cfg.secondsPerRequest)
        response = requests.get(api_url1, headers=cfg.headers)
        if response.status_code == 200:
            featuredGames = json.loads(response.content.decode('utf-8'))
            for i,game in enumerate(featuredGames["gameList"]):
                gameMode = game["gameMode"]
                gameType = game["gameType"]
                platID = game["platformId"]
                print("Game number: "+str(game["gameId"]))
                if gameMode == "CLASSIC" and gameType == "MATCHED_GAME" and platID == "LA1":
                    while True:
                        try:
                            con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
                        except:
                            continue
                        break
                    bannedChampions = game["bannedChampions"]
                    for participant in game["participants"]:
                        print(participant["summonerName"]+" champ:"+str(participant["championId"])+" sumSpell1:"+str(participant["spell1Id"])
                        +" sumSpell2:"+str(participant["spell2Id"]))
                        response2 = requests.get(api_url2+participant["summonerName"], headers=cfg.headers)
                        if response2.status_code == 200:
                            summonerInfo = json.loads(response2.content.decode('utf-8'))
                            try:
                                cur = con.cursor()
                                cur.execute("INSERT INTO summoners VALUES ('"+participant["summonerName"]+"','"+summonerInfo["id"]+"','"+summonerInfo["accountId"]+"')")
                                con.commit()
                                print("Record inserted successfully")
                            except :
                                pass
                    con.close()
    except KeyboardInterrupt:
        raise
    except :
        pass
