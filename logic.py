# logic.py
# Максимальные значения шкал (Группа А - 8, Группа Б - 5)
MAX_RANKS = {'fin': 8, 'oper': 8, 'jur': 5, 'rep': 5, 'strat': 5}

# 1. Базовые ранги от Категории Доступа (Таблица 4.3 из отчета)
BASE_RANKS_BY_CATEGORY = {
    "public": {'jur': 1, 'fin': 1, 'oper': 1, 'rep': 1, 'strat': 1},
    "internal": {'jur': 2, 'fin': 2, 'oper': 2, 'rep': 1, 'strat': 2},
    "personal_data": {'jur': 3, 'fin': 2, 'oper': 2, 'rep': 3, 'strat': 2},
    "trade_secret": {'jur': 2, 'fin': 4, 'oper': 3, 'rep': 2, 'strat': 3},
    "state_secret": {'jur': 5, 'fin': 5, 'oper': 4, 'rep': 5, 'strat': 4},
    "copyright": {'jur': 2, 'fin': 5, 'oper': 3, 'rep': 2, 'strat': 5}
}

# 2. Коэффициент Типа ресурса (Таблица 4.4)
TYPE_COEFFS = {
    "software": 1.5, "database": 1.4, "financial": 1.3, "document": 1.0, "media": 0.8
}

# 3. Коэффициент Жизненного цикла (Таблица 4.5)
LIFECYCLE_COEFFS = {
    "long_term": 1.2, "medium_term": 1.0, "short_term": 0.8
}

# 4. Коэффициент Формата данных (Из пункта 1.4 отчета)
FORMAT_COEFFS = {
    "structured": 1.2,  # БД, JSON, CSV
    "source_code": 1.5,  # Исходный код
    "text": 1.0,         # Документы
    "archive": 0.9,      # Резервные копии
    "multimedia": 0.8    # Графика, видео
}

# 5. Коэффициент Масштаба использования (Из анализа рисков)
SCALE_COEFFS = {
    "enterprise": 1.3,   # Вся компания
    "department": 1.0,    # Отдел
    "local": 0.8          # Несколько сотрудников
}

def calculate_base_ranks(category, res_type, lifecycle, data_format, scale):
    base = BASE_RANKS_BY_CATEGORY.get(category, BASE_RANKS_BY_CATEGORY["public"]).copy()

    # Собираем все коэффициенты
    k_t = TYPE_COEFFS.get(res_type, 1.0)
    k_l = LIFECYCLE_COEFFS.get(lifecycle, 1.0)
    k_f = FORMAT_COEFFS.get(data_format, 1.0)
    k_s = SCALE_COEFFS.get(scale, 1.0)

    calculated_ranks = {}

    for criterion, r_base in base.items():
        # Комплексная формула: База * Тип * Цикл * Формат * Масштаб
        # (Масштаб сильнее влияет на операции, Формат - на финансы/утечки)
        if criterion == 'oper':
            val = r_base * k_t * k_s  # Масштаб бьет по операциям
        elif criterion == 'fin':
            val = r_base * k_t * k_l * k_f  # Формат и цикл бьют по финансам
        else:
            val = r_base * k_t * k_l

        val = int(round(val))
        val = max(1, min(val, MAX_RANKS.get(criterion, 5)))
        calculated_ranks[criterion] = val

    return calculated_ranks


def calculate_normalization(ranks):
    s_scores = {}
    total_s = 0.0
    for key, val in ranks.items():
        max_r = MAX_RANKS.get(key, 5)
        s_val = (val - 1) / (max_r - 1) if max_r > 1 else 0
        s_scores[key] = round(s_val, 3)
        total_s += s_val
    return s_scores, round(total_s, 3)


def get_final_rank(sum_s):
    if sum_s <= 0.625:
        return 1
    elif sum_s <= 1.250:
        return 2
    elif sum_s <= 1.875:
        return 3
    elif sum_s <= 2.500:
        return 4
    elif sum_s <= 3.125:
        return 5
    elif sum_s <= 3.750:
        return 6
    elif sum_s <= 4.375:
        return 7
    elif sum_s <= 4.999:
        return 8
    else:
        return 9