import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Таблиця для голосувань
    cursor.execute('''CREATE TABLE IF NOT EXISTS votes (
                        event_id TEXT, user_id INTEGER, full_name TEXT, choice TEXT, PRIMARY KEY (event_id, user_id))''')
    # Таблиця для статистики (ігри, голи, асисти)
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats (
                        user_id INTEGER PRIMARY KEY, games INTEGER DEFAULT 0, goals INTEGER DEFAULT 0, assists INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def update_vote(event_id, user_id, full_name, choice):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO votes VALUES (?, ?, ?, ?)', (event_id, user_id, full_name, choice))
    conn.commit()
    conn.close()

def get_votes(event_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, user_id, choice FROM votes WHERE event_id = ?', (event_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_player_stat(user_id, goals, assists):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO stats (user_id, games, goals, assists) VALUES (?, 1, ?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET 
                      games = games + 1, goals = goals + ?, assists = assists + ?''', 
                   (user_id, goals, assists, goals, assists))
    conn.commit()
    conn.close()

def get_all_stats():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, games, goals, assists FROM stats')
    rows = cursor.fetchall()
    conn.close()
    return rows
  
