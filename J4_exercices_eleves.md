# J4 — Exercices : suite de tests API EventFlow

Les exercices suivent l'ordre du cours (`J4_cours_etudiant.md`). Chacun indique ce qu'il vous apprend : si vous avez l'impression de juste « écrire encore un test », relisez cette ligne.

Règles communes à tous les exercices :

- chaque appel HTTP a un `timeout` ;
- chaque assert sur un status code affiche le corps (`, response.text`) ;
- les tests vont dans `tests/`, dans des fichiers `test_*.py` ;
- un test a un nom qui dit **ce qu'il vérifie**, pas comment.

La documentation interactive de l'API (`http://localhost:8000/docs`) est votre alliée.

| # | Exercice | Section du cours |
|---|---|---|
| 0 | Mise en place | 0 |
| 1 | Un catalogue qui peut casser de plusieurs façons | 1 |
| 2 | Concevoir, puis piloter par les données | 2 |
| 3 | Refactorer la suite | 3 |
| 4 | Le contrat d'un événement (JSON Schema) | 4 |
| 5 | Premier POST authentifié | 5 |
| 6 | Règles métier, pilotées par les données | 6 |
| 7 | Un test de stock qui donne toujours le même résultat | 7 |
| 8 | Mission autonome | 8-9 |
| 9 | Relancez votre suite | 9 |
| Bonus | Pour ceux qui ont fini | — |

---

## Exercice 0 — Mise en place

**Ce que ça apprend :** travailler dans un projet de tests propre, isolé, et vérifier l'environnement avant d'accuser le code.

1. Décompressez le starter `j4-api-pytest/` et suivez son `README.md` (environnement virtuel, installation).
2. Vérifiez que l'API répond : `GET /api/health`.
3. Lancez `python scripts/explorer_catalogue.py`, puis `pytest`.

**C'est bon quand :** le script affiche le catalogue et `pytest` répond `no tests ran` (le dossier `tests/` est vide, c'est voulu).

---

## Exercice 1 — Un catalogue qui peut casser de plusieurs façons

**Ce que ça apprend :** passer d'un script qui affiche à des tests qui jugent ; un `200` ne prouve presque rien ; un test utile vise une panne précise.

Dans `tests/test_events.py`, écrivez des tests sur `GET /api/events` (sans paramètre).

Consigne : vos tests doivent échouer si le catalogue était cassé d'**au moins trois façons différentes**. Au-dessus de chaque test, écrivez en commentaire **la panne qu'il détecte**.

Contrainte : l'un de vos tests doit vérifier la **structure** des événements (les champs attendus et leur type), à la main, avec des `assert`. Le README d'EventFlow et `/docs` décrivent ce qu'est un événement.

**Vérification :** dans un de vos tests, remplacez volontairement `/api/events` par `/api/eventz`, lancez `pytest`, et lisez le message d'échec. Retrouvez-vous la réponse de l'API dans le message ? Remettez l'URL correcte.

**Question à noter :** quelle vérification vous a paru la plus fastidieuse à écrire ? Pourquoi ?

---

## Exercice 2 — Concevoir, puis piloter par les données

**Ce que ça apprend :** appliquer les techniques de conception (partitions, positif/négatif, formats) à une API, écrire l'attendu **avant** d'exécuter, puis implémenter les cas en data-driven.

### Partie A — Concevoir (10 min, sans code, sans exécuter de requête)

Construisez un tableau de cas de test pour :

- `GET /api/events?q=...` (recherche dans le titre) ;
- `GET /api/events?city=...` (filtre par ville) ;
- `GET /api/events/{id}` (détail d'un événement).

| ID | Endpoint / paramètre | Idée testée (partition, limite...) | Entrée | Résultat attendu | Pourquoi cet attendu ? |
|---|---|---|---|---|---|

Contraintes :

- au moins **8 cas**, répartis sur les trois ;
- au moins deux cas **négatifs** ;
- pour chaque attendu, dites d'où vous le tenez (documentation, règle, logique métier... ou « supposition » si c'en est une).

