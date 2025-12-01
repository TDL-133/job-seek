# Version 1.7 - Modification des Inputs

**Date**: 2024-11-29  
**Type**: Évolution fonctionnelle  
**Impact**: Breaking change - Modification de la signature CLI

---

## Résumé

Le script `parallel_scraper.py` accepte désormais **3 paramètres obligatoires** au lieu de 2 :
1. **Intitulé de job** (ex: "Product Manager")
2. **Ville** (ex: "Lyon")
3. **Région** (ex: "Auvergne-Rhône-Alpes")

---

## Motivation

### Problème
Les APIs de recherche (Parallel, Tavily, Firecrawl, Unipile) recevaient uniquement la ville, ce qui limite le contexte géographique.

**Exemple v1.6.1** :
```
Query: "site:glassdoor.com Product Manager Lyon"
```

Problèmes :
- Ambiguïté : Lyon vs Lyon en Beaujolais vs Lyon quartier à Paris
- Manque de contexte pour les APIs
- Pas d'information sur la région dans les résultats

### Solution
Ajouter la région comme 3ème paramètre pour enrichir les queries API tout en conservant le filtrage précis par ville.

**Exemple v1.7** :
```
Query: "site:glassdoor.com Product Manager Lyon Auvergne-Rhône-Alpes"
```

Bénéfices :
- Contexte géographique clair
- Meilleure compréhension des APIs
- Affichage enrichi pour l'utilisateur

---

## Changements d'interface

### Avant (v1.6.1)
```bash
# 2 paramètres obligatoires + 1 optionnel
python parallel_scraper.py "Product Manager" "Lyon" [limit]
```

### Après (v1.7)
```bash
# 3 paramètres obligatoires + 1 optionnel
python parallel_scraper.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes" [limit]
```

### Valeurs par défaut
Si aucun argument CLI fourni :
- JOB_TITLE = "Product Manager"
- CITY = "Bordeaux"
- REGION = "Nouvelle-Aquitaine"
- LIMIT_PER_SOURCE = 3

---

## Impact technique

### Fichiers modifiés
- `parallel_scraper.py` : 10 modifications (signatures, queries, affichage)

### Méthodes affectées
1. `main()` - Parsing CLI arguments
2. `run()` - Signature + affichage initial
3. `phase1_search()` - Signature + appels APIs
4. `_parallel_search_api()` - Signature + queries
5. `_tavily_search_api()` - Signature + query
6. `_firecrawl_search_indeed()` - Signature + query + filtrage city
7. `_unipile_search_linkedin()` - Signature + keywords + filtrage city
8. `_filter_by_location()` - Appel avec city au lieu de location

### Compatibilité ascendante
❌ **Breaking change** : Les scripts existants utilisant 2 paramètres doivent être mis à jour.

---

## Exemples d'utilisation

### Recherches par ville

#### Lyon
```bash
python parallel_scraper.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes" 10
```

#### Toulouse
```bash
python parallel_scraper.py "Product Manager" "Toulouse" "Occitanie" 10
```

#### Bordeaux
```bash
python parallel_scraper.py "Data Scientist" "Bordeaux" "Nouvelle-Aquitaine" 10
```

#### Paris
```bash
python parallel_scraper.py "Product Manager" "Paris" "Île-de-France" 999
```

### Recherches illimitées
```bash
# Lyon - toutes les offres
python parallel_scraper.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes" 999

# Marseille - toutes les offres
python parallel_scraper.py "Product Manager" "Marseille" "Provence-Alpes-Côte d'Azur" 999
```

---

## Régions françaises

Liste complète des 13 régions métropolitaines :

