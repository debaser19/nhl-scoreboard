from datetime import date, datetime

import pytz
import requests
from dateutil.parser import parse

import creds

url = 'https://statsapi.web.nhl.com/'


def get_game_ids():
    print('Grabbing game IDs...')
    endpoint = 'api/v1/schedule'

    r = requests.get(url + endpoint)
    data = r.json()

    game_ids = []

    for date in data['dates']:
        for game in date['games']:
            game_ids.append(game['gamePk'])

    print(f'Game IDs: {game_ids}')

    return game_ids


def get_game_feeds():
    game_ids = get_game_ids()
    game_feeds = []
    for game_id in game_ids:
        endpoint = f'/api/v1/game/{game_id}/feed/live'
        r = requests.get(url + endpoint)
        data = r.json()
        game_feed_dict = {
            "id": game_id,
            "feed": data
        }
        game_feeds.append(game_feed_dict)

    return game_feeds


def parse_game_feeds():
    game_feeds = get_game_feeds()
    parsed_feeds = []
    for game_feed in game_feeds:
        game_data = game_feed['feed']['gameData']
        live_data = game_feed['feed']['liveData']
        print(f'Parsing feed for {game_feed["id"]}')

        # convert start time
        start_time = game_data['datetime']['dateTime']
        start_time = parse(start_time)
        est_timezone = pytz.timezone('America/New_York')
        start_time = start_time.astimezone(est_timezone)
        start_time = start_time.strftime('%I:%M %p')

        try:
            parsed_feed = {
                "start_time": start_time,
                "end_time": game_data['datetime']['endDateTime'],
                "game_state": game_data['status']['detailedState'],
                "away_team": game_data['teams']['away']['name'],
                "away_abbreviation": game_data['teams']['away']['abbreviation'],
                "home_team": game_data['teams']['home']['name'],
                "home_abbreviation": game_data['teams']['home']['abbreviation'],
                "linescore": live_data['linescore'],
                "boxscore": live_data['boxscore'],
                "decisions": live_data['decisions']
            }
        except KeyError as e:
            print(f'Game not finished - no decisions: {e}')
            parsed_feed = {
                "start_time": start_time,
                "end_time": "TBD",
                "game_state": game_data['status']['detailedState'],
                "away_team": game_data['teams']['away']['name'],
                "away_abbreviation": game_data['teams']['away']['abbreviation'],
                "home_team": game_data['teams']['home']['name'],
                "home_abbreviation": game_data['teams']['home']['abbreviation'],
                "linescore": live_data['linescore'],
                "boxscore": live_data['boxscore'],
                "decisions": live_data['decisions']
            }
        parsed_feeds.append(parsed_feed)

    return parsed_feeds


