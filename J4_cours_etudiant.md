# J4 — Construire une vraie suite de tests API avec PyTest

> **J2** : je sais appeler et exploiter une API avec `requests`.
> **J3** : je sais concevoir et organiser des tests avec PyTest.
> **J4** : je sais construire une suite de tests API maintenable sur EventFlow.

Aujourd'hui on ne réapprend ni `requests` ni PyTest. On les assemble, et on découvre les problèmes qui n'existent **que** quand on teste un vrai système : une API qui tourne ailleurs, des données qui changent, un contrat à respecter, une authentification à gérer, des tests qui modifient l'état de l'application.

Le fil de la journée :

1. Je transforme mes appels `requests` en vrais tests PyTest.
2. Je conçois correctement des tests d'API.
3. Je rends ma suite maintenable : configuration, fixtures, données dynamiques.
4. Je fais du Data-Driven Testing avec `parametrize`.
5. Je teste le contrat JSON avec JSON Schema.
6. Je teste des POST authentifiés et des règles métier.
7. Je comprends l'état, l'isolation et `yield`.
8. Je termine par une mission autonome, et une chasse aux régressions.

À la fin de la journée, votre projet `j4-api-pytest/` ressemblera à ceci :

```text
j4-api-pytest/
    pytest.ini
    requirements.txt
    schemas/
        event.schema.json      le contrat d'un événement
    data/
        order_quantities.json  un jeu de données de test
    tests/
        conftest.py            fixtures partagées (configuration, auth, données)
        helpers.py             fonctions ordinaires réutilisées
        test_events.py
        test_contract.py
        test_orders.py
        test_order_lines.py    (mission)
```

Cette structure n'est pas donnée d'avance. Elle va **apparaître**, au fur et à mesure que les problèmes la rendent nécessaire.

Les exercices sont dans `J4_exercices_eleves.md`. Le cours indique où ils s'insèrent.

---

## 0. Avant de commencer

EventFlow doit tourner et répondre sur `http://localhost:8000`. La documentation interactive de l'API est disponible sur `http://localhost:8000/docs` : c'est votre référence pour les routes et les payloads.

Suivez le `README.md` du starter pour créer l'environnement virtuel et installer les dépendances (`pytest`, `requests`, `jsonschema`).

➡️ **Exercice 0** — Mise en place.

---

## 1. Du script au test

### 1.1 Un script constate, un test juge

Au J2, vous écriviez des scripts comme `scripts/explorer_catalogue.py` :

```python
response = requests.get(f"{BASE_URL}/api/events", timeout=5)
print(response.status_code)
print(response.json())
```

Ce script **affiche**. C'est vous qui regardez la sortie et qui décidez si c'est normal. Si demain la réponse change, le script affichera autre chose... et personne ne s'en rendra compte, sauf si quelqu'un relit la console avec attention.

Un test fait la même requête, mais il **porte un jugement**. Exemple sur l'endpoint technique `/api/health` :

```python
"""Exemple du cours (section 1) : un endpoint technique, trois dimensions vérifiées."""
import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 5


def test_health_repond_ok():
    response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["status"] == "ok"
```

Trois différences essentielles :

- **Le verdict est automatique.** PASS ou FAIL, sans relire la console.
- **L'attendu est écrit.** Ce que « normal » veut dire est noté dans le code, pas dans votre tête.
- **Il est rejouable.** Cent fois, sur n'importe quel poste, par n'importe qui, ou par une CI.

### 1.2 Le message d'échec : `, response.text`

Comparez ces deux lignes :

```python
assert response.status_code == 200
assert response.status_code == 200, response.text
```

Si le test échoue, la première affiche seulement :

```text
E   assert 404 == 200
```

La seconde affiche aussi ce que l'API a répondu :

```text
E   AssertionError: {"detail":"Event not found"}
E   assert 404 == 200
```

Dans un test API, le corps de la réponse contient presque toujours la cause de l'échec. Sans lui, vous devez relancer la requête à la main pour comprendre. **Prenez le réflexe d'ajouter `, response.text` à l'assert du status code.**

### 1.3 Toujours un `timeout`

Vu au J2 : sans `timeout`, `requests` peut attendre indéfiniment une API qui ne répond plus. Pour un script, c'est gênant. Pour une suite de 50 tests lancée par une CI, c'est une suite bloquée pendant des heures sans aucun message. Chaque appel de ce cours utilise `timeout=5`.

### 1.4 Un `200` ne prouve presque rien

Imaginez un test du catalogue qui vérifie seulement :

```python
assert response.status_code == 200
```

Ce test resterait vert si l'API renvoyait :

- une liste vide alors que des événements existent ;
- du HTML au lieu de JSON ;
- des événements sans leur titre ;
- des brouillons qui ne devraient pas être publics.

Un bon test API vérifie plusieurs **dimensions**, selon ce qui compte pour ce endpoint :

| Dimension | Question | Exemple |
|---|---|---|
| Statut HTTP | La requête a-t-elle abouti comme prévu ? | `200`, `201`, `404`... |
| Format | Est-ce bien ce qu'on attend comme type de contenu ? | `content-type` JSON |
| Structure | La forme de la réponse est-elle correcte ? | une liste, des champs présents et bien typés |
| Contenu | Les valeurs sont-elles les bonnes ? | l'event demandé est bien celui renvoyé |
| Règle métier | Le comportement respecte-t-il les règles du produit ? | le catalogue public ne montre que des events publiés |

Il ne s'agit pas de cocher les cinq cases dans chaque test. Il s'agit de se demander, pour chaque test : **« quelle panne réelle ce test détecterait-il ? »** Si la réponse est « aucune qui compte », le test n'apporte rien.

➡️ **Exercice 1** — Un catalogue qui peut casser de plusieurs façons.

---

## 2. Concevoir les tests d'une API, et les piloter par les données

