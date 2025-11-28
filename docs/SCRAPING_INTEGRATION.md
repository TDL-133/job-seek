# Intégration des services de scraping

Ce document explique comment Job Seeker utilise Firecrawl et BrightData pour scraper les plateformes d'emploi (Indeed, Glassdoor, WTTJ).

## Architecture

### ScrapingService

Le service centralisé `src/services/scraping_service.py` gère le scraping avec une stratégie de fallback :

```
1. Firecrawl API  →  2. BrightData API  →  3. httpx simple
   (rapide)            (puissant)             (fallback)
```

Chaque scraper (Indeed, Glassdoor, WTTJ) hérite de `BaseScraper` qui utilise automatiquement `ScrapingService`.

### Flux de scraping

```
IndeedScraper.search()
  └─> BaseScraper.fetch_page(url)
      └─> ScrapingService.fetch_page(url)
          ├─> _fetch_with_firecrawl(url)      [Essai #1]
          ├─> _fetch_with_brightdata(url)     [Essai #2 si #1 échoue]
          └─> _fetch_with_httpx(url)          [Essai #3 si #2 échoue]
```

## Configuration

### 1. Firecrawl (Recommandé)

**Service** : https://firecrawl.dev/  
**Avantages** :
- ✅ Bypass anti-bot automatique
- ✅ Rapide (~2 secondes)
- ✅ Free tier : 500 requêtes/mois
- ✅ Fiable et maintenu

**Setup** :
1. Créer un compte sur https://firecrawl.dev/
2. Générer une clé API
3. Ajouter dans `.env` :
   ```bash
   FIRECRAWL_API_KEY=your_api_key_here
   ```

**API utilisée** :
- Endpoint : `POST https://api.firecrawl.dev/v1/scrape`
- Headers : `Authorization: Bearer {API_KEY}`
- Body : `{"url": "...", "formats": ["html"]}`

### 2. BrightData (Fallback)

**Service** : https://brightdata.com/ (via ScraperAPI)  
**Avantages** :
- ✅ Proxies rotatifs résidentiels
- ✅ Gestion CAPTCHA automatique
- ✅ JavaScript rendering disponible
- ✅ Très fiable pour sites complexes

**Setup** :
1. Créer un compte sur https://brightdata.com/
2. Ou utiliser ScraperAPI : https://www.scraperapi.com/
3. Générer une clé API
4. Ajouter dans `.env` :
   ```bash
   BRIGHTDATA_API_KEY=your_api_key_here
   ```

**API utilisée** :
- Endpoint : `GET http://api.scraperapi.com/`
- Params : `api_key={KEY}&url={TARGET_URL}&render=false`

### 3. httpx simple (Toujours disponible)

Si aucune clé API n'est configurée, le système utilise `httpx` avec des headers standards.

**Limitations** :
- ❌ Facilement bloqué par anti-bot
- ❌ Taux de succès faible (~30%)
- ✅ Gratuit et sans configuration

## Logs et monitoring

Le service log chaque tentative de scraping :

```python
logger.info(f"Successfully scraped {url} with Firecrawl")
logger.warning(f"Firecrawl failed for {url}, trying BrightData")
logger.error(f"All scraping methods failed for {url}")
```

Pour activer les logs dans FastAPI :

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Performance

| Méthode    | Temps moyen | Taux de succès | Coût          |
|------------|-------------|----------------|---------------|
| Firecrawl  | ~2s         | ~95%           | Gratuit (500/mois) |
| BrightData | ~5s         | ~99%           | Payant        |
| httpx      | ~1s         | ~30%           | Gratuit       |

## Tests

Pour tester les scrapers :

```bash
# Lancer l'app
docker-compose up -d

# Tester une recherche
curl -X POST http://localhost:8001/api/search/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "Product Manager",
    "location": "Paris",
    "platforms": ["indeed", "glassdoor", "welcometothejungle"]
  }'
```

Vérifier les logs pour voir quelle méthode a été utilisée :

```bash
docker-compose logs -f app | grep "Successfully scraped"
```

## Coûts estimés

### Scénario : 100 recherches/jour

Chaque recherche scanne 3 plateformes (Indeed, Glassdoor, WTTJ) = 300 requêtes/jour

**Option 1 : Firecrawl seul**
- 300 req/jour × 30 jours = 9,000 req/mois
- Free tier : 500 req/mois ⚠️ Insuffisant
- Plan Pro : ~$50/mois pour 10,000 req

**Option 2 : Firecrawl + httpx fallback**
- Utiliser Firecrawl pour les 500 premières requêtes
- Fallback httpx pour le reste (gratuit mais moins fiable)
- Coût : $0/mois

**Option 3 : BrightData**
- Plan Starter : $60/mois pour 250,000 requêtes
- Largement suffisant
- Taux de succès très élevé

**Recommandation** : Commencer avec Firecrawl (free tier) + httpx fallback, puis upgrader vers BrightData si nécessaire.

## Dépannage

### "All scraping methods failed"

**Causes possibles** :
1. Clés API invalides ou expirées
2. Limites de quota atteintes
3. URL cible temporairement indisponible

**Solutions** :
1. Vérifier que les clés API sont correctes dans `.env`
2. Vérifier les quotas sur les dashboards Firecrawl/BrightData
3. Tester manuellement l'URL dans un navigateur

### Scraping très lent

**Causes** :
- BrightData est utilisé (plus lent mais plus fiable)
- Plusieurs requêtes en parallèle saturent les APIs

**Solutions** :
- Ajouter des délais entre requêtes (`asyncio.sleep(0.5)`)
- Limiter le nombre de recherches parallèles

### Taux de succès faible avec httpx

**Normal** : Les sites anti-bot bloquent les requêtes simples.

**Solution** : Configurer Firecrawl ou BrightData.

## Évolutions futures

- [ ] Support Playwright pour scraping JavaScript complexe
- [ ] Cache des résultats pour éviter requêtes inutiles
- [ ] Rotation automatique des User-Agents
- [ ] Détection intelligente du scraper optimal par site