On met les tableaux en commun avant la partie B.

### Partie B — Implémenter

Implémentez dans `tests/test_events.py` au moins **6 cas** du tableau (complété après la mise en commun).

Contraintes :

- au moins **deux** tests data-driven (`parametrize`), avec des `ids=` lisibles ;
- au-dessus de chacun, une phrase qui dit **quel scénario commun** partagent ses cas ;
- ne supposez pas qu'un identifiant ou une ville précise existe si vous pouvez le lire dans le catalogue.

Lancez `pytest -v` : le rapport doit être compréhensible sans ouvrir le code.

**Si un test échoue :** avant de toucher à quoi que ce soit, décidez si c'est votre test ou votre attendu qui est faux, ou si l'application se comporte d'une manière que la documentation ne tranche pas. Notez-le : on en discutera.

---

## Exercice 3 — Refactorer la suite

**Ce que ça apprend :** rendre une suite configurable et maintenable, et distinguer configuration, constante, helper et fixture.

1. Comptez : combien d'endroits faudrait-il modifier aujourd'hui si l'API tournait sur `http://recette:8000` ?
2. Créez `tests/conftest.py` avec une fixture `base_url` qui lit la variable d'environnement `API_URL` (valeur par défaut : `http://localhost:8000`).
3. Créez `tests/helpers.py` pour ce qui n'a pas besoin d'être une fixture.
4. Plusieurs de vos tests chargent le catalogue pour y choisir des données. Factorisez ce chargement. **Fixture ou fonction : à vous de choisir**, et écrivez pourquoi en commentaire.
5. Adaptez vos tests : plus aucune URL ni constante recopiée. Lancez toute la suite : elle doit rester verte.
6. Lancez-la avec `API_URL=http://localhost:9999` (syntaxe selon votre système dans le README du starter). Observez, puis revenez à la configuration normale.

**Question :** `TIMEOUT` : fixture ou `helpers.py` ? Justifiez en une phrase.

---

## Exercice 4 — Le contrat d'un événement (JSON Schema)

**Ce que ça apprend :** décrire le contrat d'une réponse avec JSON Schema, le valider, et prouver que le schéma détecte vraiment une réponse non conforme.

### Partie A — Écrire le contrat

Dans `schemas/event.schema.json`, écrivez le schéma d'**un événement du catalogue** :

- tous les champs qu'un événement expose doivent être décrits et requis ;
- chaque champ a son type ;
- ajoutez au moins **deux contraintes** qui vont plus loin que le type (bornes, valeurs possibles, format...). Pour chacune, demandez-vous : est-ce une contrainte de **forme** (contrat) ou une **règle métier** ?

### Partie B — Valider l'API

Dans `tests/test_contract.py`, écrivez un test qui valide **tout le catalogue** (`GET /api/events`) contre votre schéma.

Puis supprimez de `test_events.py` le test de structure manuel de l'exercice 1. **Question :** qu'avez-vous supprimé ? Et qu'est-ce que le schéma ne remplace **pas** dans vos autres tests ?

### Partie C — Prouver que le schéma sait dire non

Un schéma qui accepte tout ne teste rien. Écrivez des tests qui prennent un vrai événement du catalogue, l'**abîment** volontairement, et vérifient que la validation **échoue**.

Contraintes :

- au moins **deux sortes** d'abîmage différentes ;
- au moins trois cas au total, en data-driven.

**Vérification :** remplacez temporairement votre schéma par `{}` et relancez. Que se passe-t-il pour la partie B ? Pour la partie C ? Remettez votre schéma.

### Partie D — Si vous avez fini : le détail d'un événement

`GET /api/events/{id}` renvoie davantage : la liste des `categories` (chacune avec ses propres champs) et la disponibilité globale `available`. Écrivez son schéma dans un second fichier, et un test qui valide le détail d'un événement **et** vérifie une règle métier que le schéma ne peut pas exprimer.

---

## Exercice 5 — Premier POST authentifié

