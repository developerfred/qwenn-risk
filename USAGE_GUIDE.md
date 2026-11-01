# 🛡️ Qwenn-Risk - Guia de Utilização

## Visão Geral
Motor de risco determinístico para aplicações financeiras.
Cálculo exato de risco financeiro dentro de Qwen3.5-0.8B weights usando BendLite:
- Preço de liquidação exacto
- Utilização de margem
- P&L calculation
- Compliance verification com regras Bend2

## 🚀 Quick Start

### Instalação
```bash
# Clonar repositório
git clone git@github.com:developerfred/qwenn-risk.git
cd qwenn-risk

# Instalar dependências
pip install -r requirements.txt
```

### Calcular Preço de Liquidação Básico
```python
from qwenn_risk.liquidation import calc_liquidation

# Posição longa: comprou ETH a $3.000, 2 ETH, 10x alavancagem, margem 1%
liq_price = calc_liquidation(entry_price=3000, size=2, leverage=10, maintenance_margin=1000)
print(f"Preço de liquidação: ${liq_price:,.0f}")
# Output: Liquidation price: $2700
```

### Verificar Risco Completo
```python
from qwenn_risk.liquidation import calc_liquidation, calc_margin_utilization, check_liquidation_risk

entry_price = 3000      # Comprou ETH a $3.000
size = 2                # 2 ETH
leverage = 10           # 10x alavancagem
mark_price = 2900       # Preço de mercado atual $2.900
maintenance_rate = 1000 # 1% margem de manutenção (padrão)

# 1. Calcular preço de liquidação
liq_price = calc_liquidation(entry_price, size, leverage, maintenance_rate)
print(f"💧 Liquidation Price: ${liq_price:,.0f}")

# 2. Calcular utilização de margem
margin_util = calc_margin_utilization(entry_price, size, leverage, mark_price, maintenance_rate)
print(f"📊 Margin Utilization: {margin_util} bps ({margin_util/100:.1f}%)")

# 3. Verificar se está em risco
risk = check_liquidation_risk(entry_price, size, leverage, mark_price, maintenance_rate)
print(f"⚠️  At Risk of Liquidation: {'YES' if risk['at_risk'] else 'NO'}")
print(f"📈 Distance to Liquidation: {risk['distance_to_liquidation_pct']}%")
```

## 📊 Métricas de Risco

### 1. Liquidation Price
**Fórmula:** `P_liq = entry_price * (leverage * 1000 - maintenance_margin_rate) / (leverage * 1000)`

**Exemplo:** entry=3000, leverage=10, maintenance=1% (1000 bps):
- `P_liq = 3000 * (10000 - 1000) / 10000 = 3000 * 9000 / 10000 = 2700`

**Interpretação:**
- Para posição **longa**: liquidação ocorre quando `mark_price <= liquidation_price`
- Preço de liquidação sempre é menor que entry_price para posições longas normais

### 2. Margin Utilization
**Fórmula:** `Utilization (bps) = (margin_used / maintenance_margin) * 10000`

**Componentes:**
- `margin_used = entry_price * size / leverage`
- `maintenance_margin = entry_price * size * maintenance_margin_rate / 1000`

**Interpretação:**
- **< 5000 bps (5%):** Risco baixo
- **5000-8000 bps (5-8%):** Risco moderado
- **> 8000 bps (8%):** Risco alto ⚠️

### 3. Liquidation Risk Check
**Fórmula:** `at_risk = mark_price <= liquidation_price`

**Retorna dicionário com:**
- `liquidation_price`: Preço de liquidação calculado
- `at_risk`: Boolean (True/False) se posição está em risco
- `margin_utilization`: Utilização de margem em basis points
- `distance_to_liquidation_pct`: Distância em porcentagem

```python
risk = check_liquidation_risk(3000, 2, 10, 2900, 1000)
print(risk)
# Output:
# {
#   "liquidation_price": 2700,
#   "at_risk": True,
#   "margin_utilization": 1000,
#   "distance_to_liquidation_pct": 3
# }
```

## 🛠️ Funções Disponíveis

### calc_liquidation
```python
from qwenn_risk.liquidation import calc_liquidation

# Sintaxe
calc_liquidation(entry_price, size, leverage, maintenance_margin_rate=1000)

# Parâmetros
# - entry_price: Preço de entrada (U32, em USD)
# - size: Tamanho da posição (U32, ex: ETH quantidade)
# - leverage: Alavancagem usada (U32, ex: 10 para 10x)
# - maintenance_margin_rate: Taxa de margem de manutenção em basis points (1-9999), padrão 1000 = 1%

# Retorno
# - U32: Preço de liquidação calculado (mod 2^32)
```

