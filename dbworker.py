import sqlite3
import config



def init_db():
    with sqlite3.connect(config.db_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id TEXT PRIMARY KEY,
                state TEXT NOT NULL
            )
        ''')
        conn.commit()



def get_current_state(user_id):
    with sqlite3.connect(config.db_file) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT state FROM user_states WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row:
            return row[0]
        else:
            return config.States.S_START.value



def set_state(user_id, value):
    with sqlite3.connect(config.db_file) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR REPLACE INTO user_states (user_id, state) VALUES (?, ?)', (user_id, value))
            conn.commit()
            return True
        except Exception as e:

            print(f"Ошибка при сохранении состояния: {e}")
            return False



init_db()
