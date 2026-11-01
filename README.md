# Qwenn-Risk

Deterministic risk engine for financial applications.

## Maintainer
**codingsh <codingsh@pm.me>**

## Description
Exact financial risk calculation within Qwen3.5-0.8B weights using BendLite:
- Exact liquidation price
- Margin utilization
- P&L calculation
- Bend2 compliance verification

### Key Features
- ✅ Exact computation (no floating point errors)
- ✅ Token-for-token audit trail
- ✅ Automatic Bend2 rules (type, affine, termination)
- ✅ QwenBend engine integration

### Risk Metrics
- **Liquidation Price**: Exact calculation using U32 arithmetic
- **Margin Utilization**: Precise bps (basis points) calculation
- **P&L Calculation**: Deterministic profit and loss
- **Compliance**: Bend2 rules verification

## Status
- [x] Liquidation price calculation (concluído)
- [x] Margin calculations (concluído)
- [x] P&L computation (concluído)
- [x] Compliance verification (concluído)
- [ ] Clanker integration (planejado)

## Tests
```
$ cd /Volumes/MASS/qwenn-risk
$ python3 -m pytest tests/
# 11 tests passing
```

## Architecture
```
Qwenn-Risk
├── qwenn_risk/             # Risk engine modules
├── liquidation.py          # Liquidation calculations
├── tests/                  # Test suite
├── pyproject.toml         # Project config
└── README.md              # This file
```

## Quick Start
```bash
# Install
pip install -r requirements.txt

# Calculate liquidation price
python3 -c "
from qwenn_risk.liquidation import calc_liquidation
result = calc_liquidation(entry_price=3000, size=2, leverage=10, maintenance_margin=1000)
print(f'Liquidation price: {result}')
"
```

## Integration with Clanker
This risk engine can be integrated with Clanker token launcher for:
- Pre-deployment risk assessment
- Ongoing position monitoring
- AI droid risk management