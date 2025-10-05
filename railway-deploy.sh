#!/bin/bash

# 🚂 Script de Deploy Rápido para Railway.app
# FlowerSight - NASA Space Apps 2025

set -e

echo "🌸 FlowerSight - Deploy Railway.app"
echo "====================================="
echo ""

# Verificar se railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI não encontrado!"
    echo ""
    echo "Instale com:"
    echo "  brew install railway"
    echo "  ou"
    echo "  npm install -g @railway/cli"
    echo ""
    exit 1
fi

echo "✅ Railway CLI encontrado"
echo ""

# Login (se necessário)
echo "🔐 Verificando autenticação..."
railway whoami &> /dev/null || railway login

echo "✅ Autenticado no Railway"
echo ""

# Perguntar credenciais NASA
echo "🛰️  Configuração NASA Earthdata"
echo "--------------------------------"
read -p "NASA Username: " NASA_USER
read -sp "NASA Password: " NASA_PASS
echo ""
echo ""

# Criar ou linkar projeto
echo "📦 Configurando projeto Railway..."
echo ""
echo "Escolha uma opção:"
echo "  1) Criar novo projeto"
echo "  2) Linkar a projeto existente"
read -p "Opção (1/2): " OPTION

if [ "$OPTION" = "1" ]; then
    railway init
else
    railway link
fi

echo ""
echo "✅ Projeto configurado"
echo ""

# Configurar variáveis de ambiente do backend
echo "⚙️  Configurando variáveis do Backend..."
railway variables set NASA_USERNAME="$NASA_USER" --service backend
railway variables set NASA_PASSWORD="$NASA_PASS" --service backend
railway variables set PYTHONUNBUFFERED=1 --service backend
railway variables set TF_CPP_MIN_LOG_LEVEL=2 --service backend
railway variables set PORT=8000 --service backend

echo "✅ Backend configurado"
echo ""

# Deploy backend
echo "🚀 Deploy do Backend..."
echo ""
echo "⏳ Isso pode levar 15-20 minutos (treina modelos na primeira vez)"
echo ""
cd backend
railway up --service backend
cd ..

echo ""
echo "✅ Backend deployed!"
echo ""

# Obter URL do backend
BACKEND_URL=$(railway domain --service backend)
echo "📡 Backend URL: https://$BACKEND_URL"
echo ""

# Configurar variáveis do frontend
echo "⚙️  Configurando variáveis do Frontend..."
railway variables set NEXT_PUBLIC_API_URL="https://$BACKEND_URL" --service frontend
railway variables set NODE_ENV=production --service frontend
railway variables set NEXT_TELEMETRY_DISABLED=1 --service frontend
railway variables set PORT=3000 --service frontend

echo "✅ Frontend configurado"
echo ""

# Deploy frontend
echo "🚀 Deploy do Frontend..."
echo ""
cd frontend
railway up --service frontend
cd ..

echo ""
echo "✅ Frontend deployed!"
echo ""

# Obter URL do frontend
FRONTEND_URL=$(railway domain --service frontend)

echo ""
echo "🎉 DEPLOY CONCLUÍDO!"
echo "===================="
echo ""
echo "📍 URLs do seu projeto:"
echo "  🌐 Frontend:  https://$FRONTEND_URL"
echo "  🔌 Backend:   https://$BACKEND_URL"
echo "  📚 API Docs:  https://$BACKEND_URL/docs"
echo ""
echo "✅ Acesse o frontend e faça uma predição de teste!"
echo ""
echo "💡 Comandos úteis:"
echo "  railway logs --service backend   # Ver logs do backend"
echo "  railway logs --service frontend  # Ver logs do frontend"
echo "  railway status                   # Status dos serviços"
echo ""
echo "🌸 FlowerSight está no ar!"

