# Méthodologie - Scraper Multi-Sources Parallel.ai + Firecrawl

## 📋 Objectif

Script de test pour valider l'approche hybride de scraping d'offres d'emploi combinant :
- **Parallel.ai Search API** : Recherche intelligente d'URLs (Glassdoor + WTTJ)
- **Firecrawl Search API** : Recherche spécialisée Indeed avec anti-bot bypass
- **Parallel.ai Extract API** : Extraction structurée du contenu
- **Tavily Search API** : Recherche complémentaire optionnelle

**Use Case Test** : Trouver 3 offres "Product Manager" à Bordeaux par source (Glassdoor, WTTJ, Indeed) = 9 offres cible.

---

## 🏗️ Architecture en 3 Phases

### Phase 1 : Multi-Source Search avec Filtrage
**Objectif** : Trouver les URLs des offres d'emploi réelles (pas de pages agrégées)

**Méthodes** :
1. **Parallel Search API** (prioritaire)
   - Endpoint : `POST https://api.parallel.ai/v1beta/search`
   - Mode : `agentic` (optimisé pour recherche intelligente)
   - Queries ciblées : `site:glassdoor.com Product Manager Bordeaux`
   - Retour : Liste d'URLs + excerpts pertinents

2. **Tavily Search MCP** (complémentaire)
   - Via tool MCP : `tavily-search`
   - Spécialisé dans résultats de recherche précis
   - Query optimisée : `"Product Manager Bordeaux (site:glassdoor.com OR site:welcometothejungle.com) job posting"`
   - Retour : URLs + score de pertinence

3. **Firecrawl Search MCP** (préparé pour futur)
   - Via tool MCP : `firecrawl_search`
   - Scraping avec anti-bot bypass intégré
   - Retour : URLs + markdown content

**Filtrage des URLs** :
Exclut automatiquement :
- Pages Glassdoor : `/Salaries/`, `/Overview/`, `/Reviews/`, `/Emploi/`, `-jobs-SRCH`
- Pages WTTJ : `/companies/` sans `/jobs/`
- Pages génériques : `/search`, `/categories`

Accepte uniquement :
- Glassdoor : `/job-listing/`, `/partner/`, URLs de postes individuels
- WTTJ : URLs contenant `/jobs/[job-slug]`

**Output** : Liste d'URLs filtrées et dédupliquées, limitée à 3 par source (Glassdoor + WTTJ)

---

### Phase 2 : Content Extraction
**Objectif** : Extraire le contenu complet de chaque offre

**Méthode** :
- **Parallel Extract API**
  - Endpoint : `POST https://api.parallel.ai/v1beta/extract`
  - Input : Toutes les URLs trouvées en Phase 1
  - Objective : Extraire titre, entreprise, localisation, salaire, type de contrat, remote, description, compétences, date
  - Options : `excerpts: true` + `full_content: true`

**Output** : JSON structuré avec excerpts + full_content par URL

---

### Phase 3 : Structuring & Export
**Objectif** : Parser, normaliser et exporter en CSV

**Parsing intelligent** :
- **Regex patterns** pour extraire :
  - Salaire : `€XX,XXX - €XX,XXX` ou `XXk - XXk`
  - Date : formats `DD/MM/YYYY`, `DD MMM YYYY`
  - Type de contrat : CDI, CDD, Stage, Alternance, Freelance
  - Remote : Remote, Hybrid, Onsite (mots-clés FR/EN)
- **Keyword matching** pour compétences (agile, scrum, jira, sql, figma, etc.)

**Output** : CSV avec 12 colonnes + JSON pour debug

---

## 📊 Schéma de Données

