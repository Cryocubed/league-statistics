import time

import requests

from config import *
from util import DatabaseIO


class RiotAPI:

    # Initialize variables
    key_list = []
    api_requests_made = 0
    api_key_index = 0
    keys_working = len(key_list)

    # Rate limiting
    rate_usage = {}
    rate_max = {}
    limit_time = 0

    def __init__(self):
        # Import API key
        api_key_file = open(API_KEY_FILE, 'r')
        for line in api_key_file:
            self.key_list.append(str(line).rstrip('\n'))

        # Connect to database
        self.db = DatabaseIO.DatabaseIO()

    ##############################
    # Main API functions
    ##############################
    def set_rate_limit_delay(self, headers):

        if not self.rate_max:
            self.rate_max = self.process_limit_headers(headers['X-App-Rate-Limit'])

        self.rate_usage = self.process_limit_headers(headers['X-App-Rate-Limit-Count'])

        new_limit_time = 0
        for limit_key in self.rate_max.keys():
            if self.rate_usage[limit_key] > 0.9 * self.rate_max[limit_key]:
                new_limit_time = time.time() + self.rate_max[limit_key] + 1

        if new_limit_time > self.limit_time:
            self.limit_time = new_limit_time

    @staticmethod
    def process_limit_headers(datastr):
        return_dict = {}

        for rate_data in datastr.split(','):
            split_data = rate_data.split(':')
            return_dict[int(split_data[1])] = int(split_data[0])

        return return_dict

    def make_request(self, api_link, region='na1', filters=str()):

        # Create API uri
        uri = region + '.' + API_BASE_SITE + api_link + '?' + filters

        # Lookup uri in persistent data first if not blocked in config
        if not any(x in uri for x in ALWAYS_UPDATE):
            dict_entry = self.db.read_api_data(uri)
        else:
            dict_entry = {}
            if DEBUG_MODE:
                print('INTERNAL DATA SEARCH FOR ' + uri + ' WAS OVERRIDDEN')

        # Return stored data if available
        if USE_STORED_DATA and dict_entry:
            return dict_entry
        else:
            # Create web ready url
            final_url = 'https://' + uri + 'api_key='

            if DEBUG_MODE:
                # Print link that can be used on web
                print(final_url + self.key_list[0])

            # Contact API
            attempt_counter = 0  # Count web API access attempts

            # Delay if rate limited
            if time.time() < self.limit_time:
                sleep_time = self.limit_time - time.time() + 1
                print('Sleeping ' + str(sleep_time) + ' seconds due to rate limits')
                time.sleep(sleep_time)

            response = None
            while True:
                try:
                    if attempt_counter >= 5:
                        print('API HAS BEEN UNAVAILABLE FOR 10 MINUTES.')

                    # Make request to riot api
                    r = requests.get(final_url + self.key_list[self.api_key_index % len(self.key_list)])

                    # Update rate limiting
                    self.set_rate_limit_delay(r.headers)

                    # Read response
                    response = r.json()
                    if int(response['status']['status_code']) == 429:
                        self.api_key_index += 1
                        self.keys_working -= 1
                        if self.keys_working == 0:
                            print("Sleeping 2 minutes.")
                            attempt_counter += 1
                            self.keys_working = len(self.key_list)
                            time.sleep(120)
                except (KeyError, TypeError):
                    self.keys_working = len(self.key_list)
                    break

            # Save API request to database
            if response:
                self.db.save_api_data(uri, response)
                self.api_requests_made += 1

                return response
            return None  # if no data (should never occur due to previous while loop)

    ##############################
    # Static data requests
    ##############################
    def update_static_data(self):
        """
            Updates all of the data saved from riots static-data API
            :return: None
            """
        ALWAYS_UPDATE.add('/lol/static-data/v3/')
        self.make_request('/lol/static-data/v3/champions')
        self.make_request('/lol/static-data/v3/items')
        self.make_request('/lol/static-data/v3/language-strings')
        self.make_request('/lol/static-data/v3/languages')
        self.make_request('/lol/static-data/v3/maps')
        self.make_request('/lol/static-data/v3/masteries')
        self.make_request('/lol/static-data/v3/profile-icons')
        self.make_request('/lol/static-data/v3/realms')
        self.make_request('/lol/static-data/v3/runes')
        self.make_request('/lol/static-data/v3/summoner-spells')
        self.make_request('/lol/static-data/v3/versions')

    def get_id_from_champion(self, name):
        """
        Looks up a champion id from stored static-data given a name
        :param name: Champion name
        :return: Id of champion
        """
        return self.make_request('/lol/static-data/v3/champions')['data'][name]['id']

    def get_champion_from_id(self, c_id):
        """
        Looks up a champion name from stored static-data. There is a way to do this through the API, but this uses
        internal data instead.
        :param c_id: Champion id
        :return: String of champion name, or None if not found
        """
        data = self.make_request('/lol/static-data/v3/champions/')['data']
        for champion, c_data in data.items():
            if int(c_id) == int(c_data['id']):
                return champion
        return None

    ##############################
    # Summoner info requests
    ##############################
    def get_summoner(self, data, mode='summonerName'):
        """
        Returns a summoner DTO using Riot's API standards
        :param data: Summoner name, accountId, or summonerId
        :param mode: summonerName, accountId, or summonerId
        :return: summoner DTO
        """
        # Map lookup types to API URIs
        retrieval_types = {'accountId': '/by-account/', 'summonerName': '/by-name/', 'summonerId': '/'}

        data = data.replace(' ', '').lower()
        if mode in retrieval_types:
            return self.make_request('/lol/summoner/v3/summoners' + retrieval_types[mode] + data)
        print('Invalid summoner retrieval type')
        return None

    ##############################
    # Match info requests
    ##############################
    def get_match_by_id(self, match_id):
        """
        Returns match data given a match id
        :param match_id: Match id
        :return: Match data
        """
        return self.make_request('/lol/match/v3/matches/' + str(match_id))

    def get_current_match_info(self, name):
        """
        Returns match data of game a player is currently in
        :param name: Summoner name of player
        :return: Match data
        """
        return self.make_request('/lol/spectator/v3/active-games/by-summoner/' + str(self.get_summoner(name)['id']))

    def get_matches_by_filter(self, name, season=list(), begin_index=0, champion=list(), queue=list()):

        filter_str = 'beginIndex=' + str(begin_index)

        for item in season:
            filter_str += '&season=' + str(item)
        for item in champion:
            filter_str += '&champion=' + str(item)
        for item in queue:
            filter_str += '&queue=' + str(item)
        filter_str += '&'

        account_id = self.get_summoner(name)['accountId']

        match_list = []
        data = self.make_request('/lol/match/v3/matchlists/by-account/' + str(account_id), filters=filter_str)
        for match in data['matches']:
            match_list.append(match['gameId'])

        return match_list

    def get_recent_matches(self, name):
        return self.make_request('/lol/match/v3/matchlists/by-account/' + str(self.get_summoner(name)['accountId']) +
                                 '/recent')

    # Class helper functions
    def shutdown(self):
        print('Made ' + str(self.api_requests_made) + ' API requests')
