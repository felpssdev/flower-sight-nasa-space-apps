"""
Script de Treinamento dos Modelos BloomWatch
Gera dados, treina ensemble e salva modelos
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime
from ml_pipeline import BloomWatchEnsemble
from data_generator import BloomDataGenerator, generate_historical_bloom_dates
import json


def train_model_for_crop(crop_type: str, n_years: int = 5, start_year: int = 2020):
    """
    Treina modelo completo para uma cultura específica
    
    Args:
        crop_type: 'almond', 'apple' ou 'cherry'
        n_years: Número de anos de dados históricos
        start_year: Ano inicial dos dados
    """
    
    print("\n" + "="*70)
    print(f"🌸 TREINANDO MODELO PARA: {crop_type.upper()}")
    print("="*70)
    
    # 1. Gerar dados
    print("\n[1/3] Gerando dados sintéticos...")
    generator = BloomDataGenerator(crop_type=crop_type, seed=42)
    data, target = generator.generate_dataset(
        n_years=n_years, 
        start_year=start_year,
        include_climate_change=True
    )
    
    # Filtrar apenas dados válidos (0-90 dias antes da floração)
    valid_mask = (target >= 0) & (target <= 90)
    data_filtered = data[valid_mask].copy()
    target_filtered = target[valid_mask]
    
    print(f"✓ Dados filtrados: {len(data_filtered)} amostras válidas (0-90 dias)")
    
    # Salvar dados brutos
    os.makedirs('data', exist_ok=True)
    data.to_csv(f'data/{crop_type}_full_data.csv', index=False)
    data_filtered.to_csv(f'data/{crop_type}_training_data.csv', index=False)
    np.save(f'data/{crop_type}_target.npy', target_filtered)
    
    # 2. Treinar ensemble
    print("\n[2/3] Treinando ensemble de modelos...")
    ensemble = BloomWatchEnsemble()
    
    metrics = ensemble.train(
        data=data_filtered,
        target=target_filtered,
        val_split=0.2
    )
    
    # 3. Salvar modelos
    print("\n[3/3] Salvando modelos...")
    model_path = f'models/{crop_type}/'
    ensemble.save_models(path=model_path)
    
    # Salvar métricas
    metrics_data = {
        'crop_type': crop_type,
        'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'n_samples': len(data_filtered),
        'n_years': n_years,
        'start_year': start_year,
        'metrics': {
            'mae': float(metrics['mae']),
            'rmse': float(metrics['rmse']),
            'r2': float(metrics['r2'])
        },
        'validation': {
            'target_passed': metrics['mae'] < 5.0,
            'excellent': metrics['mae'] < 4.0 and metrics['r2'] > 0.85
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


def test_trained_model(crop_type: str):
    """
    Testa modelo treinado com predição de exemplo
    """
    
    print("\n" + "="*70)
    print(f"🧪 TESTANDO MODELO: {crop_type.upper()}")
    print("="*70)
    
    # Carregar modelo
    ensemble = BloomWatchEnsemble()
    ensemble.load_models(path=f'models/{crop_type}/')
    
    # Gerar janela de dados (últimos 90 dias)
    print("\n[1/2] Gerando dados de teste (últimos 90 dias)...")
    generator = BloomDataGenerator(crop_type=crop_type, seed=123)
    
    # Simular que estamos 30 dias antes da floração esperada
    pattern = generator.CROP_PATTERNS[crop_type]
    current_doy = pattern['peak_doy'] - 30  # 30 dias antes
    
    test_data = generator.generate_prediction_window(
        current_doy=current_doy,
        year=2025,
        window_days=90
    )
    
    print(f"✓ Janela de teste: {len(test_data)} dias")
    print(f"  Período: DOY {test_data['day_of_year'].min()} até {test_data['day_of_year'].max()}")
    
    # Fazer predição
    print("\n[2/2] Fazendo predição...")
    prediction = ensemble.predict(test_data)
    
    print(f"\n🌸 RESULTADO DA PREDIÇÃO:")
    print(f"   Dias até floração: {prediction['predicted_days']} dias")
    print(f"   Intervalo de confiança: {prediction['confidence_interval']}")
    print(f"   Concordância entre modelos: {prediction['agreement_score']:.1%}")
    
    print(f"\n   Predições individuais:")
    for model_name, pred_value in prediction['individual_predictions'].items():
        print(f"      {model_name.upper():5s}: {pred_value:.1f} dias")
    
    # Validar se está próximo do esperado (30 dias)
    error = abs(prediction['predicted_days'] - 30)
    print(f"\n   Erro em relação ao esperado (30 dias): {error:.1f} dias")
    
    if error < 5:
        print("   ✓ Predição EXCELENTE!")
    elif error < 10:
        print("   ✓ Predição BOA")
    else:
        print("   ⚠️ Predição precisa melhorar")
    
    return prediction


def main():
    """Função principal - treina modelos para todas as culturas"""
    
    print("\n" + "🚀"*35)
    print("BLOOMWATCH - TREINAMENTO COMPLETO DE MODELOS")
    print("🚀"*35 + "\n")
    
    crops = ['almond', 'apple', 'cherry']
    results = {}
    
    # Treinar para cada cultura
    for crop in crops:
        try:
            ensemble, metrics = train_model_for_crop(
                crop_type=crop,
                n_years=5,
                start_year=2020
            )
            results[crop] = {'status': 'success', 'metrics': metrics}
            
            # Testar modelo
            test_trained_model(crop)
            
        except Exception as e:
            print(f"\n❌ ERRO ao treinar {crop}: {str(e)}")
            results[crop] = {'status': 'failed', 'error': str(e)}
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
            print(f"✗ Falhou | {result['error']}")
    
    print("\n" + "="*70)
    print("✅ TREINAMENTO CONCLUÍDO!")
    print("="*70)
    print("\nPróximos passos:")
    print("  1. Revisar métricas em models/*/metrics.json")
    print("  2. Iniciar API FastAPI com: uvicorn main:app --reload")
    print("  3. Testar endpoint: curl -X POST http://localhost:8000/api/predict")
    print("\n")


if __name__ == "__main__":
    main()