### 2.1 Les techniques de conception s'appliquent aussi aux API

Ce que vous avez appris en conception de tests (positif / négatif, classes d'équivalence, valeurs limites) s'applique directement aux paramètres d'une API. `GET /api/events` accepte deux paramètres optionnels, `q` (recherche dans le titre) et `city` (ville). `GET /api/events/{id}` prend un identifiant dans l'URL.

Pour chaque paramètre, posez-vous les mêmes questions qu'en conception « classique » :

- Paramètre **absent** ou **présent** ?
- Valeur qui **correspond** à des données / qui ne correspond **à rien** ?
- Variantes d'**écriture** d'une même valeur ?
- Valeur **bien formée** mais inexistante / valeur **mal formée** ?
- Deux paramètres **combinés** ?

Le résultat attendu doit être écrit **avant** de lancer la requête. Sinon, vous ne testez pas : vous constatez.

### 2.2 Deux erreurs différentes : 404 et 422

Sur `GET /api/events/{id}`, deux familles d'erreurs vont apparaître :

- **404 Not Found** : la requête est correcte, mais la ressource demandée n'existe pas.
- **422 Unprocessable Entity** : la requête elle-même est mal formée. EventFlow est construit avec FastAPI, qui valide automatiquement les paramètres et les corps de requête. Quand la validation échoue, il répond `422` avec un `detail` qui indique **où** est le problème :

```json
{"detail": [{"type": "int_parsing", "loc": ["path", "event_id"], "msg": "...", "input": "..."}]}
```

`loc` est précieux pour un testeur : il permet de vérifier que l'API a refusé la requête **pour la bonne raison**, sur le bon champ.

### 2.3 Data-Driven Testing : séparer le scénario des données

Après la conception, vous aurez souvent plusieurs cas qui se ressemblent énormément. Par exemple « un identifiant invalide est refusé » :

```python
# ❌ Le même test, recopié : seules les données changent
def test_id_inexistant():
    response = requests.get(f"{BASE_URL}/api/events/999999", timeout=TIMEOUT)
    assert response.status_code == 404, response.text

def test_id_texte():
    response = requests.get(f"{BASE_URL}/api/events/abc", timeout=TIMEOUT)
    assert response.status_code == 422, response.text

def test_id_decimal():
    ...  # et ainsi de suite
```

Le jour où la façon d'appeler l'API change, il faut corriger chaque copie. Et en lisant le fichier, on ne voit pas d'un coup d'œil **quels cas** sont couverts.

Un test **data-driven** (piloté par les données) **sépare la logique du test des jeux de données qu'il utilise** :

- la logique (le scénario) est écrite **une fois** ;
- les données (entrée → résultat attendu) sont rangées dans un **tableau**, lisible et facile à compléter.

Bonne nouvelle : vous le faites déjà. `@pytest.mark.parametrize` **est** du Data-Driven Testing.

```python
@pytest.mark.parametrize(
    "event_id, statut_attendu",
    [
        ("999999", 404),
        ("abc", 422),
    ],
    ids=["inexistant", "texte"],
)
def test_detail_id_invalide_est_refuse(event_id, statut_attendu):
    response = requests.get(f"{BASE_URL}/api/events/{event_id}", timeout=TIMEOUT)

    assert response.status_code == statut_attendu, response.text
```

Ajouter un cas, c'est ajouter **une ligne de données**, pas un test.

Le critère pour savoir si des cas vont ensemble : **même scénario, mêmes vérifications, seules les données changent.** Si vous devez écrire des `if` dans le test pour traiter certains cas différemment, ce ne sont plus les mêmes scénarios : faites des tests séparés.

### 2.4 `ids=` : un rapport lisible

Sans `ids`, PyTest nomme les cas d'après leurs valeurs, ce qui devient illisible dès que les valeurs sont des fonctions, des dictionnaires ou des chaînes longues :

```text
test_exemple[<function <lambda> at 0x7f3a...>]    ← sans ids
test_exemple[majuscules]                          ← avec ids
```

Quand un cas échoue à 3 h du matin dans une CI, le nom du cas est la première information qu'on lit. Il doit dire **quelle donnée** a posé problème.

### 2.5 Utiliser les données réelles

Pour tester un filtre, il faut une valeur qui **devrait** donner des résultats. Plutôt que de supposer qu'une ville précise existe, vous pouvez la prendre dans le catalogue lui-même (par exemple la ville du premier événement). Le test reste valable même si les données de démonstration changent. On généralisera cette idée à la section 3.

### 2.6 Un test révèle un comportement ; il ne décide pas seul que c'est un bug

Il arrive qu'un test échoue parce que votre attendu était faux, ou parce que la spécification ne dit rien. Face à un comportement surprenant :

1. Vérifiez que votre requête et votre attendu sont corrects.
2. Cherchez la règle : documentation, README, critères d'acceptation.
3. Si la règle n'existe pas, **c'est une question au produit**, pas un verdict du testeur.

Ne modifiez jamais l'attendu d'un test « pour qu'il passe » sans savoir quel comportement est le bon.

➡️ **Exercice 2** — Concevoir, puis piloter par les données.

---

## 3. Rendre la suite maintenable

### 3.1 Le problème

Après les premiers exercices, chaque fichier de test commence probablement par :

```python
BASE_URL = "http://localhost:8000"
TIMEOUT = 5
```

Question : **si demain l'API tourne sur un serveur de recette, ou dans une CI, combien de fichiers faut-il modifier ?**

Aujourd'hui : un par fichier de test. Dans trois semaines, avec quinze fichiers : quinze. Et le jour où un fichier est oublié, une partie de la suite teste le mauvais environnement sans le dire.

### 3.2 `conftest.py`

Un fichier nommé `conftest.py` est lu automatiquement par PyTest. Les fixtures qu'il définit sont disponibles pour **tous les tests de son dossier** (et des sous-dossiers), sans aucun `import`.

C'est l'endroit naturel pour ce qui prépare les tests et qui est partagé par toute la suite.

### 3.3 La fixture `base_url` et la variable `API_URL`

```python
# tests/conftest.py
import os

import pytest


@pytest.fixture(scope="session")
def base_url():
    """URL de l'API. Lue dans API_URL pour pouvoir viser un autre environnement."""
    return os.getenv("API_URL", "http://localhost:8000").rstrip("/")
```

Un test la demande simplement par son nom :

```python
def test_quelque_chose(base_url):
    response = requests.get(f"{base_url}/api/health", timeout=TIMEOUT)
```

- `os.getenv("API_URL", ...)` lit une **variable d'environnement**, avec une valeur par défaut pour travailler en local sans rien configurer.
- `.rstrip("/")` évite les `//` si quelqu'un écrit `http://serveur:8000/`.
- `scope="session"` : l'URL ne change pas pendant un lancement, inutile de la recalculer pour chaque test.

C'est ainsi qu'une CI pourra, plus tard, lancer **la même suite** contre un autre serveur, sans modifier une ligne de code.

### 3.4 Et `TIMEOUT` : fixture aussi ?

Non. `TIMEOUT = 5` est une simple constante : rien à préparer, rien à nettoyer, rien qui dépende d'autre chose. En faire une fixture n'apporterait que de la complexité.

Les constantes et les fonctions ordinaires partagées vont dans un module Python classique, par exemple `tests/helpers.py` :

```python
# tests/helpers.py
TIMEOUT = 5
```

```python
# tests/test_events.py
from helpers import TIMEOUT
```

> `from helpers import ...` fonctionne parce que PyTest ajoute le dossier `tests/` au chemin d'import quand il ne contient pas de fichier `__init__.py` (configuration par défaut). N'ajoutez pas de `__init__.py` dans `tests/`.

### 3.5 Des données de test qui ne supposent rien

Pour tester le détail d'un événement, puis pour créer des commandes cet après-midi, il faut des identifiants. La tentation :

```python
event_id = 1
category_id = 2
```

Ça fonctionne sur votre poste, aujourd'hui. Mais :

- les identifiants sont attribués par la base de données : sur une autre base (un collègue, la CI, un serveur de recette), l'ID 1 peut être un autre événement, ou ne pas exister ;
- l'événement 1 peut être archivé demain ;
- la catégorie 2 peut ne plus avoir de places, parce que **d'autres tests** ont réservé avant vous.

Le test échoue alors pour une raison qui n'a rien à voir avec ce qu'il vérifie.

C'est une vraie compétence de testeur de faire la différence entre :

| « Je connais une règle stable » | « Je suppose une donnée » |
|---|---|
| Une commande est limitée à 6 billets (règle métier documentée) | L'événement n°1 existe |
| Le catalogue public ne montre que les events publiés | La catégorie VIP de tel event a encore 5 places |
| Un id mal formé est refusé en 422 | Il y a exactement 4 événements |

La règle, on l'écrit dans l'attendu. La donnée, on la **découvre** au moment du test :

1. **Lire** ce qui existe (le catalogue, puis le détail d'un event).
2. **Choisir** selon un critère qui compte pour le test (« au moins N places disponibles »).
3. **Décider quoi faire** s'il n'y a rien d'utilisable : échouer avec un message clair, ou `pytest.skip("raison")`. Un test *skipped* ne prétend ni avoir réussi ni avoir trouvé un bug : il dit qu'il n'a pas pu s'exécuter, et pourquoi.

> Certaines données de démonstration sont documentées et font partie du contrat de l'environnement de test : les comptes du seed, les codes promo `WELCOME10` et `EXPIRED`. Les utiliser est acceptable, à condition de savoir que c'est une hypothèse sur l'environnement.

### 3.6 Fixture ou fonction ?

Plusieurs de vos tests commencent par charger le catalogue. Il faut le factoriser. Question légitime : **« Pourquoi une fixture ? Je peux écrire une fonction `charger_catalogue()` et l'appeler dans mes tests. »**

Réponse honnête : **oui, parfois une fonction est le meilleur choix.** Une fixture n'est pas « une meilleure fonction ». C'est un outil pour un besoin précis : une **préparation de test** que PyTest doit gérer.

Une fixture devient intéressante quand vous voulez que PyTest :

| Besoin | Exemple EventFlow |
|---|---|
| **injecte** la préparation par son nom | `def test_x(base_url, events)` |
| la **partage** selon un scope | un seul login pour toute la session (cet après-midi) |
| la **compose** avec d'autres préparations | `events` a besoin de `base_url` |
| la **prépare avant** le test | créer des données dédiées |
| la **nettoie après** le test, même en cas d'échec | archiver ces données |

À l'inverse, une fonction ordinaire est parfaite pour :

- une **transformation** (retrouver une catégorie par son nom dans un dictionnaire) ;
- une action que le test déclenche **lui-même**, au moment qu'il choisit (envoyer une commande) ;
- un calcul (un total attendu).

Un bon indice : si la chose n'a **ni cycle de vie, ni dépendances, ni besoin de partage**, une fonction suffit.

On a maintenant quatre notions à ne pas confondre :

| Notion | Rôle | Où la mettre |
|---|---|---|
| **Configuration** | ce qui change selon l'environnement (URL, identifiants) | variable d'environnement, lue par une fixture |
| **Constante** | valeur fixe partagée (`TIMEOUT`) | `helpers.py` |
| **Helper** | fonction ordinaire qui calcule ou transforme | `helpers.py` |
| **Fixture** | préparation de test gérée par PyTest | `conftest.py` |

➡️ **Exercice 3** — Refactorer la suite.

---

## 4. Tester le contrat : JSON Schema

### 4.1 Le problème

À l'exercice 1, vous avez vérifié la structure d'un événement à la main :

```python
assert "id" in event
assert "title" in event
assert isinstance(event["id"], int)
assert isinstance(event["title"], str)
...
```

Ça marche. Mais :

- un événement a 9 champs, le détail d'un événement en a 11, dont une liste de catégories qui ont chacune 5 champs ;
- une commande, un utilisateur, une réponse d'erreur ont chacun leur propre forme ;
- les vérifications sont noyées dans le code, mélangées aux règles métier ;
- personne d'autre qu'un développeur Python ne peut les relire.

**Et si la réponse avait 25 champs ?**

### 4.2 Un contrat

Le front d'EventFlow, une application mobile, un partenaire : tous ceux qui consomment l'API comptent sur une **forme** de réponse. Si un champ disparaît ou change de type, leur code casse, même si l'API répond `200`. Cette forme promise, c'est le **contrat** de l'API.

**JSON Schema** est un standard pour décrire ce contrat : c'est lui-même un document JSON, qui dit à quoi doit ressembler un autre document JSON.

```json
{
  "type": "object",
  "required": ["id", "title", "city"],
  "properties": {
    "id": {"type": "integer"},
    "title": {"type": "string"},
    "city": {"type": "string"}
  }
}
```

Se lit : « un objet, qui doit contenir `id`, `title` et `city` ; `id` est un entier, `title` et `city` sont des chaînes ».

Les mots-clés les plus utiles :

| Mot-clé | Sens | Exemple |
|---|---|---|
| `type` | type JSON attendu | `"object"`, `"array"`, `"string"`, `"integer"`, `"number"`, `"boolean"`, `"null"` |
| `required` | champs obligatoires d'un objet | `["id", "title"]` |
| `properties` | le schéma de chaque champ | `{"id": {"type": "integer"}}` |
| `items` | le schéma de chaque élément d'une liste | `{"type": "array", "items": {...}}` |
| `minItems` | nombre minimal d'éléments d'une liste | `{"type": "array", "minItems": 1}` |
| `minimum` / `maximum` | bornes d'un nombre | `{"type": "integer", "minimum": 0}` |
| `minLength` | longueur minimale d'une chaîne | `{"type": "string", "minLength": 1}` |
| `enum` | liste fermée de valeurs autorisées | `{"enum": ["draft", "published", "archived"]}` |
| `pattern` | expression régulière qu'une chaîne doit respecter | `{"pattern": "^#[0-9A-Fa-f]{6}$"}` |

Attention à un piège : un champ décrit dans `properties` mais absent de `required` est **facultatif**. S'il est présent, il doit respecter son schéma ; s'il est absent, le schéma ne dit rien.

### 4.3 Valider avec la bibliothèque `jsonschema`

La bibliothèque `jsonschema` (déjà dans votre `requirements.txt`) valide un document contre un schéma :

```python
from jsonschema import validate

EVENT_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "city"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "city": {"type": "string"},
    },
}

validate(instance=event, schema=EVENT_SCHEMA)
```

- si le document respecte le schéma, `validate` ne renvoie rien et le test continue ;
- sinon, elle lève une `ValidationError`, et le test échoue avec un message précis. Par exemple, pour un `id` reçu sous forme de texte :

```text
'4' is not of type 'integer'

Failed validating 'type' in schema['properties']['id']:
    {'type': 'integer'}

On instance['id']:
    '4'
```

Le message dit **quel champ**, **quelle règle du schéma**, et **quelle valeur** a été reçue. Pas besoin d'écrire un message d'assert.

### 4.4 Ranger les schémas hors du code

Un schéma est un document JSON : sa place naturelle est un fichier `.json`, dans le dossier `schemas/`. Il devient lisible et relisible par d'autres (un développeur, un analyste), et réutilisable par d'autres outils.

Pour le charger depuis les tests, une petite fonction dans `helpers.py` :

```python
# tests/helpers.py
import json
from pathlib import Path

# tests/helpers.py -> tests/ -> racine du projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_json(relative_path):
    """Charge un fichier JSON du projet (schéma, jeu de données), où que soit lancé pytest."""
    with open(PROJECT_ROOT / relative_path, encoding="utf-8") as f:
        return json.load(f)
```

Pourquoi `Path(__file__)` plutôt que `open("schemas/event.schema.json")` ? Un chemin relatif est interprété depuis le dossier **d'où l'on lance** `pytest`. Lancé depuis la racine du projet, ça marche ; lancé depuis `tests/` ou par un outil de CI, le fichier est introuvable. `Path(__file__)` part de l'emplacement de `helpers.py` lui-même : le chemin est juste quel que soit le dossier courant.

Dans un fichier de test :

```python
from jsonschema import validate

from helpers import load_json

EVENT_SCHEMA = load_json("schemas/event.schema.json")
```

### 4.5 Valider une liste : composer les schémas

Le catalogue est une **liste** d'événements. Inutile de réécrire le schéma d'un événement : on le réutilise dans `items` :

```python
CATALOGUE_SCHEMA = {"type": "array", "minItems": 1, "items": EVENT_SCHEMA}

validate(instance=response.json(), schema=CATALOGUE_SCHEMA)
```

Une seule ligne vérifie maintenant **chaque champ de chaque événement** du catalogue.

### 4.6 Ce que le schéma vérifie... et ce qu'il ne vérifie pas

C'est la distinction la plus importante de cette section.

| JSON Schema vérifie **le contrat** | Les assertions PyTest vérifient **le fonctionnel** |
|---|---|
| la structure (objet, liste) | les règles métier |
| les champs requis | la cohérence entre plusieurs valeurs |
| les types | que c'est le **bon** résultat pour **cette** requête |
| des contraintes de forme (bornes, format, liste de valeurs possibles) | l'effet réel de l'action |

Exemple sur le détail d'un événement :

```python
validate(instance=detail, schema=EVENT_DETAIL_SCHEMA)   # contrat : structure, types
assert detail["available"] <= detail["capacity"]        # métier : le schéma ne le voit pas
```

Le schéma peut dire que `available` et `capacity` sont des entiers positifs. Il ne sait pas dire que l'un doit être inférieur à l'autre. De même, le schéma peut dire que `status` vaut `draft`, `published` ou `archived` (les valeurs possibles, c'est du contrat) ; mais « le catalogue **public** ne montre que des events `published` » est une **règle métier**, qui reste une assertion.

**Un schéma ne remplace pas les assertions. Il remplace les assertions de structure.** Et il rend les assertions restantes plus lisibles : elles ne parlent plus que du métier.

> **Pour aller plus loin :** `"additionalProperties": false` interdit tout champ non déclaré. C'est utile pour détecter une fuite de données (un champ `password_hash` qui apparaîtrait dans une réponse), mais le schéma casse aussi dès qu'un développeur ajoute légitimement un champ. C'est un choix d'équipe, à faire consciemment.

### 4.7 Un schéma qui dit toujours oui ne teste rien

Un schéma trop permissif valide tout. Le cas extrême : le schéma vide `{}` accepte **n'importe quel** document. Un test qui valide contre lui est toujours vert, et ne détecte rien.

Un testeur vérifie donc que son schéma **sait dire non** : on prend une vraie réponse, on l'abîme volontairement, et on vérifie que la validation échoue.

```python
from jsonschema import ValidationError

mutant = dict(event)          # une copie : on ne modifie pas la vraie donnée
del mutant["title"]           # on retire un champ requis

with pytest.raises(ValidationError):
    validate(instance=mutant, schema=EVENT_SCHEMA)
```

`pytest.raises` (vu au J3) vérifie ici que **le schéma refuse** la réponse abîmée. Chaque « abîmage » est une donnée : c'est un excellent candidat pour `parametrize`.

➡️ **Exercice 4** — Le contrat d'un événement.

---

## 5. L'authentification comme infrastructure, et le premier POST

### 5.1 Le besoin

`POST /api/orders` exige d'être connecté. Au J2, vous l'avez fait à la main :

1. `POST /api/auth/token` avec `username` et `password` **en form-data** (`data=...`, pas `json=...`) ;
2. récupérer `access_token` dans la réponse ;
3. envoyer `Authorization: Bearer <token>` dans les requêtes suivantes.

Tous les tests de commande en ont besoin. Et aucun d'eux ne cherche à tester la connexion : ils la **consomment**. L'authentification est une préparation, pas l'objet du test.

### 5.2 Une fonction, une fixture, et la question du scope

Deux besoins distincts, deux outils :

- **transformer des identifiants en headers** : c'est une transformation, donc une **fonction** `login(base_url, email, password)` dans `helpers.py` (elle servira pour d'autres comptes) ;
- **fournir aux tests les headers du client** : c'est une préparation partagée, donc une **fixture** `auth_headers` dans `conftest.py`, qui appelle `login`.

```python
@pytest.fixture(scope="session")
def auth_headers(base_url):
    ...  # appelle login(...) avec les identifiants du client du seed
```

Remarquez la **composition** : `auth_headers` demande `base_url`. PyTest résout la chaîne tout seul.

Le vrai choix est le **scope** :

- `scope="function"` (défaut) : un login **par test**. Vingt tests de commande = vingt appels à `/api/auth/token`. Plus lent, et ça sollicite inutilement l'API.
- `scope="session"` : un seul login pour tout le lancement.

Ici `session` est logique, parce que le token :

- n'est **pas modifié** par les tests ;
- reste valable pendant toute la durée d'un lancement (EventFlow le fait expirer au bout de deux heures dans sa configuration par défaut).

La règle générale : **ce qui est coûteux et que les tests ne modifient pas peut être partagé. Ce que les tests modifient ne doit pas l'être** (on y reviendra à la section 7).

### 5.3 Garder `headers=auth_headers` visible

Dans chaque test de commande, écrivez explicitement :

```python
requests.post(f"{base_url}/api/orders", json=payload, headers=auth_headers, timeout=TIMEOUT)
```

On voit immédiatement quel test est authentifié. Ce sera utile quand on testera ce qui se passe **sans** token.

> **Culture : `requests.Session`.** `requests` propose un objet `Session` qui mémorise des paramètres (headers, cookies) et réutilise les connexions entre requêtes. C'est utile dans certains projets. On ne l'utilise pas aujourd'hui : on préfère que l'authentification reste visible dans chaque test.

On ne teste pas l'authentification elle-même aujourd'hui : mauvais mot de passe, token absent ou invalide, droits selon les rôles, accès aux commandes d'un autre utilisateur. C'est un sujet à part entière, traité dans le bloc suivant.

### 5.4 Anatomie d'un test de création

Un bon test de création suit ce fil :

1. **Données** : récupérer ce dont on a besoin (event, catégorie avec du stock) sans rien supposer (section 3.5).
2. **Payload** : construire le corps de la requête. Pour EventFlow :
   ```json
   {"event_id": 3, "items": [{"category_id": 8, "quantity": 2}], "promo_code": "WELCOME10"}
   ```
   (`promo_code` est facultatif, les valeurs ici sont un exemple.)
3. **Envoi** : `POST /api/orders` authentifié.
4. **Statut** : `201 Created` pour une création réussie.
5. **Corps** : la commande renvoyée contient-elle ce qu'on a demandé ?
6. **Métier** : les informations importantes sont-elles correctes (statut de la réservation, total) ?

Une commande EventFlow fraîchement créée est une **réservation** : elle a le statut `pending` et une date d'expiration. Elle bloque les places pendant dix minutes (règle RM2). Le paiement est une autre étape, qu'on ne fait pas ici.

Envoyer la commande est une action que **le test** déclenche, au moment qu'il choisit, et dont il veut examiner la réponse, y compris quand elle est refusée. C'est donc une fonction (par exemple `create_order(...)` dans `helpers.py`) qui renvoie la réponse **brute**, sans rien vérifier elle-même.

### 5.5 L'oracle indépendant

L'**oracle**, c'est ce qui permet de dire si le résultat est correct. Regardez ce test :

```python
commande = response.json()
total_attendu = commande["total_cents"]
assert commande["total_cents"] == total_attendu     # ❌
```

Il ne peut **jamais** échouer : il compare la réponse à elle-même. Même avec un total faux, il est vert.

Un oracle indépendant **calcule** l'attendu à partir de données connues et de la règle :

```python
total_attendu = categorie["price_cents"] * quantite     # prix lu dans le catalogue, règle de calcul connue
assert commande["total_cents"] == total_attendu          # ✅
```

Les montants EventFlow sont en **centimes entiers** (`price_cents`, `total_cents`) : `3500` signifie 35,00 €.

Quand vous ne savez pas calculer l'attendu (règle d'arrondi inconnue, par exemple), ce n'est pas au test de « deviner » : c'est une question à poser au produit.

### 5.6 Écrire, puis relire

Un `201` et un corps correct prouvent que l'API **a répondu** qu'elle avait créé la commande. Ils ne prouvent pas qu'on la **retrouve** ensuite. D'où un réflexe : **après une écriture, relire via l'API**, avec `GET /api/orders/{id}`.

Cette réponse est enrichie (`event_title`, `category_name`) : le test compare des **informations**, pas deux JSON à l'identique. Et attention : deux réponses de la même API peuvent être cohérentes **et fausses toutes les deux**. La relecture ne remplace pas l'oracle.

On vérifie ici le comportement **à travers l'API**. On ne regarde pas directement dans PostgreSQL : ce sera un autre angle de test, plus tard dans le module.

➡️ **Exercice 5** — Premier POST authentifié.

---

## 6. Règles métier, erreurs, et données de test externalisées

### 6.1 Pourquoi CETTE erreur ?

Les règles métier d'EventFlow qui concernent la commande :

| Règle | Énoncé |
|---|---|
| RM1 | On ne vend jamais plus de places que le stock disponible. |
| RM3 | Maximum six billets par commande. |
| RM4 | Un code promo a un nombre d'usages maximum et une date d'expiration. |

Quand une commande est refusée, l'API choisit un statut. Ne les apprenez pas par cœur : **raisonnez**.

| Statut | Question à se poser | Idée |
|---|---|---|
| **422** | La requête est-elle **mal formée** ? | champ manquant, mauvais type : FastAPI refuse avant même d'appliquer les règles |
| **400** | La requête est bien formée, mais une **règle** l'interdit ? | on demande quelque chose que le métier refuse |
| **404** | Une **ressource désignée** n'existe pas ? | on référence quelque chose d'introuvable |
| **409** | La requête est valide, mais elle est en **conflit avec l'état actuel** ? | elle aurait été acceptée si l'état était différent |

Le 409 est le plus subtil : la même requête peut être acceptée à 10h00 et refusée à 10h05, parce que l'état a changé entre-temps.

Et parfois, le choix d'une API est **discutable** : deux statuts seraient défendables. Dans ce cas, le test documente le comportement retenu, pour que tout changement futur soit détecté et discuté.

### 6.2 Vérifier la raison, pas seulement le code

```python
assert response.status_code == 400, response.text
```

Ce test passe si la commande est refusée... **pour n'importe quelle raison.** Imaginez que vous testez le plafond de six billets, mais que votre payload contient aussi, par erreur, une catégorie invalide : l'API répond `400` pour la catégorie, votre test est vert, et le plafond n'a jamais été vérifié.

**Un 400 pour la mauvaise raison reste potentiellement un bug.** Quand l'API fournit une raison (`detail`), vérifiez-la :

```python
assert response.status_code == 400, response.text
assert response.json()["detail"] == "..."
```

Pour les `422`, vérifiez le champ incriminé via `loc`.

### 6.3 Parametrize ou tests séparés ?

`parametrize` est tentant pour tout regrouper. Comparez :

```python
# ❌ Un parametrize fourre-tout
@pytest.mark.parametrize(
    "items, promo, event_ok, statut, detail, verifier_total, total",
    [ ... 12 lignes ... ],
)
def test_commandes(...):
    ...  # des if pour savoir quoi vérifier selon le cas
```

Quand ce test échoue, que teste-t-il vraiment ? Quand on ajoute un cas, quelle colonne remplir ? Les `if` dans le test sont un signal d'alarme : ce sont plusieurs tests déguisés en un seul.

Le critère de la section 2.3 reste valable :

- **même scénario, mêmes vérifications, seules les données changent** → data-driven ;
- **scénarios différents, vérifications différentes** → tests séparés, avec des noms qui disent ce qu'ils vérifient.

Le but n'est pas d'avoir le moins de lignes possible. Le but est qu'en lisant le rapport PyTest, on comprenne **ce qui est cassé**.

### 6.4 Sortir les données du code

Avec `parametrize`, les données sont dans le fichier Python. Quand le jeu de données grossit, ou quand quelqu'un qui ne code pas (un analyste, un PO) doit pouvoir le relire ou le compléter, on peut le ranger dans un **fichier de données**, comme les schémas :

```json
[
  {"cas": "un_billet", "quantity": 1, "expected_status": 201},
  {"cas": "juste_au_dessus", "quantity": 7, "expected_status": 400}
]
```

```python
CAS_QUANTITES = load_json("data/order_quantities.json")


@pytest.mark.parametrize("cas", CAS_QUANTITES, ids=[c["cas"] for c in CAS_QUANTITES])
def test_quantite_sur_une_ligne(base_url, auth_headers, cas):
    ...  # utilise cas["quantity"], vérifie cas["expected_status"]
```

- `load_json` est la fonction de la section 4.4 : le fichier est lu une fois, au chargement du module de test.
- chaque élément de la liste devient un cas ; le champ `cas` fournit les `ids`.
- ajouter un cas = ajouter une ligne dans le JSON, sans toucher au Python.

Deux remarques pour que ça reste utile :

- **Ne construisez pas un framework.** Un fichier, une liste, `parametrize`. Si le fichier devient plus compliqué que le test, vous êtes allé trop loin.
- **Quand la forme de la donnée change, c'est un autre scénario.** Si un cas ne rentre pas dans les colonnes du fichier (par exemple une commande sur **deux** lignes), ne tordez pas le fichier : écrivez un test séparé.

> En JSON, l'absence de valeur s'écrit `null` ; `json.load` la transforme en `None` en Python.

➡️ **Exercice 6** — Règles métier, pilotées par les données.

---

## 7. L'état : quand un test ne donne plus le même résultat

### 7.1 Ce qui vient de se passer

Un test qui passe, puis échoue au lancement suivant, puis repasse dix minutes plus tard. Le code de l'application n'a pas changé. Le code du test non plus.

Ce qui a changé, c'est **l'état** de l'application. Chaque commande créée par un test réserve des places pendant dix minutes (RM2). Le test « commander les 5 dernières places » a réservé ces places au premier lancement. Au second, elles sont prises. Dix minutes plus tard, la réservation expire et les places reviennent.

Un test API n'est pas une fonction pure : **il agit sur un système réel, et ce système se souvient.**

### 7.2 Ce qu'on attend d'une suite fiable

- **Déterminisme** : même code, même application → même résultat.
- **Indépendance** : un test ne dépend pas de ce qu'un autre a fait avant lui.
- **Ordre indifférent** : lancer un seul test, ou toute la suite dans un autre ordre, ne change pas les verdicts.
- **Pas de pollution** : un test ne laisse pas derrière lui un état qui fait échouer les autres.

Un test qui passe et échoue de façon imprévisible s'appelle un test **flaky**. C'est l'un des pires ennemis d'une suite automatisée : au bout de quelques fausses alertes, plus personne ne croit au rouge.

### 7.3 Quelles stratégies ?

| Stratégie | Idée | Dans EventFlow |
|---|---|---|
| Réinitialiser la base avant chaque test | repartir de zéro | possible mais lourd (redémarrage, reseed), pas par test |
| Nettoyer après le test via l'API | supprimer ce qu'on a créé | **impossible pour les commandes : l'API n'a pas de DELETE** |
| Créer des données neuves pour chaque test | chaque test a son propre terrain | **possible** : un organisateur peut créer un événement dédié |

On ne simule pas un nettoyage qui n'existe pas. On choisit la stratégie que l'application permet réellement.

### 7.4 Une fixture qui prépare... et qui range : `yield`

Au J3, vous avez vu `yield` dans une fixture. Voici enfin pourquoi il existe.

```text
SETUP        la fixture prépare (crée un event dédié)
  ↓
yield        elle donne la ressource au test
  ↓
TEST         le test l'utilise
  ↓
TEARDOWN     la fixture reprend la main et range (même si le test a échoué)
```

La fixture fournie pour la suite de la journée :

```python
# tests/conftest.py : imports à ajouter en haut du fichier
import os
import uuid
from datetime import datetime, timedelta, timezone

from helpers import TIMEOUT, login
```

```python
# tests/conftest.py : fixtures à ajouter
@pytest.fixture(scope="session")
def orga_headers(base_url):
    """Organisateur du seed : sert uniquement à PRÉPARER des données de test."""
    return login(
        base_url,
        os.getenv("EF_ORGA_EMAIL", "orga@eventflow.test"),
        os.getenv("EF_ORGA_PASSWORD", "orga1234"),
    )


@pytest.fixture
def small_event(base_url, orga_headers):
    """Crée un event dédié (2 catégories de 3 places), puis l'archive après le test.

    Limite assumée : EventFlow n'a pas de DELETE. Le teardown n'efface rien,
    il retire seulement l'event du catalogue public en l'archivant.
    """
    starts_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
    payload = {
        "title": f"[TEST J4] {uuid.uuid4().hex[:8]}",
        "city": "Testville",
        "starts_at": starts_at.isoformat(),
        "capacity": 10,
        "categories": [
            {"name": "Standard", "price_cents": 1000, "quota": 3},
            {"name": "Reduit", "price_cents": 600, "quota": 3},
        ],
    }
    response = requests.post(
        f"{base_url}/api/admin/events", json=payload, headers=orga_headers, timeout=TIMEOUT
    )
    assert response.status_code == 201, response.text
    event = response.json()

    yield event

    requests.put(
        f"{base_url}/api/admin/events/{event['id']}",
        json={"status": "archived"},
        headers=orga_headers,
        timeout=TIMEOUT,
    )
```

(`login` est la fonction de connexion de l'exercice 5 : adaptez le nom si le vôtre est différent. Les identifiants de l'organisateur sont ceux du seed, surchargeables par variables d'environnement, comme `API_URL`.)

Ce qu'il faut comprendre :

- **Chaque test qui demande `small_event` reçoit un événement neuf**, avec un stock connu : 3 places « Standard » à 10,00 € et 3 places « Reduit » à 6,00 €. Aucun autre test n'y a touché.
- Le titre contient un identifiant aléatoire (`uuid`) pour que les events de test ne se confondent jamais.
- On utilise le compte organisateur **pour préparer** des données, pas pour tester les droits d'un organisateur.
- `response.json()` renvoie ici la vue « back-office » de l'event, avec ses `categories` (dont les `id`).

Et la limite, à dire honnêtement : **le teardown n'efface rien.** EventFlow n'a pas de suppression d'événement. L'archivage retire l'event du catalogue public, mais il reste en base, avec les réservations créées pendant le test. C'est un **compromis** : la suite devient déterministe, au prix de données de test qui s'accumulent dans l'environnement. Dans un vrai projet, on complèterait avec une réinitialisation périodique de l'environnement de test.

### 7.5 Scope et données mutables

| Préparation | Les tests la modifient ? | Scope logique |
|---|---|---|
| `base_url` | non | `session` |
| `auth_headers` | non | `session` |
| `events` (catalogue lu) | non, mais il **change** au fil des tests | `function` (défaut) |
| `small_event` | **oui** (on y réserve des places) | `function` (défaut) |

Si `small_event` était en `scope="session"`, tous les tests partageraient le même event de 3 places : le premier qui réserve change le résultat de tous les suivants. On retrouverait exactement le problème de la section 7.1.

➡️ **Exercice 7** — Un test de stock qui donne toujours le même résultat.

---

## 8. Quand un test révèle un vrai bug

Votre test est correct, votre attendu est justifié par une règle, et l'application ne la respecte pas. Que faire du test rouge ?

**Ne le supprimez pas.** Et ne changez pas l'attendu pour le rendre vert. Le test a fait exactement son travail.

Mais un test rouge **connu**, qui reste rouge en permanence, pose un problème : tout le monde s'habitue au rouge, et un **nouveau** rouge passe inaperçu.

PyTest propose `xfail` (vu brièvement au J3) avec l'option `strict=True` :

```python
@pytest.mark.xfail(
    strict=True,
    reason="ANO-123 : description courte de l'anomalie et de la règle violée",
)
def test_regle_respectee(...):
    ...
```

| Situation | Résultat | Sens |
|---|---|---|
| le bug est toujours là (le test échoue) | `xfailed` | échec attendu et documenté : la suite reste lisible |
| le bug est corrigé (le test passe) | **`XPASS(strict)` → FAILED** | la suite vous prévient : retirez le marker, le test redevient un test normal |

Le `reason` doit permettre de retrouver l'anomalie (référence de ticket) et comprendre la règle violée.

On ne met un `xfail` **qu'après** avoir confirmé le bug : jamais « au cas où », jamais pour faire taire un test qu'on ne comprend pas.

---

## 9. Mission

➡️ **Exercice 8** — Mission autonome.
➡️ **Exercice 9** — Relancez votre suite.

---

## Annexe A — Organiser une campagne : markers et commandes utiles

À lire après le cours (et à utiliser dès que votre suite dépasse quelques dizaines de tests).

Avant de lancer une campagne complète, ou juste après un déploiement, on veut souvent savoir en quelques secondes : **l'API est-elle vivante, et les parcours essentiels fonctionnent-ils ?** C'est le rôle d'une suite **smoke** : quelques tests choisis, rapides. Si elle échoue, inutile de lancer le reste.

```python
@pytest.mark.smoke
def test_un_parcours_essentiel(base_url):
    ...
```

Un marker se déclare dans `pytest.ini` :

```ini
[pytest]
testpaths = tests
addopts = --strict-markers
markers =
    smoke: vérification rapide que l'API répond et que les parcours clés fonctionnent
```

Avec `--strict-markers`, une faute de frappe (`@pytest.mark.smok`) provoque une **erreur** au lieu de créer silencieusement un marker que personne ne sélectionne.

| Commande | Usage |
|---|---|
| `pytest -m smoke` | ne lancer que les tests marqués `smoke` |
| `pytest -m "not smoke"` | tout sauf eux |
| `pytest -v` | un test par ligne, avec son nom complet (et ses `ids`) |
| `pytest -k promo` | les tests dont le nom contient « promo » |
| `pytest --lf` | relancer seulement les tests qui ont échoué la dernière fois (*last failed*) |
| `pytest -x` | s'arrêter au premier échec |
| `pytest -s` | afficher les `print` (utile pour explorer, pas à laisser dans les tests) |

---

## Aide-mémoire

### Anatomie d'un test API

```python
def test_ce_que_ca_verifie(base_url, auth_headers, donnees_preparees):
    # Arrange : données découvertes ou créées, payload
    # Act     : une requête, avec timeout
    # Assert  : statut (+ response.text), contrat (schéma), puis le métier (contenu, règle, detail)
```

### Erreurs fréquentes

- Vérifier seulement le status code.
- Oublier `, response.text` : l'échec devient illisible.
- Oublier le `timeout`.
- Écrire des IDs en dur.
- Recopier le même test au lieu de le piloter par les données.
- Un `parametrize` géant avec des `if` à l'intérieur.
- Croire qu'un schéma valide remplace les assertions métier.
- Un schéma qui accepte tout (jamais testé contre une réponse abîmée).
- Prendre l'attendu dans la réponse elle-même (oracle non indépendant).
- Vérifier `400` sans vérifier la raison.
- Un test qui dépend de l'état laissé par un autre test.
- Une donnée mutable partagée en `scope="session"`.
- Modifier l'attendu pour faire passer un test sans connaître la règle.
- Supprimer un test rouge au lieu de documenter l'anomalie.

### Endpoints EventFlow utilisés aujourd'hui

| Méthode | Route | Accès |
|---|---|---|
| GET | `/api/health` | public |
| GET | `/api/events` (`q`, `city`) | public |
| GET | `/api/events/{id}` | public |
| POST | `/api/auth/token` (form-data) | public |
| POST | `/api/orders` | connecté |
| GET | `/api/orders/{id}` | connecté (propriétaire) |
| POST / PUT | `/api/admin/events` , `/api/admin/events/{id}` | organisateur, uniquement via la fixture `small_event` |
