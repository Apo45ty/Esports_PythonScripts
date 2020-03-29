import json


with open('champion.json', encoding="utf8") as json_file:
    data = json.load(json_file)
    result = {}
    for championKey in data["data"]:
        champion = data["data"][championKey]
        result[champion["key"]]=champion

    with open('champData.json', 'w') as outfile:
        json.dump(result, outfile)

    