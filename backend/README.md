# 🌸 BloomWatch Backend

Backend completo com Machine Learning para predição de floração usando dados de satélite NASA.

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciais NASA

```bash
export NASA_USERNAME='seu_usuario'
export NASA_PASSWORD='sua_senha'
```

Registre-se grátis em: https://urs.earthdata.nasa.gov/users/new

### 3. Treinar Modelos com Dados NASA

```bash
python train_models.py
```

Este comando irá:
- Buscar dados REAIS da NASA (MODIS + POWER API)
- Coletar dados de múltiplas localizações
- Treinar ensemble de modelos (LSTM + Random Forest + ANN)
- Salvar modelos treinados em `models/`
- Exibir métricas de validação (MAE, RMSE, R²)

**Tempo estimado:** 15-30 minutos (depende da NASA APIs)

### 4. Iniciar API

```bash
uvicorn main:app --reload
```

A API estará disponível em: http://localhost:8000

### 5. Testar API

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

### Fontes (100% NASA)
- **MODIS MOD13Q1**: NDVI, EVI (250m, 16 dias) via NASA AppEEARS
- **NASA POWER**: Temperatura, Precipitação (dados diários)

### Sem Dados Simulados
Todos os dados são **REAIS da NASA**. Credenciais obrigatórias.

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

### Fontes de Dados NASA

**NASA AppEEARS:**
- MODIS MOD13Q1 (NDVI, EVI)
- 250m resolução
- 16 dias frequência
- Direto da NASA (sem Google)

**NASA POWER API:**
- Temperatura diária
- Precipitação
- Sem autenticação adicional
- Dados climáticos globais

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

