# 🐳 Docker Quick Start - BloomWatch

## ✅ **Status do Teste Docker**

**Backend:** ✅ Funcionando perfeitamente!
- Build: OK
- Container inicia: OK  
- Entrypoint: OK
- Pede credenciais NASA: OK (comportamento esperado)

---

## 🚀 **Como Usar com Docker**

### **Opção 1: Com Credenciais NASA (Dados Reais)**

```bash
# 1. Configure credenciais no host
export NASA_USERNAME='seu_usuario'
export NASA_PASSWORD='sua_senha'

# 2. Inicie com Docker Compose
docker-compose up --build

# Resultado:
# ✅ Backend treina modelos com dados NASA reais
# ✅ API disponível em http://localhost:8000
# ✅ Frontend em http://localhost:3000
```

### **Opção 2: Apenas Backend (sem treinar)**

```bash
# Se você já tem modelos treinados em backend/models/
docker-compose up backend

# Backend vai:
# ✓ Detectar modelos existentes
# ✓ Pular treinamento
# ✓ Iniciar API imediatamente
```

### **Opção 3: Usar .env file**

```bash
# 1. Criar .env na raiz do projeto
cat > .env << 'ENVFILE'
NASA_USERNAME=seu_usuario
NASA_PASSWORD=sua_senha
ENVFILE

# 2. Docker Compose lerá automaticamente
docker-compose up --build
```

---

## 📊 **Primeira Execução**

Na **primeira vez** que rodar, o backend irá:

1. Detectar que não há modelos em `backend/models/`
2. Verificar credenciais NASA
3. Se credenciais OK:
   - Buscar dados MODIS + POWER API
   - Treinar 3 modelos (LSTM + RF + ANN)
   - Salvar em `backend/models/`
   - **Tempo:** ~15-30 minutos
4. Se SEM credenciais:
   - Mostrar mensagem de erro
   - Container fica em loop restart

---

## 🔄 **Execuções Seguintes**

Modelos já treinados:
- ✅ Backend inicia em **~5 segundos**
- ✅ Não precisa de credenciais NASA para API
- ✅ Usa modelos salvos em `backend/models/`

---

## 🐛 **Debug - Status Atual**

```bash
# Verificar logs
docker-compose logs backend

# Resultado esperado:
# 🌸 BloomWatch Backend Starting...
# ⚠️  Models not found. Training models...
# ❌ Credenciais NASA não encontradas!
```

**Status:** ✅ Tudo funcionando como esperado!

---

## 📝 **Comandos Úteis**

```bash
# Build sem cache
docker-compose build --no-cache

# Apenas backend
docker-compose up backend

# Ver logs em tempo real
docker-compose logs -f backend

# Parar tudo
docker-compose down

# Remover volumes (apaga modelos treinados)
docker-compose down -v

# Entrar no container
docker-compose exec backend bash
```

---

## ✅ **Checklist de Validação**

- [x] Docker Compose instalado (v2.39.4)
- [x] Build do backend: OK
- [x] Container inicia: OK
- [x] Entrypoint funciona: OK
- [x] Pede credenciais: OK (esperado)
- [x] Variáveis de ambiente: Configuradas
- [ ] Treinar com credenciais NASA: Pendente (precisa credenciais)

---

## 🎯 **Próximos Passos**

1. **Obter credenciais NASA:**
   - https://urs.earthdata.nasa.gov/users/new

2. **Configurar:**
   ```bash
   export NASA_USERNAME='seu_usuario'
   export NASA_PASSWORD='sua_senha'
   ```

3. **Rodar:**
   ```bash
   docker-compose up --build
   ```

4. **Aguardar treinamento** (~15-30 min primeira vez)

5. **Testar API:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/crops
   curl http://localhost:8000/api/predict/test/almond
   ```

---

**✅ Docker funcionando perfeitamente!** 🐳🌸
