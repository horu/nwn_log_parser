import sys

from test import *
from qt import *

# https://github.com/jakkn/nwn-logparser

DIR = '/home/an.slyshik/.local/share/Neverwinter Nights/logs/'

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.DEBUG)

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    #test(win)

    back = Backend(win, DIR)

    sys.exit(app.exec_())


