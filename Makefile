# BloomWatch - Makefile
# Comandos úteis para desenvolvimento e deploy

.PHONY: help build up down restart logs test clean train

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[1;33m
NC     := \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo ""
	@echo "$(GREEN)🌸 BloomWatch - Comandos Disponíveis$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Docker Compose
# =============================================================================

build: ## Build das imagens Docker
	@echo "$(GREEN)🔨 Building Docker images...$(NC)"
	docker-compose build

build-no-cache: ## Build sem cache (força rebuild completo)
	@echo "$(GREEN)🔨 Building Docker images (no cache)...$(NC)"
	docker-compose build --no-cache

up: ## Inicia todos os serviços
	@echo "$(GREEN)🚀 Starting all services...$(NC)"
	docker-compose up

up-d: ## Inicia todos os serviços em background
	@echo "$(GREEN)🚀 Starting all services (detached)...$(NC)"
	docker-compose up -d

up-build: ## Build e inicia todos os serviços
	@echo "$(GREEN)🚀 Building and starting all services...$(NC)"
	docker-compose up --build

down: ## Para todos os serviços
	@echo "$(YELLOW)⏹️  Stopping all services...$(NC)"
	docker-compose down

down-v: ## Para todos os serviços e remove volumes (⚠️ apaga modelos)
	@echo "$(YELLOW)⚠️  Stopping all services and removing volumes...$(NC)"
	docker-compose down -v

restart: ## Reinicia todos os serviços
	@echo "$(YELLOW)🔄 Restarting all services...$(NC)"
	docker-compose restart

restart-backend: ## Reinicia apenas backend
	@echo "$(YELLOW)🔄 Restarting backend...$(NC)"
	docker-compose restart backend

restart-frontend: ## Reinicia apenas frontend
	@echo "$(YELLOW)🔄 Restarting frontend...$(NC)"
	docker-compose restart frontend

# =============================================================================
# Logs
# =============================================================================

logs: ## Mostra logs de todos os serviços
	docker-compose logs -f

logs-backend: ## Mostra logs do backend
	docker-compose logs -f backend

logs-frontend: ## Mostra logs do frontend
	docker-compose logs -f frontend

# =============================================================================
# Status e Monitoring
# =============================================================================

ps: ## Mostra status dos containers
	docker-compose ps

stats: ## Mostra uso de recursos (CPU, memória)
	docker stats

health: ## Verifica health dos serviços
	@echo "$(GREEN)🏥 Checking health...$(NC)"
	@echo "\nBackend:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend não está respondendo"
	@echo "\nFrontend:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 && echo "✅ Frontend está rodando" || echo "❌ Frontend não está respondendo"

# =============================================================================
# Development
# =============================================================================

shell-backend: ## Abre shell no container backend
	docker-compose exec backend bash

shell-frontend: ## Abre shell no container frontend
	docker-compose exec frontend sh

train: ## Treina modelos ML dentro do container
	@echo "$(GREEN)🧠 Training ML models...$(NC)"
	docker-compose exec backend python train_models.py

test-backend: ## Roda testes do backend
	@echo "$(GREEN)🧪 Running backend tests...$(NC)"
	docker-compose exec backend python test_api.py

test-api: ## Testa API endpoints (do host)
	@echo "$(GREEN)🧪 Testing API endpoints...$(NC)"
	@echo "\n1. Health Check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo "\n2. List Crops:"
	@curl -s http://localhost:8000/api/crops | python3 -m json.tool
	@echo "\n3. Test Prediction (Almond):"
	@curl -s http://localhost:8000/api/predict/test/almond | python3 -m json.tool

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove containers, images e volumes (limpeza completa)
	@echo "$(YELLOW)🧹 Cleaning up Docker resources...$(NC)"
	docker-compose down -v --rmi all

clean-models: ## Remove modelos treinados (vai retreinar na próxima execução)
	@echo "$(YELLOW)🗑️  Removing trained models...$(NC)"
	rm -rf backend/models/*/
	@echo "$(GREEN)✓ Models removed. Will retrain on next startup.$(NC)"

prune: ## Remove todos os recursos Docker não utilizados
	@echo "$(YELLOW)🧹 Pruning unused Docker resources...$(NC)"
	docker system prune -af

# =============================================================================
# Local Development (sem Docker)
# =============================================================================

install-backend: ## Instala dependências do backend (local)
	@echo "$(GREEN)📦 Installing backend dependencies...$(NC)"
	cd backend && pip install -r requirements.txt

install-frontend: ## Instala dependências do frontend (local)
	@echo "$(GREEN)📦 Installing frontend dependencies...$(NC)"
	cd frontend && npm install

dev-backend: ## Inicia backend local (sem Docker)
	@echo "$(GREEN)🚀 Starting backend (local)...$(NC)"
	cd backend && uvicorn main:app --reload

dev-frontend: ## Inicia frontend local (sem Docker)
	@echo "$(GREEN)🚀 Starting frontend (local)...$(NC)"
	cd frontend && npm run dev

train-local: ## Treina modelos localmente (sem Docker)
	@echo "$(GREEN)🧠 Training models (local)...$(NC)"
	cd backend && python train_models.py

# =============================================================================
# Documentation
# =============================================================================

docs: ## Abre documentação da API no navegador
	@echo "$(GREEN)📚 Opening API docs...$(NC)"
	open http://localhost:8000/docs

redoc: ## Abre ReDoc da API no navegador
	@echo "$(GREEN)📚 Opening ReDoc...$(NC)"
	open http://localhost:8000/redoc

# =============================================================================
# Quick Commands
# =============================================================================

demo: up-build ## Build e inicia demo completo (equivalente a up-build)

stop: down ## Para todos os serviços (atalho para down)

fresh: down-v up-build ## Recomeça do zero (remove tudo e rebuilda)

quick-test: ## Teste rápido de todas as culturas
	@echo "$(GREEN)🧪 Quick test of all crops...$(NC)"
	@echo "\n🌰 Almonds:"
	@curl -s http://localhost:8000/api/predict/test/almond | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  Bloom in {data['days_until_bloom']} days ({data['predicted_bloom_date']})\")"
	@echo "\n🍎 Apples:"
	@curl -s http://localhost:8000/api/predict/test/apple | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  Bloom in {data['days_until_bloom']} days ({data['predicted_bloom_date']})\")"
	@echo "\n🍒 Cherries:"
	@curl -s http://localhost:8000/api/predict/test/cherry | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  Bloom in {data['days_until_bloom']} days ({data['predicted_bloom_date']})\")"
	@echo ""

# =============================================================================
# Info
# =============================================================================

info: ## Mostra informações do projeto
	@echo ""
	@echo "$(GREEN)🌸 BloomWatch - Project Information$(NC)"
	@echo ""
	@echo "  Backend:  Python 3.11 + FastAPI + TensorFlow"
	@echo "  Frontend: Next.js 14 + React + TypeScript"
	@echo "  ML:       LSTM + Random Forest + ANN Ensemble"
	@echo ""
	@echo "  URLs:"
	@echo "    Frontend:  http://localhost:3000"
	@echo "    Backend:   http://localhost:8000"
	@echo "    API Docs:  http://localhost:8000/docs"
	@echo ""
	@echo "  Docker:"
	@docker-compose version 2>/dev/null || echo "    ⚠️  Docker Compose not found"
	@docker --version 2>/dev/null || echo "    ⚠️  Docker not found"
	@echo ""

version: ## Mostra versões das ferramentas
	@echo "$(GREEN)Versions:$(NC)"
	@python3 --version 2>/dev/null || echo "Python: not found"
	@node --version 2>/dev/null || echo "Node: not found"
	@docker --version 2>/dev/null || echo "Docker: not found"
	@docker-compose version 2>/dev/null || echo "Docker Compose: not found"

# Default target
.DEFAULT_GOAL := help

