import json
import requests
import time
import psycopg2
import config as cfg

teamoneplayercount = 1
teamtwoplayercount = 1
def setTeam(playerDict,teamDict):
    global teamoneplayercount
    global teamtwoplayercount
    teamindex = 0
    if playerDict["teamid"] == teamDict[teamindex]["teamid"]:
        teamDict[teamindex]["player"+str(teamoneplayercount)+"summonername"]=playerDict["summonername"]
        teamoneplayercount+=1
    else:
        teamindex = 1
        teamDict[teamindex]["player"+str(teamtwoplayercount)+"summonername"]=playerDict["summonername"]
        teamtwoplayercount+=1
    

api_url_base = 'https://la1.api.riotgames.com'
api_url1 = api_url_base+"/lol/match/v4/matchlists/by-account/"
api_url2 = api_url_base+"/lol/match/v4/matches/"

print("Database opened successfully")

while True:
    try:
        con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
        cur = con.cursor()
        while True:
            try:
                cur.execute("select summonername,summonerencryptedid,accountid from summoners")
            except KeyboardInterrupt:
                raise
            except:
                continue
            break
        rows = cur.fetchall()
        con.close()
        for row in rows:
            try:
                summonerAccountID=row[2]
                time.sleep(cfg.secondsPerRequest)
                response = requests.get(api_url1+summonerAccountID, headers=cfg.headers)
                #print(response)

                if response.status_code == 200:
                    featuredGames = json.loads(response.content.decode('utf-8'))
                    for game in featuredGames["matches"]:
                        matchid = game["gameId"]
                        #print(str(matchid))
                        response2 = requests.get(api_url2+str(matchid), headers=cfg.headers)
                        if response2.status_code == 200:
                            matchJSON = json.loads(response2.content.decode('utf-8'))
                            #game table
                            print(matchJSON["gameMode"] + " "+matchJSON["gameType"]+" "+str(matchid))
                            if matchJSON["queueId"] not in {4,14,42,420,400}:
                                continue
                            print("Saving game")
                            season = matchJSON["seasonId"]
                            gameversion = matchJSON["gameVersion"]
                            gamemode = matchJSON["gameMode"]
                            mapid = matchJSON["mapId"]
                            gametype = matchJSON["gameType"]
                            gameduration = matchJSON["gameDuration"]
                            platformid = matchJSON["platformId"]
                            gameid = matchid
                            while True:
                                try:
                                    con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
                                except KeyboardInterrupt:
                                    raise
                                except:
                                    continue
                                break
                            try: 
                                cur = con.cursor()
                                cur.execute("INSERT INTO game VALUES ('"+str(season) + "','"+str(gameversion) + "','"+gamemode + "','"+str(mapid) + "','"+gametype + "','"+str(gameduration) +"','"+ str(platformid) + "','"+str(gameid) +"')")
                                con.commit()
                                print("Record inserted successfully")
                            except KeyboardInterrupt:
                                raise
                            except:
                                pass
                            
                            con.close()
                            # team table
                            teamsJSON = matchJSON["teams"]
                            teams = [{},{}]
                            for i,team in enumerate(teamsJSON):
                                #print(team)
                                (teams[i])["gameid"] = matchid
                                (teams[i])["teamid"] = team["teamId"]
                                (teams[i])["firstdragon"] = team["firstDragon"]
                                (teams[i])["banone"] = ((team["bans"])[0])["championId"]
                                (teams[i])["bantwo"] = ((team["bans"])[1])["championId"]
                                (teams[i])["banthree"] = ((team["bans"])[2])["championId"]
                                (teams[i])["banfour"] = ((team["bans"])[3])["championId"]
                                (teams[i])["banfive"] = ((team["bans"])[4])["championId"]
                                (teams[i])["firstinhibitor"] = team["firstInhibitor"]
                                (teams[i])["win"] = team["win"]
                                (teams[i])["firstriftherald"] = team["firstRiftHerald"]
                                (teams[i])["firstbaron"]  = team["firstBaron"]
                                (teams[i])["baronkills"]  = team["baronKills"]
                                (teams[i])["riftheraldkills"] = team["riftHeraldKills"]
                                (teams[i])["firstblood"] = team["firstBlood"]
                                (teams[i])["firsttower"] = team["firstTower"]
                                (teams[i])["vilemawkills"] = team["vilemawKills"]
                                (teams[i])["inhibitorkills"] = team["inhibitorKills"]
                                (teams[i])["towerkills"] = team["towerKills"]
                                (teams[i])["dominionvictoryscore"] = team["dominionVictoryScore"]
                                (teams[i])["dragonkills"] = team["dragonKills"]
                            #Player table
                            teamoneplayercount = 1
                            teamtwoplayercount = 1
                            players = [{},{},{},{},{},{},{},{},{},{}] 
                            participantsidentities = matchJSON["participantIdentities"]
                            for identity in participantsidentities:
                                (players[identity["participantId"]-1])["summonername"]=(identity["player"])["summonerName"]
                                while True:
                                    try:
                                        con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
                                    except KeyboardInterrupt:
                                        raise
                                    except:
                                        continue
                                    break
                                try:
                                    cur = con.cursor()
                                    cur.execute("INSERT INTO summonergame VALUES ('"+(identity["player"])["summonerName"]+"','"+str(matchid)+"')")
                                    con.commit()
                                except KeyboardInterrupt:
                                    raise
                                except:
                                    pass
                                con.close()
                            participants = matchJSON["participants"]
                            for player in participants:
                                participantid = player["participantId"]-1
                                (players[participantid])["teamid"]=player["teamId"]
                                setTeam(players[participantid],teams)
                                (players[participantid])["gameid"]=matchid
                                (players[participantid])["lane"]=(player["timeline"])["lane"]
                                (players[participantid])["champion"]=player["championId"]
                                (players[participantid])["spell1id"]=player["spell1Id"]
                                (players[participantid])["spell2id"]=player["spell2Id"]
                                (players[participantid])["srole"]=(player["timeline"])["role"]

                                if "csDiffPerMinDeltas" in player["timeline"]:
                                    if "0-10" in (player["timeline"])["csDiffPerMinDeltas"] :
                                        (players[participantid])["csdiffpermindeltas010"] =(player["timeline"])["csDiffPerMinDeltas"]["0-10"]
                                    else: 
                                        (players[participantid])["csdiffpermindeltas010"]  ="0"
                                    if "10-20" in (player["timeline"])["csDiffPerMinDeltas"] :
                                        (players[participantid])["csdiffpermindeltas1020"] =(player["timeline"])["csDiffPerMinDeltas"]["10-20"]
                                    else: 
                                        (players[participantid])["csdiffpermindeltas1020"]  ="0"
                                    if "20-30" in (player["timeline"])["csDiffPerMinDeltas"] :
                                        (players[participantid])["csdiffpermindeltas2030"] =(player["timeline"])["csDiffPerMinDeltas"]["20-30"]
                                    else:
                                        (players[participantid])["csdiffpermindeltas2030"]  ="0"
                                    if "30-40" in (player["timeline"])["csDiffPerMinDeltas"] :
                                        (players[participantid])["csdiffpermindeltas3040"] =(player["timeline"])["csDiffPerMinDeltas"]["30-40"]
                                    else :
                                        (players[participantid])["csdiffpermindeltas3040"]  ="0"
                                    if "40-50" in (player["timeline"])["csDiffPerMinDeltas"] :
                                        (players[participantid])["csdiffpermindeltas4050"] =(player["timeline"])["csDiffPerMinDeltas"]["40-50"]
                                    else:
                                        (players[participantid])["csdiffpermindeltas4050"]  ="0"
                                    if "50-60" in (player["timeline"])["csDiffPerMinDeltas"] :
                                        (players[participantid])["csdiffpermindeltas5060"] =(player["timeline"])["csDiffPerMinDeltas"]["50-60"]
                                    else:
                                        (players[participantid])["csdiffpermindeltas5060"]  ="0"
                                else:
                                    (players[participantid])["csdiffpermindeltas010"]  ="0"
                                    (players[participantid])["csdiffpermindeltas1020"] ="0"
                                    (players[participantid])["csdiffpermindeltas2030"] ="0"
                                    (players[participantid])["csdiffpermindeltas3040"] ="0"
                                    (players[participantid])["csdiffpermindeltas4050"] ="0"
                                    (players[participantid])["csdiffpermindeltas5060"] ="0"
                                
                                if "goldPerMinDeltas" in player["timeline"]:
                                    if "0-10" in (player["timeline"])["goldPerMinDeltas"] :
                                        (players[participantid])["goldpermindeltas010"] =(player["timeline"])["goldPerMinDeltas"]["0-10"]
                                    else:
                                        (players[participantid])["goldpermindeltas010"]  ="0"
                                    if "10-20" in (player["timeline"])["goldPerMinDeltas"] :
                                        (players[participantid])["goldpermindeltas1020"] =(player["timeline"])["goldPerMinDeltas"]["10-20"]    
                                    else:
                                        (players[participantid])["goldpermindeltas1020"]  ="0"
                                    if "20-30" in (player["timeline"])["goldPerMinDeltas"] :
                                        (players[participantid])["goldpermindeltas2030"] =(player["timeline"])["goldPerMinDeltas"]["20-30"]
                                    else:
                                        (players[participantid])["goldpermindeltas2030"]  ="0"
                                    if "30-40" in (player["timeline"])["goldPerMinDeltas"] :
                                        (players[participantid])["goldpermindeltas3040"] =(player["timeline"])["goldPerMinDeltas"]["30-40"]
                                    else:
                                        (players[participantid])["goldpermindeltas3040"]  ="0"
                                    if "40-50" in (player["timeline"])["goldPerMinDeltas"] :
                                        (players[participantid])["goldpermindeltas4050"] =(player["timeline"])["goldPerMinDeltas"]["40-50"]
                                    else:
                                        (players[participantid])["goldpermindeltas4050"]  ="0"
                                    if "50-60" in (player["timeline"])["goldPerMinDeltas"] :
                                        (players[participantid])["goldpermindeltas5060"] =(player["timeline"])["goldPerMinDeltas"]["50-60"]
                                    else:
                                        (players[participantid])["goldpermindeltas5060"]  ="0"
                                    
                                else:
                                    (players[participantid])["goldpermindeltas010"]  ="0"
                                    (players[participantid])["goldpermindeltas1020"] ="0"
                                    (players[participantid])["goldpermindeltas2030"] ="0"
                                    (players[participantid])["goldpermindeltas3040"] ="0"
                                    (players[participantid])["goldpermindeltas4050"] ="0"
                                    (players[participantid])["goldpermindeltas5060"] ="0"

                                if "creepsPerMinDeltas" in player["timeline"]:
                                    if "0-10" in (player["timeline"])["creepsPerMinDeltas"] :
                                        (players[participantid])["creepspermindeltas010"] =(player["timeline"])["creepsPerMinDeltas"]["0-10"]
                                    else:
                                        (players[participantid])["creepspermindeltas010"]  ="0"
                                    if "10-20" in (player["timeline"])["creepsPerMinDeltas"] :
                                        (players[participantid])["creepspermindeltas1020"] =(player["timeline"])["creepsPerMinDeltas"]["10-20"]
                                    else:
                                        (players[participantid])["creepspermindeltas1020"]  ="0"
                                    if "20-30" in (player["timeline"])["creepsPerMinDeltas"] :
                                        (players[participantid])["creepspermindeltas2030"] =(player["timeline"])["creepsPerMinDeltas"]["20-30"]
                                    else:
                                        (players[participantid])["creepspermindeltas2030"]  ="0"
                                    if "30-40" in (player["timeline"])["creepsPerMinDeltas"] :
                                        (players[participantid])["creepspermindeltas3040"] =(player["timeline"])["creepsPerMinDeltas"]["30-40"]
                                    else:
                                        (players[participantid])["creepspermindeltas3040"]  ="0"
                                    if "40-50" in (player["timeline"])["creepsPerMinDeltas"] :
                                        (players[participantid])["creepspermindeltas4050"] =(player["timeline"])["creepsPerMinDeltas"]["40-50"]
                                    else:
                                        (players[participantid])["creepspermindeltas4050"]  ="0"
                                    if "50-60" in (player["timeline"])["creepsPerMinDeltas"] :
                                        (players[participantid])["creepspermindeltas5060"] =(player["timeline"])["creepsPerMinDeltas"]["50-60"]
                                    else:
                                        (players[participantid])["creepspermindeltas5060"]  ="0"
                                    
                                else:
                                    (players[participantid])["creepspermindeltas010"]  ="0"
                                    (players[participantid])["creepspermindeltas1020"] ="0"
                                    (players[participantid])["creepspermindeltas2030"] ="0"
                                    (players[participantid])["creepspermindeltas3040"] ="0"
                                    (players[participantid])["creepspermindeltas4050"] ="0"
                                    (players[participantid])["creepspermindeltas5060"] ="0"

                                if "xpPerMinDeltas" in player["timeline"]:
                                    if "0-10" in (player["timeline"])["xpPerMinDeltas"] :
                                        (players[participantid])["xppermindeltas010"] =(player["timeline"])["xpPerMinDeltas"]["0-10"]
                                    else:
                                        (players[participantid])["xppermindeltas010"]  ="0"
                                    if "10-20" in (player["timeline"])["xpPerMinDeltas"] :
                                        (players[participantid])["xppermindeltas1020"] =(player["timeline"])["xpPerMinDeltas"]["10-20"]
                                    else:
                                        (players[participantid])["xppermindeltas1020"]  ="0"
                                    if "20-30" in (player["timeline"])["xpPerMinDeltas"] :
                                        (players[participantid])["xppermindeltas2030"] =(player["timeline"])["xpPerMinDeltas"]["20-30"]
                                    else:
                                        (players[participantid])["xppermindeltas2030"]  ="0"
                                    if "30-40" in (player["timeline"])["xpPerMinDeltas"] :
                                        (players[participantid])["xppermindeltas3040"] =(player["timeline"])["xpPerMinDeltas"]["30-40"]
                                    else:
                                        (players[participantid])["xppermindeltas3040"]  ="0"
                                    if "40-50" in (player["timeline"])["xpPerMinDeltas"] :
                                        (players[participantid])["xppermindeltas4050"] =(player["timeline"])["xpPerMinDeltas"]["40-50"]
                                    else:
                                        (players[participantid])["xppermindeltas4050"]  ="0"
                                    if "50-60" in (player["timeline"])["xpPerMinDeltas"] :
                                        (players[participantid])["xppermindeltas5060"] =(player["timeline"])["xpPerMinDeltas"]["50-60"]
                                    else:
                                        (players[participantid])["xppermindeltas5060"]  ="0"
                                    
                                else:
                                    (players[participantid])["xppermindeltas010"]  ="0"
                                    (players[participantid])["xppermindeltas1020"] ="0"
                                    (players[participantid])["xppermindeltas2030"] ="0"
                                    (players[participantid])["xppermindeltas3040"] ="0"
                                    (players[participantid])["xppermindeltas4050"] ="0"
                                    (players[participantid])["xppermindeltas5060"] ="0"

                                (players[participantid])["visionscore"] = (player["stats"])["visionScore"]
                                (players[participantid])["magicdamagedealttochampions"] = (player["stats"])["magicDamageDealtToChampions"]
                                (players[participantid])["totaltimecrowdcontroldealt"] = (player["stats"])["totalTimeCrowdControlDealt"]
                                (players[participantid])["longesttimespentliving"] = (player["stats"])["longestTimeSpentLiving"]
                                (players[participantid])["neutralminionskilledteamjungle"] = (player["stats"])["neutralMinionsKilledTeamJungle"]
                                (players[participantid])["largestmultikill"] = (player["stats"])["largestMultiKill"]
                                (players[participantid])["perk1var1"] = (player["stats"])["perk1Var1"]
                                (players[participantid])["perk1var3"] = (player["stats"])["perk1Var3"]
                                (players[participantid])["perk1var2"] = (player["stats"])["perk1Var2"]
                                (players[participantid])["triplekills"] = (player["stats"])["tripleKills"]
                                (players[participantid])["perk5"]= (player["stats"])["perk5"]
                                (players[participantid])["perk4"]= (player["stats"])["perk4"]
                                (players[participantid])["playerscore9"]= (player["stats"])["playerScore9"]
                                (players[participantid])["playerscore8"]= (player["stats"])["playerScore8"]
                                (players[participantid])["kills"]= (player["stats"])["kills"]
                                (players[participantid])["playerscore1"]= (player["stats"])["playerScore1"]
                                (players[participantid])["playerscore0"]= (player["stats"])["playerScore0"]
                                (players[participantid])["playerscore3"]= (player["stats"])["playerScore3"]
                                (players[participantid])["playerscore2"]= (player["stats"])["playerScore2"]
                                (players[participantid])["playerscore5"]= (player["stats"])["playerScore5"]
                                (players[participantid])["playerscore4"]= (player["stats"])["playerScore4"]
                                (players[participantid])["playerscore7"]= (player["stats"])["playerScore7"]
                                (players[participantid])["playerscore6"]= (player["stats"])["playerScore6"]
                                (players[participantid])["perk5var1"]= (player["stats"])["perk5Var1"]
                                (players[participantid])["perk5var3"]= (player["stats"])["perk5Var3"]
                                (players[participantid])["perk5var2"]= (player["stats"])["perk5Var2"]
                                (players[participantid])["totalscorerank"]= (player["stats"])["totalScoreRank"]
                                (players[participantid])["neutralminionskilled"]= (player["stats"])["neutralMinionsKilled"]
                                
                                if "statperk1" in (player["stats"]):
                                    (players[participantid])["statperk1"]= (player["stats"])["statperk1"]
                                else:
                                    (players[participantid])["statperk1"]="None" 
                                if "statperk0" in (player["stats"]):
                                    (players[participantid])["statperk0"]= (player["stats"])["statperk0"]
                                else:
                                    (players[participantid])["statperk0"]="None" 
                                if "statperk2" in (player["stats"]):
                                    (players[participantid])["statperk2"]= (player["stats"])["statperk2"]
                                else:
                                    (players[participantid])["statperk2"]="None" 
                                
                                (players[participantid])["damagedealttoturrets"]= (player["stats"])["damageDealtToTurrets"]
                                (players[participantid])["physicaldamagedealttochampions"]= (player["stats"])["physicalDamageDealtToChampions"]
                                (players[participantid])["damagedealttoobjectives"]= (player["stats"])["damageDealtToObjectives"]
                                (players[participantid])["perk2var2"]= (player["stats"])["perk2Var2"]
                                (players[participantid])["perk2var3"]= (player["stats"])["perk2Var3"]
                                (players[participantid])["totalunitshealed"]= (player["stats"])["totalUnitsHealed"]
                                (players[participantid])["perk2var1"]= (player["stats"])["perk2Var1"]
                                (players[participantid])["perk4var1"]= (player["stats"])["perk4Var1"]
                                (players[participantid])["totaldamagetaken"]= (player["stats"])["totalDamageTaken"]
                                (players[participantid])["perk4var3"]= (player["stats"])["perk4Var3"]
                                (players[participantid])["wardskilled"]= (player["stats"])["wardsKilled"]
                                (players[participantid])["largestcriticalstrike"]= (player["stats"])["largestCriticalStrike"]
                                (players[participantid])["largestkillingspree"]= (player["stats"])["largestKillingSpree"]
                                (players[participantid])["quadrakills"]= (player["stats"])["quadraKills"]
                                (players[participantid])["magicdamagedealt"]= (player["stats"])["magicDamageDealt"]
                                (players[participantid])["firstbloodassist"]= (player["stats"])["firstBloodAssist"]
                                (players[participantid])["item2"]= (player["stats"])["item2"]
                                (players[participantid])["item3"]= (player["stats"])["item3"]
                                (players[participantid])["item0"]= (player["stats"])["item0"]
                                (players[participantid])["item1"]= (player["stats"])["item1"]
                                (players[participantid])["item6"]= (player["stats"])["item6"]
                                (players[participantid])["item4"]= (player["stats"])["item4"]
                                (players[participantid])["item5"]= (player["stats"])["item5"]
                                (players[participantid])["perk1"]= (player["stats"])["perk1"]
                                (players[participantid])["perk0"]= (player["stats"])["perk0"]
                                (players[participantid])["perk3"]= (player["stats"])["perk3"]
                                (players[participantid])["perk2"]= (player["stats"])["perk2"]
                                (players[participantid])["perk3var3"]= (player["stats"])["perk3Var1"]
                                (players[participantid])["perk3var2"]= (player["stats"])["perk3Var2"]
                                (players[participantid])["perk3var1"]= (player["stats"])["perk3Var1"]
                                (players[participantid])["damageselfmitigated"]= (player["stats"])["damageSelfMitigated"]
                                (players[participantid])["magicaldamagetaken"]= (player["stats"])["magicalDamageTaken"]
                                (players[participantid])["perk0var2"]= (player["stats"])["perk0Var2"]
                                if "firstInhibitorKill" in player["stats"]:
                                    (players[participantid])["firstinhibitorkill"]= (player["stats"])["firstInhibitorKill"]
                                else :
                                    (players[participantid])["firstinhibitorkill"]="None"
                                (players[participantid])["truedamagetaken"]= (player["stats"])["trueDamageTaken"]
                                (players[participantid])["assists"]= (player["stats"])["assists"]
                                (players[participantid])["perk4var2"]= (player["stats"])["perk4Var2"]
                                (players[participantid])["goldspent"]= (player["stats"])["goldSpent"]
                                (players[participantid])["truedamagedealt"]= (player["stats"])["trueDamageDealt"]
                                (players[participantid])["participantid"]= (player["stats"])["participantId"]
                                (players[participantid])["physicaldamagedealt"]= (player["stats"])["physicalDamageDealt"]
                                (players[participantid])["sightwardsboughtingame"]= (player["stats"])["sightWardsBoughtInGame"]
                                (players[participantid])["totaldamagedealttochampions"]= (player["stats"])["totalDamageDealtToChampions"]
                                (players[participantid])["physicaldamagetaken"]= (player["stats"])["physicalDamageTaken"]
                                (players[participantid])["totalplayerscore"]= (player["stats"])["totalPlayerScore"]
                                (players[participantid])["objectiveplayerscore"]= (player["stats"])["objectivePlayerScore"]
                                (players[participantid])["totaldamagedealt"]= (player["stats"])["totalDamageDealt"]
                                (players[participantid])["neutralminionskilledenemyjungle"]= (player["stats"])["neutralMinionsKilledEnemyJungle"]
                                (players[participantid])["deaths"]= (player["stats"])["deaths"]
                                (players[participantid])["wardsplaced"]= (player["stats"])["wardsPlaced"]
                                (players[participantid])["perkprimarystyle"]= (player["stats"])["perkPrimaryStyle"]
                                (players[participantid])["perksubstyle"]= (player["stats"])["perkSubStyle"]
                                (players[participantid])["turretkills"]= (player["stats"])["turretKills"]
                                (players[participantid])["firstbloodkill"]= (player["stats"])["firstBloodKill"]
                                (players[participantid])["truedamagedealttochampions"]= (player["stats"])["trueDamageDealtToChampions"]
                                (players[participantid])["goldearned"]= (player["stats"])["goldEarned"]
                                (players[participantid])["killingsprees"]= (player["stats"])["killingSprees"]
                                (players[participantid])["unrealkills"]= (player["stats"])["unrealKills"]
                                if "firstTowerAssist" in player["stats"]:
                                    (players[participantid])["firsttowerassist"]= (player["stats"])["firstTowerAssist"]
                                else:
                                    (players[participantid])["firsttowerassist"]="None"
                                if "firstTowerKill" in player["stats"]:
                                    (players[participantid])["firsttowerkill"]= (player["stats"])["firstTowerKill"]
                                else:
                                    (players[participantid])["firsttowerkill"]="None"
                                (players[participantid])["champlevel"]= (player["stats"])["champLevel"]
                                (players[participantid])["doublekills"]= (player["stats"])["doubleKills"]
                                (players[participantid])["inhibitorkills"]= (player["stats"])["inhibitorKills"]
                                if "firstInhibitorAssist" in player["stats"]:
                                    (players[participantid])["firstinhibitorassist"]= (player["stats"])["firstInhibitorAssist"]
                                else:
                                    (players[participantid])["firstinhibitorassist"]= "None"
                                (players[participantid])["perk0var1"]= (player["stats"])["perk0Var1"]
                                (players[participantid])["combatplayerscore"]= (player["stats"])["combatPlayerScore"]
                                (players[participantid])["perk0var3"]= (player["stats"])["perk0Var3"]
                                (players[participantid])["visionwardsboughtingame"]= (player["stats"])["visionWardsBoughtInGame"]
                                (players[participantid])["pentakills"]= (player["stats"])["pentaKills"]
                                (players[participantid])["totalheal"]= (player["stats"])["totalHeal"]
                                #print()(player["stats"])["totalHeal"]
                                (players[participantid])["totalminionskilled"]= (player["stats"])["totalMinionsKilled"]
                                (players[participantid])["timeccingothers"]= (player["stats"])["timeCCingOthers"]
                            #print(players)
                            #print(teams)

                            while True:
                                try:
                                    con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
                                except KeyboardInterrupt:
                                    raise
                                except:
                                    continue
                                break
                            try:
                                for team in teams: 
                                    cur = con.cursor()
                                    cur.execute("INSERT INTO playedgameteam VALUES ('"+str((team)["gameid"]) + "','"+((team)["player1summonername"]) + "','"+
                                    ((team)["player2summonername"]) + "','"+((team)["player3summonername"]) + "','"+((team)["player4summonername"]) +
                                    "','"+((team)["player5summonername"]) + "','"+str((team)["teamid"]) +"','"+str((team)["firstdragon"]) +"','"+str((team)["banone"]) +
                                    "','"+str((team)["bantwo"]) +"','"+str((team)["banthree"]) +"','"+str((team)["banfour"]) +"','"+str((team)["banfive"]) +
                                    "','"+str((team)["firstinhibitor"]) +"','"+str((team)["win"]) +"','"+str((team)["firstriftherald"]) +"','"+str((team)["firstbaron"]) +
                                    "','"+str((team)["baronkills"]) +"','"+str((team)["riftheraldkills"]) +"','"+str((team)["firstblood"]) +"','"+str((team)["firsttower"]) +
                                    "','"+str((team)["vilemawkills"]) +"','"+str((team)["inhibitorkills"]) +"','"+str((team)["towerkills"]) +"','"+str((team)["dominionvictoryscore"]) +
                                    "','"+str((team)["dragonkills"]) +"')")
                                    con.commit()#"','"+str((team)[""]) +
                                    print("Record inserted successfully")
                            except KeyboardInterrupt:
                                raise
                            except:
                                pass
                            con.close()
                            while True:
                                try:
                                    con = psycopg2.connect(database=cfg.sql["database"], user=cfg.sql["user"], password=cfg.sql["password"], host=cfg.sql["host"], port=cfg.sql["port"])
                                except KeyboardInterrupt:
                                    raise
                                except:
                                    continue
                                break
                            for player in players: 
                                try:
                                    cur = con.cursor()
                                    query = "INSERT INTO playerplayedgamehistory VALUES ('"+str(player["gameid"]) + "','"+str(player["summonername"]) + \
                                    "','"+str(player["lane"]) + "','"+str(player["champion"]) + "','"+str(player["spell1id"]) + \
                                    "','"+str(player["spell2id"]) + "','"+str(player["srole"]) +"','"+str(player["csdiffpermindeltas010"]) +"','"+str(player["csdiffpermindeltas1020"]) + \
                                    "','"+str(player["csdiffpermindeltas2030"]) +"','"+str(player["csdiffpermindeltas3040"]) +"','"+str(player["csdiffpermindeltas4050"]) +"','"+str(player["csdiffpermindeltas5060"]) + \
                                    "','"+str(player["goldpermindeltas010"]) +"','"+str(player["goldpermindeltas1020"]) +"','"+str(player["goldpermindeltas2030"]) +"','"+str(player["goldpermindeltas3040"]) + \
                                    "','"+str(player["goldpermindeltas4050"]) +"','"+str(player["goldpermindeltas5060"]) +"','"+str(player["creepspermindeltas010"]) +"','"+str(player["creepspermindeltas1020"])+  \
                                    "','"+str(player["creepspermindeltas2030"]) +"','"+str(player["creepspermindeltas3040"]) +"','"+str(player["creepspermindeltas4050"]) +"','"+str(player["creepspermindeltas5060"]) +"','"+str(player["xppermindeltas010"]) + \
                                    "','"+str(player["xppermindeltas1020"]) +"','"+str(player["xppermindeltas2030"]) +"','"+str(player["xppermindeltas3040"])  +"','"+str(player["xppermindeltas4050"])  +"','"+str(player["xppermindeltas5060"])+  \
                                    "','"+str(player["visionscore"]) +"','"+str(player["magicdamagedealttochampions"]) +"','"+str(player["totaltimecrowdcontroldealt"]) +"','"+str(player["longesttimespentliving"]) + \
                                    "','"+str(player["neutralminionskilledteamjungle"]) +"','"+str(player["largestmultikill"]) +"','"+str(player["perk1var1"]) +"','"+str(player["perk1var3"]) +"','"+str(player["perk1var2"]) + \
                                    "','"+str(player["triplekills"]) +"','"+str(player["perk5"]) +"','"+str(player["perk4"]) +"','"+str(player["playerscore9"]) +"','"+str(player["playerscore8"]) + \
                                    "','"+str(player["kills"]) +"','"+str(player["playerscore1"]) +"','"+str(player["playerscore0"]) +"','"+str(player["playerscore3"]) +"','"+str(player["playerscore2"])+  \
                                    "','"+str(player["playerscore5"]) +"','"+str(player["playerscore4"]) +"','"+str(player["playerscore7"]) +"','"+str(player["playerscore6"]) +"','"+str(player["perk5var1"])+  \
                                    "','"+str(player["perk5var3"]) +"','"+str(player["perk5var2"]) +"','"+str(player["totalscorerank"]) +"','"+str(player["neutralminionskilled"]) +"','"+str(player["statperk1"])+  \
                                    "','"+str(player["statperk0"]) +"','"+str(player["damagedealttoturrets"]) +"','"+str(player["physicaldamagedealttochampions"]) +"','"+str(player["damagedealttoobjectives"]) + \
                                    "','"+str(player["perk2var2"]) +"','"+str(player["perk2var3"]) +"','"+str(player["totalunitshealed"]) +"','"+str(player["perk2var1"]) +"','"+str(player["perk4var1"])  + \
                                    "','"+str(player["totaldamagetaken"]) +"','"+str(player["perk4var3"]) +"','"+str(player["wardskilled"]) +"','"+str(player["largestcriticalstrike"]) +"','"+str(player["largestkillingspree"]) + \
                                    "','"+str(player["quadrakills"]) +"','"+str(player["magicdamagedealt"]) +"','"+str(player["firstbloodassist"]) +"','"+str(player["item2"]) +"','"+str(player["item3"]) + \
                                    "','"+str(player["item0"]) +"','"+str(player["item1"]) +"','"+str(player["item6"]) +"','"+str(player["item4"]) +"','"+str(player["item5"])  + \
                                    "','"+str(player["perk1"]) +"','"+str(player["perk0"]) +"','"+str(player["perk3"]) +"','"+str(player["perk2"]) +"','"+str(player["perk3var3"]) +"','"+str(player["perk3var2"])+  \
                                    "','"+str(player["perk3var1"]) +"','"+str(player["damageselfmitigated"]) +"','"+str(player["magicaldamagetaken"]) +"','"+str(player["perk0var2"]) +"','"+str(player["firstinhibitorkill"])+  \
                                    "','"+str(player["truedamagetaken"]) +"','"+str(player["assists"]) +"','"+str(player["perk4var2"]) +"','"+str(player["goldspent"]) +"','"+str(player["truedamagedealt"]) + \
                                    "','"+str(player["participantid"]) +"','"+str(player["physicaldamagedealt"]) +"','"+str(player["sightwardsboughtingame"]) +"','"+str(player["totaldamagedealttochampions"])+ \
                                    "','"+str(player["physicaldamagetaken"]) +"','"+str(player["totalplayerscore"]) +"','"+str(player["objectiveplayerscore"]) +"','"+str(player["totaldamagedealt"]) + \
                                    "','"+str(player["neutralminionskilledenemyjungle"]) +"','"+str(player["deaths"]) +"','"+str(player["wardsplaced"]) +"','"+str(player["perkprimarystyle"]) + \
                                    "','"+str(player["perksubstyle"]) +"','"+str(player["turretkills"]) +"','"+str(player["firstbloodkill"]) +"','"+str(player["truedamagedealttochampions"]) + \
                                    "','"+str(player["goldearned"]) +"','"+str(player["killingsprees"]) +"','"+str(player["unrealkills"]) +"','"+str(player["firsttowerassist"]) +"','"+str(player["firsttowerkill"])+  \
                                    "','"+str(player["champlevel"]) +"','"+str(player["doublekills"]) +"','"+str(player["inhibitorkills"]) +"','"+str(player["firstinhibitorassist"]) +"','"+str(player["perk0var1"]) + \
                                    "','"+str(player["combatplayerscore"]) +"','"+str(player["perk0var3"]) +"','"+str(player["visionwardsboughtingame"]) +"','"+str(player["pentakills"]) +"','"+str(player["totalheal"]) + \
                                    "','"+str(player["totalminionskilled"]) +"','"+str(player["timeccingothers"]) +"','"+str(player["statperk2"]) +"','"+str(player["teamid"]) +"')"
                                    #print(query)
                                    cur.execute(query)
                                    con.commit()#"','"+str(player[""]) +
                                    print("Record inserted successfully")
                                except KeyboardInterrupt:
                                    raise
                                except:
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