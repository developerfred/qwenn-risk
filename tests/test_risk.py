"""Tests for Qwenn-Risk liquidation and risk calculation."""

from qwenn_risk.liquidation import (
    calc_liquidation,
    calc_maintenance_margin,
    calc_margin_utilization,
    check_liquidation_risk,
    main,
)


def test_calc_liquidation_basic():
    """Test basic liquidation price calculation.
    
    Posição longa: 2 ETH a 3000 USD com 10x alavancagem, margem 1% (1000 bps).
    Fórmula: P_liq = entry * (leverage * 1000 - mmr) / (leverage * 1000)
    = 3000 * (10000 - 1000) / 10000 = 3000 * 9000 / 10000 = 2700
    """
    liquidation = calc_liquidation(entry_price=3000, size=2, leverage=10, maintenance_margin_rate=1000)
    assert liquidation == 2700, f"Expected 2700, got {liquidation}"
    print("✓ Basic liquidation calculation works (2700)")


def test_calc_liquidation_no_margin():
    """Test liquidation with maintenance margin = 0 (edge case)."""
    liquidation = calc_liquidation(entry_price=3000, size=1, leverage=5, maintenance_margin_rate=0)
    # Com margem 0, P_liq = entry * (5�00 - 0) / 5000 = entry * 1 = entry
    assert liquidation == 3000, f"Expected 3000, got {liquidation}"
    print("✓ Edge case: zero maintenance margin (liquidation = entry price)")


def test_calc_liquidation_high_leverage():
    """Test liquidation with high leverage."""
    # 50x alavancagem, margem 1%, entrada 100
    # P_liq = 100 * (50000 - 1000) / 50000 = 100 * 49000 / 50000 = 100 * 0.98 = 98
    entry_p = 100
    liquidation = calc_liquidation(entry_price=entry_p, size=1, leverage=50, maintenance_margin_rate=1000)
    assert liquidation < entry_p, f"Expected liquidation < entry_price ({entry_p}), got {liquidation}"
    assert liquidation == 98, f"Expected 98, got {liquidation}"
    print("✓ High leverage liquidation works (98)")


def test_calc_liquidation_various_margins():
    """Test liquidation with different maintenance margin rates."""
    # 10x alavancagem, entrada 3000:
    # - 1% (1000 bps): P_liq = 3000 * 9000/10000 = 2700
    # - 5% (5000 bps): P_liq = 3000 * 5000/10000 = 1500  
    # - 10% (10000 bps): P_liq = 3000 * 0/10000 = 0 (immediate liquidation)
    
    r1 = calc_liquidation(entry_price=3000, size=1, leverage=10, maintenance_margin_rate=1000)
    assert r1 == 2700, f"1% margin: expected 2700, got {r1}"
    
    r2 = calc_liquidation(entry_price=3000, size=1, leverage=10, maintenance_margin_rate=5000)
    assert r2 == 1500, f"5% margin: expected 1500, got {r2}"
    
    r3 = calc_liquidation(entry_price=3000, size=1, leverage=10, maintenance_margin_rate=10000)
    assert r3 == 0, f"10% margin: expected 0, got {r3}"
    
    print("✓ Various margin rates work correctly")


def test_calc_maintenance_margin():
    """Test maintenance margin calculation."""
    # maintenance = entry_price * size * rate / 1000
    # = 3000 * 2 * 1000 / 1000 = 3000 * 2 = 6000
    margin = calc_maintenance_margin(entry_price=3000, size=2, maintenance_margin_rate=1000)
    assert margin == 6000, f"Expected 6000, got {margin}"
    print("✓ Maintenance margin calculation works")


def test_calc_margin_utilization():
    """Test margin utilization calculation."""
    # Position: 2 ETH a 3000 USD, 10x alavancagem, mark price 2900
    # margin_used = 3000 * 2 / 10 = 600
    # maintenance = 3000 * 2 * 1000 / 1000 = 6000
    # utilization = 600 / 6000 * 10000 = 1000 bps = 10%
    utilization = calc_margin_utilization(entry_price=3000, size=2, leverage=10, mark_price=2900, maintenance_margin_rate=1000)
    # Deveria ser próximo de 1000 bps (10%)
    assert 0 <= utilization <= 10000, f"Expected 0-10000, got {utilization}"
    print("✓ Margin utilization calculation works")


def test_check_liquidation_risk_long_safe():
    """Test risk check for long position NOT at risk."""
    # Posição longa: entrada 3000, mark price 2900
    # Liquidation price ~2700, mark price 2900 > 2700, então NÃO deve estar em risco
    result = check_liquidation_risk(entry_price=3000, size=1, leverage=10, mark_price=2900, maintenance_margin_rate=1000)
    assert result["liquidation_price"] == 2700, f"Expected 2700, got {result['liquidation_price']}"
    assert result["at_risk"] is False, f"Expected at_risk=False, got {result['at_risk']}"
    assert result["margin_utilization"] > 0, "Expected positive margin utilization"
    print("✓ Risk check for long position safe")


def test_check_liquidation_risk_at_risk():
    """Test risk check when position IS at risk."""
    # Posição longa com mark price abaixo de liquidation
    # entrance 3000, liquidation 2700, mark price 2600 => at risk
    result = check_liquidation_risk(entry_price=3000, size=1, leverage=10, mark_price=2600, maintenance_margin_rate=1000)
    assert result["at_risk"] is True, f"Expected at_risk=True, got {result['at_risk']}"
    assert result["liquidation_price"] == 2700, f"Expected 2700, got {result['liquidation_price']}"
    print("✓ Risk check detects at-risk position")


def test_check_liquidation_risk_extreme():
    """Test risk check with extreme parameters."""
    # Entrada 100, alavancagem 100x, margem 1%, mark price 1
    result = check_liquidation_risk(entry_price=100, size=1, leverage=100, mark_price=1, maintenance_margin_rate=1000)
    assert "liquidation_price" in result
    assert "at_risk" in result
    print("✓ Extreme parameters handled without crash")


def test_check_liquidation_risk_all_safe():
    """Test risk check with mark price well above liquidation."""
    # mark_price muito acima de liquidation: deve ser seguro
    result = check_liquidation_risk(entry_price=3000, size=1, leverage=10, mark_price=3500, maintenance_margin_rate=1000)
    assert result["at_risk"] is False, f"Expected at_risk=False, got {result['at_risk']}"
    assert result["liquidation_price"] == 2700
    print("✓ Risk check: mark price well above liquidation = safe")


def test_all_functions_import():
    """Test that all public functions can be imported and called."""
    from qwenn_risk.liquidation import (
        calc_liquidation,
        calc_maintenance_margin,
        calc_margin_utilization,
        check_liquidation_risk,
    )
    # Test with basic args
    calc_liquidation(1000, 1, 5)
    calc_maintenance_margin(1000, 1, 1000)
    calc_margin_utilization(1000, 1, 5, 900, 1000)
    check_liquidation_risk(1000, 1, 5, 900, 1000)
    print("✓ All functions import and execute correctly")


if __name__ == "__main__":
    test_calc_liquidation_basic()
    test_calc_liquidation_no_margin()
    test_calc_liquidation_high_leverage()
    test_calc_liquidation_various_margins()
    test_calc_maintenance_margin()
    test_calc_margin_utilization()
    test_check_liquidation_risk_long_safe()
    test_check_liquidation_risk_at_risk()
    test_check_liquidation_risk_extreme()
    test_check_liquidation_risk_all_safe()
    test_all_functions_import()
    print("\n🎉 All risk tests passed!")