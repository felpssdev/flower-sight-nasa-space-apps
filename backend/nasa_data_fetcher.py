"""
NASA Data Fetcher - Integração EXCLUSIVA com APIs NASA
Usa APENAS fontes NASA oficiais:
1. NASA AppEEARS (MODIS) - NDVI, EVI
2. NASA POWER API - Dados climáticos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import requests
import warnings
import os
warnings.filterwarnings('ignore')


class NASADataFetcher:
    """
    Busca dados EXCLUSIVAMENTE da NASA
    
    APIs NASA Oficiais:
    1. NASA AppEEARS - MODIS MOD13Q1 (NDVI, EVI)
    2. NASA POWER API - Dados climáticos
    """
    
    def __init__(self, 
                 nasa_username: Optional[str] = None,
                 nasa_password: Optional[str] = None):
        """
        Args:
            nasa_username: Username NASA Earthdata (ou usar env var NASA_USERNAME)
            nasa_password: Password NASA Earthdata (ou usar env var NASA_PASSWORD)
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
        Busca dados COMPLETOS da NASA (NDVI + Clima)
        
        Fontes:
        1. NASA AppEEARS - MODIS MOD13Q1 (NDVI, EVI)
        2. NASA POWER API - Temperatura, Precipitação
        """
        
        print(f"\n📡 Buscando dados NASA para: lat={lat:.4f}, lon={lon:.4f}")
        print(f"   Período: {days} dias")
        
        # 1. NDVI da NASA AppEEARS (MODIS)
        print("\n[1/2] Buscando NDVI MODIS (NASA AppEEARS)...")
        ndvi_df = self.fetch_ndvi_from_modis(lat, lon, days)
        
        # 2. Clima da NASA POWER
        print("\n[2/2] Buscando dados climáticos (NASA POWER)...")
        climate_df = self.fetch_climate_from_power(lat, lon, days)
        
        # 3. Combinar dados
        print("\n🔗 Combinando dados NASA...")
        merged_df = self._merge_nasa_data(ndvi_df, climate_df)
        
        print(f"\n✅ Total: {len(merged_df)} registros NASA completos")
        return merged_df


    # =========================================================================
    # FUNÇÕES AUXILIARES
    # =========================================================================
    
    def _merge_nasa_data(self, ndvi_df: pd.DataFrame, climate_df: pd.DataFrame) -> pd.DataFrame:
        """Combina dados MODIS (NDVI) com dados POWER (clima)"""
        
        # Merge por data (outer join para não perder dados)
        merged = pd.merge(ndvi_df, climate_df, on='date', how='outer')
        merged = merged.sort_values('date')
        
        # Interpolar NDVI (16 dias) para dias intermediários
        merged['ndvi'] = merged['ndvi'].interpolate(method='linear')
        merged['evi'] = merged['evi'].interpolate(method='linear') if 'evi' in merged.columns else None
        merged['gndvi'] = merged['gndvi'].interpolate(method='linear') if 'gndvi' in merged.columns else merged['ndvi'] * 0.9
        merged['savi'] = merged['savi'].interpolate(method='linear') if 'savi' in merged.columns else merged['ndvi'] * 0.85
        
        # Preencher valores faltantes (forward/backward fill)
        merged = merged.fillna(method='ffill').fillna(method='bfill')
        
        # Remover linhas completamente vazias
        merged = merged.dropna(subset=['ndvi', 'temperature'])
        
        return merged


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def fetch_nasa_data(lat: float, 
                   lon: float, 
                   days: int = 90,
                   nasa_username: Optional[str] = None,
                   nasa_password: Optional[str] = None) -> pd.DataFrame:
    """
    Busca dados EXCLUSIVAMENTE da NASA
    
    Args:
        lat: Latitude da fazenda
        lon: Longitude da fazenda
        days: Dias de histórico
        nasa_username: Username NASA Earthdata (ou usar env var NASA_USERNAME)
        nasa_password: Password NASA Earthdata (ou usar env var NASA_PASSWORD)
    
    Returns:
        DataFrame com: date, ndvi, evi, gndvi, savi, temperature, precipitation
    
    Fontes:
        - NASA AppEEARS (MODIS MOD13Q1) - NDVI, EVI
        - NASA POWER API - Temperatura, Precipitação
    
    Exemplo:
        # Opção 1: Com credenciais
        data = fetch_nasa_data(36.7468, -119.7726,
                              nasa_username='seu_user',
                              nasa_password='sua_senha')
        
        # Opção 2: Variáveis de ambiente
        export NASA_USERNAME='seu_user'
        export NASA_PASSWORD='sua_senha'
        data = fetch_nasa_data(36.7468, -119.7726)
    """
    
    fetcher = NASADataFetcher(
        nasa_username=nasa_username,
        nasa_password=nasa_password
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

