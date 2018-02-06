import collections


def compute_all_stats(api, name, season_list=list(), queue_list=list()):
    """
    Calculates a variety of statistics on a league player
    :param api: A supplied riot api instance to avoid duplicating saved data
    :param name: Player name
    :param season_list: A list of the seasons to parse. Empty uses all data.
    :param queue_list: A list of the queues to parse. Empty uses all data.
    :return:
    """

    # Initialize variables
    statistics = {'filters': {'Seasons': season_list, 'Queues': queue_list}}

    # Get all matches given provided parameters
    match_list = []
    curr_index = 0
    prev_len = - 100
    while len(match_list) % 100 == 0 and len(match_list) != prev_len:
        prev_len = len(match_list)
        match_list += api.get_matches_by_filter(name, begin_index=curr_index, season=season_list, queue=queue_list)
        curr_index += 100

    # Print the number of matches to process
    print(str(len(match_list)), 'matches to process.')

    # Build list of all champion ids
    champion_data = api.make_request('/lol/static-data/v3/champions')
    champion_id_list = []
    for champion in champion_data['data']:
        champion_id_list.append(champion_data['data'][champion]['id'])

    # Build champion stats dictionary
    champion_stats = {'self': {}, 'team': {}, 'enemy': {}}
    for champion in champion_id_list:
        for team in champion_stats.keys():
            champion_stats[team][champion] = {'win': 0, 'loss': 0}

    # Iterate over all matches to collect champ W/Ls
    for match in match_list:
        match_champion_list = api.get_match_champion_list(match, name)

        # Update stats for all teams
        for team in champion_stats.keys():
            for champion in match_champion_list[team]:
                if match_champion_list['win_status'] == 'Win':
                    champion_stats[team][champion]['win'] += 1
                else:
                    champion_stats[team][champion]['loss'] += 1

    # Calculate overall winrate
    wins_counter = 0
    for champion in champion_stats['self'].keys():
        wins_counter += champion_stats['self'][champion]['win']

    statistics['total_wins'] = wins_counter
    statistics['total_losses'] = len(match_list) - wins_counter

    # Compute champion winrates
    for team in champion_stats.keys():
        statistics['winrate_' + team] = compute_champ_winrates(api, champion_stats[team])

    return statistics


def compute_champ_winrates(api, champion_stats):
    # Calculate self winrates and # of games played
    stats = collections.defaultdict(dict)
    for champion in champion_stats:
        try:
            wins = champion_stats[champion]['win']
            losses = champion_stats[champion]['loss']

            stats[api.get_champion_from_id(champion)]['winrate'] = round(100 * wins / (wins + losses), 2)
            stats[api.get_champion_from_id(champion)]['games'] = wins + losses

        except ZeroDivisionError:
            continue

    formatted_list = []
    for champion, data in stats.items():
        formatted_list.append((champion, data['winrate'], data['games']))

    formatted_list.sort(key=lambda tup: tup[1])
    return formatted_list[::-1]
