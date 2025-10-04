# 📡 BloomWatch API - Parâmetros de Predição

## 🎯 **Endpoint Principal: `/api/predict`**

### **Método:** `POST`

### **Content-Type:** `application/json`

---

## 📥 **Parâmetros de Entrada (Request Body)**

### **Schema: `PredictionRequest`**

```json
{
  "lat": 36.7468,
  "lon": -119.7726,
  "crop_type": "almond",
  "farm_name": "Central Valley Farm"
}
```

### **Campos Obrigatórios:**

| Parâmetro | Tipo | Descrição | Validação |
|-----------|------|-----------|-----------|
| `lat` | `float` | **Latitude da fazenda** | `-90` ≤ lat ≤ `90` |
| `lon` | `float` | **Longitude da fazenda** | `-180` ≤ lon ≤ `180` |
| `crop_type` | `string` | **Tipo de cultura** | `almond`, `apple`, `cherry` |

### **Campos Opcionais:**

| Parâmetro | Tipo | Descrição | Default |
|-----------|------|-----------|---------|
| `farm_name` | `string` | Nome da fazenda (identificação) | `"My Farm"` |

---

## 📤 **Resposta (Response)**

### **Schema: `PredictionResponse`**

```json
{
  "farm_name": "Central Valley Farm",
  "crop_type": "almond",
  "location": {
    "lat": 36.7468,
    "lon": -119.7726
  },
  "predicted_bloom_date": "2025-02-19",
  "confidence_low": "2025-02-15",
  "confidence_high": "2025-02-23",
  "days_until_bloom": 137,
  "agreement_score": 0.92,
  "recommendations": [
    "🌱 Preparar para floração...",
    "📊 Monitorar NDVI..."
  ],
  "ndvi_trend": [
    {"date": "2024-10-01", "ndvi": 0.65},
    {"date": "2024-10-17", "ndvi": 0.68}
  ],
  "individual_predictions": {
    "lstm": 45.2,
    "rf": 47.1,
    "ann": 46.8
  },
  "historical_average": "2025-02-19",
  "days_shift": 0
}
```

### **Campos Retornados:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `farm_name` | `string` | Nome da fazenda |
| `crop_type` | `string` | Cultura analisada |
| `location` | `object` | Coordenadas GPS |
| `predicted_bloom_date` | `string` | **Data prevista de floração** (YYYY-MM-DD) |
| `confidence_low` | `string` | Limite inferior do intervalo de confiança |
| `confidence_high` | `string` | Limite superior do intervalo de confiança |
| `days_until_bloom` | `int` | **Dias até a floração** |
| `agreement_score` | `float` | Score de concordância entre modelos (0-1) |
| `recommendations` | `array` | Recomendações agronômicas |
| `ndvi_trend` | `array` | Histórico de NDVI dos últimos 90 dias |
| `individual_predictions` | `object` | Predições individuais (LSTM, RF, ANN) |
| `historical_average` | `string` | Data média histórica de floração |
| `days_shift` | `int` | Diferença vs média histórica |

---

## 🔧 **Endpoint de Teste: `/api/predict/test/{crop_type}`**

### **Método:** `GET`

### **Parâmetros:**

| Parâmetro | Tipo | Onde | Descrição | Valores |
|-----------|------|------|-----------|---------|
| `crop_type` | `string` | **Path** | Cultura para teste | `almond`, `apple`, `cherry` |

### **Localizações de Teste:**

```json
{
  "almond": {
    "lat": 36.7468,
    "lon": -119.7726,
    "name": "Central Valley, CA"
  },
  "apple": {
    "lat": 46.6021,
    "lon": -120.5059,
    "name": "Yakima Valley, WA"
  },
  "cherry": {
    "lat": 44.7631,
    "lon": -85.6206,
    "name": "Traverse City, MI"
  }
}
```

---

## 📚 **Exemplos de Uso**

### **1. Predição para Almond (Amêndoa)**

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 36.7468,
    "lon": -119.7726,
    "crop_type": "almond",
    "farm_name": "My Almond Farm"
  }'
