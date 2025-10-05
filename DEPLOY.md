# 🚀 Deploy FlowerSight - Railway (Simplificado)

## ⚡ Deploy em 4 Passos

Railway precisa de deploy **separado** para cada serviço.

---

### **1. Preparar Backend**

```bash
# railway.toml já está configurado para backend
git add .
git commit -m "Backend ready for Railway"
git push origin main
```

---

### **2. Deploy Backend**

1. **Railway**: https://railway.app/new
2. **Deploy from GitHub repo**
3. **Selecione** seu repositório
4. Railway usa `railway.toml` e `backend/Dockerfile`
5. **Variables** (em Settings):
   ```
   NASA_USERNAME=seu_usuario_nasa
   NASA_PASSWORD=sua_senha_nasa
   PORT=8000
   ```
6. **Deploy** → Aguarde 20 min ⏳

---

### **3. Obter URL do Backend**

Copie a URL (ex: `flowersight-backend-production.up.railway.app`)

---

### **4. Deploy Frontend (Separado)**

**EM OUTRA ABA/PROJETO:**

1. Railway → **+ New Service**
2. **GitHub Repo** → Mesmo repositório
3. **Settings**:
   - Build Command: `cd frontend && npm ci && npm run build`
   - Start Command: `cd frontend && node .next/standalone/server.js`
4. **Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://SUA-URL-BACKEND.up.railway.app
   NODE_ENV=production
   PORT=3000
   ```
5. **Deploy** → 5 min ⏳

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
