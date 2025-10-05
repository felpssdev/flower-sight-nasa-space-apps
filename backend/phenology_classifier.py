"""
Classificador Fenológico para Culturas de Floração

Identifica o estágio fenológico atual da planta baseado em NDVI,
temperatura e época do ano, determinando se é possível fazer
uma previsão assertiva de floração.

Estágios Fenológicos:
1. DORMANCY (Dormência): NDVI < 0.25, temperatura baixa
2. BUD_BREAK (Brotação): NDVI 0.25-0.40, aumento rápido
3. VEGETATIVE_GROWTH (Crescimento): NDVI 0.40-0.60
4. PRE_BLOOM (Pré-Floração): NDVI 0.60-0.75, estabilização
5. BLOOMING (Floração): NDVI > 0.75, estável alto
6. POST_BLOOM (Pós-Floração): NDVI alto, início de declínio
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from enum import Enum


class PhenologyStage(Enum):
    """Estágios fenológicos de culturas perenes"""
    DORMANCY = "dormancy"
    BUD_BREAK = "bud_break"
    VEGETATIVE_GROWTH = "vegetative_growth"
    PRE_BLOOM = "pre_bloom"
    BLOOMING = "blooming"
    POST_BLOOM = "post_bloom"
    UNKNOWN = "unknown"


class PhenologyClassifier:
    """
    Classifica o estágio fenológico atual e determina
    se é possível fazer previsão assertiva de floração.
    
    Suporta hemisfério norte e sul (ajusta meses automaticamente).
    """
    
    # Configurações por cultura (HEMISFÉRIO NORTE)
    CROP_CONFIG = {
        'almond': {
            'bloom_month_range': (2, 4),  # Fev-Abr (HN)
            'chill_hours_required': 200,
            'ndvi_thresholds': {
                'dormancy': 0.25,
                'bud_break': 0.40,
                'vegetative': 0.60,
                'pre_bloom': 0.75
            }
        },
        'apple': {
            'bloom_month_range': (3, 5),  # Mar-Mai (HN)
            'chill_hours_required': 800,
            'ndvi_thresholds': {
                'dormancy': 0.25,
                'bud_break': 0.40,
                'vegetative': 0.60,
                'pre_bloom': 0.75
            }
        },
        'cherry': {
            'bloom_month_range': (3, 5),  # Mar-Mai
            'chill_hours_required': 900,
            'ndvi_thresholds': {
                'dormancy': 0.25,
                'bud_break': 0.40,
                'vegetative': 0.60,
                'pre_bloom': 0.75
            }
        }
    }
    
    def __init__(self, crop_type: str, latitude: float = 0.0):
        """
        Inicializa classificador para uma cultura específica
        
        Args:
            crop_type: 'almond', 'apple' ou 'cherry'
            latitude: latitude da fazenda (para detectar hemisfério)
        """
        if crop_type not in self.CROP_CONFIG:
            raise ValueError(f"Cultura não suportada: {crop_type}")
        
        self.crop_type = crop_type
        self.latitude = latitude
        self.is_southern_hemisphere = latitude < 0
        
        # Copiar configuração
        self.config = self.CROP_CONFIG[crop_type].copy()
        
        # AJUSTAR MESES DE FLORAÇÃO PARA HEMISFÉRIO SUL
        if self.is_southern_hemisphere:
            original_months = self.config['bloom_month_range']
            # Inverter estações: adicionar 6 meses (com wrap)
            adjusted_start = (original_months[0] + 6) % 12
            adjusted_end = (original_months[1] + 6) % 12
            # Se wrap (ex: out-dez = 10-12), manter ordem
            if adjusted_start == 0:
                adjusted_start = 12
            if adjusted_end == 0:
                adjusted_end = 12
            self.config['bloom_month_range'] = (adjusted_start, adjusted_end)
            print(f"🌎 Hemisfério Sul detectado! Meses ajustados: {original_months} → {self.config['bloom_month_range']}")
    
    def classify_stage(self, data: pd.DataFrame) -> Dict:
        """
        Classifica o estágio fenológico atual
        
        Args:
            data: DataFrame com colunas 'ndvi', 'temperature', 'date'
        
        Returns:
            Dict com:
            - stage: PhenologyStage atual
            - confidence: confiança da classificação (0-1)
            - can_predict: se pode fazer previsão assertiva
            - message: mensagem explicativa
            - estimated_bloom_window: janela estimada de floração (se disponível)
        """
        
        # Dados recentes (últimos 30 dias)
        recent_data = data.tail(30).copy()
        
        # Métricas principais
        current_ndvi = recent_data['ndvi'].iloc[-1]
        avg_ndvi = recent_data['ndvi'].mean()
        ndvi_trend = self._calculate_trend(recent_data['ndvi'])
        
        avg_temp = recent_data['temperature'].mean() if 'temperature' in recent_data else None
        
        current_date = datetime.now()
        current_month = current_date.month
        
        # Classificar estágio
        stage, confidence = self._determine_stage(
            current_ndvi, avg_ndvi, ndvi_trend, avg_temp, current_month
        )
        
        # Determinar se pode prever
        can_predict = stage in [PhenologyStage.PRE_BLOOM, PhenologyStage.VEGETATIVE_GROWTH]
        
        # Gerar mensagem e janela de floração
        message, bloom_window = self._generate_response(
            stage, confidence, current_month, current_ndvi, ndvi_trend
        )
        
        return {
            'stage': stage.value,
            'stage_name': self._get_stage_name(stage),
            'confidence': float(confidence),
            'can_predict': can_predict,
            'message': message,
            'current_ndvi': float(current_ndvi),
            'avg_ndvi': float(avg_ndvi),
            'ndvi_trend': ndvi_trend,
            'estimated_bloom_window': bloom_window,
            'current_month': current_month
        }
    
    def _determine_stage(self, current_ndvi: float, avg_ndvi: float, 
                         ndvi_trend: str, avg_temp: Optional[float],
                         current_month: int) -> Tuple[PhenologyStage, float]:
        """Determina o estágio fenológico atual"""
        
        thresholds = self.config['ndvi_thresholds']
        bloom_months = self.config['bloom_month_range']
        
        confidence = 0.8  # Base
        
        # 1. DORMÊNCIA (NDVI muito baixo)
        if avg_ndvi < thresholds['dormancy']:
            # Alta confiança se fora da época de floração
            if not (bloom_months[0] <= current_month <= bloom_months[1]):
                confidence = 0.95
            return PhenologyStage.DORMANCY, confidence
        
        # 2. BROTAÇÃO (NDVI subindo rapidamente)
        if thresholds['dormancy'] <= avg_ndvi < thresholds['bud_break']:
            if ndvi_trend == 'increasing':
                confidence = 0.9
                return PhenologyStage.BUD_BREAK, confidence
            else:
                # NDVI baixo mas sem crescimento = ainda em dormência
                return PhenologyStage.DORMANCY, 0.7
        
        # 3. CRESCIMENTO VEGETATIVO
        if thresholds['bud_break'] <= avg_ndvi < thresholds['vegetative']:
            return PhenologyStage.VEGETATIVE_GROWTH, 0.85
        
        # 4. PRÉ-FLORAÇÃO (NDVI alto, crescimento desacelerando)
        if thresholds['vegetative'] <= avg_ndvi < thresholds['pre_bloom']:
            if ndvi_trend in ['stable', 'decreasing']:
                # Se estamos na época de floração
                if bloom_months[0] <= current_month <= bloom_months[1]:
                    return PhenologyStage.PRE_BLOOM, 0.95
            return PhenologyStage.VEGETATIVE_GROWTH, 0.8
        
        # 5. FLORAÇÃO ou PÓS-FLORAÇÃO
        if avg_ndvi >= thresholds['pre_bloom']:
            if bloom_months[0] <= current_month <= bloom_months[1] + 1:
                return PhenologyStage.BLOOMING, 0.9
            else:
                return PhenologyStage.POST_BLOOM, 0.85
        
        return PhenologyStage.UNKNOWN, 0.5
    
    def _calculate_trend(self, series: pd.Series) -> str:
        """Calcula tendência da série (increasing, decreasing, stable)"""
        if len(series) < 5:
            return 'stable'
        
        # Regressão linear simples
        x = np.arange(len(series))
        y = series.values
        
        # Coeficiente angular
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalizar pela média
        relative_slope = slope / (np.mean(y) + 1e-6)
        
        if relative_slope > 0.01:  # 1% de mudança
            return 'increasing'
        elif relative_slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_response(self, stage: PhenologyStage, confidence: float,
                          current_month: int, current_ndvi: float,
                          ndvi_trend: str) -> Tuple[str, Optional[Dict]]:
        """Gera mensagem e janela de floração estimada"""
        
        bloom_months = self.config['bloom_month_range']
        
        # DORMÊNCIA
        if stage == PhenologyStage.DORMANCY:
            # Calcular meses até próxima floração
            if current_month < bloom_months[0]:
                months_until = bloom_months[0] - current_month
            else:
                months_until = (12 - current_month) + bloom_months[0]
            
            message = (
                f"🌱 **Planta em Dormência Invernal**\n\n"
                f"NDVI atual: {current_ndvi:.3f} (muito baixo)\n"
                f"Estágio: Sem atividade fotossintética significativa\n\n"
                f"⏳ **Previsão não disponível**\n"
                f"Aguarde aproximadamente **{months_until} meses** para o início da brotação.\n"
                f"Floração esperada: **{self._get_month_name(bloom_months[0])}-{self._get_month_name(bloom_months[1])}**"
            )
            
            # Janela de floração (ano seguinte se necessário)
            year = datetime.now().year
            if current_month > bloom_months[1]:
                year += 1
            
            bloom_window = {
                'earliest': datetime(year, bloom_months[0], 1).strftime('%Y-%m-%d'),
                'latest': datetime(year, bloom_months[1], 28).strftime('%Y-%m-%d'),
                'confidence': 'low'
            }
            
            return message, bloom_window
        
        # BROTAÇÃO
        elif stage == PhenologyStage.BUD_BREAK:
            weeks_until = 4  # Estimativa: 4 semanas de brotação até floração
            
            message = (
                f"🌿 **Planta em Fase de Brotação**\n\n"
                f"NDVI atual: {current_ndvi:.3f} (crescimento ativo)\n"
                f"Tendência: {ndvi_trend.upper()}\n\n"
                f"⚠️ **Previsão preliminar**\n"
                f"Floração esperada em aproximadamente **{weeks_until} semanas**.\n"
                f"Previsão assertiva estará disponível quando NDVI > 0.50"
            )
            
            bloom_window = {
                'earliest': (datetime.now() + timedelta(weeks=weeks_until-1)).strftime('%Y-%m-%d'),
                'latest': (datetime.now() + timedelta(weeks=weeks_until+2)).strftime('%Y-%m-%d'),
                'confidence': 'medium'
            }
            
            return message, bloom_window
        
        # CRESCIMENTO VEGETATIVO
        elif stage == PhenologyStage.VEGETATIVE_GROWTH:
            message = (
                f"🌳 **Planta em Crescimento Vegetativo**\n\n"
                f"NDVI atual: {current_ndvi:.3f} (ativo)\n"
                f"Tendência: {ndvi_trend.upper()}\n\n"
                f"✅ **Previsão disponível**\n"
                f"A planta está próxima da floração. Use o modelo de ML para previsão assertiva."
            )
            
            return message, None
        
        # PRÉ-FLORAÇÃO
        elif stage == PhenologyStage.PRE_BLOOM:
            message = (
                f"🌸 **Planta em Pré-Floração**\n\n"
                f"NDVI atual: {current_ndvi:.3f} (muito alto)\n"
                f"Estágio: Botões florais visíveis\n\n"
                f"✅ **Previsão de alta precisão disponível**\n"
                f"Use o modelo de ML para previsão assertiva (margem de erro: ±3 dias)"
            )
            
            return message, None
        
        # FLORAÇÃO
        elif stage == PhenologyStage.BLOOMING:
            message = (
                f"🌺 **Planta em Floração**\n\n"
                f"NDVI atual: {current_ndvi:.3f}\n"
                f"Status: Flores abertas\n\n"
                f"ℹ️ A floração já está ocorrendo!"
            )
            
            return message, None
        
        # PÓS-FLORAÇÃO
        elif stage == PhenologyStage.POST_BLOOM:
            # Calcular meses até próxima floração
            if current_month < bloom_months[0]:
                months_until = bloom_months[0] - current_month
            else:
                months_until = (12 - current_month) + bloom_months[0]
            
            message = (
                f"🍃 **Planta em Pós-Floração**\n\n"
                f"NDVI atual: {current_ndvi:.3f}\n"
                f"Status: Desenvolvimento de frutos\n\n"
                f"ℹ️ Floração já concluída. Próxima floração em {months_until} meses."
            )
            
            bloom_window = {
                'earliest': datetime(datetime.now().year + 1, bloom_months[0], 1).strftime('%Y-%m-%d'),
                'latest': datetime(datetime.now().year + 1, bloom_months[1], 28).strftime('%Y-%m-%d'),
                'confidence': 'low'
            }
            
            return message, bloom_window
        
        # DESCONHECIDO
        else:
            message = "⚠️ Não foi possível determinar o estágio fenológico atual. Dados insuficientes."
            return message, None
    
    def _get_stage_name(self, stage: PhenologyStage) -> str:
        """Retorna nome em português do estágio"""
        names = {
            PhenologyStage.DORMANCY: "Dormência",
            PhenologyStage.BUD_BREAK: "Brotação",
            PhenologyStage.VEGETATIVE_GROWTH: "Crescimento Vegetativo",
            PhenologyStage.PRE_BLOOM: "Pré-Floração",
            PhenologyStage.BLOOMING: "Floração",
            PhenologyStage.POST_BLOOM: "Pós-Floração",
            PhenologyStage.UNKNOWN: "Desconhecido"
        }
        return names.get(stage, "Desconhecido")
    
    def _get_month_name(self, month: int) -> str:
        """Retorna nome do mês em português"""
        months = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        return months.get(month, "")

