# database.py (ПОЛНАЯ ВЕРСИЯ с новыми параметрами)
import sqlite3
import json
from datetime import datetime

DB_NAME = "resources.db"


def init_db():
    """Инициализация базы данных с проверкой структуры и добавлением новых полей"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем, существует ли таблица resources
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resources'")
    table_exists = c.fetchone()

    if not table_exists:
        # Создаем новую таблицу со всеми полями (ВКЛЮЧАЯ НОВЫЕ)
        c.execute('''CREATE TABLE resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            description TEXT, 
            category_type TEXT, 
            resource_type TEXT,
            lifecycle TEXT,
            data_format TEXT,
            usage_scale TEXT,
            confidentiality TEXT DEFAULT 'unknown',
            users_count TEXT DEFAULT 'unknown',
            business_criticality TEXT DEFAULT 'unknown',
            backup TEXT DEFAULT 'unknown',
            created_at TEXT
        )''')
        print("✅ Таблица resources создана с новыми полями")
    else:
        # Проверяем наличие всех необходимых колонок в resources
        c.execute("PRAGMA table_info(resources)")
        columns = [column[1] for column in c.fetchall()]

        # Список всех нужных колонок (включая новые)
        required_columns = [
            'resource_type', 'lifecycle', 'data_format', 'usage_scale',
            'confidentiality', 'users_count', 'business_criticality', 'backup'
        ]

        for col in required_columns:
            if col not in columns:
                try:
                    c.execute(f"ALTER TABLE resources ADD COLUMN {col} TEXT DEFAULT 'unknown'")
                    print(f"✅ Добавлена колонка {col} в таблицу resources")
                except Exception as e:
                    print(f"❌ Ошибка при добавлении колонки {col}: {e}")

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
        calculation_details TEXT,
        FOREIGN KEY (resource_id) REFERENCES resources (id)
    )''')

    # Проверяем и добавляем колонку calculation_details в evaluations
    c.execute("PRAGMA table_info(evaluations)")
    eval_columns = [column[1] for column in c.fetchall()]

    if 'calculation_details' not in eval_columns:
        try:
            c.execute("ALTER TABLE evaluations ADD COLUMN calculation_details TEXT")
            print("✅ Добавлена колонка calculation_details в таблицу evaluations")
        except Exception as e:
            print(f"❌ Ошибка при добавлении колонки calculation_details: {e}")
    else:
        print("✅ Колонка calculation_details уже существует")

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


def add_resource(
        name,
        description,
        category,
        res_type,
        lifecycle,
        data_format,
        scale,
        confidentiality="unknown",
        users_count="unknown",
        business_criticality="unknown",
        backup="unknown"
):
    """
    Добавляет ресурс со всеми параметрами классификации (включая новые)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем, есть ли новые колонки
    c.execute("PRAGMA table_info(resources)")
    columns = [col[1] for col in c.fetchall()]

    has_new_fields = all([
        'confidentiality' in columns,
        'users_count' in columns,
        'business_criticality' in columns,
        'backup' in columns
    ])

    if has_new_fields:
        # Полный INSERT с новыми полями
        c.execute("""
            INSERT INTO resources (
                name, description, category_type, resource_type, lifecycle, 
                data_format, usage_scale, confidentiality, users_count, 
                business_criticality, backup, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, description, category,
            res_type, lifecycle, data_format, scale,
            confidentiality, users_count, business_criticality, backup,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        print(f"✅ Ресурс '{name}' добавлен с новыми параметрами")
    else:
        # Старый INSERT (без новых полей)
        c.execute("""
            INSERT INTO resources (
                name, description, category_type, resource_type, lifecycle, 
                data_format, usage_scale, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, description, category,
            res_type, lifecycle, data_format, scale,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        print(f"✅ Ресурс '{name}' добавлен (старый формат)")

    conn.commit()
    res_id = c.lastrowid
    conn.close()
    return res_id


def get_all_resources_full():
    """Получает все ресурсы с полной информацией"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем структуру
    c.execute("PRAGMA table_info(resources)")
    columns = [col[1] for col in c.fetchall()]

    if all(col in columns for col in ['confidentiality', 'users_count', 'business_criticality', 'backup']):
        # Если есть новые поля, получаем их
        c.execute("""
            SELECT id, name, category_type, description, created_at,
                   confidentiality, users_count, business_criticality, backup
            FROM resources 
            ORDER BY id DESC
        """)
    else:
        # Старый формат
        c.execute("SELECT id, name, category_type, description, created_at FROM resources ORDER BY id DESC")

    data = c.fetchall()
    conn.close()
    return data


def get_resource_by_id(res_id):
    """Получает ресурс по ID со всеми параметрами"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем структуру
    c.execute("PRAGMA table_info(resources)")
    columns = [col[1] for col in c.fetchall()]

    if all(col in columns for col in ['confidentiality', 'users_count', 'business_criticality', 'backup']):
        # С новыми полями
        c.execute("""
            SELECT name, description, category_type, resource_type, lifecycle, 
                   data_format, usage_scale, confidentiality, users_count, 
                   business_criticality, backup, created_at 
            FROM resources WHERE id = ?
        """, (res_id,))
    else:
        # Без новых полей
        c.execute("""
            SELECT name, description, category_type, resource_type, lifecycle, 
                   data_format, usage_scale, created_at,
                   'unknown', 'unknown', 'unknown', 'unknown'
            FROM resources WHERE id = ?
        """, (res_id,))

    data = c.fetchone()
    conn.close()
    return data


def get_resource_full_by_id(res_id):
    """Получает полную информацию о ресурсе по ID (включая ID в результате)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем структуру
    c.execute("PRAGMA table_info(resources)")
    columns = [col[1] for col in c.fetchall()]

    if all(col in columns for col in ['confidentiality', 'users_count', 'business_criticality', 'backup']):
        # С новыми полями
        c.execute("""
            SELECT id, name, description, category_type, resource_type, lifecycle, 
                   data_format, usage_scale, confidentiality, users_count, 
                   business_criticality, backup, created_at 
            FROM resources WHERE id = ?
        """, (res_id,))
    else:
        # Без новых полей
        c.execute("""
            SELECT id, name, description, category_type, resource_type, lifecycle, 
                   data_format, usage_scale, 'unknown', 'unknown', 'unknown', 'unknown', created_at 
            FROM resources WHERE id = ?
        """, (res_id,))

    data = c.fetchone()
    conn.close()
    return data


def save_evaluation(resource_id, ranks, norm_score, final_rank, trigger="Initial", details=None):
    """
    Сохраняет оценку ресурса
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Проверяем, есть ли колонка calculation_details
    c.execute("PRAGMA table_info(evaluations)")
    columns = [col[1] for col in c.fetchall()]
    has_details_col = 'calculation_details' in columns

    # Преобразуем детали в JSON, если они есть
    details_json = None
    if details and has_details_col:
        try:
            details_json = json.dumps(details, ensure_ascii=False, indent=None)
        except Exception as e:
            print(f"❌ Ошибка при сериализации details: {e}")

    if has_details_col:
        c.execute('''
            INSERT INTO evaluations (
                resource_id, rank_fin, rank_oper, rank_jur, rank_rep, rank_strat, 
                norm_score, final_rank, event_trigger, evaluation_date, calculation_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            resource_id,
            ranks['fin'], ranks['oper'], ranks['jur'], ranks['rep'], ranks['strat'],
            norm_score, final_rank, trigger,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            details_json
        ))
    else:
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
    eval_id = c.lastrowid
    conn.close()
    return eval_id


def get_evaluation_history(res_id):
    """Получает историю оценок ресурса"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("PRAGMA table_info(evaluations)")
    columns = [col[1] for col in c.fetchall()]

    if 'calculation_details' in columns:
        c.execute("""
            SELECT 
                evaluation_date, 
                event_trigger, 
                final_rank, 
                rank_fin, 
                rank_oper, 
                rank_jur, 
                rank_rep, 
                rank_strat, 
                norm_score,
                calculation_details
            FROM evaluations 
            WHERE resource_id = ? 
            ORDER BY evaluation_date ASC
        """, (res_id,))
    else:
        c.execute("""
            SELECT 
                evaluation_date, 
                event_trigger, 
                final_rank, 
                rank_fin, 
                rank_oper, 
                rank_jur, 
                rank_rep, 
                rank_strat, 
                norm_score,
                NULL as calculation_details
            FROM evaluations 
            WHERE resource_id = ? 
            ORDER BY evaluation_date ASC
        """, (res_id,))

    data = c.fetchall()
    conn.close()
    return data


def get_evaluation_by_id(eval_id):
    """Получает конкретную оценку по ID"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM evaluations WHERE id = ?", (eval_id,))
    data = c.fetchone()
    conn.close()
    return data


def get_recent_evaluations(limit=10):
    """Получает последние оценки всех ресурсов"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT 
            e.id,
            r.name,
            e.final_rank,
            e.norm_score,
            e.event_trigger,
            e.evaluation_date
        FROM evaluations e
        JOIN resources r ON e.resource_id = r.id
        ORDER BY e.evaluation_date DESC
        LIMIT ?
    """, (limit,))
    data = c.fetchall()
    conn.close()
    return data


def get_resources_by_category():
    """Получает статистику распределения ресурсов по категориям"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT category_type, COUNT(*) as count
        FROM resources
        GROUP BY category_type
        ORDER BY count DESC
    """)
    data = c.fetchall()
    conn.close()
    return data


def delete_resource(res_id):
    """Удаляет ресурс и все его оценки"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM evaluations WHERE resource_id = ?", (res_id,))
    deleted_eval = c.rowcount

    c.execute("DELETE FROM resources WHERE id = ?", (res_id,))
    deleted_res = c.rowcount

    conn.commit()
    conn.close()

    return deleted_res > 0


def get_latest_evaluation(res_id):
    """Получает самую свежую оценку ресурса"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("PRAGMA table_info(evaluations)")
    columns = [col[1] for col in c.fetchall()]

    if 'calculation_details' in columns:
        c.execute("""
            SELECT 
                rank_fin, rank_oper, rank_jur, rank_rep, rank_strat,
                norm_score, final_rank, event_trigger, calculation_details
            FROM evaluations 
            WHERE resource_id = ? 
            ORDER BY evaluation_date DESC
            LIMIT 1
        """, (res_id,))
    else:
        c.execute("""
            SELECT 
                rank_fin, rank_oper, rank_jur, rank_rep, rank_strat,
                norm_score, final_rank, event_trigger, NULL as calculation_details
            FROM evaluations 
            WHERE resource_id = ? 
            ORDER BY evaluation_date DESC
            LIMIT 1
        """, (res_id,))

    data = c.fetchone()
    conn.close()
    return data


def get_stats():
    """Получает общую статистику по базе данных"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    stats = {}

    c.execute("SELECT COUNT(*) FROM resources")
    stats['total_resources'] = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM evaluations")
    stats['total_evaluations'] = c.fetchone()[0]

    c.execute("SELECT AVG(final_rank) FROM evaluations")
    avg = c.fetchone()[0]
    stats['avg_final_rank'] = round(avg, 2) if avg else 0

    c.execute("SELECT MIN(final_rank), MAX(final_rank) FROM evaluations")
    min_r, max_r = c.fetchone()
    stats['min_rank'] = min_r if min_r else 0
    stats['max_rank'] = max_r if max_r else 0

    conn.close()
    return stats


def vacuum_db():
    """Оптимизирует базу данных"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("VACUUM")
    conn.close()
    print("✅ База данных оптимизирована")


def migrate_db():
    """Принудительная миграция базы данных"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Добавляем новые колонки в resources
    c.execute("PRAGMA table_info(resources)")
    columns = [col[1] for col in c.fetchall()]

    new_columns = [
        ('confidentiality', 'TEXT DEFAULT "unknown"'),
        ('users_count', 'TEXT DEFAULT "unknown"'),
        ('business_criticality', 'TEXT DEFAULT "unknown"'),
        ('backup', 'TEXT DEFAULT "unknown"')
    ]

    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                c.execute(f"ALTER TABLE resources ADD COLUMN {col_name} {col_type}")
                print(f"✅ Миграция: добавлена колонка {col_name}")
            except Exception as e:
                print(f"❌ Ошибка миграции {col_name}: {e}")

    # Добавляем calculation_details в evaluations
    c.execute("PRAGMA table_info(evaluations)")
    eval_columns = [col[1] for col in c.fetchall()]

    if 'calculation_details' not in eval_columns:
        try:
            c.execute("ALTER TABLE evaluations ADD COLUMN calculation_details TEXT")
            print("✅ Миграция: добавлена колонка calculation_details")
        except Exception as e:
            print(f"❌ Ошибка миграции calculation_details: {e}")

    conn.commit()
    conn.close()


# Инициализация при импорте
if __name__ != "__main__":
    try:
        migrate_db()
        init_db()
    except Exception as e:
        print(f"⚠️ Ошибка инициализации: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Тестирование database.py")
    print("=" * 50)

    migrate_db()
    init_db()

    # Тестовое добавление с новыми параметрами
    test_id = add_resource(
        name="Тестовая медицинская система",
        description="Тестовая система с новыми параметрами",
        category="👤 Персональные данные (ПДн)",
        res_type="🗄️ База данных",
        lifecycle="📆 Долгосрочный (более 1 года)",
        data_format="🗂️ Структурированные (БД/JSON)",
        scale="🏭 Масштаб предприятия",
        confidentiality="confidential",
        users_count="10000+",
        business_criticality="critical",
        backup="daily"
    )

    print(f"\n✅ Создан тестовый ресурс с ID: {test_id}")

    # Проверка чтения
    resource = get_resource_full_by_id(test_id)
    if resource and len(resource) > 11:
        print(f"   Новые параметры: конфид={resource[8]}, пользователи={resource[9]}, "
              f"критичность={resource[10]}, бэкап={resource[11]}")

    print("\n✅ Тестирование завершено")