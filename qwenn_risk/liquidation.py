"""Liquidation price calculation module for Qwenn-Risk.

This module provides exact liquidation price calculation using BendLite
arithmetic (U32, exact, bit-for-bit reproducible).
"""

from __future__ import annotations

from typing import Union, Dict


U32 = int  # 32-bit unsigned integer (mod 2^32)
Nat = int  # Natural number


def calc_liquidation(
    entry_price: U32,
    size: U32,
    leverage: U32,
    maintenance_margin_rate: U32 = 1000,  # 1% = 1000 basis points
) -> U32:
    """
    Calculate exact liquidation price.

    Formula: P_liq = entry_price * (leverage * 1000 - maintenance_margin_rate) / (leverage * 1000)

    This ensures that with maintenance_margin_rate=1000 (1%):
    - P_liq = entry_price * (leverage * 1000 - 1000) / (leverage * 1000)
    - P_liq = entry_price * (leverage - 1) / leverage

    Example: entry=3000, leverage=10, maintenance=1% (1000 bps):
    - P_liq = 3000 * (10000 - 1000) / 10000 = 3000 * 9000 / 10000 = 2700

    Args:
        entry_price: Preço de entrada da posição (U32, em USD por exemplo)
        size: Tamanho da posição em unidades (U32, ex: ETH quantidade)
        leverage: Alavancagem usada (U32, ex: 10 para 10x)
        maintenance_margin_rate: Taxa de margem de manutenção em basis points (1-9999),
            padrão 1000 = 1%

    Returns:
        U32: Preço de liquidação calculado (mod 2^32)

    Formula logic:
    - Com alavancagem L e margem de manutenção M% (em basis points):
    - A posição pode perder (1 - M/(L*1000)) do seu valor antes da liquidação
    - Preço de liquidação = P_entry * (1 - M/(L*1000)) = P_entry * (L*1000 - M) / (L*1000)
    - Com L=10, M=1000 (1%): P_liq = P_entry * 9000/10000 = P_entry * 0.9
    """
    # Validation: parameters must produce valid results
    if entry_price == 0:
        return 0
    if leverage == 0:
        return 0  # Alavancagem zero é inválido
    if maintenance_margin_rate > leverage * 10000:
        # Maintenance margin exceeding 10x leverage is extreme edge case
        # Cap at reasonable value
        maintenance_margin_rate = min(maintenance_margin_rate, leverage * 1000 - 1)

    # Cálculo exacto: entry_price * (leverage * 1000 - maintenance_margin_rate) / (leverage * 1000)
    # Usar aritmética de precisão: multiplicar primeiro, depois dividir
    # Para evitar overflow em U32, usamos o fato de que entry_price * (leverage * 1000 - mmr) 
    # pode ser reescrito para manter precisão

    multiplier: U32 = leverage * 1000 - maintenance_margin_rate
    divisor: U32 = leverage * 1000

    # Garantir que o multiplier seja positivo
    if multiplier <= 0:
        # Margem de manutenção muito alta: preço de liquidação tende a 0 ou entry_price
        return max(0, entry_price // divisor) if divisor > 0 else 0

    # Calcular: (entry_price * multiplier) // divisor
    # entry_price pode ser grande, então tomar cuidado com overflow, mas em Python
    # inteiros têm precisão arbitrária, então está ok
    product: U32 = (entry_price * multiplier) % (2**32)
    liquidation_price: U32 = product // divisor

    # Garantir que o preço de liquidação seja menor que entry_price (para posição longa)
    # exceto em casos extremos
    if liquidation_price >= entry_price and entry_price > 0:
        # Ajuste: usar fórmula alternativa
        # P_liq = entry_price - (entry_price * maintenance_margin_rate) / (leverage * 1000)
        adjustment: U32 = (entry_price * maintenance_margin_rate) // divisor
        liquidation_price = entry_price - adjustment
        # Garantir que não seja negativo (wrap-around U32)
        if liquidation_price > entry_price:
            liquidation_price = max(0, entry_price - 1)

    # Garantir bounds [0, entry_price] para posição longa
    if liquidation_price > entry_price:
        liquidation_price = entry_price

    return liquidation_price


def calc_maintenance_margin(
    entry_price: U32,
    size: U32,
    maintenance_margin_rate: U32 = 1000,  # 1% padrão
) -> U32:
    """
    Calculate maintenance margin requirement.

    Manutenção margin = entry_price * size * maintenance_margin_rate / 1000

    Args:
        entry_price: Preço de entrada (U32)
        size: Tamanho da posição (U32)
        maintenance_margin_rate: Taxa em basis points (padrão 1000 = 1%)

    Returns:
        U32: Margem de manutenção requerida
    """
    # maintenance_margin = entry_price * size * rate / 1000
    # Divisão primeiro para evitar overflow, então multiplicação

    # stage 1: entry_price * size
    product_rs: U32 = (entry_price * size) % (2**32)

    # stage 2: product * rate
    product_rs2: U32 = (product_rs * maintenance_margin_rate) % (2**32)

    # stage 3: divide by 1000
    maintenance: U32 = product_rs2 // 1000

    return maintenance


def calc_margin_utilization(
    entry_price: U32,
    size: U32,
    leverage: U32,
    mark_price: U32,
    maintenance_margin_rate: U32 = 1000,
) -> U32:
    """
    Calculate margin utilization percentage.

    Utilization = (margin_used / maintenance_margin) * 10000 (em basis points)

    Args:
        entry_price: Preço de entrada (U32)
        size: Tamanho da posição (U32)
        leverage: Alavancagem (U32)
        mark_price: Preço de mercado atual (U32)
        maintenance_margin_rate: Taxa de manutenção em basis points (padrão 1000)

    Returns:
        U32: Porcentagem de utilização de margem em basis points (0-10000)
    """
    # margin_used = entry_price * size / leverage (para posição longa opening)
    margin_used_num: U32 = (entry_price * size) % (2**32)
    if leverage > 0:
        margin_used: U32 = margin_used_num // leverage
    else:
        margin_used = 0

    # maintenance_margin = entry_price * size * maintenance_margin_rate / 1000
    maintenance_margin: U32 = calc_maintenance_margin(entry_price, size, maintenance_margin_rate)

    if maintenance_margin == 0:
        return 10000  # 100% utilization if no maintenance margin configured

    # utilization = (margin_used / maintenance_margin) * 10000 (em basis points)
    # Usar aritmética segura: (margin_used * 10000) / maintenance_margin
    if maintenance_margin > 0:
        utilization_bps: U32 = (margin_used * 10000) // maintenance_margin
    else:
        utilization_bps = 0

    # Garantir bounds
    if utilization_bps > 10000:
        utilization_bps = 10000
    if utilization_bps < 0:
        utilization_bps = 0

    return utilization_bps


def check_liquidation_risk(
    entry_price: U32,
    size: U32,
    leverage: U32,
    mark_price: U32,
    maintenance_margin_rate: U32 = 1000,
) -> Dict[str, Union[U32, bool]]:
    """
    Check if a position is at risk of liquidation.

    Verifica se uma posição está em risco de liquidação baseado no preço de mercado atual.

    Args:
        entry_price: Preço de entrada (U32)
        size: Tamanho da posição (U32)
        leverage: Alavancagem (U32)
        mark_price: Preço de mercado atual (U32)
        maintenance_margin_rate: Taxa de margem de manutenção em basis points (padrão 1000)

    Returns:
        Dict com:
        - liquidation_price: Preço de liquidação calculado (U32)
        - at_risk: Whether position is at risk (bool)
        - margin_utilization: Utilização de margem em basis points (U32)
        - distance_to_liquidation_pct: Distância em porcentagem (U32)
    """
    # Calcular preço de liquidação
    liquidation_price = calc_liquidation(entry_price, size, leverage, maintenance_margin_rate)

    # Calcular utilização de margem atual
    margin_utilization = calc_margin_utilization(entry_price, size, leverage, mark_price, maintenance_margin_rate)

    # Verificar se está em risco
    # Para posição longa: mark_price <= liquidation_price significa risco
    at_risk: bool = mark_price <= liquidation_price if liquidation_price > 0 else False

    # Distância para liquidação em porcentagem
    # distância = (entry_price - mark_price) / entry_price * 100, em basis points
    if entry_price > 0 and liquidation_price > 0:
        # Usar o preço de entrada para calcular distância da entrada até o mark price
        # Se mark_price <= liquidation_price, então a distância da entrada é >= distance_to_liquidation
        distance_bps: U32 = ((entry_price - mark_price) * 10000) // entry_price
        # Garantir bounds
        if distance_bps > 10000:
            distance_bps = 10000
        if distance_bps < 0:
            distance_bps = 0
        distance_pct: U32 = distance_bps // 100  # 0-100%
    else:
        distance_pct = 0

    return {
        "liquidation_price": liquidation_price,
        "at_risk": at_risk,
        "margin_utilization": margin_utilization,
        "distance_to_liquidation_pct": distance_pct,
    }


def main() -> None:
    """Entry point para cálculo de risco e liquidação."""
    import sys

    if len(sys.argv) < 4:
        print("Uso: qwenn-risk <comando> [argumentos]")
        print()
        print("Comandos disponíveis:")
        print("  liquidation <entry_price> <size> <leverage> [maintenance_rate]  - Calcular liquidation price")
        print("  margin <entry_price> <size> <leverage> [mark_price] [rate]      - Calcular utilization")
        print("  risk <entry_price> <size> <leverage> <mark_price> [rate]       - Verificar risco completo")
        print("  help                                                                 - Show this help message")
        sys.exit(1)

    comando = sys.argv[1]

    if comando == "liquidation":
        if len(sys.argv) < 6:
            print("Erro: liquidation requiere entry_price, size, leverage, maintenance_rate")
            sys.exit(1)
        try:
            entry_price = int(sys.argv[2])
            size = int(sys.argv[3])
            leverage = int(sys.argv[4])
            maintenance_rate = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
        except ValueError:
            print("Erro: todos os argumentos devem ser números inteiros")
            sys.exit(1)

        result = calc_liquidation(entry_price, size, leverage, maintenance_rate)
        print("=" * 60)
        print("Liquidation Price Calculation")
        print("=" * 60)
        print(f"Entry price:    {entry_price}")
        print(f"Position size:  {size}")
        print(f"Leverage:       {leverage}x")
        print(f"Maintenance:    {maintenance_rate} bps ({maintenance_rate/100:.1f}%)")
        print(f"Liquidation price: {result} USD")
        print()
        if result > 0:
            print(f"✓ Liquidation price calculado com sucesso")
            print(f"  Para posição longa: liquidation ocorre quando mark_price <= {result}")
        else:
            print("⚠️  Erro no cálculo - condições de mercado extremas")

    elif comando == "margin":
        if len(sys.argv) < 7:
            print("Erro: margin requiere entry_price, size, leverage, mark_price, maintenance_rate")
            sys.exit(1)
        try:
            entry_price = int(sys.argv[2])
            size = int(sys.argv[3])
            leverage = int(sys.argv[4])
            mark_price = int(sys.argv[5])
            maintenance_rate = int(sys.argv[6]) if len(sys.argv) > 6 else 1000
        except ValueError:
            print("Erro: todos os argumentos devem ser números inteiros")
            sys.exit(1)

        utilization = calc_margin_utilization(entry_price, size, leverage, mark_price, maintenance_rate)
        maintenance_margin = calc_maintenance_margin(entry_price, size, maintenance_rate)

        print("=" * 60)
        print("Margin Utilization Calculation")
        print("=" * 60)
        print(f"Entry price:      {entry_price}")
        print(f"Position size:    {size}")
        print(f"Leverage:         {leverage}x")
        print(f"Mark price:       {mark_price}")
        print(f"Maintenance rate: {maintenance_rate} bps ({maintenance_rate/100:.1f}%)")
        print()
        print(f"Margin used:      {utilization // 100}% (aproximado)")
        print(f"Maintenance req:  {maintenance_margin} USD")
        print(f"Utilization:      {utilization} bps ({utilization/100:.1f}%)")
        print()
        if utilization >= 8000:  # >= 80%
            print("⚠️  ALERTA: Utilização alta de margem (>80%)")
        elif utilization >= 5000:  # >= 50%
            print("⚠️  Atenção: Utilização média de margem (50-80%)")
        else:
            print("✅  OK: Utilização de margem baixa (<50%)")

    elif comando == "risk":
        if len(sys.argv) < 7:
            print("Erro: risk requiere entry_price, size, leverage, mark_price, maintenance_rate")
            sys.exit(1)
        try:
            entry_price = int(sys.argv[2])
            size = int(sys.argv[3])
            leverage = int(sys.argv[4])
            mark_price = int(sys.argv[5])
            maintenance_rate = int(sys.argv[6]) if len(sys.argv) > 6 else 1000
        except ValueError:
            print("Erro: todos os argumentos devem ser números inteiros")
            sys.exit(1)

        result = check_liquidation_risk(entry_price, size, leverage, mark_price, maintenance_rate)

        print("=" * 60)
        print("Risk Assessment")
        print("=" * 60)
        print(f"Entry price:           {entry_price}")
        print(f"Position size:         {size}")
        print(f"Leverage:              {leverage}x")
        print(f"Mark price:            {mark_price}")
        print(f"Maintenance rate:      {maintenance_rate} bps")
        print()
        print(f"Liquidation price:     {result['liquidation_price']}")
        print(f"At risk of liquidation:{' ✅ SIM' if result['at_risk'] else ' ✅ NÃO'}")
        print(f"Margin utilization:    {result['margin_utilization']} bps ({result['margin_utilization']/100:.1f}%)")
        print(f"Distance to liquidation: {result['distance_to_liquidation_pct']}%")
        print()
        if result['at_risk']:
            print("🚨  POSIÇÃO EM RISCO DE LIQUIDAÇÃO!")
            print(f"   Preço de mercado ({mark_price}) <= Preço de liquidação ({result['liquidation_price']})")
        else:
            print("✅  Posicao segura - longe do preco de liquidacao")
            print(f"   Mercado ({mark_price}) ainda acima de liquidacao ({result['liquidation_price']})")

    elif comando == "help":
        print("""
Qwenn-Risk Commands:

  liquidation <entry_price> <size> <leverage> [maintenance_rate]
    Calculate liquidation price for a position.
    Example: qwenn-risk liquidation 3000 2 10 1000
    Example: qwenn-risk liquidation 5000 1 5 1000

  margin <entry_price> <size> <leverage> <mark_price> [maintenance_rate]
    Calculate margin utilization percentage.
    Example: qwenn-risk margin 3000 2 10 2900 1000
    Example: qwenn-risk margin 5000 1 3 4800 1000

  risk <entry_price> <size> <leverage> <mark_price> [maintenance_rate]
    Full risk assessment (liquidation price + utilization + at_risk flag).
    Example: qwenn-risk risk 3000 2 10 2900 1000
    Example: qwenn-risk risk 5000 1 3 4500 1000

  help
    Show this help message.

Notes:
- All prices are in U32 (mod 2^32), suitable for cryptocurrency prices in USD
- Calculations are exact, no floating-point errors
- Positions with high utilization (>8000 bps = >80%) carry elevated liquidation risk
- Maintenance margin rate is in basis points (1000 = 1%)
- Distance to liquidation is calculated from entry price to mark price
""")

    else:
        print(f"Comando desconhecido: {comando}")
        print("Use 'qwenn-risk help' para ver comandos disponíveis.")
        sys.exit(1)


if __name__ == "__main__":
    main()