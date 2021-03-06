import server.init_test

import os
import json
import datetime
import unittest
from urllib.parse import unquote
from logging import getLogger

logger = getLogger(__name__)

from lib.settings import TWEET_DELIMITER
from common import configs
from common.lib import db
test_db_path = 'data/db.sqlite3'
configs.db_path = test_db_path
DATETIME_FORMAT = configs.datetime_format

import app
from test_utils import fixture, db as test_db


TIMEZONE_JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
TIMEZONE_UTC = datetime.timezone(datetime.timedelta(hours=+0), 'UTC')


def _parse_response(response: str):
    data = response.split('|')
    message_list = data[2].split(TWEET_DELIMITER)
    messages = []
    parsed = {
        'datetime': datetime.datetime.strptime(data[0], DATETIME_FORMAT)
            .replace(tzinfo=TIMEZONE_JST).astimezone(TIMEZONE_UTC).strftime(DATETIME_FORMAT),
        'num_of_messages': int(data[1]),
        'messages': messages
    }
    for mes in message_list:
        message_data = mes.split(';')
        message = {
            'created_at': datetime.datetime.strptime(unquote(message_data[0]), DATETIME_FORMAT)
                .replace(tzinfo=TIMEZONE_JST).astimezone(TIMEZONE_UTC).strftime(DATETIME_FORMAT),
            'user.name': unquote(message_data[1]),
            'user.profile_image_url_https': unquote(message_data[2]),
            'media': list(map(unquote, message_data[3].split(','))),
            'text': unquote(message_data[4])
        }
        if message_data[3] == '':
            message['media'] = []
        parsed['messages'].append(message)
    return parsed


class TestServer(unittest.TestCase):
    def setUp(self):
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        db.migration()
        fixture.generate_normal_db('01')
        self.db_data = fixture.get_db_data(delete=False, dict_row=True)
        self.tweets = fixture.get_normal_tweets('01')

    def test_get_recent(self):
        count = 3
        offset = 1
        start_time = '2020-07-03 15:01:00'
        table_name = 'neotter_users'
        results = {}
        expected = {
            '01': {
                'num_of_messages': 2,
                'messages': [
                    fixture.response_from_fixture(self.tweets['01'][2]),
                    fixture.response_from_fixture(self.tweets['01'][3])
                ]
            },
            '02': {
                'num_of_messages': 1,
                'messages': [
                    fixture.response_from_fixture(self.tweets['02'][1])
                ]
            }
        }
        for user in self.db_data[table_name]:
            user_token = user['token']
            remote_addr = user['remote_addr']
            response = app._get_recent(count, offset, start_time, user_token, remote_addr)
            parsed = _parse_response(response)
            results[user['id']] = parsed
            expected_data = expected[user['id']]
            for key, value in expected_data.items():
                self.assertEqual(parsed[key], value)
        print(json.dumps(results, ensure_ascii=False, indent=4))
