import json
import requests
import time
import psycopg2
import config as cfg

api_url_base = 'https://la1.api.riotgames.com'
api_url1 = api_url_base+"/lol/summoner/v4/summoners/by-name/"

print("Database opened successfully")

while True:
    try:
        con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
        cur = con.cursor()
        while True:
            try:
                cur.execute("select s.summonername from playerplayedgamehistory s where s.summonername not in (select summonername from summoners)")
            except KeyboardInterrupt:
                raise
            except:
                continue
            break
        rows = cur.fetchall()
        con.close()
        for row in rows:
            try:
                summonername=row[0]
                time.sleep(cfg.secondsPerRequest)
                response = requests.get(api_url1+summonername, headers=cfg.headers)
                #print(response)

                if response.status_code == 200:
                    while True:
                        try:
                            con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
                        except:
                            continue
                        break
                    summonerInfo = json.loads(response.content.decode('utf-8'))
                    print(summonername+" "+summonerInfo["id"])
                    try:
                        cur = con.cursor()
                        cur.execute("INSERT INTO summoners VALUES ('"+summonername+"','"+summonerInfo["id"]+"','"+summonerInfo["accountId"]+"')")
                        con.commit()
                        print("Record inserted successfully")
                    except KeyboardInterrupt:
                        raise
                    except :
                        pass
                    con.close()
            except KeyboardInterrupt:
                raise
            except:
                pass
    except KeyboardInterrupt:
        raise
    except:
        pass