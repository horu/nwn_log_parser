import time
import os
import typing

ROUND_DURATION = 6000
KNOCKDOWN_PVE_CD = 6000
KNOCKDOWN_PVP_CD = 12000
STUNNING_FIST_DURATION = 12000
STEALTH_MODE_CD = 10000

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
STUNNING_FIST = 'Stunning Fist'

ITEM_POTION_OF_HEAL = 'Potion of Heal'

LOG_LEVEL = os.environ.get('LOG_LEVEL', default='DEBUG')
LOG_DIR = os.environ.get('LOG_DIR', default='{}/.local/share/Neverwinter Nights/logs/'.format(os.getenv('HOME')))
PLAYER_HP = int(os.environ.get('PLAYER_HP'))


def get_ts():
    return int(time.time_ns() / 1000000)


def append_fix_size(list_to_append, el, size):
    list_to_append.append(el)
    if len(list_to_append) > size:
        list_to_append.pop(0)