def create_scores_feed():
    parsed_feeds = parse_game_feeds()
    post_content = ''
    style_string = '''
    <style>
    .scoreboard-container {
        font-family: verdana,arial,helvetica,sans-serif;
        font-size: 12px;
    }
    table {
        border-collapse:collapse;
        font-family: verdana,arial,helvetica,sans-serif;
        text-align: center;
        font-size: 12px;
        }
    table th{
        background-color: #214d8d;
        color:white;
        border-top: 1px solid #214d8d;
        border-right: 1px solid #214d8d;
        border-bottom: 2px solid #214d8d;
        border-left: 1px solid #214d8d;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: normal;
        height: 22px;
        vertical-align: middle;
        padding: 6px 40px;
    }
    table td {
        border: 1px solid #214d8d;
        padding: 6px;
        }
    .goalies ul li, 
    .threestars ul li,
    .headline ul li {
        list-style: none;
        display: inline;
        padding: 10px;
        font-weight: bold;
    }
    </style>
    '''

    for feed in parsed_feeds:
        # get scores by period
        per1HomeGoals = per2HomeGoals = per3HomeGoals = 0
        per1AwayGoals = per2AwayGoals = per3AwayGoals = 0
        for period in feed['linescore']['periods']:
            if period['num'] == 1:
                per1HomeGoals = period['home']['goals']
                per1AwayGoals = period['away']['goals']
            elif period['num'] == 2:
                per2HomeGoals = period['home']['goals']
                per2AwayGoals = period['away']['goals']
            elif period['num'] == 3:
                per3HomeGoals = period['home']['goals']
                per3AwayGoals = period['away']['goals']

        if 'winner' in feed['decisions']:
            goalies_string = f'''
            <div class="goalies">
            <ul>
            <li>W: {feed["decisions"]["winner"]["fullName"]}</li>
            <li>L: {feed["decisions"]["loser"]["fullName"]}</li>
            </ul>
            </div>
            '''
        else:
            goalies_string = ''

        if 'firstStar' in feed['decisions']:
            threestars_string = f'''
            <div class="threestars">
            <ul>
            <li>1st Star: {feed["decisions"]["firstStar"]["fullName"]}</li>
            <li>2nd Star: {feed["decisions"]["secondStar"]["fullName"]}</li>
            <li>3rd Star: {feed["decisions"]["thirdStar"]["fullName"]}</li>
            </ul>
            </div>
            '''
        else:
            threestars_string = ''

        if 'currentPeriodOrdinal' not in feed['linescore']:
            feed["linescore"]["currentPeriodOrdinal"] = feed['game_state']
            feed["linescore"]["currentPeriodTimeRemaining"] = '00:00'

        totalAwayGoals = feed['linescore']['teams']['away']['goals']
        totalHomeGoals = feed['linescore']['teams']['home']['goals']

        linescore_string = f'''
        <div class="scoreboard-container">
        <div class="linescore">
        <div class="headline">
        <ul>
        <li>{feed["start_time"]}</li>
        <li>{feed["away_abbreviation"]} @ {feed["home_abbreviation"]}</li>
        <li>{feed["linescore"]["currentPeriodOrdinal"]}</li>
        <li>{feed["linescore"]["currentPeriodTimeRemaining"]}</li>
        </ul>
        </div>
        <table>
        <thead>
        <tr>
        <th>Teams</th>
        <th>1st</th>
        <th>2nd</th>
        <th>3rd</th>
        <th>Total</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>{feed["away_abbreviation"]}</td>
        <td>{per1AwayGoals}</td>
        <td>{per2AwayGoals}</td>
        <td>{per3AwayGoals}</td>
        <td><strong>{totalAwayGoals}</strong></td>
        </tr>
        <tr>
        <td>{feed["home_abbreviation"]}</td>
        <td>{per1HomeGoals}</td>
        <td>{per2HomeGoals}</td>
        <td>{per3HomeGoals}</td>
        <td><strong>{totalHomeGoals}</strong></td>
        </tr>
        </tbody>
        </table>
        </div>
        {threestars_string}
        {goalies_string}
        <br/><hr align="left" width="600px"/><br/>
        '''

        post_content += linescore_string

    post_content = style_string + post_content

    return post_content


def get_current_date():
    current_date = date.today()
    month = current_date.month
    day = current_date.day
    year = current_date.year
    formatted_date = f'{month}/{day}/{year}'

    return formatted_date


def post_thread():
    apikey = creds.creds['apikey']
    url = f'http://leafsconnected.com/api/forums/topics?key={apikey}'

    payload = {
        "forums": [10],
        "pinned": 1
    }

    r = requests.get(url, params=payload)
    data = r.json()
    topics = data['results']

    list_of_topics = []
    for topic in topics:
        topic_dict = {
            "id": topic['id'],
            "title": topic['title']
        }
        list_of_topics.append(topic_dict)

    topic_title = f'[{get_current_date()}] Out of Town Scoreboard'

    post_content = create_scores_feed()
    current_time = datetime.now()
    current_time = current_time.strftime('%b %d %Y %I:%M:%S %p')

    post_content += f'<p><strong>Last updated: {current_time}</strong></p>'

    # check if today's post is already created
    for pinned_topic in list_of_topics:
        if topic_title not in pinned_topic['title']:
            topic_exists = False
        else:
            topic_exists = True
    if not topic_exists:
        print("Creating topic...")
        payload = {
            "forum": 10,
            "title": topic_title,
            "post": post_content,
            "author": 2,
            "pinned": 1
        }
        r = requests.post(url, data=payload)
    else:
        # create it if it doesn't exist
        print("Updating post...")
        post_id = topic['firstPost']['id']
        url = f'http://leafsconnected.com/api/forums/posts/{post_id}?key={apikey}'
        payload = {
            "post": post_content
        }
        r = requests.post(url, data=payload)


post_thread()
