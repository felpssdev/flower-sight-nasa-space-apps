"""
Google Earth Engine Data Fetcher - Complementar à NASA
Fornece dados de alta resolução (Sentinel-2 10m, Landsat 30m)
"""

import ee
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import os


class EarthEngineFetcher:
    """Cliente para Google Earth Engine (dados complementares)"""
    
    def __init__(self):
        """Inicializa e autentica Google Earth Engine"""
        try:
            # Tentar autenticação com service account
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                ee.Initialize()
                print("✓ Google Earth Engine autenticado (service account)")
            else:
                # Fallback: autenticação interativa
                try:
                    ee.Initialize()
                    print("✓ Google Earth Engine autenticado")
                except:
                    print("⚠️  Google Earth Engine não disponível")
                    print("   Execute: earthengine authenticate")
                    self.available = False
                    return
            
            self.available = True
            
        except Exception as e:
            print(f"⚠️  Google Earth Engine não disponível: {e}")
            self.available = False
    
    
    def fetch_sentinel2_ndvi(self, lat: float, lon: float, days: int = 90) -> Optional[pd.DataFrame]:
        """
        Busca NDVI de alta resolução do Sentinel-2 (10m)
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Dias de histórico
            
        Returns:
            DataFrame com colunas: date, ndvi_s2, evi_s2
        """
        if not self.available:
            return None
        
        try:
            print(f"📡 Buscando Sentinel-2 (10m) via Google Earth Engine...")
            
            # Definir área de interesse (buffer de 500m)
            point = ee.Geometry.Point([lon, lat])
            aoi = point.buffer(500)
            
            # Data inicial e final
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Coleção Sentinel-2 Surface Reflectance
            s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterBounds(aoi) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
            def calculate_indices(image):
                """Calcula NDVI e EVI"""
                # NDVI = (NIR - Red) / (NIR + Red)
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi')
                
                # EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))
                evi = image.expression(
                    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                    {
                        'NIR': image.select('B8'),
                        'RED': image.select('B4'),
                        'BLUE': image.select('B2')
                    }
                ).rename('evi')
                
                return image.addBands([ndvi, evi])
            
            # Aplicar cálculo de índices
            s2_indices = s2.map(calculate_indices)
            
            # Extrair série temporal
            def extract_values(image):
                """Extrai valores médios para o AOI"""
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                ndvi = image.select('ndvi').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=10,
                    maxPixels=1e9
                ).get('ndvi')
                
                evi = image.select('evi').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=10,
                    maxPixels=1e9
                ).get('evi')
                
                return ee.Feature(None, {
                    'date': date,
                    'ndvi': ndvi,
                    'evi': evi
                })
            
            features = s2_indices.map(extract_values).getInfo()
            
            # Converter para DataFrame
            data = []
            for feature in features['features']:
                props = feature['properties']
                if props['ndvi'] is not None:
                    data.append({
                        'date': pd.to_datetime(props['date']),
                        'ndvi_s2': float(props['ndvi']),
                        'evi_s2': float(props['evi']) if props['evi'] else None
                    })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            print(f"✓ Sentinel-2: {len(df)} registros de alta resolução")
            return df
            
        except Exception as e:
            print(f"⚠️  Erro ao buscar Sentinel-2: {e}")
            return None
    
    
    def fetch_landsat_ndvi(self, lat: float, lon: float, days: int = 365) -> Optional[pd.DataFrame]:
        """
        Busca NDVI histórico do Landsat 8/9 (30m)
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Dias de histórico (padrão 1 ano)
            
        Returns:
            DataFrame com colunas: date, ndvi_l8, evi_l8
        """
        if not self.available:
            return None
        
        try:
            print(f"📡 Buscando Landsat 8/9 (30m) via Google Earth Engine...")
            
            # Definir área de interesse
            point = ee.Geometry.Point([lon, lat])
            aoi = point.buffer(500)
            
            # Data inicial e final
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Coleção Landsat 8/9 Surface Reflectance
            l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(aoi) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20))
            
            l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
                .filterBounds(aoi) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20))
            
            # Merge Landsat 8 e 9
            landsat = l8.merge(l9)
            
            def calculate_indices(image):
                """Calcula NDVI e EVI para Landsat"""
                # Aplicar fatores de escala
                optical = image.select('SR_B.').multiply(0.0000275).add(-0.2)
                
                # NDVI = (NIR - Red) / (NIR + Red)
                ndvi = optical.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')
                
                # EVI
                evi = optical.expression(
                    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                    {
                        'NIR': optical.select('SR_B5'),
                        'RED': optical.select('SR_B4'),
                        'BLUE': optical.select('SR_B2')
                    }
                ).rename('evi')
                
                return image.addBands([ndvi, evi])
            
            # Aplicar cálculo
            landsat_indices = landsat.map(calculate_indices)
            
            # Extrair valores
            def extract_values(image):
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                ndvi = image.select('ndvi').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=30,
                    maxPixels=1e9
                ).get('ndvi')
                
                evi = image.select('evi').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=30,
                    maxPixels=1e9
                ).get('evi')
                
                return ee.Feature(None, {
                    'date': date,
                    'ndvi': ndvi,
                    'evi': evi
                })
            
            features = landsat_indices.map(extract_values).getInfo()
            
            # Converter para DataFrame
            data = []
            for feature in features['features']:
                props = feature['properties']
                if props['ndvi'] is not None:
                    data.append({
                        'date': pd.to_datetime(props['date']),
                        'ndvi_l8': float(props['ndvi']),
                        'evi_l8': float(props['evi']) if props['evi'] else None
                    })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            print(f"✓ Landsat 8/9: {len(df)} registros históricos")
            return df
            
        except Exception as e:
            print(f"⚠️  Erro ao buscar Landsat: {e}")
            return None


# Função de conveniência
def fetch_gee_data(lat: float, lon: float, days: int = 90) -> Optional[pd.DataFrame]:
    """
    Busca dados complementares do Google Earth Engine
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Dias de histórico
        
    Returns:
        DataFrame combinado com Sentinel-2 e Landsat
    """
    fetcher = EarthEngineFetcher()
    
    if not fetcher.available:
        return None
    
    # Buscar Sentinel-2 (últimos 90 dias, alta frequência)
    s2_data = fetcher.fetch_sentinel2_ndvi(lat, lon, days=min(days, 90))
    
    # Buscar Landsat (histórico longo)
    l8_data = fetcher.fetch_landsat_ndvi(lat, lon, days=days)
    
    # Combinar datasets
    if s2_data is not None and l8_data is not None:
        merged = pd.merge(s2_data, l8_data, on='date', how='outer')
        merged = merged.sort_values('date').reset_index(drop=True)
        return merged
    elif s2_data is not None:
        return s2_data
    elif l8_data is not None:
        return l8_data
    else:
        return None

