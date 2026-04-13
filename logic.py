# logic.py
# Система оценки ценности информационных ресурсов
# Методика: сложение базовых рангов + бонусы от параметров (каждый бонус = +1)

# ============================================================================
# МАКСИМАЛЬНЫЕ ЗНАЧЕНИЯ ШКАЛ
# ============================================================================
MAX_RANKS = {
    'fin': 10,  # Финансовый ущерб
    'oper': 10,  # Операционный сбой
    'jur': 8,  # Юридический риск
    'rep': 8,  # Репутационный ущерб
    'strat': 8  # Стратегический ущерб
}

MIN_RANKS = {
    'fin': 1,
    'oper': 1,
    'jur': 1,
    'rep': 1,
    'strat': 1
}

# ============================================================================
# 1. БАЗОВЫЕ РАНГИ (ЗАВИСЯТ ОТ КАТЕГОРИИ ДОСТУПА)
# ============================================================================
BASE_RANKS_BY_CATEGORY = {
    "public": {
        'fin': 1, 'oper': 1, 'jur': 1, 'rep': 1, 'strat': 1
    },
    "internal": {
        'fin': 2, 'oper': 2, 'jur': 2, 'rep': 2, 'strat': 2
    },
    "personal_data": {
        'fin': 3, 'oper': 3, 'jur': 4, 'rep': 4, 'strat': 3
    },
    "trade_secret": {
        'fin': 4, 'oper': 3, 'jur': 3, 'rep': 3, 'strat': 4
    },
    "state_secret": {
        'fin': 5, 'oper': 4, 'jur': 6, 'rep': 5, 'strat': 5
    },
    "copyright": {
        'fin': 4, 'oper': 3, 'jur': 3, 'rep': 3, 'strat': 5
    }
}

# ============================================================================
# 2. БОНУСЫ ОТ ТИПА РЕСУРСА
# ============================================================================
# Обоснование: каждый "особенный" тип ресурса добавляет +1 к соответствующим рискам
TYPE_BONUS = {
    "unknown": {},
    "software": {
        'fin': 1,  # ПО сложно восстанавливать, высокие затраты на разработку
        'jur': 1  # Нарушение лицензий, авторских прав
    },
    "database": {
        'fin': 1,  # Утечка БД = массовый ущерб
        'jur': 1  # Персональные данные, ответственность по 152-ФЗ
    },
    "financial": {
        'fin': 1  # Финансовая отчётность под особым контролем регуляторов
    },
    "document": {},
    "config": {},
    "media": {}
}

# ============================================================================
# 3. БОНУСЫ ОТ ЖИЗНЕННОГО ЦИКЛА
# ============================================================================
# Обоснование: чем дольше хранится информация, тем выше стратегическая ценность
LIFECYCLE_BONUS = {
    "unknown": {},
    "short_term": {},  # до 1 года
    "medium_term": {
        'strat': 1  # 1-3 года
    },
    "long_term": {
        'strat': 1,  # более 3 лет
        'jur': 1  # длительный срок ответственности
    }
}

# ============================================================================
# 4. БОНУСЫ ОТ ФОРМАТА ДАННЫХ
# ============================================================================
# Обоснование: разные форматы имеют разную ценность для злоумышленников
FORMAT_BONUS = {
    "unknown": {},
    "structured": {
        'fin': 1  # Структурированные данные легко извлекаются и анализируются
    },
    "source_code": {
        'fin': 1,  # Исходный код = интеллектуальная собственность
        'oper': 1  # Утечка кода может нарушить работу систем
    },
    "text": {},
    "archive": {},
    "multimedia": {}
}

# ============================================================================
# 5. БОНУСЫ ОТ МАСШТАБА ИСПОЛЬЗОВАНИЯ
# ============================================================================
# Обоснование: чем шире используется ресурс, тем больше последствия сбоя
SCALE_BONUS = {
    "unknown": {},
    "local": {},
    "department": {
        'oper': 1  # Сбой в отделе влияет на работу подразделения
    },
    "enterprise": {
        'oper': 1,  # Сбой на уровне предприятия = остановка бизнес-процессов
        'strat': 1  # Влияет на стратегические показатели компании
    }
}

# ============================================================================
# 6. БОНУСЫ ОТ УРОВНЯ КОНФИДЕНЦИАЛЬНОСТИ
# ============================================================================
# Обоснование: высокая степень секретности увеличивает юридические риски
CONFIDENTIALITY_BONUS = {
    "unknown": {},
    "open": {},
    "internal": {},
    "confidential": {
        'jur': 1  # Конфиденциальная информация защищена законом
    },
    "secret": {
        'jur': 1,  # Секретные данные = повышенная ответственность
        'rep': 1  # Утечка секретов наносит репутационный ущерб
    },
    "top_secret": {
        'jur': 2,  # Гостайна = максимальная юридическая ответственность
        'rep': 1  # Утечка гостайны = катастрофа для репутации
    }
}

