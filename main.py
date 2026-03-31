import sys
import sysv_ipc
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QInputDialog, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
from baze_de_date import DatabaseManager

CHEIE_IPC = 1236

class TicTacToeGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.nume_jucator = ""
        self.nume_adversar = "Așteptare..."
        self.scor_meu = 0
        self.scor_adv = 0
        self.db = DatabaseManager()

        self.init_retea()
        self.init_ui()
        self.cere_nume_jucator()

        if not self.sunt_host:
            self.queue.send(f"NUME:{self.nume_jucator}".encode(), type=self.tip_trimitere)

        self.timer = QTimer()
        self.timer.timeout.connect(self.verifica_mesaje)
        self.timer.start(100)

    def init_retea(self):
        try:
            self.queue = sysv_ipc.MessageQueue(CHEIE_IPC, sysv_ipc.IPC_CREX)
            self.sunt_host = True
            self.simbol_meu = 'X'
            self.simbol_adversar = 'O'
            self.randul_meu = True
            self.tip_trimitere = 2
            self.tip_citire = 1
        except sysv_ipc.ExistentialError:
            self.queue = sysv_ipc.MessageQueue(CHEIE_IPC)
            self.sunt_host = False
            self.simbol_meu = 'O'
            self.simbol_adversar = 'X'
            self.randul_meu = False
            self.tip_trimitere = 1
            self.tip_citire = 2

    def init_ui(self):
        self.setWindowTitle('Joc P2P - X și 0')
        self.resize(350, 400)
        main_layout = QVBoxLayout()

        text_rol = "Tu ești X (Primul)" if self.sunt_host else "Tu ești 0 (Al doilea)"
        self.score_label = QLabel(f"Scor: 0 - 0\n{text_rol}")
        self.score_label.setFont(QFont('Arial', 12))
        main_layout.addWidget(self.score_label)

        grid_layout = QGridLayout()
        self.buttons = []
        for rand in range(3):
            rand_de_butoane = []
            for coloana in range(3):
                btn = QPushButton('')
                btn.setFixedSize(100, 100)
                btn.setFont(QFont('Arial', 24, QFont.Bold))
                btn.clicked.connect(lambda checked, r=rand, c=coloana: self.buton_apasat(r, c))
                grid_layout.addWidget(btn, rand, coloana)
                rand_de_butoane.append(btn)
            self.buttons.append(rand_de_butoane)

        main_layout.addLayout(grid_layout)
        self.setLayout(main_layout)

    def cere_nume_jucator(self):
        nume, ok = QInputDialog.getText(self, 'Identificare', 'Introdu numele tău:')
        if ok and nume.strip() != "":
            self.nume_jucator = nume
        else:
            self.nume_jucator = "Anonim"

    def buton_apasat(self, rand, coloana):
        if not self.randul_meu:
            return

        buton_curent = self.buttons[rand][coloana]
        if buton_curent.text() == '':
            buton_curent.setText(self.simbol_meu)
            buton_curent.setEnabled(False)
            self.randul_meu = False

            mesaj = f"MOVE:{rand}:{coloana}"
            self.queue.send(mesaj.encode(), type=self.tip_trimitere)

            self.verifica_victorie()

    def verifica_mesaje(self):
        try:
            mesaj_brut, tip_mesaj = self.queue.receive(block=False, type=self.tip_citire)
            mesaj = mesaj_brut.decode()

            if mesaj.startswith("NUME:"):
                self.nume_adversar = mesaj.split(":")[1]

                if self.sunt_host:
                    self.queue.send(f"NUME:{self.nume_jucator}".encode(), type=self.tip_trimitere)

                self.scor_meu, self.scor_adv = self.db.preia_scor(self.nume_jucator, self.nume_adversar)
                self.actualizeaza_scor_afisat()

            elif mesaj.startswith("MOVE:"):
                parti = mesaj.split(":")
                r = int(parti[1])
                c = int(parti[2])

                self.buttons[r][c].setText(self.simbol_adversar)
                self.buttons[r][c].setEnabled(False)
                self.randul_meu = True

                self.verifica_victorie()

        except sysv_ipc.BusyError:
            pass

    def verifica_victorie(self):
        linii_castigatoare = [
            [(0, 0), (0, 1), (0, 2)], [(1, 0), (1, 1), (1, 2)], [(2, 0), (2, 1), (2, 2)],
            [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 2), (2, 2)],
            [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]
        ]

        for linie in linii_castigatoare:
            valori = [self.buttons[r][c].text() for r, c in linie]
            if valori[0] != '' and valori[0] == valori[1] == valori[2]:
                self.finalizeaza_runda(valori[0])
                return

        toate_pline = True
        for r in range(3):
            for c in range(3):
                if self.buttons[r][c].text() == '':
                    toate_pline = False

        if toate_pline:
            self.finalizeaza_runda('REMIZA')

    def finalizeaza_runda(self, castigator):
        if castigator == self.simbol_meu:
            self.scor_meu += 1
            mesaj_box = "Ai câștigat runda!"
        elif castigator == self.simbol_adversar:
            self.scor_adv += 1
            mesaj_box = "Ai pierdut runda!"
        else:
            mesaj_box = "Egalitate!"

        if self.sunt_host:
            self.db.salveaza_scor(self.nume_jucator, self.nume_adversar, self.scor_meu, self.scor_adv)

        self.actualizeaza_scor_afisat()
        QMessageBox.information(self, "Sfârșit rundă", mesaj_box)
        self.reseteaza_tabla()

    def reseteaza_tabla(self):
        for r in range(3):
            for c in range(3):
                self.buttons[r][c].setText('')
                self.buttons[r][c].setEnabled(True)
        self.randul_meu = self.sunt_host

    def actualizeaza_scor_afisat(self):
        self.score_label.setText(
            f"Scor: {self.nume_jucator} ({self.scor_meu}) - {self.nume_adversar} ({self.scor_adv})\nJoacă {self.simbol_meu}")

    def closeEvent(self, event):
        if self.sunt_host:
            try:
                self.queue.remove()
            except sysv_ipc.ExistentialError:
                pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fereastra = TicTacToeGUI()
    fereastra.show()
    sys.exit(app.exec_())