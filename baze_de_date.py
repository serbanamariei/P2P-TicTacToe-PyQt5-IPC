import os
import sqlite3


class DatabaseManager:
    def __init__(self):
        cale_curenta = os.path.dirname(os.path.abspath(__file__))
        self.cale_db = os.path.join(cale_curenta, 'scoruri_joc.db')

        comanda_creare = '''CREATE TABLE IF NOT EXISTS Scores \
        ( \
            id \
            INTEGER \
            PRIMARY \
            KEY \
            AUTOINCREMENT, \
            player1 \
            VARCHAR \
                            ( \
            100 \
                            ),
            player2 VARCHAR \
                            ( \
                                100 \
                            ),
            score_p1 INTEGER,
            score_p2 INTEGER)'''

        with sqlite3.connect(self.cale_db) as db:
            cursor = db.cursor()
            cursor.execute(comanda_creare)

    def preia_scor(self, p1, p2):
        comanda_select = '''SELECT score_p1, score_p2 \
                            FROM Scores
                            WHERE (player1 = ? AND player2 = ?)'''

        with sqlite3.connect(self.cale_db) as db:
            cursor = db.cursor()
            cursor.execute(comanda_select, (p1, p2))
            rand = cursor.fetchone()

            if rand:
                return rand[0], rand[1]

            comanda_select_invers = '''SELECT score_p1, score_p2 \
                                       FROM Scores
                                       WHERE (player1 = ? AND player2 = ?)'''
            cursor.execute(comanda_select_invers, (p2, p1))
            rand_invers = cursor.fetchone()

            if rand_invers:
                return rand_invers[1], rand_invers[0]

            return 0, 0

    def salveaza_scor(self, p1, p2, scor_p1, scor_p2):
        with sqlite3.connect(self.cale_db) as db:
            cursor = db.cursor()

            cursor.execute('SELECT id FROM Scores WHERE player1=? AND player2=?', (p1, p2))
            rezultat = cursor.fetchone()

            if rezultat:
                comanda_update = '''UPDATE Scores \
                                    SET score_p1=?, \
                                        score_p2=? \
                                    WHERE id = ?'''
                id_rand = rezultat[0]
                cursor.execute(comanda_update, (scor_p1, scor_p2, id_rand))
            else:
                cursor.execute('SELECT id FROM Scores WHERE player1=? AND player2=?', (p2, p1))
                rez_invers = cursor.fetchone()

                if rez_invers:
                    comanda_update = '''UPDATE Scores \
                                        SET score_p1=?, \
                                            score_p2=? \
                                        WHERE id = ?'''
                    id_rand = rez_invers[0]
                    cursor.execute(comanda_update, (scor_p2, scor_p1, id_rand))
                else:
                    comanda_insert = '''INSERT INTO Scores (player1, player2, score_p1, score_p2)
                                        VALUES (?, ?, ?, ?)'''
                    cursor.execute(comanda_insert, (p1, p2, scor_p1, scor_p2))


if __name__ == '__main__':
    db = DatabaseManager()

    print("Scor initial intre Alex si Mihai:", db.preia_scor("Alex", "Mihai"))
    db.salveaza_scor("Alex", "Mihai", 2, 1)
    print("Noul scor luat din baza de date:", db.preia_scor("Alex", "Mihai"))
    print("Ce se intampla daca intrebam de Mihai si Alex?", db.preia_scor("Mihai", "Alex"))