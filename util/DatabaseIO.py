import json

import dataset

from config import *


class DatabaseIO:

    def __init__(self):
        self.db = dataset.connect(DATABASE_URL)
        self.api_table = self.db['riotapi']

    def read_api_data(self, riot_url):

        try:
            db_response = self.api_table.find_one(url=riot_url)['data']
        except TypeError:
            return None
        data = json.loads(db_response)
        return data

    def save_api_data(self, riot_url, riot_data):
        riot_data = json.dumps(riot_data)
        self.api_table.upsert(dict(url=riot_url, data=riot_data), ['url'])
