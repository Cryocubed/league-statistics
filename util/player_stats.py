import collections


def compute_champion_winrates(api, name, season_list=list(), queue_list=list()):
    """
    Calculates a variety of statistics on a league player
    :param api: A supplied riot api instance to avoid duplicating saved data
    :param name: Player name
    :param season_list: A list of the seasons to parse. Empty uses all data.
    :param queue_list: A list of the queues to parse. Empty uses all data.
    :return:
    """

    # Initialize variables and counters
    match_list = []
    curr_index = 0
    statistics = {'filters': {'Seasons': season_list, 'Queues': queue_list}}

    # Get all matches given provided parameters
    while len(match_list) % 100 == 0:
        match_list += api.get_matches_by_filter(name, begin_index=curr_index, season=season_list, queue=queue_list)
        curr_index += 100

    # Print the number of matches to process
    print(str(len(match_list)), 'matches to process.')

    # Build list of all champion ids
    champion_data = api.make_request('/lol/static-data/v3/champions')
    champion_id_list = []
    for champion in champion_data['data']:
        champion_id_list.append(champion_data['data'][champion]['id'])

    # Initialize champion stats dictionary
    # Format:
    # {same_team: {
    #     champion: {
    #         win: int,
    #         loss: int
    #     }
    # },
    # enemy_team: {
    #     champion: {
    #         win: int,
    #         loss: int
    #     }
    # }}
    champion_stats = {'same_team': {}, 'enemy_team': {}, 'self': {}}

    # Build champion stats dictionary
    for champion in champion_id_list:
        champion_stats['same_team'][champion] = {'win': 0, 'loss': 0}
        champion_stats['enemy_team'][champion] = {'win': 0, 'loss': 0}
        champion_stats['self'][champion] = {'win': 0, 'loss': 0}

    total_wins = 0
    total_losses = 0

    # Iterate over all matches
    for match in match_list:
        # Get W/Ls for each champion in match
        match_champion_list = api.get_match_champion_list(match, name)

        # Update stats on team side
        for champion in match_champion_list['same_team']:
            if match_champion_list['win_status'] == 'Win':
                champion_stats['same_team'][champion]['win'] += 1
            else:
                champion_stats['same_team'][champion]['loss'] += 1

        # Update stats on enemy side
        for champion in match_champion_list['enemy_team']:
            if match_champion_list['win_status'] == 'Win':
                champion_stats['enemy_team'][champion]['win'] += 1
            else:
                champion_stats['enemy_team'][champion]['loss'] += 1

        # Update stats for self
        for champion in match_champion_list['self']:
            if match_champion_list['win_status'] == 'Win':
                champion_stats['self'][champion]['win'] += 1
                total_wins += 1
            else:
                champion_stats['self'][champion]['loss'] += 1
                total_losses += 1

    statistics['total_wins'] = total_wins
    statistics['total_losses'] = total_losses

    print("Parsed " + str(len(match_list)) + " matches")
    # TODO From here on can be moved into a new function
    # TODO Add functionality to keep track of teammates as well
    # Calculate self winrates and # of games played
    self_stats = collections.defaultdict(dict)
    for champion in champion_stats['self']:
        try:
            wins = champion_stats['self'][champion]['win']
            losses = champion_stats['self'][champion]['loss']

            self_stats[api.get_champion_from_id(champion)]['winrate'] = round(100 * wins/(wins + losses), 2)
            self_stats[api.get_champion_from_id(champion)]['games'] = wins + losses

        except ZeroDivisionError:
            continue

    formatted_list = []
    for champion, data in self_stats.items():
        formatted_list.append((champion, data['winrate'], data['games']))

    formatted_list.sort(key=lambda tup: tup[1])
    statistics['winrate_self'] = formatted_list[::-1]

    # print("Self champion winrates and # of games played")
    # for item in formatted_list[::-1]:
    #     print(item)

    # Calculate lose rates
    enemy_stats = collections.defaultdict(dict)
    for champion in champion_stats['enemy_team']:
        try:
            wins = champion_stats['enemy_team'][champion]['win']
            losses = champion_stats['enemy_team'][champion]['loss']

            enemy_stats[api.get_champion_from_id(champion)]['winrate'] = round(100 * wins/(wins + losses), 2)
            enemy_stats[api.get_champion_from_id(champion)]['games'] = wins + losses

        except ZeroDivisionError:
            continue

    formatted_enemy_list = []
    for champion, data in enemy_stats.items():
        formatted_enemy_list.append((champion, data['winrate'], data['games']))

        formatted_enemy_list.sort(key=lambda tup: tup[1])

    # print("vs enemy champion winrates and # of games played against them")
    # for item in formatted_enemy_list[::-1]:
    #     print(item)

    statistics['winrate_enemy'] = formatted_enemy_list[::-1]
    return statistics
