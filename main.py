from util import *


def main():

    # Your code here
    player_name = 'player'
    pstats = player_stats.compute_all_stats(api, player_name, season_list=[9, 10, 11])
    latex.build_champion_report(pstats, player_name)


#########
# Initialization
api = RiotAPI.RiotAPI()

main()

# Closing code
api.shutdown()
