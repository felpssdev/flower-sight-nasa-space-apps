"""
Script de teste da API FlowerSight
Testa todos os endpoints e valida respostas
"""

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


def print_section(title):
    """Imprime seção formatada"""
    print("\n" + "="*70)
    print(f"🧪 {title}")
    print("="*70)


def test_root():
    """Testa endpoint raiz"""
    print_section("Testando GET /")
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['service'] == 'FlowerSight API'
    print("✓ Teste passou!")


def test_health():
    """Testa health check"""
    print_section("Testando GET /health")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    print("✓ Teste passou!")


def test_crops():
    """Testa listagem de culturas"""
    print_section("Testando GET /api/crops")
    
    response = requests.get(f"{BASE_URL}/api/crops")
    print(f"Status: {response.status_code}")
    
    data = response.json()
    print(f"\nCulturas disponíveis:")
    for crop in data['crops']:
        print(f"  {crop['icon']} {crop['name']} ({crop['id']})")
        print(f"     Floração típica: {crop['typical_bloom']}")
    
    assert response.status_code == 200
    assert len(data['crops']) == 3
    print("\n✓ Teste passou!")


def test_prediction(crop_type='almond', lat=36.7468, lon=-119.7726, farm_name='Test Farm'):
    """Testa predição de floração"""
    print_section(f"Testando POST /api/predict ({crop_type})")
    
    payload = {
        "lat": lat,
        "lon": lon,
        "crop_type": crop_type,
        "farm_name": farm_name
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=payload
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n🌸 PREDIÇÃO DE FLORAÇÃO:")
        print(f"   Fazenda: {data['farm_name']}")
        print(f"   Cultura: {data['crop_type']}")
        print(f"   Localização: {data['location']}")
        print(f"\n   Data prevista: {data['predicted_bloom_date']}")
        print(f"   Dias até floração: {data['days_until_bloom']}")
        print(f"   Intervalo de confiança: {data['confidence_low']} até {data['confidence_high']}")
        print(f"   Concordância dos modelos: {data['agreement_score']:.1%}")
        
        print(f"\n   Predições individuais:")
        for model, value in data['individual_predictions'].items():
            print(f"      {model.upper():5s}: {value:.1f} dias")
        
        print(f"\n   Recomendações:")
        for i, rec in enumerate(data['recommendations'], 1):
            print(f"      {i}. {rec}")
        
        if data['ndvi_trend']:
            print(f"\n   NDVI Trend: {len(data['ndvi_trend'])} pontos")
            print(f"      Último valor: {data['ndvi_trend'][-1]['ndvi']:.3f} ({data['ndvi_trend'][-1]['date']})")
        
        # Validações
        assert data['days_until_bloom'] >= 0, "Dias até floração deve ser >= 0"
        assert 0 <= data['agreement_score'] <= 1, "Agreement score deve estar entre 0 e 1"
        assert len(data['recommendations']) > 0, "Deve ter recomendações"
        
        print("\n✓ Teste passou!")
        return data
    else:
        print(f"\n❌ Erro: {response.json()}")
        return None


def test_quick_prediction(crop_type='almond'):
    """Testa endpoint de teste rápido"""
    print_section(f"Testando GET /api/predict/test/{crop_type}")
    
    response = requests.get(f"{BASE_URL}/api/predict/test/{crop_type}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🌸 Predição para {crop_type}:")
        print(f"   {data['farm_name']}")
        print(f"   Floração em {data['days_until_bloom']} dias ({data['predicted_bloom_date']})")
        print("✓ Teste passou!")
        return data
    else:
        print(f"❌ Erro: {response.json()}")
        return None


def test_invalid_crop():
    """Testa cultura inválida"""
    print_section("Testando cultura inválida")
    
    payload = {
        "lat": 36.0,
        "lon": -119.0,
        "crop_type": "banana",  # Cultura não suportada
        "farm_name": "Test"
    }
    
    response = requests.post(f"{BASE_URL}/api/predict", json=payload)
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 400
    print("✓ Teste passou! (erro esperado)")


def run_all_tests():
    """Executa todos os testes"""
    
    print("\n" + "🚀"*35)
    print("FLOWERSIGHT API - SUITE DE TESTES")
    print("🚀"*35)
    
    try:
        # Testes básicos
        test_root()
        test_health()
        test_crops()
        
        # Testes de predição
        print("\n" + "🌸"*35)
        print("TESTES DE PREDIÇÃO")
        print("🌸"*35)
        
        test_prediction(crop_type='almond', lat=36.7468, lon=-119.7726, farm_name='Central Valley Farm')
        test_prediction(crop_type='apple', lat=46.6021, lon=-120.5059, farm_name='Yakima Valley Farm')
        test_prediction(crop_type='cherry', lat=44.7631, lon=-85.6206, farm_name='Traverse City Farm')
        
        # Testes rápidos
        print("\n" + "⚡"*35)
        print("TESTES RÁPIDOS")
        print("⚡"*35)
        
        for crop in ['almond', 'apple', 'cherry']:
            test_quick_prediction(crop)
        
        # Teste de erro
        test_invalid_crop()
        
        # Resumo
        print("\n" + "="*70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*70)
        print("\n🎉 API está funcionando corretamente!\n")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}\n")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar à API em {BASE_URL}")
        print("   Certifique-se que a API está rodando com: uvicorn main:app --reload\n")
        return False
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}\n")
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

