# database.py
import sqlite3
from datetime import datetime

DB_NAME = "resources.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, category_type TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations (id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id INTEGER, rank_fin INTEGER, rank_oper INTEGER, rank_jur INTEGER, rank_rep INTEGER, rank_strat INTEGER, norm_score REAL, final_rank INTEGER, event_trigger TEXT, evaluation_date TEXT, FOREIGN KEY (resource_id) REFERENCES resources (id))''')
    conn.commit()
    conn.close()

def add_resource(name, description, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO resources (name, description, category_type, created_at) VALUES (?, ?, ?, ?)", (name, description, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    res_id = c.lastrowid
    conn.close()
    return res_id

def save_evaluation(resource_id, ranks, norm_score, final_rank, trigger="Initial"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO evaluations (resource_id, rank_fin, rank_oper, rank_jur, rank_rep, rank_strat, norm_score, final_rank, event_trigger, evaluation_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (resource_id, ranks['fin'], ranks['oper'], ranks['jur'], ranks['rep'], ranks['strat'], norm_score, final_rank, trigger, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_resources_full():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, category_type, description, created_at FROM resources")
    data = c.fetchall()
    conn.close()
    return data

def get_resource_by_id(res_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, description, category_type FROM resources WHERE id = ?", (res_id,))
    data = c.fetchone()
    conn.close()
    return data

def get_evaluation_history(res_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT evaluation_date, event_trigger, final_rank, rank_fin, rank_oper, rank_jur, rank_rep, rank_strat, norm_score FROM evaluations WHERE resource_id = ? ORDER BY evaluation_date ASC""", (res_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_recent_evaluations_for_learning(limit=5):
    """Функция 'памяти' для обучения ИИ в контексте"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT r.name, e.rank_fin, e.rank_oper, e.rank_jur, e.rank_rep, e.rank_strat, e.event_trigger, e.final_rank FROM evaluations e JOIN resources r ON e.resource_id = r.id ORDER BY e.id DESC LIMIT ?""", (limit,))
    data = c.fetchall()
    conn.close()
    return data

init_db()