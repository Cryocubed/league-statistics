import cProfile

from config import *
from util import *


def main():
    # Initialization
    api = RiotAPI.RiotAPI()

    # Your code here
    player_name = 'player'
    pstats = player_stats.compute_all_stats(api, player_name, season_list=[9, 10, 11])
    latex.build_champion_report(pstats, player_name)

    # Closing code
    api.shutdown()

#########
# Debugging


if DEBUG_MODE:
    cProfile.run('main()', sort=1)
else:
    main()
