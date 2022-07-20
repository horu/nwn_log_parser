from ui_bar import *
from ui_common import *
from ui_char import *

TRANSPARENCY = 0.5


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Nwn log parser")
        self.move(600, 0)
        self.setWindowOpacity(1)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet('background-color: rgba(0,0,0,{}%); color: white'.format(int(TRANSPARENCY * 100)))

        self.setCentralWidget(self.central_widget)

        # position for move window
        self.drag_position = QPoint()


class UserInterface:
    def __init__(self, widget: QWidget):
        self.main_form = create_form()
        widget.setLayout(self.main_form)

        self.player_hp_bar = PlayerHpBar()
        self.main_form.addRow(self.player_hp_bar.pb)
        self.player_stat = CharacterStat()
        self.main_form.addRow(self.player_stat.box)

        self.target_hp_bar = TargetHpBar()
        self.main_form.addRow(self.target_hp_bar.pb)
        self.target_stat = CharacterStat()
        self.main_form.addRow(self.target_stat.box)

        self.attack_damage_bar = AttackDpsBar()
        self.main_form.addRow(self.attack_damage_bar.box)

        self.knockdown_bar = KnockdownBar()
        self.main_form.addRow(self.knockdown_bar.pb)

        self.knockdown_miss_bar = KnockdownMissBar()
        self.main_form.addRow(self.knockdown_miss_bar.pb)

        self.stunning_fist_bar = StunningFistBar()
        self.main_form.addRow(self.stunning_fist_bar.pb)

        self.stealth_cooldown_bar = StealthCooldownBar()
        self.main_form.addRow(self.stealth_cooldown_bar.pb)

        self.casting_bar = CastingBar()
        self.main_form.addRow(self.casting_bar.pb)

        self.low_hp_label = QLabel("LOW HP")
        self.low_hp_label.setFont(QFont('Monospace', 32))
        self.low_hp_label.setAlignment(Qt.AlignCenter)
        self.low_hp_label.setStyleSheet('background-color: rgba(0,0,0,0%); color: red')
        self.low_hp_label.setVisible(False)
        self.main_form.addRow(self.low_hp_label)

        self.main_label = QLabel("")
        self.main_label.setFont(QFont('Monospace', 10))
        self.main_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.main_label.setStyleSheet('background-color: rgba(0,0,0,0%); color: white')
        self.main_label.setVisible(False)
        self.main_form.addRow(self.main_label)

    def set_main_label_text(self, text: str, visible: bool) -> None:
        self.main_label.setVisible(visible)
        self.main_label.setText(text)

    def notify_low_hp(self, visible: bool):
        self.low_hp_label.setVisible(visible)
