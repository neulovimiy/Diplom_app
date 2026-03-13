# logic.py
# Максимальные значения шкал (Группа А - 8, Группа Б - 5)
MAX_RANKS = {'fin': 8, 'oper': 8, 'jur': 5, 'rep': 5, 'strat': 5}

# 1. Базовые ранги от Категории Доступа (РЕАЛИСТИЧНЫЕ - от 1 до 4)
BASE_RANKS_BY_CATEGORY = {
    "public": {'jur': 1, 'fin': 1, 'oper': 1, 'rep': 1, 'strat': 1},  # Общедоступная
    "internal": {'jur': 2, 'fin': 1, 'oper': 2, 'rep': 1, 'strat': 2},  # Внутренняя
    "personal_data": {'jur': 3, 'fin': 2, 'oper': 2, 'rep': 3, 'strat': 2},  # Персональные данные
    "trade_secret": {'jur': 2, 'fin': 3, 'oper': 2, 'rep': 2, 'strat': 3},  # Коммерческая тайна
    "state_secret": {'jur': 4, 'fin': 3, 'oper': 3, 'rep': 4, 'strat': 4},  # Государственная тайна
    "copyright": {'jur': 2, 'fin': 3, 'oper': 2, 'rep': 2, 'strat': 4}  # Интеллектуальная собственность
}

# 2. Коэффициент Типа ресурса
TYPE_COEFFS = {
    "software": 1.5,
    "database": 1.4,
    "financial": 1.3,
    "document": 1.2,
    "media": 1.1
}

# 3. Коэффициент Жизненного цикла
LIFECYCLE_COEFFS = {
    "long_term": 1.3,
    "medium_term": 1.2,
    "short_term": 1.1
}

# 4. Коэффициент Формата данных
FORMAT_COEFFS = {
    "structured": 1.3,
    "source_code": 1.4,
    "text": 1.2,
    "archive": 1.1,
    "multimedia": 1.0
}

# 5. Коэффициент Масштаба использования
SCALE_COEFFS = {
    "enterprise": 1.3,
    "department": 1.2,
    "local": 1.1
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
        # Разные формулы для разных критериев
        if criterion == 'oper':
            # Операционный зависит от масштаба и типа
            val = r_base * k_t * k_s
        elif criterion == 'fin':
            # Финансовый зависит от формата, цикла и типа
            val = r_base * k_t * k_l * k_f
        else:
            # Остальные - от типа и цикла
            val = r_base * k_t * k_l

        # Сохраняем сырое значение для отладки
        raw_val = val

        # Округляем
        val = int(round(val))

        # Ограничиваем максимальными значениями
        val = max(1, min(val, MAX_RANKS.get(criterion, 5)))

        calculated_ranks[criterion] = val
        calculated_ranks[f'{criterion}_raw'] = round(raw_val, 2)

    return calculated_ranks


def calculate_normalization(ranks):
    s_scores = {}
    total_s = 0.0
    for key, val in ranks.items():
        if key.endswith('_raw'):
            continue
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