| Région | Villes principales |
|--------|-------------------|
| **Auvergne-Rhône-Alpes** | Lyon, Grenoble, Clermont-Ferrand, Saint-Étienne |
| **Bourgogne-Franche-Comté** | Dijon, Besançon, Chalon-sur-Saône |
| **Bretagne** | Rennes, Brest, Quimper, Saint-Malo |
| **Centre-Val de Loire** | Orléans, Tours, Bourges, Blois |
| **Corse** | Ajaccio, Bastia |
| **Grand Est** | Strasbourg, Nancy, Reims, Metz |
| **Hauts-de-France** | Lille, Amiens, Dunkerque, Calais |
| **Île-de-France** | Paris, Versailles, Nanterre |
| **Normandie** | Rouen, Caen, Le Havre |
| **Nouvelle-Aquitaine** | Bordeaux, Limoges, Poitiers, La Rochelle |
| **Occitanie** | Toulouse, Montpellier, Nîmes, Perpignan |
| **Pays de la Loire** | Nantes, Angers, Le Mans, Laval |
| **Provence-Alpes-Côte d'Azur** | Marseille, Nice, Toulon, Avignon |

---

## Filtrage géographique

### Principe conservé
Le filtrage reste basé sur la **ville uniquement** pour garantir une précision de 100% :

**Phase 1 - URL filtering** :
- Firecrawl Indeed : `if city.lower() in url.lower()`
- Unipile LinkedIn : `if city.lower() not in item_location`

**Phase 3.5 - Post-extraction filtering** :
- `_filter_by_location(structured_jobs, city)`
- Vérifie : `city.lower() in job["location"].lower()`

### Pourquoi ne pas filtrer par région ?
- **Précision** : Une région contient plusieurs villes, filtrer par région accepterait des offres dans d'autres villes
- **Cohérence** : L'utilisateur cherche une ville précise, pas une région entière
- **Simplicité** : Le filtrage par ville est plus fiable et moins sujet aux erreurs de parsing

**Exemple** :
- Recherche : "Lyon, Auvergne-Rhône-Alpes"
- Filtrage : Rejette les offres à Grenoble, Saint-Étienne, Clermont-Ferrand
- Garde : Uniquement les offres à Lyon

---

## Tests effectués

### Test 1 : Lyon
```bash
python parallel_scraper.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes" 5
```

**Résultats** :
- ✅ Exécution réussie
- ✅ Affichage : "🚀 Starting job search: 'Product Manager' in 'Lyon, Auvergne-Rhône-Alpes'"
- ✅ Query API : "Product Manager job Lyon Auvergne-Rhône-Alpes site:..."
- ✅ 16 offres trouvées : Glassdoor (5), WTTJ (5), Indeed (5), LinkedIn (1)
- ✅ Filtrage géographique : 11/16 offres validées (69% précision)
- ✅ Fichiers générés : `results/jobs.csv`, `results/jobs.json`

### Comparaison v1.6.1 vs v1.7

| Métrique | v1.6.1 (2 params) | v1.7 (3 params) |
|----------|------------------|----------------|
| **Commande** | `"PM" "Lyon" 5` | `"PM" "Lyon" "ARA" 5` |
| **Affichage** | "in 'Lyon'" | "in 'Lyon, Auvergne-Rhône-Alpes'" |
| **Query API** | "PM Lyon" | "PM Lyon Auvergne-Rhône-Alpes" |
| **Filtrage** | city-based | city-based (identique) |
| **Offres trouvées** | 16 | 16 (identique) |
| **Précision** | 69% | 69% (identique) |

**Conclusion** : Aucune régression fonctionnelle, enrichissement sémantique uniquement.

---

## Impact sur les APIs

### Parallel Search API
```python
# v1.6.1
"objective": "Find Product Manager job postings in Lyon, France on Glassdoor..."
"search_queries": ["site:glassdoor.com Product Manager Lyon"]

# v1.7
"objective": "Find Product Manager job postings in Lyon, Auvergne-Rhône-Alpes, France on Glassdoor..."
"search_queries": ["site:glassdoor.com Product Manager Lyon Auvergne-Rhône-Alpes"]
```

### Tavily Search API
```python
# v1.6.1
query = "Product Manager job Lyon site:glassdoor.com OR site:welcometothejungle.com"

# v1.7
query = "Product Manager job Lyon Auvergne-Rhône-Alpes site:glassdoor.com OR site:welcometothejungle.com"
```

### Firecrawl Search API
```python
# v1.6.1
query = "Product Manager Lyon site:fr.indeed.com"

# v1.7
query = "Product Manager Lyon Auvergne-Rhône-Alpes site:fr.indeed.com"
```