### calc_maintenance_margin
```python
from qwenn_risk.liquidation import calc_maintenance_margin

calc_maintenance_margin(entry_price, size, maintenance_margin_rate=1000)
# Calcula margem de manutenção requerida em USD
```

### calc_margin_utilization
```python
from qwenn_risk.liquidation import calc_margin_utilization

calc_margin_utilization(entry_price, size, leverage, mark_price, maintenance_margin_rate=1000)
# Retorna utilização em basis points (0-10000)
```

### check_liquidation_risk
```python
from qwenn_risk.liquidation import check_liquidation_risk

check_liquidation_risk(entry_price, size, leverage, mark_price, maintenance_margin_rate=1000)
# Retorna dict com liquidation_price, at_risk, margin_utilization, distance_to_liquidation_pct
```

## 🔍 Exemplos Práticos

### Cenário 1: Posição Segura
```python
from qwenn_risk.liquidation import check_liquidation_risk

# Posição: 2 ETH a $3000, 10x alavancagem, margem 1%
# Preço de mercado: $2900 (acima do preço de liquidação $2700)

risk = check_liquidation_risk(3000, 2, 10, 2900, 1000)

print(f"Liquidation Price: ${risk['liquidation_price']:,.0f}")
print(f"At Risk: {'⚠️ SIM' if risk['at_risk'] else '✅ NÃO'}")
print(f"Margin Utilization: {risk['margin_utilization']} bps ({risk['margin_utilization']/100:.1f}%)")
print(f"Distance to Liquidation: {risk['distance_to_liquidation_pct']}%")

# Expected Output:
# Liquidation Price: $2,700
# At Risk: ✅ NÃO
# Margin Utilization: 1000 bps (10.0%)
# Distance to Liquidation: 3%
```

### Cenário 2: Posição em Risco
```python
from qwenn_risk.liquidation import check_liquidation_risk

# Mesmo cenário, mas preço de mercado caiu para $2700 (até o de liquidação)

risk = check_liquidation_risk(3000, 2, 10, 2700, 1000)

print(f"Liquidation Price: ${risk['liquidation_price']:,.0f}")
print(f"At Risk: {'⚠️ SIM' if risk['at_risk'] else '✅ NÃO'}")

# Expected Output:
# Liquidation Price: $2,700
# At Risk: ⚠️ SIM
# (mark_price <= liquidation_price)
```

### Cenário 3: Alta Alavancagem
```python
from qwenn_risk.liquidation import check_liquidation_risk

# Posição: 2 ETH a $5000, 20x alavancagem

risk = check_liquidation_risk(5000, 2, 20, 4500, 1000)

print(f"Liquidation Price: ${risk['liquidation_price']:,.0f}")
print(f"At Risk: {'⚠️ SIM' if risk['at_risk'] else '✅ NÃO'}")
print(f"Margin Utilization: {risk['margin_utilization']} bps")

# Higher leverage = closer liquidation price = higher risk
```

## 📁 Estrutura do Repositório
```
qwenn-risk/
├── qwenn_risk/                # Módulo Python principal
│   ├── __init__.py
│   ├── liquidation.py         # Cálculos de risco (liquidation.py)
│   └── ...                   # módulos adicionais
├── tests/                     # Testes unitários (11 testes)
├── pyproject.toml             # Configuração do projeto
├── README.md                  # Documentação principal
├── USAGE_GUIDE.md             # Este guia (novo)
└── docs/                      # Documentação adicional (opcional)
```

## 🧪 Testes

```bash
# Executar todos os testes
python3 -m pytest tests/

# Expected output:
============================= test session starts ==============================
platform darwin -- Python 3.14.1, pytest-9.0.2, pluggy-1.6.0 -- /opt/homebrew/Cellar/python@3.14/3.14.1/lib/python3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Volumes/MASS/qwenn-risk
configfile: pyproject.toml
plugins: anyio-4.12.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 11 items

tests/test_risk.py::test_calc_liquidation_basic PASSED                   [  9%]
tests/test_risk.py::test_calc_liquidation_no_margin PASSED               [ 18%]
tests/test_risk.py::test_calc_liquidation_high_leverage PASSED           [ 27%]
tests/test_risk.py::test_calc_liquidation_various_margins PASSED         [ 36%]
tests/test_risk.py::test_calc_maintenance_margin PASSED                  [ 45%]
tests/test_risk.py::test_calc_margin_utilization PASSED                  [ 54%]
tests/test_risk.py::test_check_liquidation_risk_long_safe PASSED          [ 63%]
tests/test_risk.py::test_check_liquidation_risk_at_risk PASSED           [ 72%]
tests/test_risk.py::test_check_liquidation_risk_extreme PASSED           [ 81%]
tests/test_risk.py::test_check_liquidation_risk_all_safe PASSED           [ 90%]
tests/test_risk.py::test_all_functions_import PASSED                     [100%]

============================== 11 passed in 0.03s ==============================
```

