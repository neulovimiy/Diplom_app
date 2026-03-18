# logic.py (ОБНОВЛЕННАЯ ВЕРСИЯ с возвратом итоговых рангов)
# Максимальные значения шкал:
# Группа А (критические) - 10
# Группа Б (качественные) - 8
MAX_RANKS = {
    'fin': 10,  # Финансовый ущерб
    'oper': 10,  # Операционный сбой
    'jur': 8,  # Юридический риск
    'rep': 8,  # Репутационный ущерб
    'strat': 8  # Стратегический ущерб
}

# 1. Базовые ранги от Категории Доступа
BASE_RANKS_BY_CATEGORY = {
    "public": {'fin': 1, 'oper': 1, 'jur': 1, 'rep': 1, 'strat': 1},
    "internal": {'fin': 2, 'oper': 2, 'jur': 2, 'rep': 2, 'strat': 2},
    "personal_data": {'fin': 3, 'oper': 3, 'jur': 4, 'rep': 4, 'strat': 3},
    "trade_secret": {'fin': 4, 'oper': 3, 'jur': 3, 'rep': 3, 'strat': 4},
    "state_secret": {'fin': 5, 'oper': 4, 'jur': 6, 'rep': 5, 'strat': 5},
    "copyright": {'fin': 4, 'oper': 3, 'jur': 3, 'rep': 3, 'strat': 5}
}

# 2. Коэффициент Типа ресурса
TYPE_COEFFS = {
    "unknown": 1.0,  # Неизвестно (не влияет)
    "software": 1.25,  # Программное обеспечение
    "database": 1.20,  # База данных
    "financial": 1.15,  # Финансовая отчетность
    "document": 1.10,  # Текстовая документация
    "config": 1.10,  # Конфигурационные файлы
    "media": 1.05  # Мультимедиа
}

# 3. Коэффициент Жизненного цикла
LIFECYCLE_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "long_term": 1.20,  # Долгосрочный (более 3 лет)
    "medium_term": 1.10,  # Среднесрочный (1-3 года)
    "short_term": 1.05  # Краткосрочный (менее 1 года)
}

# 4. Коэффициент Формата данных
FORMAT_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "structured": 1.20,  # Структурированные данные (БД/JSON)
    "source_code": 1.25,  # Исходный код
    "text": 1.10,  # Текстовые документы
    "archive": 1.05,  # Архивы
    "multimedia": 1.00  # Мультимедиа
}

# 5. Коэффициент Масштаба использования
SCALE_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "enterprise": 1.20,  # Масштаб предприятия
    "department": 1.10,  # Уровень отдела
    "local": 1.05  # Локальный
}

# ===== НОВЫЕ ПАРАМЕТРЫ =====

# 6. Коэффициент конфиденциальности (уровень секретности)
CONFIDENTIALITY_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "open": 1.0,  # Открытая информация
    "internal": 1.1,  # Для внутреннего пользования
    "confidential": 1.2,  # Конфиденциально
    "secret": 1.3,  # Секретно
    "top_secret": 1.4  # Особой важности
}

# 7. Коэффициент количества пользователей
USERS_COUNT_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "1-10": 1.0,
    "11-100": 1.05,
    "101-1000": 1.1,
    "1001-10000": 1.15,
    "10000+": 1.2
}

# 8. Коэффициент критичности для бизнеса
BUSINESS_CRITICALITY_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "low": 1.0,  # Некритично
    "medium": 1.1,  # Средняя критичность
    "high": 1.2,  # Высокая критичность
    "critical": 1.3  # Критично для выживания бизнеса
}

# 9. Коэффициент наличия резервного копирования
BACKUP_COEFFS = {
    "unknown": 1.0,  # Неизвестно
    "daily": 0.9,  # Ежедневный бэкап (снижает риск)
    "weekly": 0.95,  # Еженедельный
    "monthly": 1.0,  # Ежемесячный
    "none": 1.2  # Нет бэкапа (повышает риск)
}


