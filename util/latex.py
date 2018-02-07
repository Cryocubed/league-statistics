import os


def build_latex_file(filename):
    os.system("pdflatex " + filename + '.tex')
    os.remove(filename + '.aux')
    os.remove(filename + '.log')
    os.remove(filename + '.tex')
    os.rename(filename + '.pdf', 'exports/' + filename + '.pdf')


def build_champion_report(statistics_dict, player_name):

    # Config
    significance_color = [(0.01, 'electricblue'), (0.05, 'green'), (0.1, 'yellow'), (0.25, 'orange')]

    player_name = player_name.replace(' ', '')

    total_games = statistics_dict['total_wins'] + statistics_dict['total_losses']
    winrate = 100 * statistics_dict['total_wins'] / total_games
    total_days_in_game = statistics_dict['total_time'] / 60 / 60 / 24

    filter_str = ''
    for curr_filter, curr_data in statistics_dict['filters'].items():
        filter_str += str(curr_filter) + ': ' + str(curr_data) + '\n\n'

    file_str = '\\documentclass[paper = letter, oneside]{extarticle}\n' \
               '\\usepackage[]{geometry}\n' \
               '\\usepackage{longtable}\n' \
               '\\usepackage[dvipsnames,table]{xcolor}\n' \
               '\\definecolor{electricblue}{rgb}{0.49, 0.98, 1.0}\n' \
               '\\usepackage{array}\n' \
               '\\newcolumntype{C}[1]{>{\\centering\\arraybackslash}p{#1}}\n\n' \
               '\\begin{document}\n' \
               '\\begin{center}' \
               '\\LARGE\\textbf{Statistics for ' + player_name + '}\n\n' \
               '\\large{' + filter_str + '}\n\n' \
               '\\large{Overall winrate: ' + str(round(winrate, 2)) + '\%}\n\n' \
               '\\large{\# of games: ' + str(total_games) + '}\n\n' \
               '\\large{Total days spent: ' + str(round(total_days_in_game, 2)) + '}\n\n' \
               '\\Large{Champion winrates}\n' \
               '\\bigskip\n\n' \
               '\\normalsize\n' \
               '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth}}\n' \
               'Champion Name & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for item in statistics_dict['winrate_self']:
        file_str += str(item[0]) + '&' + str(item[1]) + '&' + str(item[2]) + '&'
        for sig, color in significance_color:
            if item[3] < sig:
                file_str += '\\cellcolor{' + color + '}'
                break
        file_str += str(item[3]) + '\\\\\n'

    file_str += '\\end{longtable}\n' \
                '\\Large{vs winrates}' \
                '\\bigskip\n\n' \
                '\\normalsize\n' \
                '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth}}\n' \
                'Champion Name & Winrate (\%)& Number of Games & Significance \\\\ \\hline\n'

    for item in statistics_dict['winrate_enemy']:
        file_str += str(item[0]) + '&' + str(item[1]) + '&' + str(item[2]) + '&'
        for sig, color in significance_color:
            if item[3] < sig:
                file_str += '\\cellcolor{' + color + '}'
                break
        file_str += str(item[3]) + '\\\\\n'

    file_str += '\\end{longtable}\n' \
                '\\Large{Synergy Winrates}' \
                '\\bigskip\n\n' \
                '\\normalsize\n' \
                '\\begin{longtable}{ C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth} | C{.2\\textwidth}}\n' \
                'Champion Name & Winrate (\%) & Number of Games & Significance \\\\ \\hline\n'

    for item in statistics_dict['winrate_team']:
        file_str += str(item[0]) + '&' + str(item[1]) + '&' + str(item[2]) + '&'
        for sig, color in significance_color:
            if item[3] < sig:
                file_str += '\\cellcolor{' + color + '}'
                break
        file_str += str(item[3]) + '\\\\\n'

    file_str += '\\end{longtable}\n' \
                '\\end{center}' \
                '\\end{document}'

    filename = player_name + '_stats'
    f = open(filename + '.tex', "w")
    f.write(file_str)
    f.close()

    build_latex_file(filename)
