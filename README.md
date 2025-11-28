# Job Seek - Intelligent Job Search Platform

Plateforme de recherche d'emploi intelligente avec scoring automatique V2, analyse de CV par IA, et recherche en temps réel sur plusieurs plateformes.

## 🚀 Quick Start

### Docker (Recommandé)
```bash
# Démarrer l'application
docker-compose up -d

# Accéder à l'app
# Frontend: http://localhost:3001
# Backend API: http://localhost:8001/docs
```

### Identifiants de test
```
Email: admin@jobseek.com
Password: admin12345678
```

## ✨ Fonctionnalités

### 🎯 Scoring V2 (100 points)
Système de notation fixe sur 6 catégories pour les postes Product Manager:
- **Role/Seniority** (35 pts) - Détection Junior/PM/Senior/Head
- **Geography** (25 pts) - Remote/Hybrid/Office + ville préférée
- **Salary** (15 pts) - Interpolation linéaire €50k-€80k+
- **Skills** (20 pts) - Matching compétences CV + prioritaires
- **Attractiveness** (10 pts) - Mots-clés mission-driven/startup
- **Penalties** (-10 pts) - Qualité (date, description, source)

### 🔍 Recherche en Temps Réel
- Panneau de recherche avec mots-clés + ville
- Streaming SSE pour voir la progression en direct
- Scraping simultané: LinkedIn, Indeed, Glassdoor, WTTJ
- Affichage de TOUTES les offres (matched + unmatched)

### 📊 Affichage Intelligent
- ✅ **Match** (score ≥ 40) - Bordure verte
- 📋 **À revoir** (score < 40) - Bordure grise, atténué
- Toggle pour masquer les non-matched
- Compteurs matched vs unmatched
- Re-scoring dynamique quand les critères changent

### 🤖 Analyse IA
- Upload de CV avec extraction automatique (Anthropic Claude)
- Génération de lettres de motivation personnalisées
- Description de profil générée par IA

## 🛠️ Architecture

```
Job Seek/
├── src/                 # Backend FastAPI
│   ├── routers/        # Endpoints API
│   ├── services/       # Logique métier (scoring, scraping)
│   ├── models/         # Models SQLAlchemy
│   └── scrapers/       # Scrapers plateforme
├── frontend/           # Frontend React + TypeScript
│   ├── src/pages/     # Pages (Dashboard, Criteria, etc.)
│   └── src/components/ # Composants réutilisables
└── docs/              # Documentation
```

## 🔧 Développement

### Backend
```bash
source venv/bin/activate
uvicorn src.main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:5174
```

### Tests
```bash
pytest tests/ -v
```

## 📝 API Endpoints

- **Docs**: http://localhost:8001/docs
- **Health**: GET `/health` et GET `/api/health`
- **Auth**: `/api/auth/` (register, login, me)
- **Profile**: `/api/profile/` (CRUD, CV upload)
- **Criteria V2**: `/api/criteria/preferences/v2` (V2 scoring system)
- **Blacklist**: `/api/blacklist/` (CRUD)
- **Jobs V2**: `/api/jobs/scored/v2` (V2 scoring with breakdown)
- **Search SSE**: `/api/search/jobs/stream` (real-time streaming)

## 🗄️ Base de Données

- PostgreSQL 15
- Port: 5433 (externe), 5432 (interne Docker)
- Credentials: `jobseek:jobseek_password`
- Database: `jobseek_db`

## 🔑 Variables d'Environnement

Créer un fichier `.env`:
```bash
JWT_SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-...
UNIPILE_DSN=https://api21.unipile.com:15160
UNIPILE_API_KEY=your-unipile-key
UNIPILE_LINKEDIN_ACCOUNT_ID=your-account-id
```

## 📚 Documentation

- **WARP.md** - Guide complet pour WARP avec tous les patterns
- **CHANGELOG.md** - Historique détaillé des modifications
- **docs/SCORING_V2.md** - Documentation technique du scoring V2

## 🚢 Déploiement

```bash
# Production build
docker-compose up -d --build

# View logs
docker-compose logs -f app       # Backend
docker-compose logs -f frontend  # Frontend

# Arrêter
docker-compose down

# Reset complet (+ DB)
docker-compose down -v
```

## 🎨 Stack Technique

**Backend**:
- FastAPI (Python 3.11)
- SQLAlchemy + PostgreSQL
- Anthropic Claude (analyse CV)
- Unipile API (LinkedIn auth)
- BeautifulSoup4, httpx (scraping)

**Frontend**:
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Zustand (state management)
- Axios + SSE (EventSource)

**Infrastructure**:
- Docker + Docker Compose
- Nginx (reverse proxy)
- SSE (Server-Sent Events)

## 📍 Ports

| Service | Docker | Local Dev |
|---------|--------|-----------|
| Frontend | http://localhost:3001 | http://localhost:5174 |
| Backend | http://localhost:8001 | http://localhost:8001 |
| API Docs | http://localhost:8001/docs | http://localhost:8001/docs |
| Database | 5433 | 5433 |

## 📄 License

Private project

---

Pour plus de détails techniques, voir **WARP.md** et **CHANGELOG.md**
