"""
Script de Treinamento dos Modelos BloomWatch
Usa DADOS REAIS DA NASA para treinar os modelos
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ml_pipeline import BloomWatchEnsemble
from nasa_data_fetcher import fetch_nasa_data
import json


def collect_training_data(crop_type: str, locations: list, years: int = 5):
    """
    Coleta dados NASA para múltiplas localizações e anos
    
    Args:
        crop_type: 'almond', 'apple' ou 'cherry'
        locations: Lista de (lat, lon, nome)
        years: Anos de dados históricos
    """
    
    print(f"\n📡 Coletando dados NASA para {crop_type}...")
    print(f"   Localizações: {len(locations)}")
    print(f"   Anos: {years}")
    
    all_data = []
    
    for lat, lon, name in locations:
        print(f"\n  Buscando: {name} ({lat:.4f}, {lon:.4f})")
        
        try:
            # Buscar últimos N dias de dados
            data = fetch_nasa_data(lat=lat, lon=lon, days=365)
            data['location'] = name
            data['crop_type'] = crop_type
            all_data.append(data)
            
            print(f"    ✓ {len(data)} registros obtidos")
            
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            continue
    
    if not all_data:
        raise Exception("Nenhum dado coletado! Verifique credenciais NASA.")
    
    # Combinar todos os dados
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"\n✓ Total: {len(combined_df)} registros de {len(all_data)} localizações")
    
    return combined_df


def create_training_target(data: pd.DataFrame, bloom_patterns: dict) -> np.ndarray:
    """
    Cria target (dias até floração) baseado em padrões conhecidos
    
    Args:
        data: DataFrame com dados
        bloom_patterns: Dict com padrões de floração por cultura
    """
    
    print("\n📊 Criando targets de treinamento...")
    
    target = []
    
    for _, row in data.iterrows():
        doy = row['date'].timetuple().tm_yday
        crop = row['crop_type']
        
        # Padrão de floração para esta cultura
        bloom_doy = bloom_patterns[crop]['peak_doy']
        
        # Calcular dias até floração
        days_to_bloom = bloom_doy - doy
        
        # Se já passou da floração este ano, considerar próximo ano
        if days_to_bloom < 0:
            days_to_bloom = 365 + days_to_bloom
        
        # Limitar a 0-90 dias
        days_to_bloom = max(0, min(90, days_to_bloom))
        
        target.append(days_to_bloom)
    
    target = np.array(target)
    
    print(f"✓ Target criado: {len(target)} amostras")
    print(f"  Range: {target.min():.0f} - {target.max():.0f} dias")
    
    return target


def train_model_for_crop(crop_type: str, locations: list):
    """
    Treina modelo completo para uma cultura usando dados NASA
    
    Args:
        crop_type: 'almond', 'apple' ou 'cherry'
        locations: Lista de (lat, lon, nome) de fazendas dessa cultura
    """
    
    print("\n" + "="*70)
    print(f"🌸 TREINANDO MODELO PARA: {crop_type.upper()}")
    print("="*70)
    
    # Padrões de floração (baseados em dados USDA/UC Davis)
    bloom_patterns = {
        'almond': {'peak_doy': 50},   # Meados de fevereiro
        'apple': {'peak_doy': 110},   # Meados de abril
        'cherry': {'peak_doy': 85},   # Final de março
    }
    
    # 1. Coletar dados NASA
    print("\n[1/4] Coletando dados NASA...")
    data = collect_training_data(crop_type, locations)
    
    # 2. Criar target
    print("\n[2/4] Preparando target...")
    target = create_training_target(data, bloom_patterns)
    
    # Filtrar apenas dados válidos (0-90 dias antes da floração)
    valid_mask = (target >= 0) & (target <= 90)
    data_filtered = data[valid_mask].copy()
    target_filtered = target[valid_mask]
    
    print(f"✓ Dados filtrados: {len(data_filtered)} amostras válidas")
    
    # Salvar dados brutos
    os.makedirs('data', exist_ok=True)
    data.to_csv(f'data/{crop_type}_nasa_data.csv', index=False)
    np.save(f'data/{crop_type}_nasa_target.npy', target_filtered)
    
    # 3. Treinar ensemble
    print("\n[3/4] Treinando ensemble de modelos...")
    ensemble = BloomWatchEnsemble()
    
    metrics = ensemble.train(
        data=data_filtered,
        target=target_filtered,
        val_split=0.2
    )
    
    # 4. Salvar modelos
    print("\n[4/4] Salvando modelos...")
    model_path = f'models/{crop_type}/'
    ensemble.save_models(path=model_path)
    
    # Salvar métricas
    metrics_data = {
        'crop_type': crop_type,
        'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'n_samples': len(data_filtered),
        'n_locations': len(locations),
        'data_source': 'NASA AppEEARS + POWER API',
        'metrics': {
            'mae': float(metrics['mae']),
            'rmse': float(metrics['rmse']),
            'r2': float(metrics['r2'])
        },
        'validation': {
            'target_passed': bool(metrics['mae'] < 5.0),
            'excellent': bool(metrics['mae'] < 4.0 and metrics['r2'] > 0.85)
        }
    }
    
    with open(f'models/{crop_type}/metrics.json', 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    print(f"\n✅ Modelo para {crop_type} treinado com sucesso!")
    print(f"📊 Métricas finais:")
    print(f"   MAE:  {metrics['mae']:.2f} dias {'✓ APROVADO' if metrics['mae'] < 5 else '✗ REPROVADO'}")
    print(f"   RMSE: {metrics['rmse']:.2f} dias")
    print(f"   R²:   {metrics['r2']:.3f} {'✓ EXCELENTE' if metrics['r2'] > 0.85 else '✓ BOM' if metrics['r2'] > 0.75 else '✗'}")
    
    return ensemble, metrics


def main():
    """Função principal - treina modelos com dados NASA reais"""
    
    print("\n" + "🚀"*35)
    print("BLOOMWATCH - TREINAMENTO COM DADOS NASA")
    print("🚀"*35 + "\n")
    
    # Verificar credenciais
    if not (os.getenv('NASA_USERNAME') and os.getenv('NASA_PASSWORD')):
        print("❌ Credenciais NASA não encontradas!")
        print("\nConfigure:")
        print("  export NASA_USERNAME='seu_usuario'")
        print("  export NASA_PASSWORD='sua_senha'")
        print("\nRegistre-se grátis:")
        print("  https://urs.earthdata.nasa.gov/users/new")
        print()
        exit(1)
    
    # Localizações por cultura (fazendas reais)
    crop_locations = {
        'almond': [
            (36.7468, -119.7726, 'Central Valley, CA'),
            (37.6688, -120.5472, 'Modesto, CA'),
            (36.3302, -119.2921, 'Fresno, CA'),
        ],
        'apple': [
            (46.6021, -120.5059, 'Yakima Valley, WA'),
            (47.0379, -122.9007, 'Olympia, WA'),
            (45.7833, -121.5167, 'Hood River, OR'),
        ],
        'cherry': [
            (44.7631, -85.6206, 'Traverse City, MI'),
            (42.3370, -85.1797, 'Kalamazoo, MI'),
            (45.4215, -122.6762, 'Portland, OR'),
        ]
    }
    
    results = {}
    
    # Treinar para cada cultura
    for crop_type, locations in crop_locations.items():
        try:
            ensemble, metrics = train_model_for_crop(crop_type, locations)
            results[crop_type] = {'status': 'success', 'metrics': metrics}
            
        except Exception as e:
            print(f"\n❌ ERRO ao treinar {crop_type}: {str(e)}")
            results[crop_type] = {'status': 'failed', 'error': str(e)}
            continue
    
    # Resumo final
    print("\n" + "="*70)
    print("📋 RESUMO FINAL DO TREINAMENTO")
    print("="*70)
    
    for crop, result in results.items():
        print(f"\n{crop.upper():10s}: ", end='')
        if result['status'] == 'success':
            m = result['metrics']
            print(f"✓ Sucesso | MAE: {m['mae']:.2f} | RMSE: {m['rmse']:.2f} | R²: {m['r2']:.3f}")
        else:
            print(f"✗ Falhou | {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*70)
    print("✅ TREINAMENTO CONCLUÍDO COM DADOS NASA!")
    print("="*70)
    print("\nPróximos passos:")
    print("  1. Revisar métricas em models/*/metrics.json")
    print("  2. Iniciar API: uvicorn main:app --reload")
    print("  3. Testar: curl http://localhost:8000/api/predict/test/almond")
    print("\n")


if __name__ == "__main__":
    main()