**Ce que ça apprend :** traiter l'authentification comme une infrastructure partagée, préparer des données sans rien supposer, et construire un test de création complet avec un oracle indépendant.

### Partie A — L'authentification comme infrastructure

1. Dans `helpers.py`, une fonction `login(base_url, email, password)` qui renvoie les headers d'autorisation.
2. Dans `conftest.py`, une fixture `auth_headers` qui fournit ceux du client du seed (`client@eventflow.test` / `client1234`).
3. Choisissez le scope de la fixture. Écrivez pourquoi en commentaire.

> Rappel : on **consomme** l'authentification. On ne teste pas les cas de connexion ratée aujourd'hui.

### Partie B — Des données pour commander

Les tests de commande auront besoin d'**un événement publié et d'une de ses catégories qui a encore au moins 6 places disponibles**. Fournissez ce couple (event, catégorie) aux tests :

- aucun identifiant écrit en dur ;
- s'il n'existe aucune catégorie avec assez de places, le message doit être clair.

### Partie C — Le premier POST

Créez `tests/test_orders.py`. Écrivez un test qui crée une commande de **2 billets** avec ces données.

Le test doit vérifier au minimum :

- le statut de création ;
- que la commande concerne le bon événement ;
- son état de réservation ;
- son contenu (lignes) ;
- son total, **calculé par le test** à partir des données du catalogue.

Contrainte : aucune valeur attendue ne doit être lue dans la réponse qu'on vérifie.

### Partie D — Si vous avez le temps : relire

Après création, relisez la commande avec `GET /api/orders/{id}` et vérifiez qu'elle correspond à ce qui a été créé (choisissez les informations qui comptent).

---

## Exercice 6 — Règles métier, pilotées par les données

**Ce que ça apprend :** raisonner sur les erreurs d'une API au lieu de mémoriser des codes, vérifier la **raison** d'un refus, et externaliser un jeu de données de test.

### Partie A — Concevoir (10 min, sans code)

Voici ce que vous savez de `POST /api/orders` :

- corps attendu : `event_id` (entier), `items` (liste de `{category_id, quantity}`), `promo_code` (facultatif) ;
- RM1 : on ne vend jamais plus que le stock disponible ;
- RM3 : maximum six billets par commande ;
- RM4 : un code promo a un nombre d'usages maximum et une date d'expiration ;
- codes promo de démonstration : `WELCOME10` (valide), `EXPIRED` (expiré).

Listez **au moins 8 scénarios** où la commande devrait être refusée :

| Scénario | Règle ou contrainte concernée | Statut attendu (400 / 404 / 409 / 422) | Pourquoi CE statut ? |
|---|---|---|---|

Pensez aux limites, aux partitions, aux références vers des choses qui n'existent pas ou ne correspondent pas, aux formats.

### Partie B — Les quantités, pilotées par un fichier

1. Dans `data/order_quantities.json`, construisez le jeu de données de la règle « au moins un billet, au plus six » **sur une seule ligne de commande** : quantité demandée → statut attendu → raison attendue (ou aucune raison si la commande est acceptée). Couvrez les limites.
2. Dans `test_orders.py`, un seul test data-driven qui lit ce fichier.

**Question :** la limite de six porte-t-elle sur une ligne ou sur la commande entière ? Votre fichier peut-il exprimer ce cas ? Sinon, que faites-vous ?

### Partie C — Les autres familles d'erreur

Implémentez vos scénarios de la partie A pour :

- les **catégories** : inexistante, et existante mais appartenant à un autre événement ;
- les **codes promo** refusés ;
- au moins un **payload mal formé**, en vérifiant le champ incriminé.

Chaque refus vérifie **la raison** donnée par l'API. Data-driven là où c'est le même scénario, tests séparés sinon.

---

## Exercice 7 — Un test de stock qui donne toujours le même résultat

**Ce que ça apprend :** isoler un test en lui fournissant des données neuves, comprendre `yield` et le choix du scope pour une donnée mutable.

