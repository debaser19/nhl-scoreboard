import requests
import json

url = 'https://statsapi.web.nhl.com/api/v1/schedule'

response = requests.get(url)
response = response.json()

list_of_games = []

for date in response['dates']:
    for game in date['games']:
        game_dict = {
            "away_team": game['teams']['away']['team']['name'],
            "away_score": game['teams']['away']['score'],
            "home_team": game['teams']['home']['team']['name'],
            "home_score": game['teams']['home']['score'],
            "game_status": game['status']['detailedState']
        }
        list_of_games.append(game_dict)

for game in list_of_games:
    print(f'{game["away_team"]}: {game["away_score"]}')
    print(f'{game["home_team"]}: {game["home_score"]}')
    print(f'{game["game_status"]}\n')
