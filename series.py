from datetime import date, datetime

import requests

import pytz
import requests
from dateutil.parser import parse

import creds


def get_current_date():
    current_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
    return current_date


def get_series_summaries():
    print('Grabbing playoff series summaries')
    endpoint = 'api/v1/tournaments/playoffs?expand=round.series,schedule.game.seriesSummary&season=20192020'
    r = requests.get(base_url+endpoint).json()
    playoff_rounds = r['rounds']
    current_round = r['defaultRound']
    series_summaries = []
    for playoff_round in playoff_rounds:
        if playoff_round['number'] == current_round:
            for series in playoff_round['series']:
                series_summaries.append(series)

    return series_summaries


def parse_series(series_summaries, current_date):
    series_list = []
    for series in series_summaries:
        top_seed = series['matchupTeams'][0]

        endpoint = f'api/v1/schedule?startDate=2020-08-10&teamId={top_seed["team"]["id"]}&endDate={current_date}'

        r = requests.get(base_url+endpoint).json()

        series_dates = r['dates']
        series_games = []
        for game_date in series_dates:
            game_pk = game_date['games'][0]['gamePk']
            game_endpoint = f'/api/v1/game/{game_pk}/feed/live'

            game_feed = requests.get(base_url+game_endpoint).json()
            live_data = game_feed['liveData']

            series_games.append(live_data)

        series_dict = {
            'series': series,
            'linescores': series_games
        }

        series_list.append(series_dict)

    return series_list


def create_html_strings():
    html_strings = []
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
    for series in parsed_series:
        linescores = ''
        # create the series scoreboard
        series_game_number = len(series['linescores'])
        series_name = series["series"]["names"]["matchupName"]
        series_status = series["series"]["currentGame"]["seriesSummary"]["seriesStatus"]
        top_seed_name = series["series"]["matchupTeams"][0]["team"]["name"]
        top_seed_wins = series["series"]["matchupTeams"][0]["seriesRecord"]['wins']
        top_seed_losses = series["series"]["matchupTeams"][0]["seriesRecord"]['losses']
        top_seed_rank = series["series"]["matchupTeams"][0]['seed']['rank']
        bottom_seed_name = series["series"]["matchupTeams"][1]["team"]["name"]
        bottom_seed_wins = series["series"]["matchupTeams"][1]["seriesRecord"]['wins']
        bottom_seed_losses = series["series"]["matchupTeams"][1]["seriesRecord"]['losses']
        bottom_seed_rank = series["series"]["matchupTeams"][1]['seed']['rank']

        series_scoreboard_string = f"""
        <div class="series-scoreboard-container">
        <h4>#{top_seed_rank} {top_seed_name} ({top_seed_wins}-{top_seed_losses})
        vs #{bottom_seed_rank} {bottom_seed_name} ({bottom_seed_wins}-{bottom_seed_losses})</h4>
        <h5>{series_status}</h5>
        </div>
        """

        for linescore in series['linescores'][::-1]:
            per1HomeGoals = per2HomeGoals = per3HomeGoals = 0
            per1AwayGoals = per2AwayGoals = per3AwayGoals = 0
            for period in linescore['linescore']['periods']:
                if period['num'] == 1:
                    per1HomeGoals = period['home']['goals']
                    per1AwayGoals = period['away']['goals']
                elif period['num'] == 2:
                    per2HomeGoals = period['home']['goals']
                    per2AwayGoals = period['away']['goals']
                elif period['num'] == 3:
                    per3HomeGoals = period['home']['goals']
                    per3AwayGoals = period['away']['goals']

            if 'winner' in linescore['decisions']:
                goalies_string = f'''
                <div class="goalies">
                <ul>
                <li>W: {linescore["decisions"]["winner"]["fullName"]}</li>
                <li>L: {linescore["decisions"]["loser"]["fullName"]}</li>
                </ul>
                </div>
                '''
            else:
                goalies_string = ''

            if 'firstStar' in linescore['decisions']:
                threestars_string = f'''
                <div class="threestars">
                <ul>
                <li>1st Star: {linescore["decisions"]["firstStar"]["fullName"]}</li>
                <li>2nd Star: {linescore["decisions"]["secondStar"]["fullName"]}</li>
                <li>3rd Star: {linescore["decisions"]["thirdStar"]["fullName"]}</li>
                </ul>
                </div>
                '''
            else:
                threestars_string = ''

            if 'currentPeriodOrdinal' not in linescore['linescore']:
                linescore['linescore']["currentPeriodOrdinal"] = '-'
                linescore['linescore']["currentPeriodTimeRemaining"] = '00:00'

            total_away_goals = linescore['linescore']['teams']['away']['goals']
            total_home_goals = linescore['linescore']['teams']['home']['goals']

            # TODO: fix game status for games that have not started
            #   need to pull in game status from earlier nhl api call
            #   and conditionally set value of game state in the string
            linescore_string = f'''
                    <div class="scoreboard-container">
                    <div class="linescore">
                    <div class="headline">
                    <ul>
                    <li>Game {series_game_number}</li>
                    <li>{linescore["linescore"]['teams']['home']['team']['name']} @ {linescore['linescore']['teams']['away']['team']['name']}</li>
                    <li>{linescore["linescore"]["currentPeriodOrdinal"]}</li>
                    <li>{linescore["linescore"]["currentPeriodTimeRemaining"]}</li>
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
                    <td>{linescore['linescore']['teams']['away']['team']['abbreviation']}</td>
                    <td>{per1AwayGoals}</td>
                    <td>{per2AwayGoals}</td>
                    <td>{per3AwayGoals}</td>
                    <td><strong>{total_away_goals}</strong></td>
                    </tr>
                    <tr>
                    <td>{linescore['linescore']['teams']['home']['team']['abbreviation']}</td>
                    <td>{per1HomeGoals}</td>
                    <td>{per2HomeGoals}</td>
                    <td>{per3HomeGoals}</td>
                    <td><strong>{total_home_goals}</strong></td>
                    </tr>
                    </tbody>
                    </table>
                    </div>
                    {threestars_string}
                    {goalies_string}
                    <br/><hr align="left" width="500px"/><br/>
                    '''

            linescores += linescore_string

            full_series_string = style_string + series_scoreboard_string + linescores

            series_dict = {
                'series_name': series_name,
                'series_string': full_series_string
            }
            series_game_number -= 1

        html_strings.append(series_dict)

    return html_strings


