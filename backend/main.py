"""
FlowerSight FastAPI Backend
API para predição de floração usando ensemble ML
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd
import os

from ml_pipeline import FlowerSightEnsemble
from phenology_classifier import PhenologyClassifier


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

def fetch_ndvi_data(lat: float, lon: float, days: int = 90) -> pd.DataFrame:
    """
    Busca dados REAIS da NASA (MODIS NDVI + Clima)
    
    Fontes:
    - NASA AppEEARS: MODIS MOD13Q1 (NDVI, EVI)
    - NASA POWER API: Temperatura, Precipitação
    
    OBRIGATÓRIO: Credenciais NASA Earthdata
    Configure: export NASA_USERNAME='usuario'
    Configure: export NASA_PASSWORD='senha'
    """
    
    from nasa_data_fetcher import fetch_nasa_data
    
    try:
        # Buscar dados NASA (AppEEARS + POWER)
        data = fetch_nasa_data(
            lat=lat,
            lon=lon,
            days=days
        )
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

