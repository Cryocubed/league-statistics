import collections
import math

from scipy import stats as scistats


def compute_all_stats(api, name, season_list=list(), queue_list=list()):
    """
    Calculates a variety of statistics on a league player
    :param api: A supplied riot api instance to avoid duplicating saved data
    :param name: Player name
    :param season_list: A list of the seasons to parse. Empty uses all data.
    :param queue_list: A list of the queues to parse. Empty uses all data.
    :return: Statistics dictionary
    """

    # Initialize variables
    champion_stats = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
    statistics = {'filters': {'Seasons': season_list, 'Queues': queue_list}, 'champion_stats': {},
                  'player_synergy': collections.defaultdict(lambda: collections.defaultdict(int)),
                  'lane_winrate': collections.defaultdict(lambda: collections.defaultdict(int)),
                  'total_time': 0, 'total_wins': 0}

    # <editor-fold desc="Get all matches given provided parameters">
    match_list = []
    curr_index = 0
    prev_len = -1
    while len(match_list) % 100 == 0 and len(match_list) != prev_len:
        prev_len = len(match_list)
        match_list += api.get_matches_by_filter(name, begin_index=curr_index, season=season_list, queue=queue_list)
        curr_index += 100
    print(str(len(match_list)), 'matches to process.')
    # </editor-fold>

    # <editor-fold desc="Iterate over all matches to collect data">
    for match_id in match_list:
        match_compiled_data = {}
        match_data = api.get_match_by_id(match_id)

        # <editor-fold desc="Determine participant id and team id of player">
        self_account_id = api.get_summoner(name)['accountId']
        for participant in match_data['participantIdentities']:
            if self_account_id == participant['player']['accountId']:
                self_id = participant['participantId']
                break

        for participant in match_data['participants']:
            if self_id == participant['participantId']:
                own_team_id = participant['teamId']
                break
        # </editor-fold>

        # Determine if the player's team won
        for team in match_data['teams']:
            if team['teamId'] == own_team_id:
                match_compiled_data['win_status'] = team['win']

        # Determine game length
        statistics['total_time'] += match_data['gameDuration']

        # Iterate over each participant, collecting various data
        for participant, participant_identity in zip(match_data['participants'], match_data['participantIdentities']):

            # Collect player synergy data
            if participant['teamId'] == own_team_id:
                player_name = participant_identity['player']['summonerName']
                statistics['player_synergy'][player_name][match_compiled_data['win_status']] += 1

            # Determine role W/Ls
            if participant['participantId'] == self_id:
                role = participant['timeline']['role']
                lane = participant['timeline']['lane']

                if lane == 'BOTTOM':
                    statistics['lane_winrate']['BOT_' + role][match_compiled_data['win_status']] += 1
                else:
                    statistics['lane_winrate'][lane][match_compiled_data['win_status']] += 1

            # Count champion W/Ls
            # Determine team
            champion = participant['championId']
            if participant['participantId'] == self_id:
                team = 'self'
            elif participant['teamId'] == own_team_id:
                team = 'team'
            else:
                team = 'enemy'

            # Update champion stats, ensuring to update team in addition to self
            if match_compiled_data['win_status'] == 'Win':
                champion_stats[team][champion]['Win'] += 1
                if team == 'self':
                    champion_stats['team'][champion]['Win'] += 1
                    statistics['total_wins'] += 1
            else:
                champion_stats[team][champion]['Fail'] += 1
                if team == 'self':
                    champion_stats['team'][champion]['Fail'] += 1
    # </editor-fold>

    # <editor-fold desc="Calculate player synergies">
    for player_name, data in list(statistics['player_synergy'].items()):
        # noinspection PyTypeChecker
        if data['Win'] + data['Fail'] > 10:  # Needs more than 10 games together
            # noinspection PyTypeChecker
            data['ratio'] = data['Win'] / (data['Win'] + data['Fail'])
        else:
            del statistics['player_synergy'][player_name]
    # </editor-fold>

    # Calculate role winrates
    for role in statistics['lane_winrate'].keys():
        statistics['lane_winrate'][role]['ratio'] = statistics['lane_winrate'][role]['Win'] / \
                                                    (statistics['lane_winrate'][role]['Win'] +
                                                     statistics['lane_winrate'][role]['Fail'])

    # Player synergy significance calculations
    for player in statistics['player_synergy'].keys():
        wins = statistics['player_synergy'][player]['Win']
        losses = statistics['player_synergy'][player]['Fail']
        statistics['player_synergy'][player]['significance'] = calculate_significance(wins, losses)

    # Role significance calculations
    for role in statistics['lane_winrate'].keys():
        wins = statistics['lane_winrate'][role]['Win']
        losses = statistics['lane_winrate'][role]['Fail']
        statistics['lane_winrate'][role]['significance'] = calculate_significance(wins, losses)

    # Calculate overall W/Ls
    statistics['total_losses'] = len(match_list) - statistics['total_wins']

    # <editor-fold desc="Compute champion winrates">
    for team in champion_stats.keys():
        cstats = collections.defaultdict(dict)
        for champion in champion_stats[team]:
            try:
                wins = champion_stats[team][champion]['Win']
                losses = champion_stats[team][champion]['Fail']
                total = wins + losses

                cstats[api.get_champion_from_id(champion)]['winrate'] = round(100 * wins / total, 2)
                cstats[api.get_champion_from_id(champion)]['games'] = total

                # Calculate significance
                cstats[api.get_champion_from_id(champion)]['significance'] = calculate_significance(wins, losses)

            except ZeroDivisionError:
                continue

        statistics['champion_stats']['winrate_' + team] = []
        for champion, data in cstats.items():
            statistics['champion_stats']['winrate_' + team].append((champion, data['winrate'], data['games'],
                                                                    data['significance']))

        statistics['champion_stats']['winrate_' + team].sort(key=lambda tup: tup[1], reverse=True)
    # </editor-fold>

    return statistics


def calculate_significance(wins, losses):
    total = wins + losses
    stdev = math.sqrt(total * math.pow(0.5, 2))
    offset = abs(wins - total / 2)
    if offset > 0:
        offset -= 0.5
    return round(2 * (1 - scistats.norm.cdf(offset / stdev)), 4)
