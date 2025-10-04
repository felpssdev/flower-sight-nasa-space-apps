# 📊 Fontes de Dados - BloomWatch

Documentação completa sobre as fontes de dados do BloomWatch.

---

## 🎯 **Status Atual: DADOS SINTÉTICOS (Demo)**

### Por que dados sintéticos?

Para o **NASA Space Apps Challenge**, estamos usando dados sintéticos **altamente realistas** porque:

1. ✅ **Demonstração funcional imediata** - Não depende de autenticação/credenciais
2. ✅ **Reprodutível** - Mesmos resultados sempre
3. ✅ **Baseado em padrões reais** - Calibrado com dados USDA e UC Davis
4. ✅ **Permite treinar modelos rapidamente** - Sem rate limits de APIs

### O que os dados sintéticos simulam?

**NDVI (Normalized Difference Vegetation Index):**
- Padrão sazonal realista:
  - Inverno: NDVI baixo (0.25-0.35) - árvores dormentes
  - Pré-floração: Crescimento gradual
  - Floração: Pico (0.70-0.80)
  - Verão: Alto e estável (desenvolvimento de frutos)
  - Outono: Declínio gradual
- Ruído realista (±0.02-0.03)
- Variação por cultura (amêndoas, maçãs, cerejas)

**Temperatura:**
- Padrão sinusoidal baseado em latitude
- Variação diária (±2.5°C)
- Eventos extremos (5% de chance de ondas de calor/frio)

**Precipitação:**
- Distribuição exponencial
- Sazonalidade (mais chuva inverno/primavera)
- 70% dos dias sem chuva (realista)

**Mudança Climática:**
- Floração 2 dias mais cedo por ano (tendência observada)

### Gerador de Dados

Arquivo: `backend/data_generator.py`

```python
generator = BloomDataGenerator(crop_type='almond', seed=42)
data, target = generator.generate_dataset(n_years=5, start_year=2020)
```

**Padrões de Floração (baseados em dados reais):**

| Cultura | Dia do Ano | Mês | Região Real |
|---------|------------|-----|-------------|
| 🌰 Amêndoas | 50 | Meados Fev | Central Valley, CA |
| 🍎 Maçãs | 110 | Meados Abr | Yakima Valley, WA |
| 🍒 Cerejas | 85 | Final Mar | Traverse City, MI |

---

## 🛰️ **DADOS REAIS DA NASA (Produção)**

### Opção 1: Google Earth Engine

**API:** https://earthengine.google.com/

**Datasets disponíveis:**

#### MODIS (Moderate Resolution Imaging Spectroradiometer)
- **Dataset:** `MODIS/006/MOD13Q1`
- **Resolução:** 250m
- **Frequência:** 16 dias
- **Índices:** NDVI, EVI
- **Período:** 2000 - presente
- **Gratuito:** ✅ Sim

#### Landsat 8/9
- **Dataset:** `LANDSAT/LC08/C02/T1_L2`
- **Resolução:** 30m
- **Frequência:** 16 dias
- **Bandas:** 
  - B3 (Green)
  - B4 (Red)
  - B5 (NIR)
- **Índices calculados:** NDVI, GNDVI, SAVI, EVI
- **Período:** 2013 - presente
- **Gratuito:** ✅ Sim

**Setup:**

```bash
# 1. Instalar
pip install earthengine-api

# 2. Autenticar
earthengine authenticate

# 3. Usar no código
from nasa_data_fetcher import fetch_nasa_data

data = fetch_nasa_data(
    lat=36.7468,
    lon=-119.7726,
    crop_type='almond',
    use_earth_engine=True  # ← Ativa Earth Engine
)
```

**Vantagens:**
- ✅ Resolução espacial excelente (30-250m)
- ✅ Histórico completo desde 2000
- ✅ Processamento na nuvem (Google)
- ✅ Gratuito
- ✅ Dados de múltiplos satélites

**Desvantagens:**
- ❌ Requer autenticação Google
- ❌ Rate limits (queries por dia)
- ❌ Latência maior (processamento remoto)

---

### Opção 2: NASA POWER API

**API:** https://power.larc.nasa.gov/

**Dados Climáticos:**
- Temperatura (T2M, T2M_MIN, T2M_MAX)
- Precipitação (PRECTOTCORR)
- Radiação solar
- Umidade relativa
- Velocidade do vento

**Especificações:**
- **Resolução:** 0.5° × 0.625° (~50km no equador)
- **Frequência:** Diária
- **Período:** 1981 - presente (tempo quase real)
- **Latência:** 3-7 dias
- **Formato:** JSON, CSV
- **Gratuito:** ✅ Sim (sem autenticação!)

**Exemplo de Uso:**

```python
from nasa_data_fetcher import NASADataFetcher

fetcher = NASADataFetcher()
climate_data = fetcher.fetch_climate_data(
    lat=36.7468,
    lon=-119.7726,
    days=90
)
```

**Já implementado e funciona agora!** ✅

**Vantagens:**
- ✅ Não requer autenticação
- ✅ Dados climáticos precisos
- ✅ API rápida e confiável
- ✅ Cobertura global
- ✅ Gratuito ilimitado

**Desvantagens:**
- ❌ Resolução espacial menor
- ❌ Não tem NDVI (apenas clima)

---

### Opção 3: NASA AppEEARS

**URL:** https://appeears.earthdatacloud.nasa.gov/

**Interface Web + API para:**
- MODIS
- VIIRS
- Landsat
- SMAP (umidade do solo)