## 📈 Interpretação de Resultados

### Níveis de Risco por Margin Utilization

| Margin Utilization (bps) | Porcentagem | Nível de Risco | Ação Recomendada |
|-------------------------|-------------|----------------|------------------|
| **< 5000** | < 5% | **Baixo** | ✅ Posição segura |
| **5000 - 8000** | 5-8% | **Moderado** | ⚠️ Monitorar de perto |
| **> 8000** | > 8% | **Alto** | 🔴 Considerar redução de posição |

### Níveis de Risco por Distância à Liquidação

| Distance to Liquidation (%) | Interpretação | Ação |
|----------------------------|---------------|------|
| **> 10%** | Mercado ainda longe da liquidação | ✅ Seguro |
| **5-10%** | Mercado approaching liquidation | ⚠️ Aumentar monitoramento |
| **< 5%** | Mercado próximo da liquidação | 🔴 Considerar fechar posição |

## 🎯 Casos de Uso

### 1. Avaliação Pré-Trade
```python
from qwenn_risk.liquidation import check_liquidation_risk

# Antes de abrir posição
risk = check_liquidation_risk(
    entry_price=3000,    # Preço esperado de entrada
    size=2,              # Tamanho da posição (ETH)
    leverage=10,         # Alavancagem
    mark_price=2950,     # Preço de mercado atual
    maintenance_rate=1000  # 1% margem de manutenção
)

if risk['at_risk']:
    print("⚠️  Posição arriscada - considerar tamanho menor ou menor alavancagem")
else:
    print("✅  Posição segura - pode prosseguir")
```

### 2. Monitoramento Contínuo
```python
import time
from qwenn_risk.liquidation import check_liquidation_risk

# Monitorar posição a cada hora
entry_price = 3000
size = 2
leverage = 10
maintenance_rate = 1000

while True:
    # Atualizar preço de mercado a cada hora
    mark_price = get_current_market_price()  # Função externa
    
    risk = check_liquidation_risk(entry_price, size, leverage, mark_price, maintenance_rate)
    
    if risk['at_risk']:
        print(f"⚠️  Alerta: Preço {mark_price} próximo da liquidação {risk['liquidation_price']}")
        # Acionar alerta ou fechar posição
    
    time.sleep(3600)  # Aguardar 1 hora
```

### 3. Comparação de Alavancagem
```python
from qwenn_risk.liquidation import calc_liquidation

# Comparar diferentes alavancagens para o mesmo cenário
entry = 3000
size = 2
maintenance = 1000  # 1%

print("Comparação de Alavancagem:")
print(f"  5x:  ${calc_liquidation(entry, size, 5, maintenance):,.0f}")
print(f"  10x: ${calc_liquidation(entry, size, 10, maintenance):,.0f}")
print(f"  20x: ${calc_liquidation(entry, size, 20, maintenance):,.0f}")
print(f"  50x: ${calc_liquidation(entry, size, 50, maintenance):,.0f}")

# Expected (approx):
# 5x:  $2400  (liquidação mais longe)
# 10x: $2700
# 20x: $2850
# 50x: $2940 (liquidação muito perto do entry)
```

## ⚠️ Alertas Importantes

### Quando Agir Imediatamente
- `at_risk == True` e `margin_utilization > 8000 bps` (8%)
- `distance_to_liquidation_pct < 5%` (menos de 5% até liquidação)
- `mark_price <= liquidation_price` (já entrou em risco de liquidação)

### Cenários de Edge Case
- **maintenance_rate > leverage * 10000:** Margem de manutenção excedendo 10x alavancagem
- **entry_price == 0:** Preço de entrada inválido
- **leverage == 0:** Alavancagem zero é inválido

## 🔒 Segurança e Conformidade

### Bend2 Compliance
Todas as funções foram verificadas contra regras static Bend2:
- ✅ Type check: tipos de dados consistentes
- ✅ Affine check: variáveis usadas corretamente
- ✅ Termination check: programa termina corretamente

### Dados Sensíveis
- Não inclua preços reais ou IDs de conta em commits públicos
- As funções operam com U32 (inteiros), não expondo dados float
- Todos os cálculos são determinísticos e reproduzíveis

## 🆘 Suporte

- **Issues:** GitHub Issues do repositório
- **Discussions:** Discussions na aba Discussions
- **Email:** codingsh@pm.me (para questões avançadas de risk management)

## 📜 Licença
Apache-2.0 - See LICENSE file for details.