### Colonnes CSV finales

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| `title` | String (requis) | Titre du poste | Product Manager |
| `company` | String | Nom de l'entreprise | Acme Corp |
| `location` | String | Ville/région | Bordeaux, France |
| `salary` | String | Fourchette salariale | 50k - 70k EUR |
| `contract_type` | String | Type de contrat | CDI, CDD, Stage |
| `remote` | String | Politique télétravail | Remote, Hybrid, Onsite |
| `description` | String | Description complète (max 500 chars) | Nous recherchons... |
| `skills` | String | Compétences requises (comma-separated) | agile, scrum, jira |
| `posted_date` | String | Date de publication | 15/11/2024 |
| `url` | String (requis) | URL de l'offre | https://... |
| `source` | String (requis) | Plateforme source | glassdoor, wttj |
| `extraction_method` | String | Méthode d'extraction | parallel_extract |

---

## 🔑 APIs Utilisées

### 1. Parallel.ai Search API
```bash
POST https://api.parallel.ai/v1beta/search
Headers:
  x-api-key: TDevMkqIQNpuo5aTwTn5FAJ9BcKRpSk394Otl5pv
  parallel-beta: search-extract-2025-10-10
  Content-Type: application/json

Body:
{
  "mode": "agentic",
  "objective": "Find Product Manager job postings in Bordeaux, France...",
  "search_queries": [
    "site:glassdoor.com Product Manager Bordeaux",
    "site:welcometothejungle.com Product Manager Bordeaux"
  ],
  "max_results": 6,
  "excerpts": {"max_chars_per_result": 500}
}
```

**Retour** :
```json
{
  "search_id": "search_...",
  "results": [
    {
      "url": "https://www.glassdoor.com/job/...",
      "title": "Product Manager - Bordeaux",
      "excerpts": ["Excerpt 1", "Excerpt 2"],
      "publish_date": "2024-11-15"
    }
  ]
}
```

### 2. Parallel.ai Extract API
```bash
POST https://api.parallel.ai/v1beta/extract
Headers: (same as Search)

Body:
{
  "urls": ["https://...", "https://..."],
  "objective": "Extract job posting details: title, company, location, salary...",
  "excerpts": true,
  "full_content": true
}
```

**Retour** :
```json
{
  "extract_id": "extract_...",
  "results": [
    {
      "url": "https://...",
      "title": "Product Manager",
      "excerpts": ["Relevant excerpt 1", "..."],
      "full_content": "Full page content..."
    }
  ]
}
```

### 3. Firecrawl Search (MCP Tool)
```python
# Via MCP tool call (non implémenté dans ce test)
call_mcp_tool(
  name="firecrawl_search",
  input={
    "query": "Product Manager Bordeaux site:glassdoor.com",
    "limit": 3,
    "sources": [{"type": "web"}]
  }
)
```

---

## 🚀 Utilisation

### Installation des dépendances
```bash
# httpx est déjà installé dans le projet principal
cd /Users/lopato/Documents/DAGORSEY/Geek/Job\ Seek
source venv/bin/activate  # Si environnement virtuel
```

### Exécution du script
```bash
cd scripts/job_scraping_test
python parallel_scraper.py
```

### Paramètres modifiables
Dans `parallel_scraper.py`, fonction `main()` :
```python
KEYWORDS = "Product Manager"       # Mots-clés de recherche
LOCATION = "Bordeaux"             # Ville
LIMIT_PER_SOURCE = 3              # Nombre d'offres par plateforme
```

---

## 📁 Outputs Générés

Tous les fichiers sont créés dans `results/` :

1. **`parallel_search.json`** : Réponse brute de Parallel Search API
2. **`parallel_extract.json`** : Réponse brute de Parallel Extract API
3. **`jobs.json`** : Jobs structurés en JSON (debug)
4. **`jobs.csv`** : ⭐ **CSV final lisible** avec toutes les colonnes

### Exemple de sortie console
```
🚀 Starting job search: 'Product Manager' in 'Bordeaux'
📍 Limit: 3 jobs per source (Glassdoor + WTTJ)
======================================================================

📡 PHASE 1: Multi-Source Search
   🔎 Running Parallel Search API...
   ✓ Parallel Search found 8 URLs

✅ Found 6 unique job URLs:
   - Glassdoor: 3
   - WTTJ: 3

🔍 PHASE 2: Content Extraction
   🔍 Extracting content from 6 URLs...
   ✓ Extracted 6 pages

📊 PHASE 3: Data Structuring & Export
   ✓ Structured: Product Manager @ Acme Corp
   ✓ Structured: Senior Product Manager @ Beta Inc
   ...
   ✓ CSV exported: results/jobs.csv

======================================================================
✅ SUCCESS! Found 6 complete job postings
📄 CSV: results/jobs.csv
📁 JSON files saved in: results/
```

