from util import *

api = RiotAPI.RiotAPI()

print(api.make_request('/lol/summoner/v3/summoners/by-name/player'))
#api.rw_test()



api.shutdown()
