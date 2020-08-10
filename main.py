import requests
import json
import pandas as pd
import creds
from datetime import date

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


def createScoreboard():
    games = getTodaysGames()

    style_content = '''
    <style>
    table{border-collapse:collapse;}
    table,th,td{border:1px solid;padding:5px;}
    td:first-child{width:170px;}
    td:last-child{width:70px;text-align:center;}
    </style>
    '''
    table_content = ''
    for game in games:
        # format the period
        if (int(game['period'])-2) not in range(1,3):
            game['period'] = ''
        elif (int(game['period'])-2) == 4:
            game['period'] = 'OT'
        else:
            game['period'] = f'Period {int(game["period"])-2}'
        table_content += f'''
        <p>
        <table>
        <thead>
        <tr>
        <th>Teams</th>
        <th>Score</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>{game['away_team']}</td>
        <td>{game['away_score']}</td>
        </tr>
        <tr>
        <td>{game['home_team']}</td>
        <td>{game['home_score']}</td>
        </tr>
        <tr>
        <td>{game['game_status']}</td>
        <td>{game['period']}</td>
        </tr>
        </tbody>
        </table>
        </p>
        '''
    post_content = style_content + table_content

    return post_content


def getCurrentDate():
    current_date = date.today()
    month = current_date.month
    day = current_date.day
    year = current_date.year
    formatted_date = f'{month}/{day}/{year}'

    return formatted_date


def postScoreboard():
    apikey = creds.creds['apikey']
    url = f'http://leafsconnected.com/api/forums/topics?key={apikey}'

    payload = {
        "forums": [56]
    }

    r = requests.get(url,params=payload)
    data = r.json()
    topics = data['results']
    
    list_of_topics = []
    for topic in topics:
        topic_dict = {
            "id": topic['id'],
            "title": topic['title']
        }
        list_of_topics.append(topic_dict)

    topic_title = f'[{getCurrentDate()}] Out of Town Scoreboard'

    post_content = f'''
        <h1>{topic_title}</h1>
        {createScoreboard()}
        '''
    
    # check if today's post is already created
    if topic['title'] != topic_title:
        print(topic['title'])
        print("Creating topic...")
        payload = {
            "forum": 56,
            "title": topic_title,
            "post": post_content,
            "author": 2,
            "pinned": 1
        }
        r = requests.post(url,data=payload)
    else:
        # create it if it doesn't exist
        print("Updating post...")
        post_id = topic['firstPost']['id']
        url = f'http://leafsconnected.com/api/forums/posts/{post_id}?key={apikey}'
        payload = {
            "post": post_content
        }
        r = requests.post(url,data=payload)


postScoreboard()

