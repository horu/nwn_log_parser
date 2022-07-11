import sys

from test import *
from qt import *

# https://github.com/jakkn/nwn-logparser

FILE = '/home/an.slyshik/.local/share/Neverwinter Nights/logs/nwclientLog1.txt'

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.DEBUG)

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    test(win)

    #back = Backend(win, FILE)

    sys.exit(app.exec_())


