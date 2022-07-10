import time
import os

ROUND_DURATION = 6
KNOCKDOWN_PVE_CD = 6
KNOCKDOWN_PVP_CD = 12
STUNNING_FIST_DURATION = 12

FAILURE = 'failure'

MISS = 'miss'
HIT = 'hit'
FAILED = 'failed'
CRITICAL_HIT = 'critical hit'

SNEAK_ATTACK = 'Sneak Attack'
DEATH_ATTACK = 'Death Attack'

FORTITUDE = 'Fortitude'
WILL = 'Will'
REFLEX = 'Reflex'

KNOCKDOWN = 'Knockdown'
STUNNING_FIST = 'Stunning Fist'

PLAYER_NAME = os.environ.get('PLAYER_NAME', default='Dunya Kulakova')

DAMAGE_LIMIT = 10000

def get_ts():
    return int(time.time())


def append_fix_size(list_to_append, el, size):
    list_to_append.insert(0, el)
    if len(list_to_append) > size:
        list_to_append.pop()