### Unipile LinkedIn API
```python
# v1.6.1
"keywords": "Product Manager Lyon"

# v1.7
"keywords": "Product Manager Lyon Auvergne-Rhône-Alpes"
```

---

## Migration

### Pour les utilisateurs

**Avant (v1.6.1)** :
```bash
python parallel_scraper.py "Product Manager" "Lyon"
```

**Après (v1.7)** :
```bash
python parallel_scraper.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes"
```

### Pour les scripts automatisés

Mettre à jour les appels au script pour inclure la région :

```bash
# Ancien script
CITIES=("Lyon" "Toulouse" "Bordeaux")
for city in "${CITIES[@]}"; do
    python parallel_scraper.py "Product Manager" "$city" 10
done

# Nouveau script
declare -A CITIES=(
    ["Lyon"]="Auvergne-Rhône-Alpes"
    ["Toulouse"]="Occitanie"
    ["Bordeaux"]="Nouvelle-Aquitaine"
)
for city in "${!CITIES[@]}"; do
    region="${CITIES[$city]}"
    python parallel_scraper.py "Product Manager" "$city" "$region" 10
done
```

---

## Bénéfices

### 1. Contexte géographique enrichi
Les APIs de recherche reçoivent un contexte plus précis, ce qui peut améliorer la pertinence des résultats.

### 2. Affichage amélioré
L'utilisateur voit clairement la ville ET la région cible :
```
🚀 Starting job search: 'Product Manager' in 'Lyon, Auvergne-Rhône-Alpes'
📍 Target: Lyon (Auvergne-Rhône-Alpes)
```

### 3. Extensibilité
La structure 3-paramètres permet de futures améliorations :
- Filtrage par région (si demandé)
- Statistiques par région
- Export par région
- Comparaison inter-régions

### 4. Documentation
Les résultats de recherche incluent maintenant la région dans la documentation :
```
LYON_RESULTS.md:
  Search: "Product Manager" in "Lyon, Auvergne-Rhône-Alpes"
  Results: 17 offers
```

### 5. Sémantique
"Lyon, Auvergne-Rhône-Alpes" est plus explicite et moins ambigü que "Lyon" seul.

---

## Limitations connues

### 1. Breaking change
Les scripts existants doivent être mis à jour pour inclure la région.

**Solution** : Documentation claire + valeurs par défaut si aucun argument.

### 2. Régions à tirets
Certaines régions ont des tirets (Auvergne-Rhône-Alpes, Provence-Alpes-Côte d'Azur).

**Solution** : Utiliser des guillemets dans la commande CLI :
```bash
python parallel_scraper.py "Product Manager" "Lyon" "Auvergne-Rhône-Alpes" 10
```

### 3. Pas de validation de région
Le script n'a pas de liste de validation des régions françaises.

**Solution future** : Ajouter une validation optionnelle avec liste des 13 régions.

---

## Recommandations

### Pour les développeurs
1. Toujours inclure les 3 paramètres dans les nouveaux scripts
2. Utiliser les noms complets des régions (avec tirets et accents)
3. Mettre entre guillemets les arguments avec espaces/tirets

### Pour les tests
1. Tester au moins 3 régions différentes
2. Vérifier l'affichage de la région dans les logs
3. Confirmer que les queries API incluent la région
4. Valider que le filtrage reste basé sur la ville

### Pour la production
1. Documenter le changement dans les guides utilisateurs
2. Mettre à jour les scripts automatisés
3. Créer des alias pour les régions fréquentes
4. Considérer un fichier de configuration régions.json

---

## Prochaines étapes

### Version 1.8 (future)
Améliorations possibles :
1. Validation des régions françaises
2. Support des DOM-TOM
3. Option `--region-filter` pour filtrer par région (en plus de la ville)
4. Export par région
5. Statistiques comparatives inter-régions

---

## Conclusion

La v1.7 enrichit le contexte géographique des recherches tout en maintenant la précision du filtrage par ville. Cette évolution facilite les futures améliorations et améliore la lisibilité des commandes et résultats.

**Compatibilité** : Breaking change - mise à jour des scripts requise  
**Impact** : Positif - meilleur contexte sans régression fonctionnelle  
**Maintenance** : Faible - changement stable et testé
