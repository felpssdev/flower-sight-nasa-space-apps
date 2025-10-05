# 🚀 Deploy FlowerSight - Guia Rápido

## ⚡ Deploy em 3 Passos (Railway.app)

### **1. Preparar**
```bash
# Certifique-se de ter um repositório GitHub
git remote -v  # Verificar se tem remote

# Se não tiver:
git remote add origin https://github.com/seu-usuario/flowersight.git
git push -u origin main
```

### **2. Deploy**

#### **Opção A: Via Web (MAIS FÁCIL)** ⭐
1. Acesse: https://railway.app/new
2. Clique em **"Deploy from GitHub repo"**
3. Selecione seu repositório
4. Railway detecta Docker automaticamente

#### **Opção B: Via CLI**
```bash
# Instalar Railway CLI
brew install railway  # macOS
# ou: npm install -g @railway/cli

# Executar script
./railway-deploy.sh
```

### **3. Configurar Variáveis**

No dashboard Railway, adicione:

**Backend:**
```
NASA_USERNAME=seu_usuario_nasa
NASA_PASSWORD=sua_senha_nasa
```

**Frontend:**
```
NEXT_PUBLIC_API_URL=https://seu-backend.up.railway.app
```

---

## ✅ Pronto!

Seu FlowerSight estará online em ~20 minutos!

**URLs:**
- Frontend: `https://flowersight.up.railway.app`
- Backend: `https://flowersight-backend.up.railway.app`
- API Docs: `https://flowersight-backend.up.railway.app/docs`

---

## 📚 Documentação Completa

- 📖 [**Guia Detalhado Railway**](RAILWAY_DEPLOY.md)
- 🐳 [**Docker Local**](DOCKER.md)
- 🔌 [**API Docs**](API_PARAMETERS.md)

---

## 💰 Custos

| Plano | Custo | Para |
|-------|-------|------|
| **Hobby** | $5/mês | Dev/Demo |
| **Pro** | $20/mês | Produção |

**Recomendação:** Comece com Hobby ($5/mês)

---

## 🆘 Problemas?

### Backend timeout no primeiro deploy?
**Normal!** Treinamento de modelos leva 15-20 min na primeira vez.

### Frontend não carrega?
Verifique se `NEXT_PUBLIC_API_URL` está configurado corretamente.

### Erro de memória?
Upgrade para Pro ($20/mês) ou otimize modelos.

---

## 📞 Suporte

- Railway: https://railway.app/help
- Issues: https://github.com/seu-repo/issues

---

**🌸 FlowerSight - Deploy Simples e Rápido!**

