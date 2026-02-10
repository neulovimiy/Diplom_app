# logic.py

# Новые границы шкал по твоему требованию
MAX_RANKS = {
    'fin': 8,
    'oper': 8,
    'jur': 5,
    'rep': 5,
    'strat': 5
}


def calculate_normalization(ranks):
    s_scores = {}
    total_s = 0.0

    for key, val in ranks.items():
        val = max(1, val)
        max_r = MAX_RANKS[key]

        # Формула S = (Rank - 1) / (MaxRank - 1)
        # Для шкал 8: делитель 7. Для шкал 5: делитель 4.
        s_val = (val - 1) / (max_r - 1)
        s_scores[key] = round(s_val, 3)
        total_s += s_val

    return s_scores, round(total_s, 3)


def get_final_rank(sum_s):
    # Максимальная сумма S теперь всегда 5.0 (так как 5 критериев по 1.0)
    # Делим диапазон 0-5 на 9 уровней
    if sum_s <= 0.55:
        return 1
    elif sum_s <= 1.11:
        return 2
    elif sum_s <= 1.66:
        return 3
    elif sum_s <= 2.22:
        return 4
    elif sum_s <= 2.77:
        return 5
    elif sum_s <= 3.33:
        return 6
    elif sum_s <= 3.88:
        return 7
    elif sum_s <= 4.44:
        return 8
    else:
        return 9