# ============================================================================
# 7. БОНУСЫ ОТ КОЛИЧЕСТВА ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================
# Обоснование: больше пользователей = шире охват при инциденте
USERS_BONUS = {
    "unknown": {},
    "1-10": {},
    "11-100": {},
    "101-1000": {
        'oper': 1  # Много пользователей = сложнее обеспечить доступность
    },
    "1001-10000": {
        'oper': 1,
        'rep': 1  # Массовые жалобы = репутационные потери
    },
    "10000+": {
        'oper': 1,
        'rep': 1  # Огромная аудитория = максимальный репутационный ущерб
    }
}

# ============================================================================
# 8. БОНУСЫ ОТ КРИТИЧНОСТИ ДЛЯ БИЗНЕСА
# ============================================================================
# Обоснование: критичность прямо коррелирует с размером потенциального ущерба
CRITICALITY_BONUS = {
    "unknown": {},
    "low": {},
    "medium": {
        'fin': 1  # Средняя критичность = ощутимые финансовые потери
    },
    "high": {
        'fin': 1,
        'oper': 1  # Высокая критичность = серьёзные операционные сбои
    },
    "critical": {
        'fin': 1,
        'oper': 1,
        'strat': 1  # Критический ресурс = угроза стратегии развития
    }
}

# ============================================================================
# 9. БОНУСЫ/ШТРАФЫ ОТ РЕЗЕРВНОГО КОПИРОВАНИЯ
# ============================================================================
# Обоснование: наличие бэкапов снижает риски, отсутствие — повышает
BACKUP_BONUS = {
    "unknown": {},
    "daily": {
        'oper': -1  # Ежедневный бэкап СНИЖАЕТ операционный риск
    },
    "weekly": {},
    "monthly": {},
    "none": {
        'oper': 1  # Отсутствие бэкапа ПОВЫШАЕТ риск при сбое
    }
}


# ============================================================================
# ОСНОВНАЯ ФУНКЦИЯ РАСЧЁТА
# ============================================================================
def calculate_ranks(
        category: str,
        res_type: str,
        lifecycle: str,
        data_format: str,
        scale: str,
        confidentiality: str,
        users_count: str,
        business_criticality: str,
        backup: str
) -> dict:
    """
    Расчёт рангов по методике "сложение бонусов"

    Аргументы:
        category - категория доступа (public, internal, personal_data, trade_secret, state_secret, copyright)
        res_type - тип ресурса (unknown, software, database, financial, document, config, media)
        lifecycle - жизненный цикл (unknown, short_term, medium_term, long_term)
        data_format - формат данных (unknown, structured, source_code, text, archive, multimedia)
        scale - масштаб использования (unknown, local, department, enterprise)
        confidentiality - конфиденциальность (unknown, open, internal, confidential, secret, top_secret)
        users_count - количество пользователей (unknown, 1-10, 11-100, 101-1000, 1001-10000, 10000+)
        business_criticality - критичность (unknown, low, medium, high, critical)
        backup - резервное копирование (unknown, daily, weekly, monthly, none)

    Возвращает:
        dict с ключами fin, oper, jur, rep, strat
    """

    # 1. Берём базовые ранги от категории доступа
    ranks = BASE_RANKS_BY_CATEGORY.get(category, BASE_RANKS_BY_CATEGORY["public"]).copy()

    # 2. Собираем все бонусы в список
    all_bonuses = [
        TYPE_BONUS.get(res_type, {}),
        LIFECYCLE_BONUS.get(lifecycle, {}),
        FORMAT_BONUS.get(data_format, {}),
        SCALE_BONUS.get(scale, {}),
        CONFIDENTIALITY_BONUS.get(confidentiality, {}),
        USERS_BONUS.get(users_count, {}),
        CRITICALITY_BONUS.get(business_criticality, {}),
        BACKUP_BONUS.get(backup, {})
    ]

    # 3. Применяем бонусы (просто складываем)
    for bonus in all_bonuses:
        for criterion, delta in bonus.items():
            ranks[criterion] = ranks.get(criterion, 0) + delta

    # 4. Ограничиваем минимумами и максимумами
    for criterion in ranks:
        ranks[criterion] = max(MIN_RANKS[criterion], min(MAX_RANKS[criterion], ranks[criterion]))

    return ranks


def calculate_normalization(ranks: dict) -> tuple:
    """
    Нормализация значений к единому диапазону [0..1]

    Аргументы:
        ranks - словарь с рангами (fin, oper, jur, rep, strat)

    Возвращает:
        s_scores - словарь нормализованных значений
        total_s - сумма нормализованных значений
    """
    s_scores = {}
    total_s = 0.0

    # Нормализация для каждого критерия
    # Формула: S = (R_факт - 1) / (R_max - 1)

    # Группа А (max = 10)
    s_scores['fin'] = (ranks['fin'] - 1) / 9
    s_scores['oper'] = (ranks['oper'] - 1) / 9

    # Группа Б (max = 8)
    s_scores['jur'] = (ranks['jur'] - 1) / 7
    s_scores['rep'] = (ranks['rep'] - 1) / 7
    s_scores['strat'] = (ranks['strat'] - 1) / 7

    total_s = sum(s_scores.values())

    return s_scores, round(total_s, 3)


