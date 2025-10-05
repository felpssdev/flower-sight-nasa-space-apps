"""
NASA Data Fetcher - Integração com APIs NASA + Google Earth Engine
Fontes de dados:
1. NASA AppEEARS (MODIS) - NDVI, EVI (250m)
2. NASA POWER API - Dados climáticos
3. Google Earth Engine - Sentinel-2 (10m) + Landsat (30m) [COMPLEMENTAR]
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import requests
import warnings
import os
warnings.filterwarnings('ignore')

# Importar Google Earth Engine (opcional)
try:
    from earth_engine_fetcher import EarthEngineFetcher
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    print("⚠️  Google Earth Engine não disponível (módulo não encontrado)")


class NASADataFetcher:
    """
    Busca dados NASA + Google Earth Engine (complementar)
    
    APIs:
    1. NASA AppEEARS - MODIS MOD13Q1 (NDVI, EVI) - 250m
    2. NASA POWER API - Dados climáticos
    3. Google Earth Engine - Sentinel-2 (10m) + Landsat (30m) [OPCIONAL]
    """
    
    def __init__(self, 
                 nasa_username: Optional[str] = None,
                 nasa_password: Optional[str] = None,
                 use_gee: bool = True):
        """
        Args:
            nasa_username: Username NASA Earthdata (ou usar env var NASA_USERNAME)
            nasa_password: Password NASA Earthdata (ou usar env var NASA_PASSWORD)
            use_gee: Se True, tenta usar Google Earth Engine como fonte complementar
        """
        self.nasa_username = nasa_username or os.getenv('NASA_USERNAME')
        self.nasa_password = nasa_password or os.getenv('NASA_PASSWORD')
        
        if not (self.nasa_username and self.nasa_password):
            raise ValueError(
                "Credenciais NASA obrigatórias!\n"
                "Configure: export NASA_USERNAME='seu_usuario'\n"
                "Configure: export NASA_PASSWORD='sua_senha'\n"
                "Registre-se: https://urs.earthdata.nasa.gov/users/new"
            )
        
        # Inicializar Google Earth Engine (se disponível e solicitado)
        self.gee_fetcher = None
        if use_gee and GEE_AVAILABLE:
            try:
                self.gee_fetcher = EarthEngineFetcher()
                if self.gee_fetcher.available:
                    print("✅ Google Earth Engine ativado (fonte complementar)")
                else:
                    print("⚠️  Google Earth Engine não autenticado")
                    self.gee_fetcher = None
            except Exception as e:
                print(f"⚠️  Google Earth Engine falhou: {e}")
                self.gee_fetcher = None


    # =========================================================================
    # MÉTODO 1: NASA AppEEARS (MODIS/VIIRS) - Direto da NASA
    # =========================================================================
    
    def fetch_ndvi_from_modis(self,
                              lat: float,
                              lon: float,
                              days: int = 90) -> pd.DataFrame:
        """
        Busca dados NDVI MODIS via NASA AppEEARS
        
        Returns:
            DataFrame com: date, ndvi, evi, gndvi, savi
        """
        
        from nasa_appeears import fetch_nasa_ndvi_direct
        
        print("📡 Buscando NDVI MODIS via NASA AppEEARS...")
        df = fetch_nasa_ndvi_direct(
            lat=lat,
            lon=lon,
            days=days,
            username=self.nasa_username,
            password=self.nasa_password
        )
        
        print(f"✓ MODIS: {len(df)} registros obtidos")
        return df


    # =========================================================================
    # NASA POWER API - Dados Climáticos
    # =========================================================================
    
    def fetch_climate_from_power(self, 
                          lat: float, 
                          lon: float, 
                          days: int = 90) -> pd.DataFrame:
        """
        Busca dados climáticos da NASA POWER API
        
        Dados disponíveis:
        - Temperatura (T2M)
        - Precipitação (PRECTOTCORR)
        - Radiação solar
        - Umidade
        
        API: https://power.larc.nasa.gov/docs/services/api/
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Parâmetros da API
        params = {
            'parameters': 'T2M,T2M_MIN,T2M_MAX,PRECTOTCORR',  # Temperatura e precipitação
            'community': 'AG',  # Agricultural community
            'longitude': lon,
            'latitude': lat,
            'start': start_date.strftime('%Y%m%d'),
            'end': end_date.strftime('%Y%m%d'),
            'format': 'JSON'
        }
        
        url = 'https://power.larc.nasa.gov/api/temporal/daily/point'
        
        try:
            print("🌍 Buscando dados NASA POWER API...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extrair dados
            parameters = data['properties']['parameter']
            
            # Criar DataFrame
            dates = []
            temps = []
            precips = []
            
            for date_str, temp in parameters['T2M'].items():
                if temp != -999:  # -999 = missing data
                    dates.append(pd.to_datetime(date_str, format='%Y%m%d'))
                    temps.append(temp)
                    precip = parameters['PRECTOTCORR'].get(date_str, 0)
                    precips.append(precip if precip != -999 else 0)
            
            df = pd.DataFrame({
                'date': dates,
                'temperature': temps,
                'precipitation': precips
            })
            
            print(f"✓ NASA POWER: {len(df)} dias de dados climáticos")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao buscar NASA POWER: {e}")
            raise Exception("Falha ao buscar dados climáticos da NASA POWER API")


    # =========================================================================
    # Combinação NASA AppEEARS + NASA POWER
    # =========================================================================
    
    def fetch_complete_data(self, 
                           lat: float, 
                           lon: float, 
                           days: int = 90) -> pd.DataFrame:
        """
        Busca dados COMPLETOS de múltiplas fontes
        
        Fontes:
        1. NASA AppEEARS - MODIS MOD13Q1 (NDVI, EVI) - 250m
        2. NASA POWER API - Temperatura, Precipitação
        3. Google Earth Engine - Sentinel-2 (10m) + Landsat (30m) [SE DISPONÍVEL]
        """
        
        print(f"\n📡 Buscando dados para: lat={lat:.4f}, lon={lon:.4f}")
        print(f"   Período: {days} dias")
        
        # 1. NDVI da NASA AppEEARS (MODIS - 250m)
        print("\n[1/3] Buscando NDVI MODIS (NASA AppEEARS - 250m)...")
        ndvi_df = self.fetch_ndvi_from_modis(lat, lon, days)
        
        # 2. Clima da NASA POWER
        print("\n[2/3] Buscando dados climáticos (NASA POWER)...")
        climate_df = self.fetch_climate_from_power(lat, lon, days)
        
        # 3. Google Earth Engine (alta resolução - OPCIONAL)
        gee_sentinel_df = None
        gee_landsat_df = None
        if self.gee_fetcher:
            print("\n[3/3] Buscando dados Google Earth Engine (alta resolução)...")
            try:
                # Sentinel-2 (10m)
                gee_sentinel_df = self.gee_fetcher.fetch_sentinel2_ndvi(lat, lon, days)
                if gee_sentinel_df is not None and not gee_sentinel_df.empty:
                    print(f"   ✓ Sentinel-2: {len(gee_sentinel_df)} registros (10m)")
                
                # Landsat (30m)
                gee_landsat_df = self.gee_fetcher.fetch_landsat_ndvi(lat, lon, days)
                if gee_landsat_df is not None and not gee_landsat_df.empty:
                    print(f"   ✓ Landsat: {len(gee_landsat_df)} registros (30m)")
            except Exception as e:
                print(f"   ⚠️  Google Earth Engine falhou: {e}")
        
        # 4. Combinar dados
        print("\n🔗 Combinando dados...")
        merged_df = self._merge_all_data(ndvi_df, climate_df, gee_sentinel_df, gee_landsat_df)
        
        print(f"\n✅ Total: {len(merged_df)} registros completos")
        return merged_df


    # =========================================================================
    # FUNÇÕES AUXILIARES
    # =========================================================================
    
    def _merge_all_data(self, 
                       nasa_ndvi: pd.DataFrame, 
                       climate: pd.DataFrame,
                       gee_sentinel: Optional[pd.DataFrame] = None,
                       gee_landsat: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Combina dados de múltiplas fontes:
        - NASA MODIS (250m) - NDVI base
        - NASA POWER - Clima
        - Google Earth Engine Sentinel-2 (10m) - NDVI alta resolução [OPCIONAL]
        - Google Earth Engine Landsat (30m) - NDVI média resolução [OPCIONAL]
        
        Estratégia:
        1. NASA MODIS serve como baseline (sempre disponível)
        2. GEE Sentinel-2/Landsat são usados para ENRIQUECER dados quando disponíveis
        3. Prioridade: Sentinel-2 (10m) > Landsat (30m) > MODIS (250m)
        """
        
        # 1. Começar com NASA MODIS + Clima
        merged = pd.merge(nasa_ndvi, climate, on='date', how='outer')
        merged = merged.sort_values('date')
        
        # 2. Adicionar Sentinel-2 (alta resolução - prioridade máxima)
        if gee_sentinel is not None and not gee_sentinel.empty:
            # Renomear para evitar conflito
            gee_sentinel_renamed = gee_sentinel.rename(columns={
                'ndvi_s2': 'ndvi_sentinel',
                'evi_s2': 'evi_sentinel'
            })
            merged = pd.merge(merged, gee_sentinel_renamed, on='date', how='outer')
            
            # Usar Sentinel-2 quando disponível (maior qualidade)
            if 'ndvi_sentinel' in merged.columns:
                merged['ndvi'] = merged['ndvi_sentinel'].fillna(merged['ndvi'])
            if 'evi_sentinel' in merged.columns and 'evi' in merged.columns:
                merged['evi'] = merged['evi_sentinel'].fillna(merged['evi'])
        
        # 3. Adicionar Landsat (média resolução - segunda prioridade)
        if gee_landsat is not None and not gee_landsat.empty:
            gee_landsat_renamed = gee_landsat.rename(columns={
                'ndvi_l8': 'ndvi_landsat',
                'evi_l8': 'evi_landsat'
            })
            merged = pd.merge(merged, gee_landsat_renamed, on='date', how='outer')
            
            # Usar Landsat para preencher lacunas (se Sentinel não disponível)
            if 'ndvi_landsat' in merged.columns:
                merged['ndvi'] = merged['ndvi'].fillna(merged['ndvi_landsat'])
            if 'evi_landsat' in merged.columns and 'evi' in merged.columns:
                merged['evi'] = merged['evi'].fillna(merged['evi_landsat'])
        
        # 4. Interpolar valores faltantes (dias sem medições)
        merged['ndvi'] = merged['ndvi'].interpolate(method='linear')
        merged['evi'] = merged['evi'].interpolate(method='linear') if 'evi' in merged.columns else merged['ndvi'] * 1.1
        merged['gndvi'] = merged['gndvi'].interpolate(method='linear') if 'gndvi' in merged.columns else merged['ndvi'] * 0.9
        merged['savi'] = merged['savi'].interpolate(method='linear') if 'savi' in merged.columns else merged['ndvi'] * 0.85
        
        # 5. Preencher valores faltantes (forward/backward fill)
        merged = merged.fillna(method='ffill').fillna(method='bfill')
        
        # 6. Remover linhas completamente vazias
        merged = merged.dropna(subset=['ndvi', 'temperature'])
        
        # 7. Limpar colunas auxiliares
        cols_to_drop = [c for c in merged.columns if c.endswith('_sentinel') or c.endswith('_landsat')]
        merged = merged.drop(columns=cols_to_drop, errors='ignore')
        
        return merged
    
    def _merge_nasa_data(self, ndvi_df: pd.DataFrame, climate_df: pd.DataFrame) -> pd.DataFrame:
        """Combina dados MODIS (NDVI) com dados POWER (clima) - LEGACY"""
        return self._merge_all_data(ndvi_df, climate_df, None, None)


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def fetch_nasa_data(lat: float, 
                   lon: float, 
                   days: int = 90,
                   nasa_username: Optional[str] = None,
                   nasa_password: Optional[str] = None,
                   use_gee: bool = True) -> pd.DataFrame:
    """
    Busca dados NASA + Google Earth Engine (opcional)
    
    Args:
        lat: Latitude da fazenda
        lon: Longitude da fazenda
        days: Dias de histórico
        nasa_username: Username NASA Earthdata (ou usar env var NASA_USERNAME)
        nasa_password: Password NASA Earthdata (ou usar env var NASA_PASSWORD)
        use_gee: Se True, tenta usar Google Earth Engine como fonte complementar
    
    Returns:
        DataFrame com: date, ndvi, evi, gndvi, savi, temperature, precipitation
    
    Fontes:
        - NASA AppEEARS (MODIS MOD13Q1) - NDVI, EVI (250m) [SEMPRE]
        - NASA POWER API - Temperatura, Precipitação [SEMPRE]
        - Google Earth Engine Sentinel-2 (10m) [SE DISPONÍVEL]
        - Google Earth Engine Landsat (30m) [SE DISPONÍVEL]
    
    Exemplo:
        # Com GEE ativado (padrão)
        data = fetch_nasa_data(36.7468, -119.7726)
        
        # Sem GEE (apenas NASA)
        data = fetch_nasa_data(36.7468, -119.7726, use_gee=False)
    """
    
    fetcher = NASADataFetcher(
        nasa_username=nasa_username,
        nasa_password=nasa_password,
        use_gee=use_gee
    )
    data = fetcher.fetch_complete_data(lat, lon, days)
    
    return data


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    
    print("🌸 NASA Data Fetcher - Teste\n")
    
    # Teste com dados reais da NASA POWER API
    print("="*70)
    print("TESTE 1: NASA POWER API (Dados Climáticos Reais)")
    print("="*70)
    
    data = fetch_nasa_data(
        lat=36.7468,
        lon=-119.7726,
        crop_type='almond',
        days=30,
        use_earth_engine=False  # Apenas NASA POWER + dados sintéticos de NDVI
    )
    
    print(f"\n📊 Resultado:")
    print(f"   {len(data)} registros")
    print(f"   Período: {data['date'].min()} até {data['date'].max()}")
    print(f"\n   NDVI: média={data['ndvi'].mean():.3f}, max={data['ndvi'].max():.3f}")
    print(f"   Temperatura: média={data['temperature'].mean():.1f}°C")
    print(f"   Precipitação total: {data['precipitation'].sum():.1f}mm")
    
    print("\n✅ Teste concluído!")
    
    print("\n" + "="*70)
    print("Para usar Earth Engine:")
    print("="*70)
    print("1. pip install earthengine-api")
    print("2. earthengine authenticate")
    print("3. use_earth_engine=True no fetch_nasa_data()")
    print()