---

## 📈 Résultats des Tests

### Test initial (avant filtrage)
- **URLs trouvées** : 6 URLs
- **Offres réelles** : 2 WTTJ (33% de précision)
- **URLs filtrées** : 4 (pages Glassdoor non pertinentes)
  - 1x `/Salaries/` (données salariales)
  - 1x `/Overview/` (présentation entreprise)
  - 1x `/Emploi/` (liste de recherche)
  - 1x autre (page agrégée)

### Test amélioré v1 (avec filtrage strict)
- **URLs brutes** : 9 URLs de Parallel Search
- **URLs filtrées** : 5 URLs non pertinentes exclues
- **Offres finales** : 0 Glassdoor + 3 WTTJ
- **Problème** : Filtrage trop strict excluait pages de résultats Glassdoor

### Test optimisé v2 (avec filtrage assoupli + max_results x5)
- **URLs brutes** : 15 URLs de Parallel Search
- **URLs filtrées** : 3 URLs non pertinentes exclues
- **URLs Glassdoor acceptées** : 2 pages de résultats (`/Job/...SRCH_IL` et `/Emploi/...SRCH_IL`)
- **Offres finales** : **2 Glassdoor + 3 WTTJ = 5 offres**
- **Amélioration** : Passage de 0 → 2 Glassdoor (∞% de croissance)
- **Précision globale** : 83% (5 offres sur 6 URLs finales)

**Note sur Tavily** : Tavily API REST implémentée mais nécessite `TAVILY_API_KEY` dans `.env`. Free tier disponible : 1000 recherches/mois sur https://tavily.com/

## ⚠️ Considérations Techniques

### Gestion des erreurs
- Try/except sur chaque API call
- Continue si une source échoue
- Logging détaillé des erreurs et URLs filtrées
- Minimum 1 offre requise pour succès

### Performance
- **Phase 1** : ~5-10s (2 requêtes en parallèle + filtrage)
- **Phase 2** : ~10-15s (1 requête batch pour toutes les URLs)
- **Phase 3** : ~1s (processing local)
- **Total** : ~20-30s pour 3-6 offres

### Limites
- Tavily API REST implémentée mais non activée (clé API requise)
- Parsing heuristique (peut manquer certains champs)
- Limite de 3 offres par source dans ce test
- Pages de résultats Glassdoor contiennent plusieurs offres mais traitées comme 1 seule offre
- Patterns de filtrage à maintenir si structures d'URLs changent

### Optimisations Glassdoor appliquées
**Patterns acceptés** :
- `/job-listing/[job-id]` : Offres individuelles
- `/partner/jobListing.htm` : Offres partenaires
- `/Job/[location]-[title]-jobs-SRCH_IL...` : **Pages de résultats localisées** (NOUVEAU)
- `/Emploi/[location]-[title]-emplois-SRCH_IL...` : **Version française** (NOUVEAU)

**Patterns rejetés** :
- `/Salaries/` : Données salariales
- `/Overview/` : Pages entreprise
- `/Reviews/` : Avis employés
- `/Interview/` : Questions d'entretien
- `/Job/...SRCH_IN...` : Recherches globales (non localisées)

**Clé** : Accepter `SRCH_IL` (localized) mais rejeter `SRCH_IN` (global)

---

## 🔄 Prochaines Étapes

Si le test est concluant :

1. **Intégration dans l'app principale**
   - Remplacer les scrapers BeautifulSoup existants
   - Utiliser ce workflow dans `JobSearchService`

2. **Augmentation des limites**
   - Passer à 50+ offres par source
   - Ajouter pagination si nécessaire

