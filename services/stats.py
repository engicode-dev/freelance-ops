from dataclasses import dataclass

@dataclass
class Stats:
    total_kop: int
    active_kop: int
    passive_kop: int
    paid_hours: float
    effective_rate_kop: int | None      # ₽/ч в копейках
    passive_share: float

MIN_SESSION_HOURS = 30 / 3600  # 30 секунд — всё, что короче, считаем «не работа»

def calculate(incomes, hours_by_income):
    active = sum(i["amount_kopecks"] for i in incomes if i["type"] == "active")
    passive = sum(i["amount_kopecks"] for i in incomes if i["type"] == "passive")
    hours = sum(hours_by_income.get(i["id"], 0.0)
                for i in incomes if i["type"] == "active")
    # отсекаем мусорные сессии
    hours = hours if hours >= MIN_SESSION_HOURS else 0.0
    total = active + passive
    return Stats(
        total_kop=total,
        active_kop=active,
        passive_kop=passive,
        paid_hours=hours,
        effective_rate_kop=int(active / hours) if hours > 0 else None,
        passive_share=(passive / total) if total > 0 else 0.0,
    )