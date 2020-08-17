from datetime import date, datetime

import requests

import pytz
import requests
from dateutil.parser import parse


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

    for series in series_summaries:
        print(series)

    return series_summaries


def parse_series(series_summaries, current_date):
    # TODO: finish loop through each series and each game
    #   need to create separate dict full of games for each series
    #   ie all phl/mtl games from round 1 need to be in single dict
    for series in series_summaries:
        top_seed = series['matchupTeams'][0]
        bottom_seed = series['matchupTeams'][1]

        endpoint = f'api/v1/schedule?startDate=2020-08-10&teamId={top_seed["team"]["id"]}&endDate={current_date}'

        r = requests.get(base_url+endpoint).json()

        series_dates = r['dates']
        series_games = []
        for game_date in series_dates:
            game_pk = game_date['games'][0]['gamePk']
            game_endpoint = f'/api/v1/game/{game_pk}/feed/live'

            game_feed = requests.get(base_url+game_endpoint).json()
            linescore = game_feed['liveData']['linescore']

            print(linescore)

    return True


if __name__ == '__main__':
    base_url = 'https://statsapi.web.nhl.com/'
    series_summaries = get_series_summaries()
    parsed_series = parse_series(series_summaries, get_current_date())

