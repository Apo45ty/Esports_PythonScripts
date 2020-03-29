import json
import requests
import shutil
import config as cfg

api = "http://ddragon.leagueoflegends.com/cdn/9.24.2/img/champion/"

with open('champion.json', encoding="utf8") as json_file:
    data = json.load(json_file)
    #print(data["data"])
    for championKey in data["data"]:
        champion = data["data"][championKey]
        imageName = champion["image"]["full"]
        path = "./images/"+imageName
        r = response = requests.get(api+imageName, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)