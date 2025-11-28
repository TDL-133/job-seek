# Quick Start - Configuration Scraping

## 🚀 Configuration rapide (2 minutes)

### Option 1 : Firecrawl (Recommandé - Gratuit)

1. **Créer un compte** : https://firecrawl.dev/
2. **Copier la clé API** depuis le dashboard
3. **Ajouter dans `.env`** :
   ```bash
   FIRECRAWL_API_KEY=fc-YOUR_KEY_HERE
   ```
4. **Redémarrer** :
   ```bash
   docker-compose restart app
   ```

✅ **C'est tout !** Les scrapers utilisent maintenant Firecrawl automatiquement.

### Option 2 : BrightData (Plus puissant)

1. **Créer un compte** : https://www.scraperapi.com/
2. **Copier la clé API**
3. **Ajouter dans `.env`** :
   ```bash
   BRIGHTDATA_API_KEY=YOUR_KEY_HERE
   ```
4. **Redémarrer** :
   ```bash
   docker-compose restart app
   ```

### Option 3 : Aucune configuration (Fallback gratuit)

Si tu ne configures rien, les scrapers utilisent `httpx` simple :
- ✅ Gratuit
- ❌ Taux de succès ~30%
- ❌ Souvent bloqué

## 🧪 Test

```bash
# Lancer une recherche
curl -X POST http://localhost:8001/api/search/jobs \
  -H "Content-Type: application/json" \
  -d '{"keywords": "Product Manager", "location": "Paris"}'

# Vérifier les logs
docker-compose logs -f app | grep "Successfully scraped"
```

Tu devrais voir :
```
✅ Successfully scraped https://www.indeed.com/jobs?... with Firecrawl
```

## 📊 Quelle option choisir ?

| Besoin | Solution | Coût |
|--------|----------|------|
| **Dev/Test** | Aucune config (httpx) | Gratuit |
| **Production légère** | Firecrawl free tier | Gratuit (500 req/mois) |
| **Production intensive** | Firecrawl Pro ou BrightData | ~$50-60/mois |

## 🆘 Problèmes ?

**"All scraping methods failed"**
→ Vérifie que la clé API est correcte dans `.env`

**Très lent**
→ Normal, BrightData prend ~5s par requête (mais très fiable)

**Toujours aucun résultat**
→ Teste manuellement l'URL dans un navigateur pour vérifier qu'elle est accessible

## 📖 Documentation complète

Voir `docs/SCRAPING_INTEGRATION.md` pour :
- Détails techniques
- Configuration avancée
- Monitoring et logs
- Coûts estimés
- Troubleshooting complet
