"""
NASA AppEEARS API - Acesso direto aos dados MODIS/VIIRS
https://appeears.earthdatacloud.nasa.gov/

Permite baixar NDVI, EVI e outros produtos MODIS/VIIRS/SRTM diretamente da NASA
sem passar pelo Google Earth Engine.

Requer: Conta gratuita NASA Earthdata
Registro: https://urs.earthdata.nasa.gov/users/new
"""

import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class NASAAppEEARS:
    """
    Cliente para NASA AppEEARS API
    
    API Documentation: https://appeears.earthdatacloud.nasa.gov/api/
    """
    
    BASE_URL = "https://appeears.earthdatacloud.nasa.gov/api"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Args:
            username: NASA Earthdata username (ou usar env var NASA_USERNAME)
            password: NASA Earthdata password (ou usar env var NASA_PASSWORD)
        """
        self.username = username or os.getenv('NASA_USERNAME')
        self.password = password or os.getenv('NASA_PASSWORD')
        self.token = None
        
        if self.username and self.password:
            self._authenticate()
        else:
            print("⚠️ Credenciais NASA não fornecidas. Use:")
            print("   export NASA_USERNAME='seu_usuario'")
            print("   export NASA_PASSWORD='sua_senha'")
            print("   Ou registre-se em: https://urs.earthdata.nasa.gov/users/new")
    
    
    def _authenticate(self):
        """Autentica na API e obtém token"""
        
        url = f"{self.BASE_URL}/login"
        response = requests.post(url, auth=(self.username, self.password))
        
        if response.status_code == 200:
            self.token = response.json()['token']
            print("✓ Autenticado na NASA AppEEARS")
        else:
            raise Exception(f"Falha na autenticação: {response.text}")
    
    
    def _headers(self) -> Dict:
        """Headers para requisições autenticadas"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    
    def list_products(self) -> List[Dict]:
        """Lista produtos disponíveis (MODIS, VIIRS, etc)"""
        
        url = f"{self.BASE_URL}/product"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao listar produtos: {response.text}")
    
    
    def get_product_layers(self, product: str) -> List[str]:
        """
        Lista layers disponíveis para um produto
        
        Exemplos de produtos:
        - MOD13Q1.061 (MODIS Terra 250m 16-day NDVI)
        - MYD13Q1.061 (MODIS Aqua 250m 16-day NDVI)
        - VNP13A1.001 (VIIRS 500m 16-day NDVI)
        """
        
        url = f"{self.BASE_URL}/product/{product}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return [layer['Name'] for layer in data.get('layers', [])]
        else:
            raise Exception(f"Erro ao buscar layers: {response.text}")
    
    
    def submit_point_request(self,
                            lat: float,
                            lon: float,
                            start_date: str,
                            end_date: str,
                            layers: List[str],
                            task_name: Optional[str] = None) -> str:
        """
        Submete requisição para ponto específico
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Data inicial (formato: MM-DD-YYYY)
            end_date: Data final (formato: MM-DD-YYYY)
            layers: Lista de layers (ex: ['_250m_16_days_NDVI', '_250m_16_days_EVI'])
            task_name: Nome da tarefa (opcional)
        
        Returns:
            task_id: ID da tarefa submetida
        """
        
        if not self.token:
            raise Exception("Não autenticado. Forneça credenciais NASA Earthdata.")
        
        # Nome da tarefa
        if not task_name:
            task_name = f"flowersight_{lat}_{lon}_{int(time.time())}"
        
        # Construir payload
        payload = {
            "task_type": "point",
            "task_name": task_name,
            "params": {
                "dates": [
                    {
                        "startDate": start_date,
                        "endDate": end_date
                    }
                ],
                "layers": [
                    {
                        "product": "MOD13Q1.061",  # MODIS Terra
                        "layer": layer
                    }
                    for layer in layers
                ],
                "coordinates": [
                    {
                        "latitude": lat,
                        "longitude": lon,
                        "id": "point1"
                    }
                ]
            }
        }
        
        url = f"{self.BASE_URL}/task"
        response = requests.post(url, json=payload, headers=self._headers())
        
        if response.status_code == 202:
            task_id = response.json()['task_id']
            print(f"✓ Requisição submetida: task_id={task_id}")
            return task_id
        else:
            raise Exception(f"Erro ao submeter requisição: {response.text}")
    
    
    def get_task_status(self, task_id: str) -> Dict:
        """Verifica status da tarefa"""
        
        url = f"{self.BASE_URL}/task/{task_id}"
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao verificar status: {response.text}")
    
    
    def wait_for_completion(self, task_id: str, timeout: int = 600, poll_interval: int = 10) -> bool:
        """
        Aguarda conclusão da tarefa
        
        Args:
            task_id: ID da tarefa
            timeout: Timeout em segundos (default: 10 min)
            poll_interval: Intervalo entre checks (default: 10s)
        
        Returns:
            True se completou, False se timeout
        """
        
        print(f"⏳ Aguardando processamento (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            state = status['status']
            
            print(f"   Status: {state}")
            
            if state == 'done':
                print("✓ Processamento concluído!")
                return True
            elif state == 'error':
                raise Exception(f"Erro no processamento: {status.get('message', 'Unknown error')}")
            
            time.sleep(poll_interval)
        
        print("❌ Timeout atingido")
        return False
    
    
    def download_results(self, task_id: str) -> pd.DataFrame:
        """
        Baixa resultados da tarefa
        
        Returns:
            DataFrame com dados NDVI/EVI
        """
        
        # Obter informações do bundle
        url = f"{self.BASE_URL}/bundle/{task_id}"
        response = requests.get(url, headers=self._headers())
        
        if response.status_code != 200:
            raise Exception(f"Erro ao buscar bundle: {response.text}")
        
        bundle_info = response.json()
        
        # Baixar arquivo CSV
        csv_file = None
        for file in bundle_info['files']:
            if file['file_name'].endswith('.csv'):
                csv_file = file['file_id']
                break
        
        if not csv_file:
            raise Exception("Arquivo CSV não encontrado nos resultados")
        
        # Download do CSV
        download_url = f"{self.BASE_URL}/bundle/{task_id}/{csv_file}"
        response = requests.get(download_url, headers=self._headers())
        
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar arquivo: {response.text}")
        
        # Salvar temporariamente e ler
        temp_file = f"/tmp/appeears_{task_id}.csv"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        # Ler CSV
        df = pd.read_csv(temp_file)
        
        print(f"✓ Dados baixados: {len(df)} registros")
        
        return df
    
    
    def fetch_ndvi(self, 
                   lat: float, 
                   lon: float, 
                   days: int = 90) -> pd.DataFrame:
        """
        Função principal: busca dados NDVI para um ponto
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Dias de histórico
        
        Returns:
            DataFrame com colunas: date, ndvi, evi, quality
        """
        
        # Calcular datas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Formato MM-DD-YYYY
        start_str = start_date.strftime('%m-%d-%Y')
        end_str = end_date.strftime('%m-%d-%Y')
        
        print(f"\n📡 Buscando dados MODIS NDVI via NASA AppEEARS")
        print(f"   Localização: {lat:.4f}, {lon:.4f}")
        print(f"   Período: {start_str} até {end_str}")
        
        # Layers MODIS MOD13Q1 (250m, 16 dias)
        layers = [
            '_250m_16_days_NDVI',
            '_250m_16_days_EVI',
            '_250m_16_days_VI_Quality'
        ]
        
        # Submeter requisição
        task_id = self.submit_point_request(
            lat=lat,
            lon=lon,
            start_date=start_str,
            end_date=end_str,
            layers=layers
        )
        
        # Aguardar processamento
        if not self.wait_for_completion(task_id):
            raise Exception("Timeout ao aguardar processamento")
        
        # Baixar resultados
        raw_df = self.download_results(task_id)
        
        # Processar DataFrame
        df = self._process_modis_data(raw_df)
        
        return df
    
    
    def _process_modis_data(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Processa dados brutos MODIS em formato limpo"""
        
        # Colunas esperadas no CSV AppEEARS
        # Date, MOD13Q1_061__250m_16_days_NDVI, MOD13Q1_061__250m_16_days_EVI, etc
        
        processed_data = []
        
        for _, row in raw_df.iterrows():
            date = pd.to_datetime(row['Date'])
            
            # AppEEARS já retorna valores NDVI/EVI escalados (0-1)!
            # Não precisa multiplicar por 0.0001
            ndvi_col = [col for col in raw_df.columns if 'NDVI' in col][0]
            evi_col = [col for col in raw_df.columns if 'EVI' in col][0]
            
            ndvi_raw = row[ndvi_col]
            evi_raw = row[evi_col]
            
            # Filtrar valores inválidos (negativos = fill values)
            if ndvi_raw >= 0:  # Valores válidos são >= 0
                ndvi = ndvi_raw  # JÁ ESCALADO!
                evi = evi_raw if evi_raw >= 0 else None  # JÁ ESCALADO!
                
                # Clip para range válido
                ndvi = np.clip(ndvi, 0, 1)
                if evi is not None:
                    evi = np.clip(evi, 0, 1)
                
                processed_data.append({
                    'date': date,
                    'ndvi': ndvi,
                    'evi': evi
                })
        
        df = pd.DataFrame(processed_data)
        
        # Calcular GNDVI e SAVI (aproximações baseadas em NDVI)
        df['gndvi'] = df['ndvi'] * 0.9
        df['savi'] = df['ndvi'] * 0.85
        
        return df


# =============================================================================
# ALTERNATIVA: NASA CMR API (Acesso direto aos arquivos HDF)
# =============================================================================

class NASA_CMR_Fetcher:
    """
    NASA Common Metadata Repository - Busca direta de granules MODIS
    Mais complexo, mas não precisa aguardar processamento
    """
    
    CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
    
    def __init__(self):
        self.session = requests.Session()
    
    
    def search_modis_granules(self, 
                             lat: float, 
                             lon: float,
                             start_date: str,
                             end_date: str) -> List[Dict]:
        """
        Busca granules MODIS que cobrem o ponto
        
        Args:
            lat, lon: Coordenadas
            start_date, end_date: Formato YYYY-MM-DD
        
        Returns:
            Lista de granules com URLs de download
        """
        
        params = {
            'short_name': 'MOD13Q1',  # MODIS Terra Vegetation Indices
            'version': '061',
            'temporal': f'{start_date}T00:00:00Z,{end_date}T23:59:59Z',
            'point': f'{lon},{lat}',
            'page_size': 100
        }
        
        response = self.session.get(self.CMR_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])
            
            print(f"✓ Encontrados {len(entries)} granules MODIS")
            
            return entries
        else:
            raise Exception(f"Erro ao buscar granules: {response.text}")
    
    
    def extract_download_urls(self, granules: List[Dict]) -> List[str]:
        """Extrai URLs de download dos granules"""
        
        urls = []
        for granule in granules:
            for link in granule.get('links', []):
                if link.get('rel') == 'http://esipfed.org/ns/fedsearch/1.1/data#':
                    urls.append(link['href'])
        
        return urls


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def fetch_nasa_ndvi_direct(lat: float, 
                          lon: float, 
                          days: int = 90,
                          username: Optional[str] = None,
                          password: Optional[str] = None) -> pd.DataFrame:
    """
    Busca NDVI direto da NASA via AppEEARS
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Dias de histórico
        username: NASA Earthdata username (ou usar env var)
        password: NASA Earthdata password (ou usar env var)
    
    Returns:
        DataFrame com date, ndvi, evi, gndvi, savi
    
    Exemplo:
        # Opção 1: Com credenciais
        df = fetch_nasa_ndvi_direct(36.7468, -119.7726, username='seu_user', password='sua_senha')
        
        # Opção 2: Com env vars
        export NASA_USERNAME='seu_user'
        export NASA_PASSWORD='sua_senha'
        df = fetch_nasa_ndvi_direct(36.7468, -119.7726)
    """
    
    client = NASAAppEEARS(username=username, password=password)
    
    if not client.token:
        print("\n❌ Autenticação necessária!")
        print("\nOpções:")
        print("1. Passar credenciais:")
        print("   fetch_nasa_ndvi_direct(..., username='X', password='Y')")
        print("\n2. Usar variáveis de ambiente:")
        print("   export NASA_USERNAME='seu_usuario'")
        print("   export NASA_PASSWORD='sua_senha'")
        print("\n3. Registrar conta grátis:")
        print("   https://urs.earthdata.nasa.gov/users/new")
        
        raise Exception("Credenciais NASA não fornecidas")
    
    return client.fetch_ndvi(lat, lon, days)


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    
    print("🛰️ NASA AppEEARS NDVI Fetcher - Teste\n")
    print("="*70)
    
    # Verificar credenciais
    username = os.getenv('NASA_USERNAME')
    password = os.getenv('NASA_PASSWORD')
    
    if not username or not password:
        print("❌ Credenciais NASA não encontradas!")
        print("\nPara testar, configure:")
        print("  export NASA_USERNAME='seu_usuario'")
        print("  export NASA_PASSWORD='sua_senha'")
        print("\nCrie uma conta grátis em:")
        print("  https://urs.earthdata.nasa.gov/users/new")
        print("\n" + "="*70)
        exit(1)
    
    # Teste
    print("Testando busca de NDVI MODIS...")
    print("Localização: Central Valley, CA (amêndoas)")
    print("="*70 + "\n")
    
    try:
        df = fetch_nasa_ndvi_direct(
            lat=36.7468,
            lon=-119.7726,
            days=60
        )
        
        print(f"\n{'='*70}")
        print("✅ SUCESSO!")
        print(f"{'='*70}")
        print(f"\n📊 Dados obtidos:")
        print(f"   Registros: {len(df)}")
        print(f"   Período: {df['date'].min()} até {df['date'].max()}")
        print(f"\n   NDVI:")
        print(f"      Média: {df['ndvi'].mean():.3f}")
        print(f"      Máximo: {df['ndvi'].max():.3f}")
        print(f"      Mínimo: {df['ndvi'].min():.3f}")
        
        print("\n   Primeiras 5 linhas:")
        print(df.head())
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nVerifique:")
        print("  1. Credenciais corretas")
        print("  2. Conexão com internet")
        print("  3. Conta NASA Earthdata ativa")

