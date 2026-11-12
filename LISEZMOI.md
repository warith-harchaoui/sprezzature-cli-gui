# sprezzature-cli-gui

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-cli-gui/main/assets/logo.png)](https://sprezzature.ai/)

Transformer un outil en ligne de commande en formulaire cliquable, automatiquement. Un outil en ligne de commande se pilote en tapant du texte (« fais ceci, avec ces options ») plutôt qu'en cliquant sur des boutons et des champs ; ce paquet lit la définition que l'outil se donne déjà de ses commandes et de ses options et construit une page web avec un champ pour chacune, pour qu'une personne qui n'a jamais ouvert de terminal puisse quand même s'en servir.

On le pointe vers un parseur : l'objet qu'un CLI (*command-line interface*, un programme qu'on pilote en tapant une ligne comme `git status` dans un terminal) écrit en Python construit pour lire et valider ce que l'utilisateur tape. `argparse` (dans la bibliothèque standard de Python), `Click` et `Typer` sont les trois façons courantes d'en construire un ; les trois sont importés et parcourus directement. Un CLI écrit avec autre chose, comme `cobra` en Go ou `clap` en Rust, passe par `--from-help`, qui lance le `--help` de l'outil dans un sous-processus et en lit le texte. Ça marche sur n'importe quel CLI, avec moins de fidélité : un texte d'aide en dit moins qu'un parseur.

À partir de ce parseur, le paquet produit une seule page autonome, écrite en JavaScript pur et mise en forme avec Tailwind, un cadre pour CSS (*Cascading Style Sheets*, les règles qui fixent couleurs, polices et marges d'une page web, comme « tous les titres en bleu ») qui fournit des classes de style prêtes à l'emploi plutôt que du CSS écrit à la main. Chaque sous-commande devient une section repliable avec son propre formulaire, et chaque drapeau (une option comme `--verbose`) un champ. La page n'exécute jamais la commande. Elle assemble la ligne de commande exacte sous forme de texte, dans le navigateur de la personne qui la visite, prête à copier-coller, à transmettre à une application de bureau par un appel `Tauri` `invoke` (`Tauri` habille une page web en application de bureau native ; `invoke` est le pont par lequel la page rappelle l'application), ou à envoyer à un serveur qui l'exécute.

Exemple : un CLI avec une sous-commande `convert INPUT OUTPUT` qui prend aussi `--verbose` devient une page avec une section `convert` contenant deux champs de texte et une case à cocher. Les remplir puis cliquer sur « Build command » affiche la ligne exacte `mytool convert in.csv out.json --verbose`, prête à copier.

Pas de cadre logiciel, pas d'étape de compilation de votre côté : la page produite est un seul fichier HTML qui ne charge rien. À chaque génération, le générateur demande au CDN (*content delivery network*, réseau de diffusion de contenu, ici `cdn.tailwindcss.com`) quelle version de Tailwind est courante, prend cette version complète (son CLI autonome, téléchargé une fois dans `~/.cache/sprezzature-cli-gui/tailwind/`, ou `SPREZZATURE_CLI_GUI_CACHE`) et en compile seulement les utilitaires que la page emploie, dans le `<style>` de la page : environ 10 ko. La version reste à jour, le navigateur du visiteur ne contacte jamais un tiers et la page se met en forme hors ligne. Sans réseau, la version la plus récente du cache sert ; `--offline` le fait exprès. La première exécution demande le réseau : le CLI pèse environ 45 Mo.

## Comment ça marche

![Schéma de flux. En haut, un outil en ligne de commande alimente deux voies, qui sont deux façons de le lire. La voie de gauche importe le module et parcourt les champs internes de l'objet parseur, avec une grande fidélité. La voie de droite lance l'aide de l'outil dans un sous-processus et en lit le texte imprimé, avec une fidélité moindre, et le dit. Les deux se rejoignent en un seul résultat, une description normalisée que le moteur de rendu transforme en une page HTML autonome.](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-cli-gui/main/assets/comment-ca-marche.svg)

## Installation

```bash
pip install sprezzature-cli-gui
```

Une seule installation apporte tout : les lecteurs argparse, Click et Typer, le lecteur `--from-help`, l'audit, l'API (*Application Programming Interface*, des adresses web auxquelles un autre programme envoie une requête et dont il reçoit une réponse) HTTP (*HyperText Transfer Protocol*, l'échange question-réponse qu'un navigateur fait pour chaque page qu'il charge) et le serveur MCP (Model Context Protocol, le protocole par lequel les agents IA appellent des outils en français), ainsi que le skill qu'un agent lit, qui voyage dans le paquet. Il n'y a aucun extra de fonctionnalité. Le seul extra, `[dev]`, est l'outillage de test (pytest, ruff, mypy, httpx2).

## Cinq surfaces

| Surface | Point d'entrée | Ce qu'elle fait |
|---|---|---|
| Bibliothèque | `from sprezzature_cli_gui import walk, render_html, audit` | Parcourir un parseur dans votre processus, produire la page, vérifier une page contre un parseur. |
| CLI | `sprezzature-cli-gui`, `sprezzature-cli-gui-audit` | Les deux mêmes travaux depuis un terminal. Ce sont deux commandes Click. |
| API HTTP | `uvicorn sprezzature_cli_gui.api:app`, ou `docker compose up` | Des routes FastAPI : un arbre de schéma en entrée, la page en sortie ; une page et un arbre en entrée, les constats en sortie. |
| MCP | `sprezzature-cli-gui-mcp` | Les mêmes routes, en outils MCP (*Model Context Protocol*) pour un hôte d'agent. |
| Skill | `sprezzature-cli-gui-skill`, `sprezzature_cli_gui.skill_path()` | Le `SKILL.md` qu'un agent comme Claude Code lit pour savoir quand router ici. Il voyage dans le paquet, dans `sprezzature_cli_gui/skill/` ; la commande le copie là où l'agent regarde. |

Le CLI et la bibliothèque importent votre module. L'API HTTP et le serveur MCP ne le font jamais : ils prennent l'arbre de schéma que `walk` produit, pas une spécification `module:fabrique`. Importer un module arbitraire nommé par un appelant non authentifié serait une exécution de code à distance ; cette étape reste donc sur votre machine.

## Ligne de commande

### `sprezzature-cli-gui` : un parseur en entrée, une page en sortie

```bash
# Depuis une fabrique de parseur dans un module importable
sprezzature-cli-gui my_pkg.my_cli:build_parser > gui.html

# Depuis un chemin de script, écrit dans un fichier avec un titre de page
sprezzature-cli-gui ./my_cli.py:make_parser --out gui.html --title "My Tool"

# Depuis un CLI qu'on ne peut pas importer, ou qui n'est pas en Python
sprezzature-cli-gui --from-help "mytool" --out gui.html
```

`SPEC` vaut `module:fabrique` ou `chemin/vers/fichier.py:fabrique`. Le nom après les deux-points est une fonction sans argument qui renvoie un `argparse.ArgumentParser`, une `click.Command` ou une `typer.Typer`. Il peut aussi nommer directement un tel objet : le chargeur l'utilise alors tel quel et ne l'appelle jamais, parce qu'appeler une commande Click ou une application Typer la lance.

| Option | Effet |
|---|---|
| `--from-help` | Traiter `SPEC` comme une ligne de commande, la lancer avec `--help` ajouté à la fin, et analyser le texte imprimé. Rien ne s'y rabat tout seul : il faut le demander. |
| `--out PATH` | Écrire le HTML dans `PATH` plutôt que sur la sortie standard. |
| `--title TEXT` | Le `<title>` de la page. Par défaut, le nom du programme. |
| `--prog TEXT` | Remplacer le nom du programme dans la page et dans la ligne construite. Le nom que donne un groupe Click ou une application Typer (un nom de fonction, ou `cli` pour une application Typer à plusieurs commandes) est rarement celui de la commande installée. |
| `--offline` | Compiler avec le Tailwind le plus récent déjà en cache, sans demander à `cdn.tailwindcss.com` quelle version est courante. Un cache vide sort avec le code 1. |
| `--json` | Imprimer l'arbre du parseur en JSON (*JavaScript Object Notation*, un format texte où les programmes rangent des données en champs nommés, comme {"nom": "Ada"}) plutôt que le HTML. |
| `-V`/`--version`, `-h`/`--help` | Version et aide. |

Une spécification introuvable, non importable ou impossible à parcourir sort avec le code 1 et une phrase sur la sortie d'erreur. Une page impossible à compiler aussi, et la phrase dit ce qui s'est passé : un statut HTTP d'un serveur qui a répondu (`HTTP 504` et l'URL), un réseau injoignable, ou `--offline` avec un cache vide sont trois phrases différentes.

Deux variables d'environnement valent pour toutes les surfaces, API HTTP et serveur MCP compris : `SPREZZATURE_CLI_GUI_OFFLINE=1` fait ce que fait `--offline`, et `SPREZZATURE_CLI_GUI_CACHE` déplace le cache.

La complétion du shell vient de Click :

```bash
eval "$(_SPREZZATURE_CLI_GUI_COMPLETE=bash_source sprezzature-cli-gui)"   # bash
eval "$(_SPREZZATURE_CLI_GUI_COMPLETE=zsh_source sprezzature-cli-gui)"    # zsh
```

### `sprezzature-cli-gui-audit` : la page couvre-t-elle encore le CLI ?

Une page produite le mois dernier peut prendre du retard sur un CLI qui a bougé depuis. L'audit prend la même `SPEC` et la page, et signale cinq sortes de désaccord :

| Règle | Sens |
|---|---|
| `flag-not-in-page` | Une option que le parseur accepte n'a aucun champ dans la page. |
| `field-has-no-flag` | Un champ construit une option que le parseur n'accepte pas. |
| `choice-dropped` | Un choix que le parseur propose manque dans la liste déroulante de la page. |
| `prog-missing` | La page n'amorce sa ligne de commande avec aucun nom de programme. |
| `prog-mismatch` | La page construit une ligne de commande pour un autre nom de programme. |

```bash
sprezzature-cli-gui-audit mytool.cli:build_parser gui.html
sprezzature-cli-gui-audit mytool.cli:build_parser gui.html --format json --prog mytool
```

Il sort avec 0 quand la page couvre le CLI et 1 dès qu'il y a au moins un constat. Une `PAGE` qui n'est pas un fichier sort aussi avec 1, et un message. `--prog` a le même sens que pour le générateur ; `--format` vaut `text` (par défaut) ou `json`.

## Bibliothèque

```python
from sprezzature_cli_gui import walk, render_html, audit

tree = walk(build_parser())               # argparse, Click ou Typer, dans votre processus
html = render_html(tree, title="My Tool")
open("gui.html", "w", encoding="utf-8").write(html)

for finding in audit(tree, html):         # une liste vide : la page couvre le CLI
    print(finding.rule, finding.subject, finding.message)
```

`walk(obj, prog=None)` renvoie l'arbre canonique : `prog`, `description`, `actions`, `sub_commands`. Elle lève `TypeError` pour tout ce qui n'est pas l'un des trois types de parseur. `render_html(tree, title="CLI GUI", offline=False, extra_content=())` renvoie la page complète. `offline=True` équivaut à `--offline`. `extra_content` est une suite de textes dont les classes doivent aussi être compilées, par exemple un script que vous ajoutez à la page et qui crée des éléments à l'exécution : Tailwind ne garde que les utilitaires qu'il voit. Elle lève `sprezzature_cli_gui.tailwind.TailwindUnavailable` quand aucun CLI Tailwind n'est disponible. `audit(tree, page)` renvoie une liste d'objets `Finding` (`rule`, `subject`, `message`). `skill_path()` renvoie le dossier du skill que le paquet livre.

## API HTTP

```bash
uvicorn sprezzature_cli_gui.api:app --host 0.0.0.0 --port 8000
```

| Méthode et chemin | `operation_id` | Ce qu'elle fait |
|---|---|---|
| `GET /health` | `health` | Sonde de vie : `{"status": "ok"}`. |
| `GET /v1/example` | `get_example_schema` | Un arbre de schéma parcouru depuis un petit parseur de démonstration, pour en copier la forme. |
| `POST /v1/render` | `render_gui` | Corps `{"tree": ..., "title": ...}` ; renvoie la page en HTML. Répond 400 quand l'arbre n'a pas `prog` ou `actions`, ou contient ce que le moteur de rendu ne sait pas lire, comme une action sans ses clés ; 503, avec la cause dans `detail`, quand aucun CLI Tailwind ne peut être téléchargé et qu'aucun n'est en cache. |
| `POST /v1/audit` | `audit_gui` | Corps `{"schema": ..., "page": ...}` ; renvoie `{"findings_total": n, "findings": [...]}`. |

La documentation interactive est servie sur `/docs` et `/redoc`.

Avec Docker, `docker compose up -d` construit l'image et sert ces routes sur le port 8000. Le fichier compose monte `./work` sur `/work` et fixe `PYTHONPATH=/work` ; la ligne de commande du conteneur peut donc importer un CLI que vous y déposez :

```bash
docker compose run --rm api sprezzature-cli-gui mytool.cli:build_parser --out /work/gui.html
```

La commande par défaut de l'image est `sprezzature-cli-gui-mcp --host 0.0.0.0 --port 8000` : un seul conteneur sert les routes HTTP et le point d'accès MCP sur `/mcp`, sur le même port.

L'image embarque le CLI Tailwind (environ 45 Mo, dans `/opt/sprezzature-cli-gui/cache`) : il est téléchargé et essayé à la construction de l'image, qui demande donc GitHub, et un conteneur neuf ne le repaie pas à sa première page. Un conteneur demande quand même au CDN quelle version est courante et ne télécharge que si Tailwind a publié depuis la construction ; `SPREZZATURE_CLI_GUI_OFFLINE=1` compile avec celui de l'image et ne sort jamais du conteneur.

## Serveur MCP

```bash
sprezzature-cli-gui-mcp                       # 127.0.0.1:8000
sprezzature-cli-gui-mcp --host 0.0.0.0 --port 9000
```

Il sert la même application FastAPI, avec un point d'accès MCP monté sur `/mcp`, en HTTP. Les valeurs par défaut viennent de `SPREZZATURE_CLI_GUI_HOST` et `SPREZZATURE_CLI_GUI_PORT` quand elles sont définies. Le nom de chaque outil est l'`operation_id` de sa route : `health`, `get_example_schema`, `render_gui`, `audit_gui`. Le routage des agents est décrit dans [TRIGGERS.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/TRIGGERS.md).

## Skill

Le skill est le dossier qu'un agent lit pour savoir quand se servir de ce paquet : un `SKILL.md`, ses `references/` (le catalogue des déclencheurs et les notes de durcissement pour un hôte qui exécute la ligne construite) et une démonstration complète dans `assets/examples/cli-gui-demo/`. Il voyage dans le paquet : `pip install` l'apporte avec les quatre autres surfaces, et `sprezzature_cli_gui.skill_path()` renvoie son dossier.

```bash
sprezzature-cli-gui-skill                          # la copie installée est-elle à jour ?
sprezzature-cli-gui-skill --install                # la copier dans ~/.claude/skills
sprezzature-cli-gui-skill --install --agent opencode   # ou dans ~/.opencode/skills
sprezzature-cli-gui-skill --path                   # où pip l'a mis
```

Sans `--install`, la commande ne fait que constater, et sort avec 0. Avec `--install`, elle copie le skill livré dans `~/.claude/skills/sprezzature-cli-gui/` (Claude Code) ou `~/.opencode/skills/sprezzature-cli-gui/` (OpenCode) ; une copie précédente est mise de côté dans `skills-superseded/`, à côté du dossier des skills et non dedans, où elle serait encore lue comme un skill.

## Ce que contient la page

- Un formulaire racine pour les options de premier niveau, puis une section repliable `<details>` par sous-commande, imbriquée aussi profond que le parseur.
- Un champ par option : une case à cocher pour un drapeau booléen, une liste déroulante pour une liste de choix, un champ numérique pour un entier ou un flottant, et un champ de texte pour tout le reste. Un compteur (`-v`, `action="count"` ou `count=True` de Click) est un champ numérique qui répète le drapeau : 3 donne `-v -v -v`. La case d'un drapeau seul part décochée et veut dire « passer ce drapeau » ; une paire marche/arrêt (`--color/--no-color`, `BooleanOptionalAction` d'argparse) part de sa valeur par défaut et écrit l'autre orthographe quand on la change. Un formulaire intact construit l'appel par défaut du parseur. Les arguments de fichier sont des champs de texte avec l'indication `path/to/file` ; un vrai sélecteur de fichier relève de l'hôte.
- Un bouton « Build command » dans chaque formulaire. Il construit la ligne à partir des champs de ce formulaire seulement ; un drapeau de premier niveau n'apparaît donc pas dans la ligne d'une sous-commande.
- Un bloc `<pre id="cli-out">` où la ligne construite apparaît, avec une mise entre guillemets prudente pour le shell.

Chaque champ porte un attribut `data-cli-flag` qui nomme l'option qu'il construit ; c'est ce que l'audit lit. Des exemples de branchement pour Tauri et les *Server-Sent Events* sont dans [EXAMPLES.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/EXAMPLES.md).

## Dans le paquet

- `adapters/` : un lecteur par source. `argparse.py` et `click.py` parcourent un objet parseur vivant ; une application Typer est convertie en sa commande Click et parcourue comme Click. `help_text.py` analyse le texte imprimé par `--help`.
- `schema.py` : `walk`, l'aiguillage qui ramène chaque source au même arbre.
- `renderer.py` : `render_html`, de l'arbre à la page autonome.
- `tailwind.py` : la version courante de Tailwind, son CLI en cache et le CSS compilé de la page.
- `loader.py` : résout une spécification `module:fabrique` ou `chemin.py:fabrique` jusqu'au parseur.
- `audit.py` : les cinq règles ci-dessus.
- `cli.py`, `audit_cli.py`, `_generate.py` : les deux commandes Click et le travail derrière le générateur.
- `api.py`, `mcp.py` : les surfaces HTTP et MCP.
- `skill/`, `_skill.py` : le skill qu'un agent lit, et la commande `sprezzature-cli-gui-skill` qui en rend compte et l'installe.

`scripts/cli_to_gui.py` réexporte le paquet pour un usage depuis un clone.

## Développement

```bash
pip install -e ".[dev]"
ruff check .
python -m pytest -q
```

La suite compile les pages avec un faux CLI Tailwind : elle n'a pas besoin du réseau. Un fichier, `tests/test_the_real_tailwind_compiles_the_page.py`, lance le vrai : ici dès qu'une vraie génération l'a mis en cache (sinon il saute et le dit), et dans le job `real-tailwind` de la CI (*continuous integration*, un serveur qui relance tous les tests à chaque envoi de code et signale ceux qui échouent), où un CLI absent est un échec et non un saut.

Voir [CONTRIBUTING.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/CONTRIBUTING.md) et, pour les voisins de ce paquet, [PAYSAGE.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/PAYSAGE.md).

## Licence

BSD (*Berkeley Software Distribution*, une licence permissive : chacun peut utiliser, modifier et revendre le code s'il garde la mention du copyright) à 3 clauses © Warith HARCHAOUI. Fait partie de la boîte à outils [sprezzature](https://sprezzature.ai/).
