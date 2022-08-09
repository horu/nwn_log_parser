import pathlib
import time
import os
import typing

ROUND_DURATION = 6000
TURN_DURATION = ROUND_DURATION * 10
HOUR_DURATION = TURN_DURATION * 2

KNOCKDOWN_PVE_CD = 6000
KNOCKDOWN_PVP_CD = 12000
CALLED_SHOT_DURATION = ROUND_DURATION * 4
STUNNING_FIST_DURATION = 12000
STEALTH_MODE_CD = 10000
CAST_TIME = 1250

KNOCKDOWN_AB_PENALTY = 4

SUCCESS = 'success'
FAILURE = 'failure'

MISS = 'miss'
HIT = 'hit'
FAILED = 'failed'
CRITICAL_HIT = 'critical hit'
RESISTED = 'resisted'
TARGET_CONCEALED = 'target concealed'

SNEAK_ATTACK = 'Sneak Attack'
DEATH_ATTACK = 'Death Attack'

FORTITUDE = 'Fortitude'
WILL = 'Will'
REFLEX = 'Reflex'

KNOCKDOWN = 'Knockdown'
SHORT_KNOCKDOWN = 'KD'
STUNNING_FIST = 'Stunning Fist'
SHORT_STUNNING_FIST = 'SF'
CALLED_SHOT = 'Called Shot'
ARM = 'Arm'
SHORT_ARM = 'A'
LEG = 'Leg'
SHORT_LEG = 'L'
SHORT_CALLED_SHOT = 'CS'

ITEM_POTION_OF_HEAL = 'Potion of Heal'
ROD_OF_FAST_CAST = 'Rod Of Fast Cast'

LOG_LEVEL = os.environ.get('LOG_LEVEL', default='DEBUG')
LOG_DIR = os.environ.get('LOG_DIR', default='{}/.local/share/Neverwinter Nights/logs/'.format(os.getenv('HOME')))
HIPS = bool(os.environ.get('HIPS', default=False))
DATA_FILE_PATH = pathlib.Path(os.environ.get('DATA_FILE_PATH', default='./data.yaml'))

Time = int  # ms
SpellName = str

SPELL_ENDURANCE = 'Endurance'


def get_ts() -> Time:
    return Time(time.time_ns() / 1000000)


def append_fix_size(list_to_append, el, size):
    list_to_append.append(el)
    while len(list_to_append) > size:
        list_to_append.pop(0)