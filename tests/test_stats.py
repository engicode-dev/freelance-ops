from services.stats import calculate, MIN_SESSION_HOURS


def _inc(id_, amount_kop, type_):
    return {"id": id_, "amount_kopecks": amount_kop, "type": type_}


def test_empty():
    s = calculate([], {})
    assert s.total_kop == 0
    assert s.effective_rate_kop is None
    assert s.passive_share == 0.0


def test_only_passive_no_rate():
    s = calculate([_inc(1, 50000, "passive")], {})
    assert s.active_kop == 0
    assert s.passive_kop == 50000
    assert s.effective_rate_kop is None   # нечего делить — часов нет


def test_zero_hours_no_division_by_zero():
    s = calculate([_inc(1, 100000, "active")], {1: 0.0})
    assert s.effective_rate_kop is None


def test_tiny_session_below_threshold():
    """Сессия короче 30 секунд не должна давать ставку."""
    tiny = MIN_SESSION_HOURS / 2
    s = calculate([_inc(1, 1200000, "active")], {1: tiny})
    assert s.paid_hours == 0.0
    assert s.effective_rate_kop is None


def test_active_rate_normal():
    s = calculate(
        [_inc(1, 1200000, "active"), _inc(2, 600000, "active")],
        {1: 10.0, 2: 5.0},
    )
    assert s.active_kop == 1800000
    assert s.paid_hours == 15.0
    assert s.effective_rate_kop == 120000     # 18000₽ / 15ч = 1200₽/ч


def test_passive_share():
    s = calculate(
        [_inc(1, 900000, "active"), _inc(2, 100000, "passive")],
        {1: 10.0},
    )
    assert abs(s.passive_share - 0.1) < 1e-9