import yaml
import pathlib

from parser import *


class DataSaver:
    def __init__(self, data_file: pathlib.Path):
        self.data_file = data_file

    def save(self, parser: Parser) -> None:
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
        parser_data['player']['name'] = player.name

        characters_data = parser_data['characters']
        for char in parser.characters.values():
            char_data = {
                'name': char.name,
                'hp_list': char.hp_list,
                'classes': char.levels.classes,
            }
            if char.experience:
                char_data.update({'experience': char.experience.value})
            characters_data.append(char_data)

        yaml_data = yaml.dump(data)
        with self.data_file.open('w') as f:
            f.write(yaml_data)

    def load(self) -> Parser:
        parser = Parser()

        data = {}
        with self.data_file.open('r') as f:
            data = yaml.load(f)

        parser_data = data['parser']
        parser.set_player(parser_data['player']['name'])

        for char_data in parser_data['characters']:
            char = parser.get_char(char_data['name'])
            char.hp_list = char_data['hp_list']
            experience = char_data.get('experience', None)
            if experience:
                char.experience = Experience.explicit_create(value=int(experience))
            char.levels.classes = char_data['classes']

        return parser
