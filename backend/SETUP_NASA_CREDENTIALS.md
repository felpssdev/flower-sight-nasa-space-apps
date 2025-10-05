# 🔐 Como Configurar Credenciais NASA (Sem Google!)

Guia completo para obter NDVI real direto da NASA via AppEEARS.

---

## 🎯 Por que AppEEARS?

**NASA AppEEARS** (Application for Extracting and Exploring Analysis Ready Samples)

✅ **Direto da NASA** - Sem passar pelo Google Earth Engine  
✅ **Dados MODIS oficiais** - 250m resolução, 16 dias  
✅ **Gratuito** - Sem custos  
✅ **API REST** - Fácil de integrar  
✅ **Sem rate limits severos** - Razoável para uso

---

## 📝 Passo 1: Criar Conta NASA Earthdata (5 minutos)

### 1.1 Acessar o Registro

**URL:** https://urs.earthdata.nasa.gov/users/new

### 1.2 Preencher Formulário

```
Username:          seu_username
Email:             seu@email.com
Password:          sua_senha_segura
Confirm Password:  sua_senha_segura
Country:           Brazil

[ ] I agree to the Earthdata Login Terms of Use
```

### 1.3 Verificar Email

Você receberá um email de confirmação. Clique no link para ativar sua conta.

### 1.4 Aprovar AppEEARS

1. Faça login em: https://appeears.earthdatacloud.nasa.gov/
2. Clique em "Log In" (canto superior direito)
3. Use suas credenciais NASA Earthdata
4. Aceite os termos de uso do AppEEARS

**✅ Conta configurada!**

---

## 🔧 Passo 2: Configurar no FlowerSight

### Opção A: Variáveis de Ambiente (Recomendado)

```bash
# Linux/Mac
export NASA_USERNAME='seu_username'
export NASA_PASSWORD='sua_senha'

# Permanente (adicionar ao ~/.bashrc ou ~/.zshrc)
echo 'export NASA_USERNAME="seu_username"' >> ~/.bashrc
echo 'export NASA_PASSWORD="sua_senha"' >> ~/.bashrc
source ~/.bashrc
```

```powershell
# Windows PowerShell
$env:NASA_USERNAME='seu_username'
$env:NASA_PASSWORD='sua_senha'

# Permanente
[System.Environment]::SetEnvironmentVariable('NASA_USERNAME', 'seu_username', 'User')
[System.Environment]::SetEnvironmentVariable('NASA_PASSWORD', 'sua_senha', 'User')
```

### Opção B: Arquivo .env

```bash
cd backend

# Criar arquivo .env
cat > .env << EOF
NASA_USERNAME=seu_username
NASA_PASSWORD=sua_senha
EOF

# Instalar python-dotenv
pip install python-dotenv
```

No código Python:
```python
from dotenv import load_dotenv
load_dotenv()

# Agora os.getenv('NASA_USERNAME') vai funcionar
```

### Opção C: Passar Direto no Código

```python
from nasa_data_fetcher import fetch_nasa_data

data = fetch_nasa_data(
    lat=36.7468,
    lon=-119.7726,
    crop_type='almond',
    use_appeears=True,
    nasa_username='seu_username',  # ← Direto aqui
    nasa_password='sua_senha'       # ← Direto aqui
)
```

---

## 🧪 Passo 3: Testar Conexão

### Teste Simples

```bash
cd backend

# Configurar credenciais
export NASA_USERNAME='seu_username'
export NASA_PASSWORD='sua_senha'

# Testar
python nasa_appeears.py
```

**Saída esperada:**
```
🛰️ NASA AppEEARS NDVI Fetcher - Teste
======================================================================
Testando busca de NDVI MODIS...
Localização: Central Valley, CA (amêndoas)
======================================================================

✓ Autenticado na NASA AppEEARS
📡 Buscando dados MODIS NDVI via NASA AppEEARS
   Localização: 36.7468, -119.7726
   Período: 10-05-2024 até 12-04-2024
✓ Requisição submetida: task_id=abc123...
⏳ Aguardando processamento (timeout: 600s)...
   Status: processing
   Status: done
✓ Processamento concluído!
✓ Dados baixados: 4 registros

======================================================================
✅ SUCESSO!
======================================================================

📊 Dados obtidos:
   Registros: 4
   Período: 2024-10-05 até 2024-11-25
   
   NDVI:
      Média: 0.523
      Máximo: 0.687
      Mínimo: 0.342
```

### Teste na API

```bash
# Terminal 1: Iniciar API
cd backend
uvicorn main:app --reload

# Terminal 2: Testar
curl http://localhost:8000/api/predict/test/almond
```

Se configurado corretamente, a API usará dados MODIS reais automaticamente!

---

## 🔄 Passo 4: Integrar no main.py

### Atualizar função fetch_ndvi_data

