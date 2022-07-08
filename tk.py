import sys
import time
import re
import logging
import json
import collections
from datetime import datetime
import time

import subprocess
import threading
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
import select


# https://github.com/jakkn/nwn-logparser

class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Python Menus & Toolbars")
        self.resize(400, 200)
        self.centralWidget = QLabel("")
        self.centralWidget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setCentralWidget(self.centralWidget)

    def setText(self, text):
        self.centralWidget.setText(text)


ROUND_DURATION = 6

MISS = 'miss'
HIT = 'hit'
FAILED = 'failed'
CRITICAL_HIT = 'critical hit'

SNEAK_ATTACK = 'Sneak Attack'
DEATH_ATTACK = 'Death Attack'

FORTITUDE = 'Fortitude'
WILL = 'Will'
REFLEX = 'Reflex'

class SpecailAttack:
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attempts ([^:]+) on ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return Attack(g)

        return None

    def __init__(self, g):
        s = g[0].split(' : ')
        self.attacker = s[-1]
        s.pop()
        self.specials = s
        self.type = g[1]
        self.target = g[2]
        self.result = g[3]
        self.roll = int(g[4])
        self.ab = int(g[5])
        self.value = int(g[6])
        assert self.roll + self.ab == self.value

    def __str__(self):
        return str(self.__dict__)


'[CHAT WINDOW TEXT] [Fri Jul  8 23:08:12] 10 AC - Undead - Chaotic Evil : Fortitude Save : *failure* : (9 + 1 = 10 vs. DC: 38)'


class SavingThrow:
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+) vs. DC: ([0-9]+)\)'
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return SavingThrow(g)

        return None

    def __init__(self, g):
        self.target = g[0]
        self.type = g[1]
        self.result = g[2]
        self.roll = int(g[3])
        self.base = int(g[4])
        self.value = int(g[5])
        self.dc = int(g[6])
        assert self.roll + self.base == self.value

    def __str__(self):
        return str(self.__dict__)


class Attack:
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attacks ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return Attack(g)

        return None

    def __init__(self, g):
        s = g[0].split(' : ')
        self.attacker = s[-1]
        s.pop()
        self.specials = s
        self.target = g[1]
        self.result = g[2]
        self.roll = int(g[3])
        self.ab = int(g[4])
        self.value = int(g[5])
        assert self.roll + self.ab == self.value

    def __str__(self):
        return str(self.__dict__)


class Character:
    def __init__(self):
        self.name = ''
        self.ac = [0, 256]
        self.ab = {} # 50/45/40/35
        self.last_ab = 0

        self.fortitude = 0
        self.will = 0

        self.timestamp = 0

    def update_ac(self, attack):
        if attack.result == MISS:
            self.ac[0] = max(self.ac[0], attack.value + 1)
        elif attack.result == HIT or attack.result == CRITICAL_HIT:
            self.ac[1] = min(self.ac[1], attack.value)

    def update_ab(self, attack):
        self.last_ab = attack.ab
        current_time = int(time.time())
        new_ab = { ab: timestamp for ab, timestamp in self.ab.items() if current_time - timestamp < ROUND_DURATION * 10 }
        new_ab.setdefault(attack.ab, current_time)
        self.ab = new_ab

        self.timestamp = current_time

    def __str__(self):
        return 'AC:\t{}/{}\tAB:\t{} {}({})\tFT:\t{}'.format(
            str(self.ac[0]),
            str(self.ac[1]),
            str(self.last_ab),
            '/'.join([str(ab) for ab in sorted(self.ab.keys(), reverse=True)][:3]),
            str(len(self.ab)),
            str(self.fortitude))


class Parser:
    def __init__(self):
        self.text = ''
        self.characters = collections.defaultdict(Character)

    def push_line(self, line):
        logging.debug(line)
        attack = Attack.create(line)
        if attack:
            logging.debug(str(attack))
            attacker = self.characters[attack.attacker]
            attacker.update_ab(attack)

            if attack.roll != 1 and attack.roll != 20:
                target = self.characters[attack.target]
                target.update_ac(attack)
            return

        throw = SavingThrow.create(line)
        if throw:
            logging.debug(str(throw))
            target = self.characters[throw.target]
            if FORTITUDE in throw.type:
                target.fortitude = throw.base
            elif WILL in throw.type:
                target.will = throw.base


    def get_stat(self):
        text = ''
        for name, char in sorted(self.characters.items()):
            text += '{}: {}\n'.format(name, char)
        return text


