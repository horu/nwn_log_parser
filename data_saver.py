import json
import pathlib

from parser import *


class DataSaver:
    def __init__(self, data_file: pathlib.Path):
        self.data_file = data_file

    def save(self, parser: Parser):
        data = {
            'parser': {
                'player': {
                    'name': ''
                },
                'characters': [

                ]
            }
        }
        parser_data = data['parser']

        player = parser.player
        parser_data = {
            'plyaer': {
                'name': player.name
            },
            'characters': [

            ]
        }
