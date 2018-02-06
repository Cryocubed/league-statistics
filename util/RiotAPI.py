from config import *
from util import data_io
import requests
import time


class RiotAPI:

    # Initialize variables
    key_list = []
    persistent_data = {}
    api_requests_made = 0
    api_key_index = 0  # Start by using first API key
    keys_working = len(key_list)

    def __init__(self):
        # Import API Keys
        api_key_file = open('api_key.txt', 'r')
        for line in api_key_file:
            self.key_list.append(str(line).rstrip('\n'))

        # Establish connection to saved data
        self.persistent_data = data_io.import_persistent_data(DATA_FILE)

    ##############################
    # Main API functions
    ##############################
    def make_request(self, api_link, region='na1', filters=str()):

        # Create API uri
        uri = region + '.' + API_BASE_SITE + api_link + '?' + filters
        uri = uri.replace(' ', '')

        # Lookup uri in persistent data first if not blocked in config
        if not any(x in uri for x in ALWAYS_UPDATE):
            dict_entry = data_io.read_persistent_data(self.persistent_data, uri)
        else:
            dict_entry = {}
            if DEBUG_MODE:
                print('INTERNAL DATA SEARCH FOR ' + uri + ' WAS OVERRIDED')

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
            attempt_counter = 0 # Count web API access attempts

            response = None
            while True:
                try:
                    if attempt_counter >= 5:
                        print('API HAS BEEN UNAVAILABLE FOR 10 MINUTES, SHUTDOWN.')
                    r = requests.get(final_url + self.key_list[self.api_key_index % len(self.key_list)])  # Use new API key
                    response = r.json()
                    if int(response['status']['status_code']) == 429:
                        print("Rate limit reached, switching API key")
                        attempt_counter += 1
                        self.api_key_index += 1
                        self.keys_working -= 1
                        if self.keys_working == 0:
                            data_io.save_persistent_data(self.persistent_data, DATA_FILE)
                            print("All API keys used, sleeping 2 minutes.")
                            self.keys_working = len(self.key_list)
                            time.sleep(120)
                except KeyError:
                    break
                except TypeError:
                    break

            self.keys_working = len(self.key_list)
            # Save API request to persistent data
            if response:
                data_io.write_persistent_data(self.persistent_data, uri, response)
                self.api_requests_made += 1

                # Write to disk every 100 requests
                if self.api_requests_made % 100 == 0:
                    data_io.save_persistent_data(self.persistent_data, DATA_FILE)
                return response
            return None # if no data (should never occur due to previous while loop)

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
        Looks up a champion name from stored static-data. There is a way to do this through the API, but this uses internal
        data instead.
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

        if mode in retrieval_types:
            return self.make_request('/lol/summoner/v3/summoners' + retrieval_types[mode] + data)
        print('Invalid summoner retrieval type')
        return None

    ##############################
    # Match info requests
    ##############################
    def get_match_by_id(self, id):
        """
        Returns match data given a match id
        :param id: Match id
        :return: Match data
        """
        return self.make_request('/lol/match/v3/matches/' + str(id))

    def get_current_match_info(self, name):
        """
        Returns match data of game a player is currently in
        :param name: Summoner name of player
        :return: Match data
        """
        return self.make_request('/lol/spectator/v3/active-games/by-summoner/' + str(self.get_summoner(name)['id']))

    def get_match_champion_list(self, match_id, own_name):
        """
        Returns a dictionary containing data about the champions in a match of form:

        same_team: list of champion ids on the team of the given player
        enemy_team: list of champion ids not on the team of the given player
        self: list containing only the champion the given player used
        win_status: 'win' or 'fail'

        :param match_id: Match id
        :param own_name: Summoner name
        :return: Dictionary as detailed above
        """
        # Gather data on the match and the player's team id
        own_team_id, self_id = self.get_team_id(match_id, own_name)
        match_data = self.get_match_by_id(match_id)

        # Initialize the return dictionary
        match_champion_list = {'team': [], 'enemy': [], 'self': []}

        # Determine if the player's team won
        for team in match_data['teams']:
            if team['teamId'] == own_team_id:
                match_champion_list['win_status'] = team['win']

        # Add champion ids to the dictionary one participant at a time
        for participant in match_data['participants']:
            if participant['teamId'] == own_team_id:
                match_champion_list['team'].append(participant['championId'])

                # Additionally add the champion id to self key if needed
                if participant['participantId'] == self_id:
                    match_champion_list['self'].append(participant['championId'])
            else:
                match_champion_list['enemy'].append(participant['championId'])

        return match_champion_list

    def get_team_id(self, match_id, own_name):
        account_id = self.get_summoner(own_name)['accountId']
        match_data = self.get_match_by_id(match_id)

        participant_id = -1
        for participant in match_data['participantIdentities']:
            if account_id == participant['player']['accountId']:
                participant_id = participant['participantId']
                break

        if participant_id != -1:
            for participant in match_data['participants']:
                if participant_id == participant['participantId']:
                    return participant['teamId'], participant_id

        return None

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

    # Class helper functions
    def shutdown(self):
        data_io.save_persistent_data(self.persistent_data, DATA_FILE)
        print('Made ' + str(self.api_requests_made) + ' API requests')