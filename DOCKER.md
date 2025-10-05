# 🐳 Docker Guide - FlowerSight

Guia completo para rodar o FlowerSight usando Docker e Docker Compose.

## 📋 Pré-requisitos

- Docker 20.10+ instalado
- Docker Compose 2.0+ instalado
- 8GB RAM disponível (para treinamento dos modelos)
- 5GB espaço em disco

## 🚀 Quick Start

### Opção 1: Build e Run (Recomendado)

```bash
# Na raiz do projeto
docker-compose up --build
```

Isso irá:
1. ✅ Build da imagem do backend (Python + TensorFlow + FastAPI)
2. ✅ Build da imagem do frontend (Next.js)
3. ✅ Treinar modelos ML automaticamente (primeira vez, ~10-15 min)
4. ✅ Iniciar ambos os serviços

**Acesso:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Opção 2: Detached Mode (Background)

```bash
docker-compose up -d --build
```

Para ver logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Opção 3: Apenas Backend

```bash
docker-compose up backend
```

---

## 📦 Serviços Configurados

### Backend (`flowersight-backend`)
- **Porta:** 8000
- **Tecnologias:** Python 3.11, FastAPI, TensorFlow, scikit-learn
- **Features:**
  - Treinamento automático de modelos na primeira execução
  - Modelos persistidos em volume Docker
  - Health check configurado
  - Auto-restart

### Frontend (`flowersight-frontend`)
- **Porta:** 3000
- **Tecnologias:** Next.js 14, React, TypeScript
- **Features:**
  - Conecta automaticamente ao backend via rede interna
  - Aguarda backend estar healthy antes de iniciar
  - Auto-restart

---

## 🔧 Comandos Úteis

### Gerenciamento de Containers

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (⚠️ apaga modelos treinados)
docker-compose down -v

# Restart de um serviço específico
docker-compose restart backend
docker-compose restart frontend

# Ver status dos containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Ver logs apenas do backend
docker-compose logs -f backend
```

### Build e Cache

```bash
# Rebuild sem cache (útil para mudanças no código)
docker-compose build --no-cache

# Rebuild apenas um serviço
docker-compose build backend
docker-compose build frontend

# Pull de novas imagens
docker-compose pull
```

### Acesso aos Containers

```bash
# Executar comando no backend
docker-compose exec backend python train_models.py

# Abrir shell no backend
docker-compose exec backend bash

# Abrir shell no frontend
docker-compose exec frontend sh

# Ver variáveis de ambiente
docker-compose exec backend env
```

---

## 📂 Volumes Persistentes

Os modelos treinados são salvos em volumes para não precisar retreinar:

```yaml
volumes:
  - ./backend/models:/app/models  # Modelos ML
  - ./backend/data:/app/data      # Dados de treinamento
```

**Localização no host:**
- Modelos: `./backend/models/`
- Dados: `./backend/data/`

### Retreinar Modelos

```bash
# Opção 1: Dentro do container
docker-compose exec backend python train_models.py

# Opção 2: Remover modelos e reiniciar (treina automaticamente)
rm -rf backend/models/*
docker-compose restart backend
```

---

## 🌐 Rede Interna

Os serviços se comunicam via rede `flower-sight-network`:

- Frontend acessa backend via: `http://backend:8000`
- Variável de ambiente: `NEXT_PUBLIC_API_URL=http://backend:8000`

**Do host (navegador):**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## 🧪 Testes

### Testar Backend (dentro do container)

```bash
docker-compose exec backend python test_api.py
```

### Testar Backend (do host)

```bash
# Health check
curl http://localhost:8000/health

# Lista culturas
curl http://localhost:8000/api/crops

# Predição de teste
curl http://localhost:8000/api/predict/test/almond

# Predição customizada
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 36.7468,
    "lon": -119.7726,
    "crop_type": "almond",
    "farm_name": "Test Farm"
  }'
```

---

## 🐛 Troubleshooting

### Container do Backend não inicia

**Problema:** `ModuleNotFoundError` ou erro de importação

**Solução:**
```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up backend
```

### Treinamento demora muito

**Esperado:** 10-15 minutos na primeira execução (treina 3 modelos)

Para pular treinamento (usar modelos pré-treinados):
```bash
# Copiar modelos pré-treinados para backend/models/
# Depois:
docker-compose up
```

### Frontend não conecta ao Backend

**Verificar:**
1. Backend está healthy:
   ```bash
   docker-compose ps
   # backend deve mostrar "healthy"
   ```

2. Variável de ambiente está correta:
   ```bash
   docker-compose exec frontend env | grep API_URL
   # Deve mostrar: NEXT_PUBLIC_API_URL=http://backend:8000
   ```

3. Acessar diretamente o backend:
   ```bash
   curl http://localhost:8000/health
   ```

### Porta já em uso

**Erro:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solução:** Alterar porta no `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Muda porta do host para 8001
```

### Falta de memória durante treinamento

**Erro:** `Killed` ou OOM

**Solução:** Aumentar memória do Docker:
- Docker Desktop → Settings → Resources → Memory → 8GB+

---

## 🔐 Variáveis de Ambiente

### Backend

| Variável | Valor Padrão | Descrição |
|----------|-------------|-----------|
| `PYTHONUNBUFFERED` | `1` | Logs em tempo real |
| `TF_CPP_MIN_LOG_LEVEL` | `2` | Reduz verbosidade do TensorFlow |

### Frontend

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `NODE_ENV` | `production` | Modo de produção |
| `NEXT_TELEMETRY_DISABLED` | `1` | Desabilita telemetria |
| `NEXT_PUBLIC_API_URL` | `http://backend:8000` | URL da API (dentro do Docker) |

Para adicionar variáveis customizadas, crie `.env` files:

```bash
# backend/.env
MY_CUSTOM_VAR=value

# frontend/.env.local
NEXT_PUBLIC_CUSTOM_VAR=value
```

Depois, no `docker-compose.yml`:
```yaml
services:
  backend:
    env_file:
      - ./backend/.env
```

---

## 📊 Monitoramento

### Health Checks

```bash
# Status dos health checks
docker-compose ps

# Logs do health check
docker-compose logs backend | grep health
```

### Uso de Recursos

```bash
# Ver uso de CPU, memória, rede
docker stats
```

### Inspecionar Container

```bash
docker inspect flowersight-backend
docker inspect flowersight-frontend
```

---

## 🚀 Deploy em Produção

### Build para produção

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Otimizações recomendadas

1. **Use multi-stage builds** para imagens menores
2. **Configure nginx** como reverse proxy
3. **Use secrets** para credenciais sensíveis
4. **Configure volumes** em storage externo
5. **Setup monitoring** com Prometheus/Grafana
6. **Configure backups** dos modelos treinados

---

## 📚 Recursos

- **Docker Docs:** https://docs.docker.com
- **Docker Compose Docs:** https://docs.docker.com/compose
- **Backend README:** [backend/README.md](backend/README.md)
- **Frontend README:** [frontend/README.md](frontend/README.md)

---

## ✅ Checklist de Validação

Após rodar `docker-compose up`, verificar:

- [ ] Backend healthy: `docker-compose ps` mostra `(healthy)`
- [ ] API responde: `curl http://localhost:8000/health`
- [ ] Modelos carregados: `docker-compose logs backend | grep "Modelos"`
- [ ] Frontend acessível: http://localhost:3000
- [ ] Frontend conecta ao backend (sem erros CORS no console)
- [ ] Predição funciona: `curl http://localhost:8000/api/predict/test/almond`

---

**🎉 Docker setup completo! Happy coding!**

