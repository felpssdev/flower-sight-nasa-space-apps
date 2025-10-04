# 🌸 BloomWatch Backend

Backend completo com Machine Learning para predição de floração usando dados de satélite NASA.

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Gerar Dados e Treinar Modelos

```bash
python train_models.py
```

Este comando irá:
- Gerar dados sintéticos realistas para 3 culturas (almond, apple, cherry)
- Treinar ensemble de modelos (LSTM + Random Forest + ANN)
- Salvar modelos treinados em `models/`
- Exibir métricas de validação (MAE, RMSE, R²)

**Tempo estimado:** 10-15 minutos

### 3. Iniciar API

```bash
uvicorn main:app --reload
```

A API estará disponível em: http://localhost:8000

### 4. Testar API

```bash
# Em outro terminal
python test_api.py
```

## 📁 Estrutura de Arquivos

```
backend/
├── main.py                  # FastAPI application
├── ml_pipeline.py           # Ensemble ML (LSTM + RF + ANN)
├── data_generator.py        # Gerador de dados sintéticos
├── train_models.py          # Script de treinamento
├── test_api.py              # Suite de testes
├── requirements.txt         # Dependências Python
├── models/                  # Modelos treinados (gerado)
│   ├── almond/
│   ├── apple/
│   └── cherry/
└── data/                    # Dados de treinamento (gerado)
```

## 🔌 API Endpoints

### GET `/`
Informações da API

```bash
curl http://localhost:8000/
```

### GET `/health`
Health check

```bash
curl http://localhost:8000/health
```

### GET `/api/crops`
Lista culturas disponíveis

```bash
curl http://localhost:8000/api/crops
```

### POST `/api/predict`
Predição de floração

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 36.7468,
    "lon": -119.7726,
    "crop_type": "almond",
    "farm_name": "Central Valley Farm"
  }'
```

**Response:**
```json
{
  "farm_name": "Central Valley Farm",
  "crop_type": "almond",
  "location": {"lat": 36.7468, "lon": -119.7726},
  "predicted_bloom_date": "2025-02-15",
  "confidence_low": "2025-02-12",
  "confidence_high": "2025-02-18",
  "days_until_bloom": 30,
  "agreement_score": 0.92,
  "recommendations": [...],
  "ndvi_trend": [...],
  "individual_predictions": {
    "lstm": 29.5,
    "rf": 31.2,
    "ann": 28.8
  }
}
```

### GET `/api/predict/test/{crop_type}`
Teste rápido com localização padrão

```bash
curl http://localhost:8000/api/predict/test/almond
```

## 🧠 Arquitetura ML

### Ensemble de 3 Modelos

1. **LSTM (45% peso)** - Série temporal
   - Sequências de 60 dias
   - 2 camadas LSTM (128, 64 units)
   - Dropout 0.3

2. **Random Forest (35% peso)** - Robustez
   - 200 árvores
   - Max depth 20
   - Feature importance

3. **ANN Feedforward (20% peso)** - Não-linearidades
   - Layers: [128, 64, 32]
   - Dropout 0.3

### Features Utilizadas

**Índices Espectrais:**
- NDVI (Normalized Difference Vegetation Index)
- GNDVI (Green NDVI)
- SAVI (Soil Adjusted Vegetation Index)

**Features Climáticas:**
- Temperatura média
- GDD (Growing Degree Days)
- Precipitação acumulada

**Features Temporais:**
- Estatísticas: média, std, max, min, percentis
- Taxa de mudança (derivadas)
- Tendência linear
- Janelas móveis (7, 14, 30 dias)

### Métricas de Performance

**Targets:**
- MAE < 4 dias
- RMSE < 5 dias
- R² > 0.85

## 🗄️ Dados

### Fontes (Produção)
- **MODIS**: NDVI, EVI (250m, 16 dias)
- **Landsat 8/9**: Bandas multiespectrais (30m, 16 dias)
- **NASA POWER**: Dados climáticos

### Simulação (Demo)
Para fins de demonstração, usamos dados sintéticos realistas baseados em:
- Padrões de floração reais (USDA, UC Davis)
- Sazonalidade climática
- Variabilidade interanual

## 🔧 Desenvolvimento

### Adicionar Nova Cultura

1. Adicionar padrão em `data_generator.py`:

```python
CROP_PATTERNS = {
    'new_crop': {
        'peak_doy': 120,
        'duration': 12,
        'ndvi_peak': 0.80,
        # ...
    }
}
```

2. Treinar modelo:

```bash
python train_models.py
```

3. Atualizar endpoint `/api/crops` em `main.py`

### Integrar Earth Engine

Descomentar em `requirements.txt`:
```
earthengine-api==0.1.379
geemap==0.29.5
```

Atualizar função `fetch_ndvi_data()` em `main.py`:

```python
import ee
ee.Initialize()

def fetch_ndvi_data(lat, lon, crop_type, days=90):
    point = ee.Geometry.Point([lon, lat])
    
    # MODIS NDVI
    modis = ee.ImageCollection('MODIS/006/MOD13Q1') \
        .filterDate('2024-01-01', '2025-01-01') \
        .filterBounds(point)
    
    # Extrair valores...
```

## 📊 Testes

### Executar Todos os Testes

```bash
python test_api.py
```

### Teste Manual

```bash
# Terminal 1: API
uvicorn main:app --reload

# Terminal 2: Teste
curl http://localhost:8000/api/predict/test/almond
```

## 🐛 Troubleshooting

### Erro: "Modelo não encontrado"
**Solução:** Execute `python train_models.py` primeiro

### Erro: ImportError tensorflow
**Solução:** 
```bash
pip install tensorflow==2.15.0
# ou para Apple Silicon:
pip install tensorflow-macos==2.15.0
```

### API não inicia
**Solução:** Verifique porta 8000 disponível
```bash
lsof -i :8000
# ou use outra porta:
uvicorn main:app --port 8001
```

## 📝 Licença

NASA Space Apps Challenge 2025 - BloomWatch Team

## 🙏 Créditos

- **Dados**: NASA Earth Observing System Data and Information System (EOSDIS)
- **MODIS**: NASA/USGS
- **Landsat**: USGS/NASA
- **ML Framework**: TensorFlow, scikit-learn

