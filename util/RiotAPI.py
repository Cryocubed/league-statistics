from config import *
from util import data_io
import requests
import time


class RiotAPI:

    # Initialize variables
    key_list = []
    persistent_data = {}
    api_requests_made = 0

    def __init__(self):
        # Import API Keys
        api_key_file = open('api_key.txt', 'r')
        for line in api_key_file:
            self.key_list.append(str(line).rstrip('\n'))

        # Establish connection to saved data
        self.persistent_data = data_io.import_persistent_data(DATA_FILE)

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
            api_key_index = 0 # Start by using first API key
            response = None
            while True:
                try:
                    if attempt_counter >= 5:
                        print('API HAS BEEN UNAVAILABLE FOR 10 MINUTES, SHUTDOWN.')
                    r = requests.get(final_url + self.key_list[api_key_index % len(self.key_list)])  # Use new API key
                    response = r.json()
                    if int(response['status']['status_code']) == 429:
                        print("Rate limit reached, switching API key")
                        attempt_counter += 1
                        api_key_index += 1
                        if api_key_index % len(self.key_list) == 0:
                            data_io.save_persistent_data(self.persistent_data, DATA_FILE)
                            print("All API keys used, sleeping 2 minutes.")
                            time.sleep(120)
                except KeyError:
                    break
                except TypeError:
                    break

            # Save API request to persistent data
            if response:
                data_io.write_persistent_data(self.persistent_data, uri, response)
                self.api_requests_made += 1

                # Write to disk every 100 requests
                if self.api_requests_made % 100 == 0:
                    data_io.save_persistent_data(self.persistent_data, DATA_FILE)
                return response
            return None # if no data (should never occur due to previous while loop)

    def shutdown(self):
        data_io.save_persistent_data(self.persistent_data, DATA_FILE)
        print('Made ' + str(self.api_requests_made) + ' API requests')