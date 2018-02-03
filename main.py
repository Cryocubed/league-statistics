from util import *
from config import *
import cProfile


def main():
    # Initialization
    api = RiotAPI.RiotAPI()

    # Your code here
    player_name = 'player'
    le_stats = player_stats.compute_champion_winrates(api, player_name)
    latex.build_champion_report(le_stats, player_name)

    # Closing code
    api.shutdown()

#########
# Debugging


if DEBUG_MODE:
    cProfile.run('main()', sort=1)
else:
    main()
