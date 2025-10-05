#!/bin/bash

# FlowerSight Backend - Setup Rápido
# Este script configura o ambiente e treina os modelos

echo ""
echo "🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸"
echo "           FLOWERSIGHT BACKEND - SETUP AUTOMÁTICO"
echo "🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.9+ primeiro."
    exit 1
fi

echo "✓ Python encontrado: $(python3 --version)"
echo ""

# Criar ambiente virtual (opcional mas recomendado)
read -p "Criar ambiente virtual? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Ambiente virtual criado e ativado"
fi

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

echo "✓ Dependências instaladas"

# Criar diretórios
echo ""
echo "📁 Criando estrutura de diretórios..."
mkdir -p models data
echo "✓ Diretórios criados"

# Treinar modelos
echo ""
read -p "Treinar modelos agora? (Demora ~10-15 min) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧠 Treinando modelos..."
    python3 train_models.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Erro ao treinar modelos"
        exit 1
    fi
    
    echo ""
    echo "✓ Modelos treinados com sucesso!"
else
    echo "⚠️  Pule esta etapa por agora. Execute 'python3 train_models.py' quando quiser treinar."
fi

# Finalização
echo ""
echo "================================================================"
echo "✅ SETUP CONCLUÍDO!"
echo "================================================================"
echo ""
echo "Próximos passos:"
echo ""
echo "1. Iniciar API:"
echo "   uvicorn main:app --reload"
echo ""
echo "2. Testar API (em outro terminal):"
echo "   python3 test_api.py"
echo ""
echo "3. Acessar documentação interativa:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. Teste rápido no navegador:"
echo "   http://localhost:8000/api/predict/test/almond"
echo ""
echo "🚀 Boa sorte com o FlowerSight!"
echo ""

