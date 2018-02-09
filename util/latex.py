import os


def build_latex_file(filename):
    os.system("pdflatex " + filename + '.tex')
    os.system("pdflatex " + filename + '.tex')  # Twice for table of contents
    try:
        os.remove(filename + '.toc')
        os.remove(filename + '.aux')
        os.remove(filename + '.log')
        if filename != 'report_template':
            os.remove(filename + '.tex')
        os.rename(filename + '.pdf', 'exports/' + filename + '.pdf')
    except FileNotFoundError:
        print('Tried to remove non existant file')


def build_champion_report(statistics_dict, player_name):
    player_name = player_name.replace(' ', '')

    # Read template into memory
    template_file = open('report_template.tex', 'r')
    file_str = template_file.read()
    template_file.close()

    # Config
    significance_color = [(0.01, 'electricblue'), (0.05, 'green'), (0.1, 'yellow'), (0.25, 'orange')]

    ######################################################
    # Modify file string

    # Player
    file_str = file_str.replace('!PLAYERNAME!', player_name)

    # Seasons
    file_str = file_str.replace('!SEASONS!', str(statistics_dict['filters']['Seasons']))

    # Queues
    file_str = file_str.replace('!QUEUES!', str(statistics_dict['filters']['Queues']))

    # ========
    # Overview

    # TODO League
    # file_str = file_str.replace('!PLAYERNAME!', player_name)

    # TODO ELO
    # file_str = file_str.replace('!PLAYERNAME!', player_name)

    # # Games
    total_games = statistics_dict['total_wins'] + statistics_dict['total_losses']
    file_str = file_str.replace('!OVERALLGAMES!', str(total_games))

    # Winrate
    winrate = round(100 * statistics_dict['total_wins'] / total_games, 2)
    file_str = file_str.replace('!OVERALLWINRATE!', str(winrate))

    # Days spent
    total_days_in_game = round(statistics_dict['total_time'] / 60 / 60 / 24, 2)
    file_str = file_str.replace('!OVERALLTOTALDAYS!', str(total_days_in_game))

    # =====================
    # Self champ stats
    champ_stats_str = ''
    champ_stats_str += '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} |' \
                       ' C{.2\\textwidth}}\n' \
                       'Champion Name & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for item in statistics_dict['champion_stats']['winrate_self']:
        champ_stats_str += str(item[0]) + '&' + str(item[1]) + '&' + str(item[2]) + '&'
        for sig, color in significance_color:
            if item[3] < sig:
                champ_stats_str += '\\cellcolor{' + color + '}'
                break
        champ_stats_str += str(item[3]) + '\\\\\n'

    champ_stats_str += '\\end{longtable}'
    file_str = file_str.replace('!SELFCHAMPSTATS!', champ_stats_str)

    # Enemy champ stats
    champ_stats_str = ''
    champ_stats_str += '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} |' \
                       ' C{.2\\textwidth}}\n' \
                       'Champion Name & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for item in statistics_dict['champion_stats']['winrate_enemy']:
        champ_stats_str += str(item[0]) + '&' + str(item[1]) + '&' + str(item[2]) + '&'
        for sig, color in significance_color:
            if item[3] < sig:
                champ_stats_str += '\\cellcolor{' + color + '}'
                break
        champ_stats_str += str(item[3]) + '\\\\\n'

    champ_stats_str += '\\end{longtable}'
    file_str = file_str.replace('!ENEMYCHAMPSTATS!', champ_stats_str)

    # Team champ stats
    champ_stats_str = ''
    champ_stats_str += '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} |' \
                       ' C{.2\\textwidth}}\n' \
                       'Champion Name & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for item in statistics_dict['champion_stats']['winrate_team']:
        champ_stats_str += str(item[0]) + '&' + str(item[1]) + '&' + str(item[2]) + '&'
        for sig, color in significance_color:
            if item[3] < sig:
                champ_stats_str += '\\cellcolor{' + color + '}'
                break
        champ_stats_str += str(item[3]) + '\\\\\n'

    champ_stats_str += '\\end{longtable}'
    file_str = file_str.replace('!TEAMCHAMPSTATS!', champ_stats_str)

    # Winrate by lane
    replacement_str = '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth}}\n'
    replacement_str += 'Lane & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for lane, data in statistics_dict['lane_winrate'].items():
        replacement_str += str(lane) + '&' + str(round(data['ratio'] * 100, 2)) + '&' + str(
            data['Fail'] + data['Win']) + '&'
        for sig, color in significance_color:
            if data['significance'] < sig:
                replacement_str += '\\cellcolor{' + color + '}'
                break
        replacement_str += str(data['significance']) + '\\\\\n'

    replacement_str += '\\end{longtable}'
    file_str = file_str.replace('!WINRATEBYLANE!', replacement_str)

    # Winrate by player synergy
    replacement_str = '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth}}\n'
    replacement_str += 'Player & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for player, data in statistics_dict['player_synergy'].items():
        replacement_str += str(player) + '&' + str(round(data['ratio'] * 100, 2)) + '&' + str(
            data['Fail'] + data['Win']) + '&'
        for sig, color in significance_color:
            if data['significance'] < sig:
                replacement_str += '\\cellcolor{' + color + '}'
                break
        replacement_str += str(data['significance']) + '\\\\\n'

    replacement_str += '\\end{longtable}'
    file_str = file_str.replace('!PLAYERSYNERGY!', replacement_str)

    ######################################################
    # Write template file to disk
    file_str = file_str.replace('_', ' ')  # Fix latex error
    player_report_filename = player_name + '_stats'
    player_report = open(player_report_filename + '.tex', 'w')
    player_report.write(file_str)
    player_report.close()

    filename = player_name + '_stats'
    build_latex_file(filename)