1. Ajoutez à votre `conftest.py` les fixtures `orga_headers` et `small_event` données dans le cours (section 7.4). Lisez-les ligne à ligne avant de les copier.
2. Écrivez un test « **stock insuffisant** » qui utilise `small_event`.
3. Ajoutez le cas limite : commander **exactement** le stock restant.
4. Lancez la suite trois fois de suite : les verdicts doivent être identiques.

**Questions :**

- Après le test, l'événement dédié est-il encore consultable via `GET /api/events/{id}` ? Et dans `GET /api/events` ? Qu'est-ce que ça vous dit sur ce teardown ?
- Que se passerait-il si `small_event` avait `scope="session"` ?

---

## Exercice 8 — Mission autonome

**Ce que ça apprend :** concevoir seul une petite campagne de tests API, du choix des cas à l'organisation du code.

### Contexte

L'équipe prépare une nouvelle version du front : un **panier multi-catégories**, où une même commande peut contenir plusieurs lignes. Côté API, `POST /api/orders` accepte déjà une liste d'`items`, mais jusqu'ici vos tests ont surtout utilisé une seule ligne.

Le Product Owner vous demande une suite de tests API qui **protège les règles de composition d'une commande** avant la mise en production du panier.

### Périmètre

- `POST /api/orders` avec une ou plusieurs lignes ;
- l'effet d'une commande sur les disponibilités (`GET /api/events/{id}`) ;
- les règles RM1 (stock) et RM3 (plafond), le calcul du total.

### Livrable

Un fichier `tests/test_order_lines.py`, et une courte note (en tête de fichier ou dans un `.md`) qui liste vos cas et, le cas échéant, les **anomalies** constatées.

### Contraintes de qualité

- chaque test vérifie une chose qui compte, et son nom le dit ;
- aucune dépendance entre tests, aucun ID écrit en dur ;
- vous choisissez vous-même vos données, vos fixtures ou helpers, votre usage du data-driven, vos schémas éventuels ;
- si un test révèle un comportement contraire à une règle : **ne modifiez pas l'attendu pour le faire passer**. Décrivez l'anomalie (titre, reproduction, attendu, obtenu, règle concernée), puis relisez la section 8 du cours.

Il n'existe pas une seule bonne réponse. On jugera la **pertinence** des cas, pas leur nombre.

---

## Exercice 9 — Relancez votre suite

**Ce que ça apprend :** à quoi sert vraiment une suite de tests.

Le formateur va vous donner une manipulation à faire sur votre environnement EventFlow.

Ensuite, **sans modifier une seule ligne de vos tests**, relancez toute votre suite.

Notez :

- quels tests sont passés au rouge ;
- pour chacun, quelle règle ou quel comportement a régressé ;
- lesquels vous paraissent les plus graves pour l'entreprise, et pourquoi.

---

## Bonus — Pour ceux qui ont fini

### Bonus 1 — Oracle et arrondi

1. Écrivez un test qui vérifie la remise du code `WELCOME10` (10 %) sur une commande de 2 billets.
2. Trouvez dans le catalogue une catégorie nommée `Early bird` avec du stock. Calculez **à la main** le total attendu avec `WELCOME10` pour 1, 2 et 3 billets. Comparez avec ce que renvoie l'API. Qu'en concluez-vous ? Pourriez-vous écrire un oracle fiable pour ces trois cas ? Que vous faudrait-il ?

### Bonus 2 — Une suite smoke

Lisez l'annexe A du cours.

1. Choisissez **au plus 4 tests** qui constituent votre suite smoke. Justifiez chaque choix en une phrase.
2. Marquez-les, déclarez le marker dans `pytest.ini` avec `--strict-markers`, lancez `pytest -m smoke`.
3. Faites une faute de frappe volontaire dans un marker et lancez `pytest`. Que se passe-t-il ?

### Bonus 3 — Le contrat d'une commande

Écrivez le schéma de la réponse de `POST /api/orders` (commande créée), et validez-la dans votre test de l'exercice 5. Quelles vérifications de votre test deviennent inutiles ? Lesquelles restent indispensables ?
