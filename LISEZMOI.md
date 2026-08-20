# sprezzature-cli-gui

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-cli-gui/main/assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

Transformer n'importe quel outil en ligne de commande Python en formulaire cliquable, automatiquement. Un outil en ligne de commande se pilote en tapant du texte (« fais ceci, avec ces options ») plutôt qu'en cliquant sur des boutons et des champs ; ce paquet lit la définition que l'outil se donne déjà de ses commandes et de ses options et construit à partir de là une page web avec un bouton et un champ pour chacune, pour qu'une personne qui n'a jamais ouvert de terminal puisse quand même s'en servir.

On pointe l'outil vers un parseur : l'objet qu'un programme en ligne de commande Python construit pour lire et valider ce que l'utilisateur tape. Trois bibliothèques servent à construire cet objet, toutes trois prises en charge : `argparse` (dans la bibliothèque standard de Python), `Click` et `Typer`. À partir de ce parseur, le paquet produit une seule page autonome, écrite en JavaScript pur et mise en forme avec Tailwind (un cadre de style CSS qui fournit des classes prêtes à l'emploi plutôt que d'écrire le CSS à la main). Chaque sous-commande devient une section, chaque drapeau (une option de la ligne de commande, comme `--verbose`) un champ. La page n'exécute jamais la commande elle-même : elle assemble la ligne de commande exacte sous forme de texte, dans le navigateur de la personne qui la visite, prête à copier-coller, à transmettre à une application de bureau via un appel `Tauri` `invoke` (`Tauri` habille une page web en application de bureau native ; `invoke` est le pont par lequel cette page rappelle l'application), ou à envoyer à un point d'entrée FastAPI (un petit serveur web Python) qui l'exécute pour de vrai.

Exemple : un outil avec un drapeau `--verbose` et une sous-commande `convert INPUT OUTPUT` devient une page avec une case à cocher pour `--verbose` et deux champs de texte pour `INPUT` et `OUTPUT` ; les remplir puis cliquer sur « Build command » affiche la ligne exacte `mytool convert in.csv out.json --verbose`, prête à copier.

Pas de cadre logiciel, pas d'étape de compilation : la page produite est un seul fichier HTML. Elle charge tout de même la version « Play » de Tailwind depuis un réseau de diffusion de contenu (`cdn.tailwindcss.com`) pour transformer les classes utilitaires en vrai CSS dans le navigateur de la personne qui l'ouvre ; une connexion internet est donc nécessaire au premier chargement. Les champs du formulaire, eux, fonctionnent sans elle, simplement sans mise en forme.

## Installation

```bash
pip install sprezzature-cli-gui           # base (argparse)
pip install "sprezzature-cli-gui[click]"  # ajoute la prise en charge de Click
pip install "sprezzature-cli-gui[typer]"  # ajoute la prise en charge de Typer
```

## Utilisation

```bash
# Depuis une fabrique de parseur dans un module importable
sprezzature-cli-gui my_pkg.my_cli:build_parser > gui.html

# Depuis un chemin de script
sprezzature-cli-gui ./my_cli.py:make_parser > gui.html
```

Quand le parseur ne peut pas être importé, l'outil se rabat sur l'analyse de la sortie `--help` de la cible ; il fonctionne donc même contre un outil qu'il ne peut pas inspecter directement, y compris un outil qui n'est pas écrit en Python.

## Fonctionnement

`cli_to_gui.py` est une façade légère qui réexporte l'implémentation réelle, elle-même dans le paquet `sprezzature_cli_gui` :

- `adapters/` : lit (inspecte, c'est-à-dire examine directement les champs internes de l'objet parseur, plutôt que de deviner à partir du texte imprimé) un parseur argparse ou Click ; ou, quand aucun objet parseur n'est accessible, se rabat sur l'analyse du texte `--help`.
- `schema.py` : la description normalisée de commande et de drapeau que chaque adaptateur produit, la même quel que soit le framework d'origine, si bien que le moteur de rendu n'a jamais besoin de savoir lequel des trois l'a produite.
- `renderer.py` : transforme cette description en la page HTML autonome, avec Tailwind et le JavaScript pur.
- `loader.py` : résout une spécification `module:fabrique` ou `chemin.py:fabrique` (une chaîne qui nomme l'endroit où vit la fonction qui construit le parseur) jusqu'à l'objet parseur réel.

## Licence

BSD à 3 clauses © Warith Harchaoui. Fait partie de la boîte à outils [sprezzature](https://harchaoui.org/warith/sprezzature/).
