###################
# CONFIG SETTINGS #
###################
USE_STORED_DATA = True
DEBUG_MODE = False
DATABASE_URL = 'sqlite:///league.db'
API_KEY_FILE = 'api_key.txt'
API_BASE_SITE = 'api.riotgames.com'
ALWAYS_UPDATE = {'/lol/spectator/v3/active-games/',
                 '/lol/match/v3/matchlists/by-account/'
                 }
