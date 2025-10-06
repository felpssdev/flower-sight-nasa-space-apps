"""
FlowerSight FastAPI Backend
API para predição de floração usando ensemble ML
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd
import os
import json
import asyncio
import hashlib
from functools import lru_cache
import numpy as np

from ml_pipeline import FlowerSightEnsemble
from phenology_classifier import PhenologyClassifier

# Simple in-memory cache for NASA data (6 hours TTL)
NASA_DATA_CACHE: Dict[str, tuple[pd.DataFrame, datetime]] = {}
CACHE_TTL_HOURS = 6


# ============================================================================
# CONFIGURAÇÃO DA API
# ============================================================================

app = FastAPI(
    title="FlowerSight API",
    description="Predição inteligente de floração usando dados de satélite NASA + Machine Learning",
    version="1.0.0"
)

# CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class PredictionRequest(BaseModel):
    """Request para predição de floração"""
    lat: float = Field(..., description="Latitude da fazenda", ge=-90, le=90)
    lon: float = Field(..., description="Longitude da fazenda", ge=-180, le=180)
    crop_type: str = Field(..., description="Tipo de cultura: almond, apple, cherry")
    farm_name: Optional[str] = Field("My Farm", description="Nome da fazenda")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 36.7468,
                "lon": -119.7726,
                "crop_type": "almond",
                "farm_name": "Central Valley Farm"
            }
        }


class PredictionResponse(BaseModel):
    """Response com predição de floração"""
    farm_name: str
    crop_type: str
    location: Dict[str, float]
    predicted_bloom_date: str
    confidence_low: str
    confidence_high: str
    days_until_bloom: int
    agreement_score: float
    recommendations: List[str]
    ndvi_trend: Optional[List[Dict]] = None
    individual_predictions: Dict[str, float]
    historical_average: Optional[str] = None
    days_shift: Optional[int] = None
    
    # Informações fenológicas
    phenology_stage: Optional[str] = None
    phenology_stage_name: Optional[str] = None
    phenology_confidence: Optional[float] = None
    phenology_message: Optional[str] = None
    can_predict_bloom: Optional[bool] = None
    estimated_bloom_window: Optional[Dict] = None


# ============================================================================
# CACHE DE MODELOS
# ============================================================================

models_cache = {}

def load_model(crop_type: str) -> FlowerSightEnsemble:
    """Carrega modelo do cache ou disco"""
    if crop_type not in models_cache:
        model_path = f'models/{crop_type}/'
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404,
                detail=f"Modelo para cultura '{crop_type}' não encontrado. Execute train_models.py primeiro."
            )
        
        ensemble = FlowerSightEnsemble()
        ensemble.load_models(path=model_path)
        models_cache[crop_type] = ensemble
    
    return models_cache[crop_type]


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def convert_to_json_serializable(obj):
    """Convert numpy/pandas types to native Python types for JSON serialization"""
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    return obj


def get_cache_key(lat: float, lon: float, days: int) -> str:
    """Generate cache key for NASA data"""
    return hashlib.md5(f"{lat:.4f}_{lon:.4f}_{days}".encode()).hexdigest()


def fetch_ndvi_data(lat: float, lon: float, days: int = 30) -> pd.DataFrame:
    """
    Busca dados REAIS da NASA (MODIS NDVI + Clima) com cache de 6 horas
    
    Fontes:
    - NASA AppEEARS: MODIS MOD13Q1 (NDVI, EVI)
    - NASA POWER API: Temperatura, Precipitação
    
    OBRIGATÓRIO: Credenciais NASA Earthdata
    Configure: export NASA_USERNAME='usuario'
    Configure: export NASA_PASSWORD='senha'
    """
    
    from nasa_data_fetcher import fetch_nasa_data
    
    # Check cache
    cache_key = get_cache_key(lat, lon, days)
    if cache_key in NASA_DATA_CACHE:
        cached_data, cached_time = NASA_DATA_CACHE[cache_key]
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
        
        if age_hours < CACHE_TTL_HOURS:
            print(f"✓ Using cached NASA data (age: {age_hours:.1f}h)")
            return cached_data.copy()
    
    try:
        # Fetch fresh NASA data
        print(f"⟳ Fetching fresh NASA data (lat={lat}, lon={lon}, days={days})...")
        data = fetch_nasa_data(
            lat=lat,
            lon=lon,
            days=days
        )
        
        # Update cache
        NASA_DATA_CACHE[cache_key] = (data.copy(), datetime.now())
        print(f"✓ NASA data cached for 6 hours")
        
        return data
        
    except ValueError as e:
        # Credenciais não configuradas
        print(f"❌ {e}")
        raise HTTPException(
            status_code=401,
            detail="Credenciais NASA não configuradas. Configure NASA_USERNAME e NASA_PASSWORD."
        )
        
    except Exception as e:
        # Erro nas APIs NASA
        print(f"❌ Erro ao buscar dados NASA: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"APIs NASA indisponíveis: {str(e)}"
        )


def generate_recommendations(days_until: int, crop_type: str) -> List[str]:
    """Gera recomendações baseadas nos dias até floração"""
    recommendations = []
    
    if days_until < 0:
        recommendations.append("🌸 Floração já ocorreu! Monitorar desenvolvimento de frutos.")
        recommendations.append("📊 Avaliar taxa de polinização e frutificação")
    elif days_until < 7:
        recommendations.append("🚨 URGENTE: Floração IMINENTE nos próximos 7 dias!")
        recommendations.append("🐝 Garantir que colmeias estão posicionadas (se não feito)")
        recommendations.append("🌡️ Monitorar previsão do tempo - risco de geada!")
        recommendations.append("💧 Evitar irrigação excessiva durante floração")
    elif days_until < 14:
        recommendations.append("⚠️ ALERTA: Floração em menos de 2 semanas")
        recommendations.append("🐝 Contatar apicultores AGORA se ainda não feito")
        recommendations.append("📋 Preparar posicionamento de colmeias")
        recommendations.append("🌡️ Verificar previsões climáticas para período de floração")
    elif days_until < 30:
        recommendations.append("📅 Floração prevista nas próximas 4 semanas")
        recommendations.append("🐝 Coordenar com apicultores nas próximas 2 semanas")
        recommendations.append("🌤️ Monitorar tendências climáticas")
        recommendations.append("📊 Planejar recursos e mão de obra")
    else:
        recommendations.append(f"📆 Floração prevista em {days_until} dias")
        recommendations.append("👀 Continuar monitorando evolução do NDVI")
        recommendations.append("📈 Revisar predição semanalmente")
    
    # Recomendações específicas por cultura
    if crop_type == 'almond':
        recommendations.append("🌰 Amêndoas: 1.5-2.0 colmeias por acre recomendado")
    elif crop_type == 'apple':
        recommendations.append("🍎 Maçãs: 1 colmeia por acre recomendado")
    elif crop_type == 'cherry':
        recommendations.append("🍒 Cerejas: 2-2.5 colmeias por acre recomendado")
    
    # Sempre adicionar
    recommendations.append("📡 Dados atualizados via satélites NASA MODIS/Landsat")
    
    return recommendations


def calculate_historical_average(crop_type: str) -> tuple:
    """
    Calcula média histórica de floração e diferença
    
    Returns:
        (historical_date_str, days_shift)
    """
    
    # Padrões históricos (simplificado)
    historical_patterns = {
        'almond': {'doy': 50, 'year': 2024},  # ~19 de fevereiro
        'apple': {'doy': 110, 'year': 2024},   # ~20 de abril
        'cherry': {'doy': 85, 'year': 2024},   # ~26 de março
    }
    
    pattern = historical_patterns.get(crop_type, {'doy': 100, 'year': 2024})
    historical_date = datetime(pattern['year'], 1, 1) + timedelta(days=pattern['doy'] - 1)
    
    return historical_date.strftime('%Y-%m-%d'), 0  # Simplificado


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "service": "FlowerSight API",
        "version": "1.0.0",
        "status": "operational",
        "description": "Predição de floração usando NASA Earth Data + Machine Learning",
        "endpoints": {
            "predict": "/api/predict",
            "health": "/health",
            "crops": "/api/crops"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": list(models_cache.keys())
    }


@app.get("/api/crops")
async def list_crops():
    """Lista culturas disponíveis"""
    return {
        "crops": [
            {
                "id": "almond",
                "name": "Amêndoas",
                "icon": "🌰",
                "typical_bloom": "Fevereiro",
                "regions": ["Central Valley, CA"]
            },
            {
                "id": "apple",
                "name": "Maçãs",
                "icon": "🍎",
                "typical_bloom": "Abril",
                "regions": ["Yakima Valley, WA", "Michigan"]
            },
            {
                "id": "cherry",
                "name": "Cerejas",
                "icon": "🍒",
                "typical_bloom": "Março-Abril",
                "regions": ["Traverse City, MI", "Oregon"]
            }
        ]
    }


@app.post("/api/predict", response_model=PredictionResponse)
async def predict_bloom(request: PredictionRequest):
    """
    Endpoint principal: predição de floração
    
    Processo:
    1. Valida entrada
    2. Carrega modelo para a cultura
    3. Busca dados NDVI (satélite ou simulado)
    4. Faz predição com ensemble
    5. Gera recomendações
    6. Retorna resultado completo
    """
    
    try:
        # Validar crop_type
        valid_crops = ['almond', 'apple', 'cherry']
        if request.crop_type not in valid_crops:
            raise HTTPException(
                status_code=400,
                detail=f"Cultura inválida. Opções: {', '.join(valid_crops)}"
            )
        
        # 1. Carregar modelo
        ensemble = load_model(request.crop_type)
        
        # 2. Buscar dados NASA (NDVI + Clima)
        data = fetch_ndvi_data(
            lat=request.lat,
            lon=request.lon,
            days=90
        )
        
        # 2.5. Classificar estágio fenológico (com detecção de hemisfério)
        phenology_classifier = PhenologyClassifier(request.crop_type, latitude=request.lat)
        phenology_info = phenology_classifier.classify_stage(data)
        
        # 3. DECISÃO: Fazer previsão ML APENAS se estágio permitir
        if phenology_info['can_predict']:
            # === CENÁRIO A: Planta pronta para previsão ===
            prediction = ensemble.predict(data)
            
            # Calcular datas
            today = datetime.now()
            bloom_date = today + timedelta(days=prediction['predicted_days'])
            ci_low_date = today + timedelta(days=prediction['confidence_interval'][0])
            ci_high_date = today + timedelta(days=prediction['confidence_interval'][1])
            
            # Gerar recomendações baseadas na previsão
            recommendations = generate_recommendations(
                prediction['predicted_days'],
                request.crop_type
            )
            
            days_until_bloom = prediction['predicted_days']
            agreement_score = prediction['agreement_score']
            individual_predictions = prediction['individual_predictions']
            
        else:
            # === CENÁRIO B: Planta NÃO pronta (NDVI baixo, dormência, etc) ===
            # NÃO fazer previsão ML - dados insuficientes/inadequados
            prediction = None
            
            # Usar janela estimada do classificador fenológico
            if phenology_info['estimated_bloom_window']:
                bloom_window = phenology_info['estimated_bloom_window']
                bloom_date_str = bloom_window['earliest']
                ci_low_date_str = bloom_window['earliest']
                ci_high_date_str = bloom_window['latest']
                
                # Calcular dias aproximados até a janela
                bloom_date = datetime.strptime(bloom_date_str, '%Y-%m-%d')
                ci_low_date = datetime.strptime(ci_low_date_str, '%Y-%m-%d')
                ci_high_date = datetime.strptime(ci_high_date_str, '%Y-%m-%d')
                
                today = datetime.now()
                days_until_bloom = (bloom_date - today).days
            else:
                # Sem janela estimada - valores padrão
                today = datetime.now()
                bloom_date = today + timedelta(days=180)  # 6 meses no futuro
                ci_low_date = today + timedelta(days=150)
                ci_high_date = today + timedelta(days=210)
                days_until_bloom = 180
            
            # Valores padrão para previsão não disponível
            agreement_score = 0.0
            individual_predictions = {}
            recommendations = [
                "⚠️ Previsão de ML não disponível: NDVI muito baixo",
                f"Planta em estágio: {phenology_info['stage_name']}",
                "Aguarde o início da brotação para previsões assertivas"
            ]
        
        # 4. Dados históricos (sempre calcular)
        historical_avg, days_shift = calculate_historical_average(request.crop_type)
        
        # 7. Preparar NDVI trend (últimos 30 dias)
        ndvi_trend = None
        if 'ndvi' in data.columns and 'date' in data.columns:
            # Garantir que date é datetime
            if not pd.api.types.is_datetime64_any_dtype(data['date']):
                data['date'] = pd.to_datetime(data['date'])
            
            recent_data = data.tail(30)
            ndvi_trend = [
                {
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'ndvi': float(row['ndvi'])
                }
                for _, row in recent_data.iterrows()
            ]
        
        # 8. Montar resposta
        response = PredictionResponse(
            farm_name=request.farm_name,
            crop_type=request.crop_type,
            location={"lat": request.lat, "lon": request.lon},
            predicted_bloom_date=bloom_date.strftime('%Y-%m-%d'),
            confidence_low=ci_low_date.strftime('%Y-%m-%d'),
            confidence_high=ci_high_date.strftime('%Y-%m-%d'),
            days_until_bloom=days_until_bloom,
            agreement_score=agreement_score,
            recommendations=recommendations,
            ndvi_trend=ndvi_trend,
            individual_predictions=individual_predictions,
            historical_average=historical_avg,
            days_shift=days_shift,
            # Informações fenológicas
            phenology_stage=phenology_info['stage'],
            phenology_stage_name=phenology_info['stage_name'],
            phenology_confidence=phenology_info['confidence'],
            phenology_message=phenology_info['message'],
            can_predict_bloom=phenology_info['can_predict'],
            estimated_bloom_window=phenology_info['estimated_bloom_window']
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar predição: {str(e)}"
        )


@app.get("/api/predict/test/{crop_type}")
async def test_prediction(crop_type: str):
    """
    Endpoint de teste rápido
    Usa localização padrão para cada cultura
    """
    
    test_locations = {
        'almond': {'lat': 36.7468, 'lon': -119.7726, 'name': 'Central Valley, CA'},
        'apple': {'lat': 46.6021, 'lon': -120.5059, 'name': 'Yakima Valley, WA'},
        'cherry': {'lat': 44.7631, 'lon': -85.6206, 'name': 'Traverse City, MI'}
    }
    
    if crop_type not in test_locations:
        raise HTTPException(status_code=400, detail=f"Cultura inválida: {crop_type}")
    
    loc = test_locations[crop_type]
    
    request = PredictionRequest(
        lat=loc['lat'],
        lon=loc['lon'],
        crop_type=crop_type,
        farm_name=loc['name']
    )
    
    return await predict_bloom(request)


@app.get("/api/predict/stream")
async def predict_bloom_stream(
    farm_name: str,
    crop_type: str,
    lat: float,
    lon: float
):
    """
    SSE Endpoint: Predição com streaming de progresso
    
    Retorna eventos Server-Sent Events com progresso em tempo real:
    - event: progress -> {step, message, percent}
    - event: complete -> {resultado completo}
    - event: error -> {error message}
    """
    
    async def event_generator():
        try:
            # Helper para enviar eventos SSE
            def send_event(event_type: str, data: dict):
                return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            
            # Validar crop_type
            valid_crops = ['almond', 'apple', 'cherry']
            if crop_type not in valid_crops:
                yield send_event('error', {
                    'message': f"Invalid crop type. Options: {', '.join(valid_crops)}"
                })
                return
            
            # 1. Carregar modelo (5%)
            yield send_event('progress', {
                'step': 1,
                'message': 'Loading ML models...',
                'percent': 5
            })
            await asyncio.sleep(0.1)
            ensemble = load_model(crop_type)
            
            # 2. Buscar dados NASA (25%)
            yield send_event('progress', {
                'step': 2,
                'message': 'Connecting to NASA satellites...',
                'percent': 15
            })
            await asyncio.sleep(0.1)
            
            yield send_event('progress', {
                'step': 3,
                'message': 'Collecting NDVI data...',
                'percent': 25
            })
            await asyncio.sleep(0.1)
            
            # Heartbeat durante fetch (lento) - múltiplos eventos para evitar timeout
            yield send_event('progress', {
                'step': 3,
                'message': 'Requesting MODIS satellite data...',
                'percent': 28
            })
            await asyncio.sleep(0.1)
            
            # Start fetch in background and send heartbeats
            fetch_complete = False
            fetch_data = None
            fetch_error = None
            
            async def fetch_with_heartbeats():
                nonlocal fetch_complete, fetch_data, fetch_error
                try:
                    print(f"🔄 Starting NASA data fetch for {lat}, {lon}")
                    # Run fetch in thread pool to not block asyncio (SEM TIMEOUT)
                    loop = asyncio.get_event_loop()
                    fetch_data = await loop.run_in_executor(
                        None,
                        fetch_ndvi_data,
                        lat,
                        lon,
                        30  # 30 days for faster fetch
                    )
                    print(f"✅ NASA data fetch complete, got {len(fetch_data)} rows")
                except Exception as e:
                    print(f"❌ NASA data fetch ERROR: {e}")
                    fetch_error = str(e)
                finally:
                    fetch_complete = True
                    print(f"🏁 fetch_complete = {fetch_complete}")
            
            # Start fetch
            fetch_task = asyncio.create_task(fetch_with_heartbeats())
            
            # Send heartbeats every 5s while fetching (para evitar timeout Vercel)
            heartbeat_percent = 29
            elapsed = 0
            heartbeat_count = 0
            print(f"📊 Starting heartbeat loop, fetch_complete={fetch_complete}")
            
            while not fetch_complete:
                await asyncio.sleep(5)  # 5s < 10s (margem de segurança)
                elapsed += 5
                heartbeat_count += 1
                
                print(f"Heartbeat #{heartbeat_count}: elapsed={elapsed}s, fetch_complete={fetch_complete}")
                
                if not fetch_complete:
                    # Cycle progress between 29-34% to show activity
                    heartbeat_percent = 29 + (heartbeat_count % 6)
                    yield send_event('progress', {
                        'step': 3,
                        'message': f'Fetching NASA data... {elapsed}s elapsed',
                        'percent': int(heartbeat_percent)
                    })
            
            print(f"Heartbeat loop ended: fetch_complete={fetch_complete}, elapsed={elapsed}s")
            
            # Wait for fetch task to finish
            await fetch_task
            print(f"fetch_task completed")
            
            # Check for errors
            if fetch_error:
                print(f"❌ NASA fetch error: {fetch_error}")
                yield send_event('error', {
                    'message': f"Failed to fetch NASA data: {fetch_error}",
                    'type': 'DataFetchError'
                })
                return  # Stop generator
            
            if fetch_data is None or len(fetch_data) == 0:
                print(f"❌ No data returned from NASA")
                yield send_event('error', {
                    'message': 'No data returned from NASA satellites',
                    'type': 'EmptyDataError'
                })
                return
            
            print(f"✅ Data fetch successful, proceeding...")
            data = fetch_data
            
            # Heartbeat após fetch
            yield send_event('progress', {
                'step': 3,
                'message': 'NDVI data received, processing...',
                'percent': 35
            })
            await asyncio.sleep(0.1)
            
            # 3. Classificar fenologia (40%)
            yield send_event('progress', {
                'step': 4,
                'message': 'Analyzing plant stage...',
                'percent': 40
            })
            await asyncio.sleep(0.1)
            
            phenology_classifier = PhenologyClassifier(crop_type, latitude=lat)
            phenology_info = phenology_classifier.classify_stage(data)
            
            # 4. Decidir se faz predição ML (50%)
            yield send_event('progress', {
                'step': 5,
                'message': 'Processing features...',
                'percent': 50
            })
            await asyncio.sleep(0.1)
            
            if phenology_info['can_predict']:
                # ML Prediction - add heartbeats
                yield send_event('progress', {
                    'step': 5,
                    'message': 'Preparing ML models...',
                    'percent': 55
                })
                await asyncio.sleep(0.1)
                
                yield send_event('progress', {
                    'step': 6,
                    'message': 'Running LSTM model...',
                    'percent': 60
                })
                await asyncio.sleep(0.1)
                
                yield send_event('progress', {
                    'step': 6,
                    'message': 'Running Random Forest...',
                    'percent': 65
                })
                await asyncio.sleep(0.1)
                
                yield send_event('progress', {
                    'step': 6,
                    'message': 'Running XGBoost...',
                    'percent': 70
                })
                await asyncio.sleep(0.1)
                
                # Run prediction (should be fast with models loaded)
                yield send_event('progress', {
                    'step': 6,
                    'message': 'Running ensemble prediction...',
                    'percent': 72
                })
                await asyncio.sleep(0.1)
                
                prediction = ensemble.predict(data)
                
                yield send_event('progress', {
                    'step': 6,
                    'message': 'Ensemble prediction complete',
                    'percent': 75
                })
                await asyncio.sleep(0.1)
                
                yield send_event('progress', {
                    'step': 7,
                    'message': 'Calculating confidence...',
                    'percent': 90
                })
                await asyncio.sleep(0.1)
                
                # Calcular datas
                today = datetime.now()
                bloom_date = today + timedelta(days=prediction['predicted_days'])
                ci_low_date = today + timedelta(days=prediction['confidence_interval'][0])
                ci_high_date = today + timedelta(days=prediction['confidence_interval'][1])
                
                recommendations = generate_recommendations(
                    prediction['predicted_days'],
                    crop_type
                )
                
                days_until_bloom = prediction['predicted_days']
                agreement_score = prediction['agreement_score']
                individual_predictions = prediction['individual_predictions']
                
            else:
                # Phenology-based estimation
                prediction = None
                
                if phenology_info['estimated_bloom_window']:
                    bloom_window = phenology_info['estimated_bloom_window']
                    bloom_date_str = bloom_window['earliest']
                    ci_low_date_str = bloom_window['earliest']
                    ci_high_date_str = bloom_window['latest']
                    
                    bloom_date = datetime.strptime(bloom_date_str, '%Y-%m-%d')
                    ci_low_date = datetime.strptime(ci_low_date_str, '%Y-%m-%d')
                    ci_high_date = datetime.strptime(ci_high_date_str, '%Y-%m-%d')
                    
                    today = datetime.now()
                    days_until_bloom = (bloom_date - today).days
                else:
                    today = datetime.now()
                    bloom_date = today + timedelta(days=180)
                    ci_low_date = today + timedelta(days=150)
                    ci_high_date = today + timedelta(days=210)
                    days_until_bloom = 180
                
                agreement_score = 0.0
                individual_predictions = {}
                recommendations = [
                    "⚠️ ML prediction not available: NDVI too low",
                    f"Plant in stage: {phenology_info['stage_name']}",
                    "Wait for budding to get accurate predictions"
                ]
            
            # 5. Montar resposta final (95% → 100%)
            yield send_event('progress', {
                'step': 7,
                'message': 'Generating recommendations...',
                'percent': 92
            })
            await asyncio.sleep(0.1)
            
            yield send_event('progress', {
                'step': 8,
                'message': 'Finalizing prediction...',
                'percent': 95
            })
            await asyncio.sleep(0.1)
            
            yield send_event('progress', {
                'step': 8,
                'message': 'Preparing response...',
                'percent': 98
            })
            await asyncio.sleep(0.1)
            
            # Preparar NDVI trend
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
            
            ndvi_trend = []
            if len(data) > 0:
                for idx, row in data.tail(30).iterrows():
                    ndvi_trend.append({
                        "date": row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (pd.Timestamp, datetime)) else str(row['date']),
                        "ndvi": float(row['ndvi'])
                    })
            
            # Montar resposta completa
            response_data = {
                'farm_name': farm_name,
                'crop_type': crop_type,
                'location': {"lat": lat, "lon": lon},
                'days_until_bloom': int(days_until_bloom),
                'predicted_bloom_date': bloom_date.strftime('%Y-%m-%d'),
                'confidence_low': int(ci_low_date.day if hasattr(ci_low_date, 'day') else (ci_low_date - today).days),
                'confidence_high': int(ci_high_date.day if hasattr(ci_high_date, 'day') else (ci_high_date - today).days),
                'confidence_low_date': ci_low_date.strftime('%Y-%m-%d'),
                'confidence_high_date': ci_high_date.strftime('%Y-%m-%d'),
                'agreement_score': float(agreement_score),
                'individual_predictions': individual_predictions,
                'ndvi_trend': ndvi_trend,
                'recommendations': recommendations,
                'phenology_stage': phenology_info['stage'],
                'phenology_stage_name': phenology_info['stage_name'],
                'phenology_confidence': float(phenology_info['confidence']),
                'phenology_message': phenology_info['message'],
                'can_predict_bloom': phenology_info['can_predict'],
                'estimated_bloom_window': phenology_info.get('estimated_bloom_window')
            }
            
            # Enviar resultado final (convert numpy types to native Python)
            response_data = convert_to_json_serializable(response_data)
            yield send_event('complete', response_data)
            
        except Exception as e:
            import traceback
            print(f"❌ Exception in event_generator: {e}")
            print(traceback.format_exc())
            yield send_event('error', {
                'message': str(e),
                'type': type(e).__name__
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a API"""
    print("\n" + "🌸"*30)
    print("FLOWERSIGHT API INICIADA")
    print("🌸"*30)
    print("\n📡 Endpoints disponíveis:")
    print("   GET  /           - Info da API")
    print("   GET  /health     - Health check")
    print("   GET  /api/crops  - Lista culturas")
    print("   POST /api/predict - Predição de floração")
    print("\n💡 Teste rápido:")
    print("   curl http://localhost:8000/api/predict/test/almond")
    print("\n🚀 API pronta para uso!\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

