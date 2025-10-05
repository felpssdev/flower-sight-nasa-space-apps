# 🚀 Deploy FlowerSight - SIMPLES COM DOCKER COMPOSE

## ⚡ Deploy em 3 Passos (Railway.app)

Railway **SUPORTA docker-compose.yml** automaticamente! 🎉

---

### **1. Push para GitHub**

```bash
git add .
git commit -m "FlowerSight - Ready for Railway"
git push origin main
```

---

### **2. Deploy no Railway**

1. Acesse: https://railway.app/new
2. Clique em **"Deploy from GitHub repo"**
3. Selecione seu repositório
4. **Railway detecta `docker-compose.yml` automaticamente!**
5. Cria 2 serviços: `backend` e `frontend`

---

### **3. Configurar Variáveis**

**Backend Service:**
```
NASA_USERNAME=seu_usuario_nasa
NASA_PASSWORD=sua_senha_nasa
```

**Frontend Service:**
```
NEXT_PUBLIC_API_URL=https://seu-backend-url.up.railway.app
```

⚠️ **IMPORTANTE:** 
1. Obtenha a URL do backend primeiro
2. Configure no frontend
3. Redeploy frontend se necessário

---

## ✅ Pronto!

**URLs:**
- Frontend: `https://flowersight.up.railway.app`
- Backend: `https://flowersight-backend.up.railway.app`
- API Docs: `https://flowersight-backend.up.railway.app/docs`

---

## 🐛 Troubleshooting

### **Backend demora 20 minutos?**
✅ Normal! Primeira vez treina modelos ML.

### **Frontend não conecta?**
1. Pegue URL real do backend
2. Atualize `NEXT_PUBLIC_API_URL` no frontend
3. Redeploy frontend

### **Erro de memória?**
Upgrade para Railway Pro ($20/mês)

---

## 💰 Custos

| Plano | Custo | Para |
|-------|-------|------|
| **Hobby** | $5/mês | Dev/Demo |
| **Pro** | $20/mês | Produção |

---

## 📋 Checklist

- [ ] Push para GitHub
- [ ] Deploy no Railway
- [ ] Railway detecta docker-compose
- [ ] Configurar NASA credentials (backend)
- [ ] Obter URL do backend
- [ ] Configurar NEXT_PUBLIC_API_URL (frontend)
- [ ] Testar!

---

## 🎯 TL;DR

```bash
# 1. Push
git push origin main

# 2. Railway
https://railway.app/new → Deploy from GitHub

# 3. Configurar variáveis NASA
# (no dashboard Railway)

# 4. PROFIT! 🎉
```

**Railway detecta docker-compose.yml e faz TUDO sozinho!**

---

**🌸 FlowerSight - Deploy Simples com Docker Compose**
