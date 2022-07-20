import sys

from test import *
from ui_common import *
from log_reader import *

# https://github.com/jakkn/nwn-logparser


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.getLevelName(LOG_LEVEL))

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    ui = UserInterface(win.central_widget)
    printer = Printer(ui)
    test(printer)

    parser = Parser()
    reader = LogReader(LOG_DIR)
    back = Backend(win, reader, parser, printer)

    sys.exit(app.exec_())


