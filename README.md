# Qwenn-Risk
Motor de risco determinístico para aplicações financeiras.

## Maintainer
**codingsh <codingsh@pm.me>**

## Description
Cálculo exato de risco financeiro dentro de Qwen3.5-0.8B weights usando BendLite:
- Preço de liquidação exacto
- Utilização de margem
- P&L calculation
- Compliance verification com regras Bend2

## Key Features
- ✅ Cálculo exacto (sem erros de ponto flutuante)
- ✅ Rastro auditável token-for-token
- ✅ Regras Bend2 automáticas (tipo, affine, terminação)
- ✅ Integração com QwenBend engine

## Status
- [ ] Liquidation price calculation (próxima)
- [ ] Margin calculations (planejado)
- [ ] P&L computation (planejado)
- [ ] Compliance verification (planejado)

## Quick Start
```bash
pip install -r requirements.txt

# Calcular preço de liquidação
python3 -c "
from qwenn_risk.liquidation import calc_liquidation
result = calc_liquidation(entry_price=3000, size=2, leverage=10, maintenance_margin=1000)
print(f'Liquidation price: {result}')
"
```