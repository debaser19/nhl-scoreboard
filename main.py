import requests
import json
import pandas as pd
import creds

def getTodaysGames():
    print('Getting list of games for today...')
    url = 'https://statsapi.web.nhl.com/api/v1/schedule'

    r = requests.get(url)
    data = r.json()

    list_of_games = []

    for date in data['dates']:
        for game in date['games']:
            game_dict = {
                "away_team": game['teams']['away']['team']['name'],
                "away_score": game['teams']['away']['score'],
                "home_team": game['teams']['home']['team']['name'],
                "home_score": game['teams']['home']['score'],
                "game_status": game['status']['detailedState'],
                "period": game['status']['statusCode']
            }
            list_of_games.append(game_dict)
    
    print('Done!')

    return list_of_games


def getLeafsRoster():
    print('Grabbing list of players...')
    url = 'https://statsapi.web.nhl.com/api/v1/teams/10/roster'

    r = requests.get(url)
    data = r.json()
    roster = data['roster']

    list_of_players = []

    for player in roster:
        player_dict = {
            "id": player['person']['id'],
            "name": player['person']['fullName'],
            "number": player['jerseyNumber'],
            "position": player['position']['abbreviation']
        }
        list_of_players.append(player_dict)

    print('Done!')

    return list_of_players


def getLeafsStats():
    print('Gathering stats for players...')
    roster = getLeafsRoster()
    list_of_player_stats = []
    for player in roster:
        url = f'https://statsapi.web.nhl.com/api/v1/people/{player["id"]}/stats?stats=statsSingleSeason'

        r = requests.get(url)
        data = r.json()
        stats = data['stats']

        # exclude goalies
        if player['position'] != 'G':
            for item in stats:
                for stat in item['splits']:
                    player_stats_dict = {
                        "name": player['name'],
                        "number": player['number'],
                        "position": player['position'],
                        "games": stat['stat']['games'],
                        "goals": stat['stat']['goals'],
                        "assists": stat['stat']['assists'],
                        "points": stat['stat']['points'],
                        "plusMinus": stat['stat']['plusMinus'],
                        "pim": stat['stat']['pim'],
                        "ppg": stat['stat']['powerPlayGoals'],
                        "shg": stat['stat']['shortHandedGoals'],
                        "shots": stat['stat']['shots'],
                        "blocked": stat['stat']['blocked']
                    }
                    list_of_player_stats.append(player_stats_dict)

    print('Done!')

    return list_of_player_stats


def sortStats():
    data = getLeafsStats()
    df = pd.DataFrame(data)
    # sort by points
    df = df.sort_values(by=['points'], ascending=False)

    return df.to_dict('records')


def doMagic():
    apikey = creds.creds['apikey']
    url = f'http://leafsconnected.com/api/forums/posts?key={apikey}'

    players = sortStats()
    td_string = ''
    for player in players:
        td_string += f'''
        <tr>
        <td>{player['name']}</td>
        <td>{player['number']}</td>
        <td>{player['position']}</td>
        <td>{player['games']}</td>
        <td>{player['goals']}</td>
        <td>{player['assists']}</td>
        <td>{player['points']}</td>
        </tr>
        '''

        post_content = f'''
        <table>
        <thead>
        <tr>
        <th>Player</th>
        <th>Num</th>
        <th>Pos</th>
        <th>GP</th>
        <th>G</th>
        <th>A</th>
        <th>P</th>
        </tr>
        </thead>
        <tbody>
        {td_string}
        </tbody>
        </table>
        '''

    payload = {
        "topic": 8709,
        "author": 2,
        "post": post_content
    }

    r = requests.post(url,data=payload)

    return r


doMagic()

