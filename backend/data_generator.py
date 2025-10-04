"""
Gerador de Dados Sintéticos Realistas para BloomWatch
Simula padrões de NDVI, clima e floração baseados em dados reais
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple


class BloomDataGenerator:
    """Gera dados sintéticos realistas de floração de culturas"""
    
    # Padrões de floração por cultura (baseado em dados reais)
    CROP_PATTERNS = {
        'almond': {
            'peak_doy': 50,           # Dia do ano (meados de fevereiro)
            'duration': 14,            # Duração da floração (dias)
            'ndvi_peak': 0.75,        # NDVI no pico
            'ndvi_base': 0.30,        # NDVI base (inverno)
            'temp_base': 10.0,        # Temperatura base para GDD
            'gdd_required': 180,      # GDD necessários para floração
            'latitude_range': (35, 40),  # Central Valley, CA
        },
        'apple': {
            'peak_doy': 110,          # Meados de abril
            'duration': 10,
            'ndvi_peak': 0.80,
            'ndvi_base': 0.25,
            'temp_base': 10.0,
            'gdd_required': 250,
            'latitude_range': (46, 48),  # Yakima Valley, WA
        },
        'cherry': {
            'peak_doy': 85,           # Final de março
            'duration': 8,
            'ndvi_peak': 0.78,
            'ndvi_base': 0.28,
            'temp_base': 10.0,
            'gdd_required': 210,
            'latitude_range': (44, 46),  # Traverse City, MI
        }
    }
    
    def __init__(self, crop_type: str = 'almond', seed: int = 42):
        """
        Args:
            crop_type: Tipo de cultura ('almond', 'apple', 'cherry')
            seed: Seed para reprodutibilidade
        """
        np.random.seed(seed)
        self.crop_type = crop_type
        self.pattern = self.CROP_PATTERNS[crop_type]
        
    def generate_dataset(self, 
                        n_years: int = 5,
                        start_year: int = 2020,
                        include_climate_change: bool = True) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Gera dataset completo com múltiplos anos
        
        Args:
            n_years: Número de anos a gerar
            start_year: Ano inicial
            include_climate_change: Se True, adiciona tendência de aquecimento
            
        Returns:
            (data_df, target_array): DataFrame com features e array com dias até floração
        """
        
        all_data = []
        all_targets = []
        
        for year in range(start_year, start_year + n_years):
            # Ajuste para mudança climática (floração cada vez mais cedo)
            climate_shift = 0
            if include_climate_change:
                climate_shift = -2 * (year - start_year)  # 2 dias mais cedo por ano
            
            year_data, year_target = self._generate_year_data(
                year, 
                bloom_shift=climate_shift
            )
            
            all_data.append(year_data)
            all_targets.append(year_target)
        
        # Concatenar todos os anos
        data_df = pd.concat(all_data, ignore_index=True)
        target_array = np.concatenate(all_targets)
        
        print(f"✓ Dataset gerado: {len(data_df)} amostras")
        print(f"  Cultura: {self.crop_type}")
        print(f"  Período: {start_year}-{start_year + n_years - 1}")
        print(f"  Range de dias até floração: {target_array.min():.0f} - {target_array.max():.0f}")
        
        return data_df, target_array
    
    def _generate_year_data(self, year: int, bloom_shift: int = 0) -> Tuple[pd.DataFrame, np.ndarray]:
        """Gera dados para um único ano"""
        
        # Calcular dia de floração para este ano
        bloom_doy = self.pattern['peak_doy'] + bloom_shift
        bloom_doy = max(30, min(150, bloom_doy))  # Limitar entre final jan e final mai
        
        # Gerar 365 dias
        dates = pd.date_range(f'{year}-01-01', periods=365, freq='D')
        day_of_year = np.arange(1, 366)
        
        # 1. NDVI com padrão sazonal realista
        ndvi = self._generate_ndvi_series(day_of_year, bloom_doy)
        
        # 2. GNDVI e SAVI correlacionados
        gndvi = ndvi * 0.9 + np.random.normal(0, 0.02, 365)
        savi = ndvi * 0.85 + np.random.normal(0, 0.03, 365)
        
        # Clip para valores válidos
        gndvi = np.clip(gndvi, 0, 1)
        savi = np.clip(savi, 0, 1)
        
        # 3. Temperatura com padrão sazonal + variação diária
        temperature = self._generate_temperature_series(day_of_year, year)
        
        # 4. Precipitação (exponencial + padrão sazonal)
        precipitation = self._generate_precipitation_series(day_of_year)
        
        # 5. Calcular target (dias até floração)
        target = np.array([max(0, bloom_doy - doy) for doy in day_of_year])
        
        # Criar DataFrame
        data_df = pd.DataFrame({
            'date': dates,
            'year': year,
            'day_of_year': day_of_year,
            'ndvi': ndvi,
            'gndvi': gndvi,
            'savi': savi,
            'temperature': temperature,
            'precipitation': precipitation,
            'bloom_doy': bloom_doy
        })
        
        return data_df, target
    
    def _generate_ndvi_series(self, day_of_year: np.ndarray, bloom_doy: int) -> np.ndarray:
        """
        Gera série temporal de NDVI com padrão realista
        - Inverno: baixo (árvores dormentes)
        - Pré-floração: crescimento rápido
        - Floração: pico
        - Pós-floração: alto (folhas)
        - Outono: declínio
        """
        
        ndvi = np.zeros_like(day_of_year, dtype=float)
        
        ndvi_base = self.pattern['ndvi_base']
        ndvi_peak = self.pattern['ndvi_peak']
        duration = self.pattern['duration']
        
        for i, doy in enumerate(day_of_year):
            if doy < bloom_doy - 60:
                # Inverno: NDVI baixo e estável
                ndvi[i] = ndvi_base + np.random.normal(0, 0.02)
                
            elif doy < bloom_doy - 20:
                # Pré-floração: crescimento gradual (brotação)
                progress = (doy - (bloom_doy - 60)) / 40
                ndvi[i] = ndvi_base + progress * (ndvi_peak - ndvi_base) * 0.3
                ndvi[i] += np.random.normal(0, 0.03)
                
            elif doy < bloom_doy:
                # Antes da floração: crescimento acelerado
                progress = (doy - (bloom_doy - 20)) / 20
                ndvi[i] = ndvi_base + 0.3 * (ndvi_peak - ndvi_base) + progress * 0.4 * (ndvi_peak - ndvi_base)
                ndvi[i] += np.random.normal(0, 0.02)
                
            elif doy <= bloom_doy + duration:
                # Floração: pico de NDVI
                ndvi[i] = ndvi_peak + np.random.normal(0, 0.02)
                
            elif doy < bloom_doy + 90:
                # Pós-floração: alto (desenvolvimento de folhas e frutos)
                ndvi[i] = ndvi_peak * 0.95 + np.random.normal(0, 0.03)
                
            elif doy < 300:
                # Verão: NDVI alto e estável
                ndvi[i] = ndvi_peak * 0.85 + np.random.normal(0, 0.03)
                
            else:
                # Outono: declínio gradual
                progress = (doy - 300) / 65
                ndvi[i] = ndvi_peak * 0.85 - progress * (ndvi_peak * 0.85 - ndvi_base)
                ndvi[i] += np.random.normal(0, 0.03)
        
        # Clip para valores válidos
        ndvi = np.clip(ndvi, 0, 1)
        
        return ndvi
    
    def _generate_temperature_series(self, day_of_year: np.ndarray, year: int) -> np.ndarray:
        """Gera série de temperatura com padrão sazonal"""
        
        # Temperatura média anual baseada na latitude
        lat_mid = np.mean(self.pattern['latitude_range'])
        base_temp = 15.0 if lat_mid > 40 else 18.0
        
        # Amplitude sazonal
        amplitude = 12.0
        
        # Padrão sinusoidal + ruído
        temp = base_temp + amplitude * np.sin((day_of_year - 80) * 2 * np.pi / 365)
        temp += np.random.normal(0, 2.5, len(day_of_year))
        
        # Adicionar eventos extremos ocasionais (ondas de calor/frio)
        for i in range(len(temp)):
            if np.random.random() < 0.05:  # 5% de chance
                temp[i] += np.random.choice([-8, 8])  # Extremo
        
        return temp
    
    def _generate_precipitation_series(self, day_of_year: np.ndarray) -> np.ndarray:
        """Gera série de precipitação (mm)"""
        
        precip = np.zeros_like(day_of_year, dtype=float)
        
        # Padrão sazonal (mais chuva no inverno/primavera)
        seasonal_factor = 1.5 - np.cos((day_of_year - 90) * 2 * np.pi / 365)
        
        for i, doy in enumerate(day_of_year):
            # Dias com chuva (30% de chance no inverno, 10% no verão)
            rain_prob = 0.3 * seasonal_factor[i] if doy < 150 or doy > 300 else 0.1
            
            if np.random.random() < rain_prob:
                # Quantidade de chuva (distribuição exponencial)
                precip[i] = np.random.exponential(5) * seasonal_factor[i]
        
        return precip
    
    def generate_prediction_window(self, 
                                   current_doy: int, 
                                   year: int = 2025,
                                   window_days: int = 90) -> pd.DataFrame:
        """
        Gera janela de dados para fazer predição (últimos 90 dias)
        
        Args:
            current_doy: Dia atual do ano
            year: Ano atual
            window_days: Tamanho da janela em dias
            
        Returns:
            DataFrame com últimos N dias de dados
        """
        
        # Gerar ano completo
        year_data, _ = self._generate_year_data(year, bloom_shift=-6)  # Assumir 6 dias mais cedo
        
        # Filtrar apenas últimos N dias antes do dia atual
        mask = (year_data['day_of_year'] >= max(1, current_doy - window_days)) & \
               (year_data['day_of_year'] <= current_doy)
        
        window_data = year_data[mask].copy()
        
        return window_data


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def generate_historical_bloom_dates(crop_type: str, 
                                   start_year: int = 2020, 
                                   n_years: int = 5) -> Dict[int, str]:
    """
    Gera datas históricas de floração para uma cultura
    
    Returns:
        Dict com {ano: 'YYYY-MM-DD'}
    """
    
    patterns = BloomDataGenerator.CROP_PATTERNS
    base_doy = patterns[crop_type]['peak_doy']
    
    historical = {}
    
    for i, year in enumerate(range(start_year, start_year + n_years)):
        # Floração cada vez mais cedo (mudança climática)
        shift = -2 * i  # 2 dias mais cedo por ano
        bloom_doy = base_doy + shift
        
        # Converter DOY para data
        date = datetime(year, 1, 1) + timedelta(days=bloom_doy - 1)
        historical[year] = date.strftime('%Y-%m-%d')
    
    return historical


if __name__ == "__main__":
    # Teste rápido
    print("\n🌸 BloomWatch Data Generator - Teste\n")
    
    for crop in ['almond', 'apple', 'cherry']:
        print(f"\n{'='*50}")
        print(f"CULTURA: {crop.upper()}")
        print('='*50)
        
        generator = BloomDataGenerator(crop_type=crop)
        data, target = generator.generate_dataset(n_years=5, start_year=2020)
        
        print(f"\nEstatísticas NDVI:")
        print(f"  Média: {data['ndvi'].mean():.3f}")
        print(f"  Máximo: {data['ndvi'].max():.3f}")
        print(f"  Mínimo: {data['ndvi'].min():.3f}")
        
        print(f"\nDatas de floração:")
        historical = generate_historical_bloom_dates(crop, 2020, 5)
        for year, date in historical.items():
            print(f"  {year}: {date}")
        
        # Salvar amostra
        data.to_csv(f'data/{crop}_data_2020_2024.csv', index=False)
        np.save(f'data/{crop}_target_2020_2024.npy', target)
        print(f"\n✓ Dados salvos em data/{crop}_*.csv")
    
    print("\n✅ Teste concluído!")