Edite `backend/main.py`:

```python
# Substituir esta função:
def fetch_ndvi_data(lat: float, lon: float, crop_type: str, days: int = 90):
    """Busca dados NDVI (atual: sintéticos)"""
    from data_generator import BloomDataGenerator
    ...

# Por esta:
def fetch_ndvi_data(lat: float, lon: float, crop_type: str, days: int = 90):
    """Busca dados NDVI REAIS da NASA AppEEARS"""
    from nasa_data_fetcher import fetch_nasa_data
    
    return fetch_nasa_data(
        lat=lat,
        lon=lon,
        crop_type=crop_type,
        days=days,
        use_appeears=True,      # ← Ativa AppEEARS
        use_earth_engine=False  # ← Sem Google
    )
```

### Reiniciar API

```bash
# Ctrl+C para parar
# Reiniciar
uvicorn main:app --reload
```

**✅ Agora sua API usa dados MODIS reais da NASA!**

---

## 📊 Dados Disponíveis

### MODIS MOD13Q1 (Terra)

| Característica | Valor |
|----------------|-------|
| Satélite | Terra |
| Resolução Espacial | 250m |
| Resolução Temporal | 16 dias |
| Produto | MOD13Q1.061 |
| Índices | NDVI, EVI |
| Cobertura | Global |
| Período | 2000 - presente |

### MODIS MYD13Q1 (Aqua)

Mesmas características, satélite diferente (pode combinar os dois para mais frequência).

---

## ⚡ Performance

### Primeira Requisição
- **Processamento:** ~30-60 segundos
- **Download:** ~5-10 segundos
- **Total:** ~1 minuto

### Cache
Para melhorar performance, implemente cache:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379)

def fetch_with_cache(lat, lon, crop_type, days):
    key = f"ndvi:{lat}:{lon}:{days}"
    
    # Verificar cache
    cached = redis_client.get(key)
    if cached:
        return pd.DataFrame(json.loads(cached))
    
    # Buscar da NASA
    data = fetch_nasa_data(lat, lon, crop_type, days)
    
    # Salvar cache (TTL: 16 dias = frequência MODIS)
    redis_client.setex(key, 16*24*3600, data.to_json())
    
    return data
```

---

## 🐛 Troubleshooting

### Erro: "Authentication failed"

**Causa:** Credenciais incorretas

**Solução:**
1. Verificar username/password
2. Testar login manual: https://urs.earthdata.nasa.gov/
3. Resetar senha se necessário

### Erro: "Timeout ao aguardar processamento"

**Causa:** Processamento demorou > 10 minutos (raro)

**Solução:**
```python
# Aumentar timeout em nasa_appeears.py
client.wait_for_completion(task_id, timeout=1800)  # 30 min
```

### Erro: "No granules found"

**Causa:** Localização/período sem dados MODIS

**Solução:**
1. Verificar se lat/lon estão corretos
2. Ampliar período (usar days=180)
3. Usar fallback para dados sintéticos

### Erro: "Connection timeout"

**Causa:** Problemas de rede

**Solução:**
1. Verificar conexão internet
2. Verificar firewall
3. Tentar novamente

---

## 📚 Recursos

### Documentação Oficial
- **AppEEARS:** https://appeears.earthdatacloud.nasa.gov/
- **API Docs:** https://appeears.earthdatacloud.nasa.gov/api/
- **Earthdata:** https://earthdata.nasa.gov/

### Suporte
- **Forum:** https://forum.earthdata.nasa.gov/
- **Email:** support@earthdata.nasa.gov

### Tutoriais
- **Python Examples:** https://github.com/nasa/appeears-api
- **Video Tutorial:** https://www.youtube.com/watch?v=X1234 (buscar no YouTube)

---

## ✅ Checklist Final

- [ ] Conta NASA Earthdata criada
- [ ] Email confirmado
- [ ] Login aprovado em AppEEARS
- [ ] Variáveis de ambiente configuradas
- [ ] Teste `nasa_appeears.py` passou
- [ ] `main.py` atualizado
- [ ] API testada com dados reais
- [ ] Cache implementado (opcional)

---

## 🎉 Pronto!

Agora você está usando **dados MODIS reais direto da NASA**! 

**Sem Google Earth Engine necessário!** 🚀

---

## 💡 Dicas

1. **Desenvolvimento:** Use dados sintéticos (mais rápido)
2. **Demo/Apresentação:** Use dados reais (mais impressionante)
3. **Produção:** Implemente cache para otimizar

```python
# Switch fácil entre modos
USE_REAL_DATA = os.getenv('USE_REAL_NASA_DATA', 'false').lower() == 'true'

if USE_REAL_DATA:
    data = fetch_nasa_data(...)  # Real
else:
    data = generate_synthetic_data(...)  # Sintético
```

**Happy coding!** 🌸