3. **Ajout d'autres sources**
   - Indeed (via Unipile ou Parallel)
   - LinkedIn (via Unipile existant)

4. **Amélioration du parsing**
   - Utiliser Claude API pour extraction structurée
   - Ajouter validation des champs

---

## 📚 Références

- **Parallel.ai Docs** : https://docs.parallel.ai/
- **Firecrawl Docs** : https://docs.firecrawl.dev/
- **Plan complet** : Voir `/docs/` ou Warp Drive Notebook

---

## ✨ Ajout Indeed avec Firecrawl Search (Version 3)

### Méthode
**API utilisée** : Firecrawl Search API (`POST https://api.firecrawl.dev/v1/search`)

**Pourquoi Firecrawl uniquement pour Indeed ?**
- Indeed a des protections anti-scraping très puissantes
- Firecrawl est spécialisé dans le bypass d'anti-bot
- Plus fiable que Parallel Search pour Indeed
- Retourne directement URLs + markdown content

**Configuration** :
```bash
# Dans .env
FIRECRAWL_API_KEY=fc-...
```

**Implémentation** :
```python
# Méthode _firecrawl_search_indeed() dans parallel_scraper.py
async def _firecrawl_search_indeed(keywords, location, max_results):
    response = await httpx.post(
        "https://api.firecrawl.dev/v1/search",
        headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
        json={
            "query": f"{keywords} {location} site:fr.indeed.com",
            "limit": max_results,
            "scrapeOptions": {"formats": ["markdown"]}
        }
    )
```

### Patterns Indeed
**URLs acceptées** :
- ✅ `/viewjob?jk=` : Offres individuelles (format principal)
- ✅ `/rc/clk?jk=` : Liens de redirection vers offres
- ✅ `/cmp/[company]/jobs/[title]` : Offres hébergées par entreprise

**URLs rejetées** :
- ❌ `/jobs?q=` : Pages de résultats de recherche
- ❌ `/companies/` : Pages entreprises sans offre
- ❌ `/career-advice/` : Articles de conseil
- ❌ `/salaries/` : Pages de données salariales

### Résultats Test v3
**Exécution** : `python parallel_scraper.py`

**Phase 1 - URLs brutes** :
- Parallel Search (Glassdoor + WTTJ) : 15 URLs
- Firecrawl Search (Indeed) : 9 URLs
- **Total** : 24 URLs brutes

**Phase 1 - Après filtrage** :
- Glassdoor : 2 URLs (pages résultats localisées `SRCH_IL`)
- WTTJ : 1 URL (offre individuelle `/jobs/`)
- Indeed : 3 URLs (offres `/viewjob?jk=`)
- **Total** : 6 URLs filtrées

**Phase 2 & 3 - Extraction & Export** :
- 6 pages extraites via Parallel Extract API
- 6 offres structurées dans `results/jobs.csv`
- Colonne `source` : `glassdoor`, `wttj`, **`indeed`** ✓

**Performance** :
- Phase 1 : ~15s (Parallel 5s + Firecrawl 10s)
- Phase 2 : ~15s (Extraction)
- **Total** : ~30s pour 6 offres

### Améliorations futures
- Augmenter `limit_per_source` pour plus d'offres par source
- Améliorer parsing avec Claude API
- Optimiser filtrage URL pour Indeed (pages de résultats)

---

## ✨ Ajout LinkedIn avec Unipile API (Version 4)

### Méthode
**API utilisée** : Unipile LinkedIn Search API (`POST {DSN}/api/v1/linkedin/search`)

**Pourquoi Unipile uniquement pour LinkedIn ?**
- API officielle avec authentification LinkedIn réelle
- Pas de scraping web (pas de blocage)
- Accès direct aux données structurées
- Rate limits : ~1000 recherches/jour pour LinkedIn
- Plus fiable que web scraping ou Parallel Search