```

### **2. Predição para Apple (Maçã)**

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 46.6021,
    "lon": -120.5059,
    "crop_type": "apple",
    "farm_name": "Yakima Orchards"
  }'
```

### **3. Predição para Cherry (Cereja)**

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 44.7631,
    "lon": -85.6206,
    "crop_type": "cherry",
    "farm_name": "Michigan Cherry Farm"
  }'
```

### **4. Teste Rápido (GET)**

```bash
# Almond
curl http://localhost:8000/api/predict/test/almond

# Apple
curl http://localhost:8000/api/predict/test/apple

# Cherry
curl http://localhost:8000/api/predict/test/cherry
```

---

## 📊 **Outros Endpoints Disponíveis**

### **Health Check**

```bash
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T12:00:00Z"
}
```

### **Listar Culturas Suportadas**

```bash
GET /api/crops
```

**Resposta:**
```json
{
  "crops": [
    {
      "id": "almond",
      "name": "Almond",
      "bloom_period": "February - March",
      "region": "California Central Valley"
    },
    {
      "id": "apple",
      "name": "Apple",
      "bloom_period": "April - May",
      "region": "Washington State"
    },
    {
      "id": "cherry",
      "name": "Cherry",
      "bloom_period": "Late March - Early April",
      "region": "Michigan"
    }
  ]
}
```

### **Informações da API**

```bash
GET /
```

---

## ⚠️ **Erros Possíveis**

### **400 Bad Request**

```json
{
  "detail": "Cultura inválida. Opções: almond, apple, cherry"
}
```

**Causa:** `crop_type` inválido

---

### **401 Unauthorized**

```json
{
  "detail": "Credenciais NASA não configuradas. Configure NASA_USERNAME e NASA_PASSWORD."
}
```

**Causa:** Variáveis de ambiente NASA não configuradas

**Solução:**
```bash
export NASA_USERNAME='seu_usuario'
export NASA_PASSWORD='sua_senha'
```

---

### **404 Not Found**

```json
{
  "detail": "Modelo para cultura 'xxx' não encontrado. Execute train_models.py primeiro."
}
```

**Causa:** Modelo não foi treinado

**Solução:**
```bash
python train_models.py
```

---

### **503 Service Unavailable**

```json
{
  "detail": "APIs NASA indisponíveis: [erro]"
}
```

**Causa:** APIs NASA fora do ar ou problema de conectividade

---

## 🔍 **Validações Automáticas**

- ✅ **Latitude:** entre -90° e +90°
- ✅ **Longitude:** entre -180° e +180°
- ✅ **Crop Type:** apenas `almond`, `apple`, `cherry`
- ✅ **Dados NASA:** verifica disponibilidade antes da predição
- ✅ **Modelos:** valida existência dos modelos treinados

---

## 🌍 **Dados NASA Utilizados**

A API busca **automaticamente** os seguintes dados em tempo real:

### **NASA AppEEARS (MODIS MOD13Q1)**
- ✅ NDVI (Normalized Difference Vegetation Index)
- ✅ EVI (Enhanced Vegetation Index)
- 📊 Resolução: 250m
- 📅 Frequência: 16 dias

### **NASA POWER API**
- ✅ Temperatura diária (°C)
- ✅ Precipitação diária (mm)
- 📊 Resolução: 0.5° × 0.625°
- 📅 Frequência: Diária

**Período:** Últimos 90 dias (padrão)

---

## 🚀 **Próximas Funcionalidades (Roadmap)**

Parâmetros que podem ser adicionados no futuro:

- [ ] `days_lookback`: Período de dados históricos (default: 90)
- [ ] `confidence_level`: Nível de confiança do intervalo (default: 0.95)
- [ ] `include_weather_forecast`: Integrar previsão meteorológica
- [ ] `elevation`: Altitude da fazenda (para GDD ajustado)
- [ ] `variety`: Variedade específica da cultura
- [ ] `historical_years`: Anos de dados históricos para comparação

---

**✅ API 100% funcional com dados NASA reais!**

