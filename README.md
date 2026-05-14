# ❌⭕ P2P Tic-Tac-Toe

A peer-to-peer Tic-Tac-Toe game for two players running on the same machine, built with PyQt5. Player actions are communicated between the two game instances via a System V message queue, and scores are persisted across sessions using a SQLite database.

---

## Project Structure

```
.
├── main.py            # Game GUI and P2P logic (PyQt5 + sysv_ipc)
├── baze_de_date.py    # SQLite database manager
└── scoruri_joc.db     # Auto-generated database file (created on first run)
```

---

## Requirements

- Python 3.x
- PyQt5
- sysv-ipc

Install dependencies:
```bash
pip install PyQt5 sysv-ipc
```

> **Note:** `sysv_ipc` is only available on **UNIX/Linux** systems. It does not work on Windows.

---

## How to Run

Open two separate terminals and run the game in each one:

```bash
# Terminal 1 (becomes the Host — plays as X)
python main.py

# Terminal 2 (becomes the Client — plays as O)
python main.py
```

The first instance to launch automatically becomes the **Host** and plays as `X`. The second instance connects to the existing message queue and plays as `O`. Each player is prompted to enter their name at startup.

---

## How It Works

### P2P Communication (System V Message Queue)

The two game instances communicate through a **System V message queue** with key `1236`.

When the first instance launches, it creates the queue using `IPC_CREX` (create exclusively — fails if it already exists). This is how the game determines who is the Host. The second instance detects that the queue already exists and connects to it as the Client.

Each player sends messages of a specific **type** to avoid reading their own messages:
- The Host sends messages of type `2` and reads type `1`
- The Client sends messages of type `1` and reads type `2`

Two kinds of messages are exchanged:
- `NUME:<name>` — sent at startup so each player learns the opponent's name
- `MOVE:<row>:<col>` — sent after each move to update the opponent's board

A `QTimer` polls the queue every 100ms in a non-blocking way (`block=False`), so the GUI stays responsive while waiting for the opponent's move.

When the Host closes the window, the message queue is destroyed (`queue.remove()`).

### Score Persistence (SQLite)

Scores are stored in `scoruri_joc.db` via the `DatabaseManager` class. The database has a single `Scores` table with columns: `player1`, `player2`, `score_p1`, `score_p2`.

When both player names are known, the previous score between those two players is loaded from the database and displayed. At the end of each round, the Host saves the updated score.

The database handles **symmetric lookups**: if a match between "Alice" and "Bob" was previously saved as `(Alice, Bob)`, querying `(Bob, Alice)` will still return the correct scores with the values swapped accordingly. This ensures scores are always retrieved correctly regardless of which player launched first.

---

## Gameplay

- The Host (`X`) always moves first
- Players take turns clicking cells on the board
- A round ends when one player completes a row, column, or diagonal, or when all cells are filled (draw)
- After each round, the result is shown in a popup and the board resets
- The score is updated live and saved to the database after every round

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS Scores (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    player1  VARCHAR(100),
    player2  VARCHAR(100),
    score_p1 INTEGER,
    score_p2 INTEGER
)
```