def calculate_base_ranks(
        category,
        res_type,
        lifecycle,
        data_format,
        scale,
        # Новые параметры со значением по умолчанию "unknown"
        confidentiality="unknown",
        users_count="unknown",
        business_criticality="unknown",
        backup="unknown"
):
    """
    Расчет рангов по методике с учетом новых параметров

    Параметры:
        category - категория доступа
        res_type - тип ресурса
        lifecycle - жизненный цикл
        data_format - формат данных
        scale - масштаб использования
        confidentiality - уровень конфиденциальности (НОВЫЙ)
        users_count - количество пользователей (НОВЫЙ)
        business_criticality - критичность для бизнеса (НОВЫЙ)
        backup - наличие резервного копирования (НОВЫЙ)

    Возвращает:
        calculated_ranks - словарь с полными результатами расчета
    """
    # Получаем базовые ранги по категории доступа
    base = BASE_RANKS_BY_CATEGORY.get(category, BASE_RANKS_BY_CATEGORY["public"]).copy()

    # Собираем все коэффициенты (с обработкой unknown)
    k_t = TYPE_COEFFS.get(res_type, 1.0)
    k_l = LIFECYCLE_COEFFS.get(lifecycle, 1.0)
    k_f = FORMAT_COEFFS.get(data_format, 1.0)
    k_s = SCALE_COEFFS.get(scale, 1.0)

    # НОВЫЕ коэффициенты
    k_conf = CONFIDENTIALITY_COEFFS.get(confidentiality, 1.0)
    k_users = USERS_COUNT_COEFFS.get(users_count, 1.0)
    k_business = BUSINESS_CRITICALITY_COEFFS.get(business_criticality, 1.0)
    k_backup = BACKUP_COEFFS.get(backup, 1.0)

    calculated_ranks = {}

    # Для каждого критерия своя формула
    for criterion, r_base in base.items():

        # Базовое произведение коэффициентов для всех критериев
        base_product = k_t * k_l

        # Добавляем специфичные коэффициенты
        if criterion == 'oper':
            # Операционный: + масштаб, + пользователи, + критичность
            val = r_base * base_product * k_s * k_users * k_business * k_backup
            formula = f"{r_base} × {k_t} (тип) × {k_l} (цикл) × {k_s} (масштаб) × {k_users} (пользователи) × {k_business} (критичность) × {k_backup} (бэкап)"

        elif criterion == 'fin':
            # Финансовый: + формат, + конфиденциальность, + пользователи, + критичность, + бэкап
            val = r_base * base_product * k_f * k_conf * k_users * k_business * k_backup
            formula = f"{r_base} × {k_t} (тип) × {k_l} (цикл) × {k_f} (формат) × {k_conf} (конфид) × {k_users} (пользователи) × {k_business} (критичность) × {k_backup} (бэкап)"

        elif criterion == 'jur':
            # Юридический: + конфиденциальность, + пользователи
            val = r_base * base_product * k_conf * k_users
            formula = f"{r_base} × {k_t} (тип) × {k_l} (цикл) × {k_conf} (конфид) × {k_users} (пользователи)"

        elif criterion == 'rep':
            # Репутационный: + пользователи, + критичность
            val = r_base * base_product * k_users * k_business
            formula = f"{r_base} × {k_t} (тип) × {k_l} (цикл) × {k_users} (пользователи) × {k_business} (критичность)"

        else:  # strat
            # Стратегический: + критичность, + конфиденциальность
            val = r_base * base_product * k_business * k_conf
            formula = f"{r_base} × {k_t} (тип) × {k_l} (цикл) × {k_business} (критичность) × {k_conf} (конфид)"

        # Сохраняем сырое значение
        raw_val = val

        # Округляем
        val = int(round(val))

        # Ограничиваем максимальными значениями
        max_val = MAX_RANKS.get(criterion, 8)
        val = max(1, min(val, max_val))

        # Сохраняем результаты
        calculated_ranks[criterion] = val
        calculated_ranks[f'{criterion}_raw'] = round(raw_val, 2)
        calculated_ranks[f'{criterion}_formula'] = formula

    # Добавляем все коэффициенты в результат
    calculated_ranks['coeff_type'] = k_t
    calculated_ranks['coeff_life'] = k_l
    calculated_ranks['coeff_format'] = k_f
    calculated_ranks['coeff_scale'] = k_s
    calculated_ranks['coeff_conf'] = k_conf
    calculated_ranks['coeff_users'] = k_users
    calculated_ranks['coeff_business'] = k_business
    calculated_ranks['coeff_backup'] = k_backup

    return calculated_ranks


def calculate_normalization(ranks):
    """Нормализация значений к единому диапазону [0..1]"""
    s_scores = {}
    total_s = 0.0

    for key, val in ranks.items():
        if key.endswith('_raw') or key.endswith('_formula') or key.startswith('coeff_'):
            continue

        max_r = MAX_RANKS.get(key, 8)

        if max_r > 1:
            s_val = (val - 1) / (max_r - 1)
        else:
            s_val = 0

        s_scores[key] = round(s_val, 3)
        total_s += s_val

    return s_scores, round(total_s, 3)


def get_final_rank(sum_s):
    """Определение итогового ранга по интегральной сумме SΣ"""
    if sum_s <= 0.55:
        return 1
    elif sum_s <= 1.11:
        return 2
    elif sum_s <= 1.67:
        return 3
    elif sum_s <= 2.22:
        return 4
    elif sum_s <= 2.78:
        return 5
    elif sum_s <= 3.33:
        return 6
    elif sum_s <= 3.89:
        return 7
    elif sum_s <= 4.44:
        return 8
    else:
        return 9


def get_protection_level(final_rank):
    """Возвращает текстовое описание уровня защиты"""
    levels = {
        1: "Базовый (открытая информация)",
        2: "Базовый",
        3: "Стандартный",
        4: "Стандартный",
        5: "Повышенный",
        6: "Повышенный",
        7: "Высокий",
        8: "Высокий",
        9: "Максимальный (особый режим)"
    }
    return levels.get(final_rank, "Не определен")