def test():
    lines = [
        '[CHAT WINDOW TEXT] [Fri Jul  8 23:08:12] 10 AC - Undead - Chaotic Evil : Fortitude Save : *failure* : (9 + 1 = 10 vs. DC: 38)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 23:16:38] TEST m r : Reflex Save vs. Electricity : *success* : (9 + 45 = 54 vs. DC: 24)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 23:16:27] TEST m r : Reflex Save vs. Electricity : *success* : (13 + 45 = 58 vs. DC: 28)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 19:15:23] 10 AC - Chaotic Evil : Will Save vs. Mind Spells : *failure* : (3 + 1 = 4 vs. DC: 20)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 23:20:05] TEST m r : Reflex Save vs. Spells : *success* : (12 + 45 = 57 vs. DC: 37)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 23:20:06] TEST m r : Fortitude Save vs. Spells : *success* : (19 + 29 = 48 vs. DC: 34)',


        '[CHAT WINDOW TEXT] [Fri Jul  8 20:22:23] Off Hand : Sneak Attack : TEST m r attacks 10 AC - Undead - Chaotic Evil : *hit* : (6 + 49 = 55)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 20:22:36] Off Hand : TEST m r attacks TRAINER : *hit* : (11 + 44 = 55)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 20:29:12] Off Hand : Flurry of Blows : Sneak Attack : TEST m r attacks 10 AC - Undead - Chaotic Evil : *hit* : (5 + 47 = 52)',

        '[CHAT WINDOW TEXT] [Fri Jul  8 20:16:56] Sneak Attack : TEST m r attacks 10 AC DUMMY - DPS TEST : *critical hit* : (19 + 49 = 68 : Threat Roll: 10 + 49 = 59)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 20:13:36] Sneak Attack : TEST m r attempts Improved Knockdown on 60 AC DUMMY : *miss* : (4 + 45 = 49)',

        '[CHAT WINDOW TEXT] [Fri Jul  8 19:23:22] TEST mr attacks TRAINER : *hit* : (2 + 52 = 54)',

        '[CHAT WINDOW TEXT] [Fri Jul  8 20:25:39] TEST m r attempts Stunning Fist on TRAINER : *failed* : (15 + 41 = 56)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 20:26:20] Sneak Attack : TEST m r attempts Stunning Fist on 10 AC - Undead - Chaotic Evil : *hit* : (6 + 41 = 47)',
        '[CHAT WINDOW TEXT] [Fri Jul  8 20:27:48] Flurry of Blows : Sneak Attack : TEST m r attempts Stunning Fist on 10 AC - Undead - Chaotic Evil : *hit* : (19 + 39 = 58)',

        '[CHAT WINDOW TEXT] [Fri Jul  8 20:24:45] Flurry of Blows : TEST m r attacks TRAINER : *hit* : (13 + 47 = 60)',

        '[CHAT WINDOW TEXT] [Fri Jul  8 22:14:55] Epic Black Dragon attacks TEST m r : *target concealed: 70%* : (9 + 47 = 56)',
    ]
    ####
    # line = '[CHAT WINDOW TEXT] [Fri Jul  8 20:24:45] Flurry of Blows : TEST m r attacks TRAINER : *hit* : (13 + 47 = 60)'

    parser = Parser()
    for line in lines:
        parser.push_line(line)
    text = parser.get_stat()
    logging.debug(text)


class Backend:
    def __init__(self, label, filename):
        self.label = label

        self.f = subprocess.Popen(['tail', '-f', filename], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.poll = select.poll()
        self.poll.register(self.f.stdout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.action)
        self.timer.start(100)

        self.parser = Parser()

    def action(self):
        while self.poll.poll(1):
            line = self.f.stdout.readline().decode()
            self.parser.push_line(line)

        text = self.parser.get_stat()
        self.label.setText(text)


FILE = '/home/an.slyshik/.local/share/Neverwinter Nights/logs/nwclientLog1.txt'

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.DEBUG)

    #test()
    #exit(0)

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    back = Backend(win, FILE)

    sys.exit(app.exec_())


