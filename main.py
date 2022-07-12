import sys

from test import *
from qt import *
from log_reader import *

# https://github.com/jakkn/nwn-logparser


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.getLevelName(LOG_LEVEL))

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    test(win)

    parser = Parser(PLAYER_NAME)
    reader = LogReader(LOG_DIR)
    back = Backend(win, reader, parser)

    sys.exit(app.exec_())