**Vantagens:**
- ✅ Download em massa
- ✅ Múltiplas regiões
- ✅ Preprocessamento automático

**Desvantagens:**
- ❌ Requer conta NASA Earthdata
- ❌ Processamento assíncrono (minutos/horas)

---

## 🔄 **Como Migrar para Dados Reais**

### Passo 1: Instalar Dependências

```bash
cd backend

# Para Earth Engine
pip install earthengine-api geemap

# Autenticar
earthengine authenticate
```

### Passo 2: Atualizar `main.py`

**Opção A: Earth Engine + NASA POWER (Recomendado)**

```python
# Em main.py, substituir fetch_ndvi_data():

from nasa_data_fetcher import fetch_nasa_data

def fetch_ndvi_data(lat: float, lon: float, crop_type: str, days: int = 90):
    """Busca dados REAIS da NASA"""
    return fetch_nasa_data(
        lat=lat,
        lon=lon,
        crop_type=crop_type,
        days=days,
        use_earth_engine=True  # Dados reais de satélite
    )
```

**Opção B: Apenas NASA POWER (sem autenticação)**

```python
from nasa_data_fetcher import fetch_nasa_data

def fetch_ndvi_data(lat: float, lon: float, crop_type: str, days: int = 90):
    """NASA POWER (clima real) + NDVI sintético"""
    return fetch_nasa_data(
        lat=lat,
        lon=lon,
        crop_type=crop_type,
        days=days,
        use_earth_engine=False  # Apenas clima real
    )
```

### Passo 3: Testar

```bash
# Iniciar API
uvicorn main:app --reload

# Testar
curl http://localhost:8000/api/predict/test/almond
```

---

## 📈 **Comparação de Fontes**

| Fonte | NDVI | Clima | Resolução | Autenticação | Custo | Status |
|-------|------|-------|-----------|--------------|-------|--------|
| **Sintéticos** | ✅ | ✅ | N/A | ❌ Não | Grátis | ✅ Implementado |
| **NASA POWER** | ❌ | ✅ | 50km | ❌ Não | Grátis | ✅ Implementado |
| **Earth Engine (MODIS)** | ✅ | ❌ | 250m | ✅ Sim | Grátis | ✅ Implementado |
| **Earth Engine (Landsat)** | ✅ | ❌ | 30m | ✅ Sim | Grátis | ✅ Implementado |
| **AppEEARS** | ✅ | ✅ | 30-250m | ✅ Sim | Grátis | ⚠️ Manual |

---

## 🎯 **Recomendação para Produção**

### Setup Ideal:

```python
# Combinação de fontes
data_fetcher = NASADataFetcher(use_earth_engine=True)

data = data_fetcher.fetch_complete_data(
    lat=36.7468,
    lon=-119.7726,
    crop_type='almond',
    days=90
)

# Resultado:
# - NDVI, GNDVI, SAVI → Landsat (30m, Earth Engine)
# - Temperatura, Precipitação → NASA POWER API
# - Fallback automático para sintéticos se APIs falharem
```

### Estratégia de Cache:

Para economizar chamadas à API:

```python
# 1. Cache em banco de dados
# 2. Atualizar apenas novos dados
# 3. TTL: 16 dias (frequência MODIS/Landsat)

# Exemplo: Redis
redis.setex(f'ndvi:{lat}:{lon}', ttl=16*24*3600, data)
```

---

## 🔍 **Validação dos Dados**

### Verificar Qualidade:

```python
# Checar cobertura de nuvens (Landsat)
if cloud_cover > 20:
    print("⚠️ Alta cobertura de nuvens, usar MODIS")

# Checar valores válidos
assert 0 <= ndvi <= 1, "NDVI fora do range válido"
assert -30 <= temp <= 50, "Temperatura fora do range esperado"

# Checar gaps temporais
gaps = data['date'].diff() > pd.Timedelta('7 days')
if gaps.any():
    print("⚠️ Gaps nos dados, interpolar")
```

---

## 📚 **Referências**

### APIs NASA:
- **Earth Engine:** https://developers.google.com/earth-engine
- **POWER API:** https://power.larc.nasa.gov/docs/
- **Earthdata:** https://earthdata.nasa.gov/

### Datasets:
- **MODIS:** https://modis.gsfc.nasa.gov/
- **Landsat:** https://landsat.gsfc.nasa.gov/
- **VIIRS:** https://www.earthdata.nasa.gov/sensors/viirs

### Tutoriais:
- **Earth Engine Python:** https://geemap.org/
- **POWER API Examples:** https://power.larc.nasa.gov/docs/tutorials/

---

## ❓ **FAQ**

**Q: Preciso pagar para usar APIs NASA?**  
A: Não! Todas as APIs NASA são **gratuitas**.

**Q: Quanto tempo demora para obter dados reais?**  
A: NASA POWER: ~2-5 segundos | Earth Engine: ~5-15 segundos

**Q: Os dados sintéticos são confiáveis?**  
A: Para demonstração sim! Foram calibrados com dados reais da USDA e UC Davis.

**Q: Posso misturar dados sintéticos e reais?**  
A: Sim! O código tem fallback automático se APIs falharem.

**Q: Qual a melhor fonte para produção?**  
A: **Earth Engine (Landsat) + NASA POWER** = melhor combinação.

---

**✅ Arquivo `nasa_data_fetcher.py` está pronto para uso!**

Para testar:
```bash
cd backend
python nasa_data_fetcher.py
```