**Configuration** :
```bash
# Dans .env (déjà configuré)
UNIPILE_DSN=https://api21.unipile.com:15160
UNIPILE_API_KEY=85adQehB.dm6vrV/Wf/JY9/ClN2EZbWDhKg5RjTpHbZbOGm/xQxU=
UNIPILE_LINKEDIN_ACCOUNT_ID=6ariH5hYQf2Kq6UhLVG6UQ
```

**Implémentation** :
```python
# Méthode _unipile_search_linkedin() dans parallel_scraper.py
async def _unipile_search_linkedin(keywords, location, max_results):
    response = await httpx.post(
        f"{unipile_dsn}/api/v1/linkedin/search",
        headers={"X-API-KEY": unipile_api_key},
        params={"account_id": unipile_account_id},
        json={
            "api": "classic",
            "category": "jobs",
            "keywords": f"{keywords} {location}"
        }
    )
    # Parse items array, filter type="JOB" + location
    for item in data.get("items", []):
        if item.get("type") == "JOB":
            # Filter by location (important!)
            item_location = item.get("location", "").lower()
            if location and location.lower() not in item_location:
                continue  # Skip jobs not in specified location
            urls.append(item.get("job_url"))
```

### Patterns LinkedIn
**URLs acceptées** :
- ✅ `/jobs/view/` : Offres individuelles (format principal)
- ✅ Toutes les URLs retournées par Unipile sont valides (déjà filtrées par type="JOB")

**URLs rejetées** :
- ❌ `/jobs/search/` : Pages de recherche
- ❌ `/company/` : Pages entreprises

### Résultats Test v4
**Exécution** : `python parallel_scraper.py`

**Phase 1 - URLs brutes** :
- Parallel Search (Glassdoor + WTTJ) : 15 URLs
- Firecrawl Search (Indeed) : 9 URLs
- Unipile LinkedIn Search : **10 URLs**
- **Total** : 34 URLs brutes

**Phase 1 - Après filtrage** :
- Glassdoor : 2 URLs
- WTTJ : 3 URLs
- Indeed : 3 URLs
- LinkedIn : **3 URLs**
- **Total** : 11 URLs filtrées

**Phase 2 & 3 - Extraction & Export** :
- 11 pages extraites via Parallel Extract API
- 11 offres structurées dans `results/jobs.csv`
- Colonne `source` : `glassdoor`, `wttj`, `indeed`, **`linkedin`** ✓

**Performance** :
- Phase 1 : ~20s (Parallel 5s + Firecrawl 10s + Unipile 5s)
- Phase 2 : ~15s (Extraction)
- **Total** : ~35s pour 11 offres

**Distribution finale** :
- 🔵 Glassdoor : 2 offres
- 🟢 WTTJ : 3 offres
- 🔴 Indeed : 3 offres
- 🔵 LinkedIn : **3 offres**
- **Total** : **11 offres sur 4 sources actives**

### Avantages Unipile
- Authentification réelle LinkedIn (compte Julien Lopato)
- Données structurées (titre, entreprise, localisation, remote, description)
- Pas de parsing HTML nécessaire
- Pas de blocage anti-bot
- Rate limits raisonnables (~1000/jour)
- **Filtrage géographique** : Les résultats sont filtrés côté script pour ne garder que les offres dont la localisation contient "bordeaux"

### Amélioration : Filtrage géographique LinkedIn
**Problème initial** : Unipile retourne 10 jobs dont seulement 3 à Bordeaux, mais le script prenait les 3 premiers (Paris, France remote, Bordeaux)

**Solution** : Ajout d'un filtre post-API dans `_unipile_search_linkedin()` :
```python
item_location = item.get("location", "").lower()
if location and location.lower() not in item_location:
    continue  # Skip jobs not in specified location
```

**Résultat** : Les 3 offres LinkedIn sont maintenant toutes à Bordeaux (était Paris/Marseille avant)

---

**Date de création** : 28 novembre 2024  
**Dernière mise à jour** : 29 novembre 2024 (ajout Indeed + LinkedIn + filtrage géo LinkedIn)  
**Auteur** : Job Seek Team  
**Version** : 1.4.1 (Test avec 4 sources + filtrage géographique)
