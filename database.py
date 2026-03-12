# database.py
import sqlite3
from datetime import datetime

DB_NAME = "resources.db"


def init_db():
    """Инициализация базы данных с проверкой структуры"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем, существует ли таблица resources
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resources'")
    table_exists = c.fetchone()

    if not table_exists:
        # Создаем новую таблицу со всеми полями
        c.execute('''CREATE TABLE resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            description TEXT, 
            category_type TEXT, 
            resource_type TEXT,
            lifecycle TEXT,
            data_format TEXT,
            usage_scale TEXT,
            created_at TEXT
        )''')
        print("Таблица resources создана")
    else:
        # Проверяем наличие всех необходимых колонок
        c.execute("PRAGMA table_info(resources)")
        columns = [column[1] for column in c.fetchall()]

        # Список нужных колонок
        required_columns = ['resource_type', 'lifecycle', 'data_format', 'usage_scale']

        for col in required_columns:
            if col not in columns:
                try:
                    c.execute(f"ALTER TABLE resources ADD COLUMN {col} TEXT")
                    print(f"Добавлена колонка {col}")
                except:
                    print(f"Ошибка при добавлении колонки {col}")

    # Создаем таблицу evaluations если её нет
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        resource_id INTEGER, 
        rank_fin INTEGER, 
        rank_oper INTEGER, 
        rank_jur INTEGER, 
        rank_rep INTEGER, 
        rank_strat INTEGER, 
        norm_score REAL, 
        final_rank INTEGER, 
        event_trigger TEXT, 
        evaluation_date TEXT,
        FOREIGN KEY (resource_id) REFERENCES resources (id)
    )''')

    conn.commit()
    conn.close()


def add_resource(name, description, category, res_type, lifecycle, data_format, scale):
    """Добавляет ресурс со всеми параметрами классификации"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO resources (
            name, description, category_type, resource_type, lifecycle, data_format, usage_scale, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, description, category,
        res_type, lifecycle, data_format, scale,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    res_id = c.lastrowid
    conn.close()
    return res_id


def get_all_resources_full():
    """Получает все ресурсы с полной информацией"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, category_type, description, created_at FROM resources")
    data = c.fetchall()
    conn.close()
    return data


def get_resource_by_id(res_id):
    """Получает ресурс по ID со всеми параметрами"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT name, description, category_type, resource_type, lifecycle, data_format, usage_scale, created_at 
        FROM resources WHERE id = ?
    """, (res_id,))
    data = c.fetchone()
    conn.close()
    return data


def save_evaluation(resource_id, ranks, norm_score, final_rank, trigger="Initial"):
    """Сохраняет оценку ресурса"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO evaluations (
            resource_id, rank_fin, rank_oper, rank_jur, rank_rep, rank_strat, 
            norm_score, final_rank, event_trigger, evaluation_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        resource_id,
        ranks['fin'], ranks['oper'], ranks['jur'], ranks['rep'], ranks['strat'],
        norm_score, final_rank, trigger,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def get_evaluation_history(res_id):
    """Получает историю оценок ресурса"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT evaluation_date, event_trigger, final_rank, rank_fin, rank_oper, rank_jur, rank_rep, rank_strat, norm_score 
        FROM evaluations 
        WHERE resource_id = ? 
        ORDER BY evaluation_date ASC
    """, (res_id,))
    data = c.fetchall()
    conn.close()
    return data


def get_recent_evaluations_for_learning(limit=5):
    """Функция 'памяти' для обучения ИИ в контексте"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT r.name, e.rank_fin, e.rank_oper, e.rank_jur, e.rank_rep, e.rank_strat, e.event_trigger, e.final_rank 
        FROM evaluations e 
        JOIN resources r ON e.resource_id = r.id 
        ORDER BY e.id DESC 
        LIMIT ?
    """, (limit,))
    data = c.fetchall()
    conn.close()
    return data
# database.py (добавьте эту функцию)
def get_resource_full_by_id(res_id):
    """Получает полную информацию о ресурсе по ID"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, description, category_type, resource_type, lifecycle, data_format, usage_scale, created_at 
        FROM resources WHERE id = ?
    """, (res_id,))
    data = c.fetchone()
    conn.close()
    return data

# Инициализация БД при импорте
init_db()