def post_threads(html_strings):
    apikey = creds.creds['apikey']
    url = f'http://leafsconnected.com/api/forums/topics?key={apikey}'

    payload = {
        "forums": [55],
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

    for string in html_strings:
        # check if topic already created
        topic_title = string['series_name']
        post_content = string['series_string']
        current_time = datetime.now()
        current_time = current_time.strftime('%b %d %Y %I:%M:%S %p')
        post_content += f'<p><strong>Last updated: {current_time}</strong></p>'
        topic_titles = []

        for pinned_topic in list_of_topics:
            topic_titles.append(pinned_topic['title'])

        if topic_title not in topic_titles:
            topic_exists = False
        else:
            topic_exists = True

        if not topic_exists:
            print(f'Creating topic: {topic_title}')
            payload = {
                "forum": 55,
                "title": topic_title,
                "post": post_content,
                "author": 2,
                "pinned": 1
            }
            requests.post(url, data=payload)
        else:
            # create it if it doesn't exist
            for topic in topics:
                if topic['title'] == topic_title:
                    post_id = topic['firstPost']['id']
            print(f"Updating post: {topic_title} - ID: {post_id}")
            url = f'http://leafsconnected.com/api/forums/posts/{post_id}?key={apikey}'
            payload = {
                "post": post_content
            }
            requests.post(url, data=payload)


if __name__ == '__main__':
    base_url = 'https://statsapi.web.nhl.com/'
    series_summaries = get_series_summaries()
    parsed_series = parse_series(series_summaries, get_current_date())
    html_series_strings = create_html_strings()
    post_threads(html_series_strings)