def get_final_rank(sum_s: float) -> int:
    """
    Определение итогового ранга по интегральной сумме SΣ

    Аргументы:
        sum_s - интегральная сумма нормализованных значений (0-5)

    Возвращает:
        итоговый ранг от 1 до 9
    """
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


def get_protection_level(final_rank: int) -> str:
    """
    Возвращает текстовое описание уровня защиты

    Аргументы:
        final_rank - итоговый ранг (1-9)

    Возвращает:
        строковое описание уровня защиты
    """
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


def get_bonus_details(
        category: str,
        res_type: str,
        lifecycle: str,
        data_format: str,
        scale: str,
        confidentiality: str,
        users_count: str,
        business_criticality: str,
        backup: str
) -> dict:
    """
    Возвращает детальную информацию о том, какие бонусы были применены
    (для отображения в интерфейсе)

    Возвращает:
        словарь с описанием каждого применённого бонуса
    """
    details = {
        "base": BASE_RANKS_BY_CATEGORY.get(category, BASE_RANKS_BY_CATEGORY["public"]).copy(),
        "bonuses": []
    }

    bonus_sources = [
        ("Тип ресурса", TYPE_BONUS.get(res_type, {})),
        ("Жизненный цикл", LIFECYCLE_BONUS.get(lifecycle, {})),
        ("Формат данных", FORMAT_BONUS.get(data_format, {})),
        ("Масштаб", SCALE_BONUS.get(scale, {})),
        ("Конфиденциальность", CONFIDENTIALITY_BONUS.get(confidentiality, {})),
        ("Количество пользователей", USERS_BONUS.get(users_count, {})),
        ("Критичность для бизнеса", CRITICALITY_BONUS.get(business_criticality, {})),
        ("Резервное копирование", BACKUP_BONUS.get(backup, {}))
    ]

    for source_name, bonus in bonus_sources:
        if bonus:
            details["bonuses"].append({
                "source": source_name,
                "bonus": bonus
            })

    return details


# ============================================================================
# ФУНКЦИЯ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ (ЕСЛИ ГДЕ-ТО ВЫЗЫВАЕТСЯ calculate_base_ranks)
# ============================================================================
def calculate_base_ranks(
        category: str,
        res_type: str,
        lifecycle: str,
        data_format: str,
        scale: str,
        confidentiality: str = "unknown",
        users_count: str = "unknown",
        business_criticality: str = "unknown",
        backup: str = "unknown"
) -> dict:
    """
    Обёртка для обратной совместимости со старым кодом.
    Вызывает calculate_ranks и возвращает результат в старом формате.
    """
    ranks = calculate_ranks(
        category=category,
        res_type=res_type,
        lifecycle=lifecycle,
        data_format=data_format,
        scale=scale,
        confidentiality=confidentiality,
        users_count=users_count,
        business_criticality=business_criticality,
        backup=backup
    )

    # Добавляем коэффициенты (для совместимости, но они не используются)
    result = ranks.copy()
    result['coeff_type'] = 1.0
    result['coeff_life'] = 1.0
    result['coeff_format'] = 1.0
    result['coeff_scale'] = 1.0
    result['coeff_conf'] = 1.0
    result['coeff_users'] = 1.0
    result['coeff_business'] = 1.0
    result['coeff_backup'] = 1.0

    # Формулы для отображения
    for crit in ['fin', 'oper', 'jur', 'rep', 'strat']:
        result[f'{crit}_formula'] = f"Базовый {result[crit]}"

    return result


# ============================================================================
# ТЕСТИРОВАНИЕ (при запуске файла напрямую)
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование logic.py")
    print("=" * 60)

    # Тестовый пример: Медицинская информационная система
    print("\n1. Тест: Медицинская информационная система")
    ranks = calculate_ranks(
        category="personal_data",
        res_type="database",
        lifecycle="long_term",
        data_format="structured",
        scale="enterprise",
        confidentiality="confidential",
        users_count="1001-10000",
        business_criticality="high",
        backup="weekly"
    )
    print(
        f"   Результат: fin={ranks['fin']}, oper={ranks['oper']}, jur={ranks['jur']}, rep={ranks['rep']}, strat={ranks['strat']}")

    # Нормализация
    s_scores, total_s = calculate_normalization(ranks)
    print(f"   Нормализация: SΣ={total_s}")

    # Итоговый ранг
    final_rank = get_final_rank(total_s)
    print(f"   Итоговый ранг: {final_rank} ({get_protection_level(final_rank)})")

    # Детали бонусов
    print("\n2. Детали применённых бонусов:")
    details = get_bonus_details(
        category="personal_data",
        res_type="database",
        lifecycle="long_term",
        data_format="structured",
        scale="enterprise",
        confidentiality="confidential",
        users_count="1001-10000",
        business_criticality="high",
        backup="weekly"
    )
    print(f"   Базовые ранги: {details['base']}")
    for bonus in details['bonuses']:
        print(f"   + {bonus['source']}: {bonus['bonus']}")

    print("\n✅ Тестирование завершено")