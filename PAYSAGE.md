# Paysage : sprezzature-cli-gui en contexte

Le tableau ci-dessous note six outils qui transforment un outil en ligne de commande en quelque chose qu'une personne qui n'utilise pas de terminal peut piloter, une colonne étoilée par axe. Une note va de 1 (faible) à 5 (excellent) ; une cellule marquée `--` signifie que l'outil ne traite pas du tout cet axe, si bien que le noter n'aurait pas de sens.

| Outil | Zéro configuration | Sortie statique | Multi-framework | Aucune dépendance ajoutée à l'outil cible | CLI non Python |
|---|---|---|---|---|---|
| **sprezzature-cli-gui** | **5** | **5** | **4** | **5** | **3** |
| Streamlit | 2 | -- | -- | 1 | -- |
| Gradio | 2 | -- | -- | 1 | -- |
| Gooey | 3 | -- | 2 | 2 | -- |
| PySimpleGUI | 2 | -- | 1 | 2 | -- |
| `--help` natif de Typer | 5 | -- | -- | 5 | -- |
| click-web | 3 | 2 | 1 | 2 | -- |

Trois colonnes désignent une propriété plutôt qu'un mot familier : **Zéro configuration** note l'effort que l'auteur de l'outil ciblé doit fournir (redécorer chaque option, restructurer l'application, ajouter un serveur) avant qu'une interface graphique apparaisse. **Sortie statique** note si le résultat est un simple fichier qu'on peut héberger n'importe où ou un processus qui doit rester en cours d'exécution. **Aucune dépendance ajoutée à l'outil cible** note si l'usage de l'outil introduit une dépendance d'exécution dans le programme qu'on enveloppe ou si tout reste du côté de la génération.

## Notes

**Streamlit** et **Gradio** construisent une vraie application web interactive, avec exécution en direct, pas seulement un formulaire : bien plus capables quand l'objectif est un outil réellement exécutable, mais ils demandent de réécrire l'interaction sous forme de widgets Streamlit ou Gradio ; le résultat est un processus Python qui doit tourner en continu, pas un fichier à transmettre.

**Gooey** décore un script argparse existant et fait apparaître une fenêtre de bureau construite avec wxPython ; proche dans l'esprit de sprezzature-cli-gui, mais il exige wxPython installé sur la machine qui exécute l'interface et ne produit rien de statique.

**PySimpleGUI** est une boîte à outils d'interface de bureau généraliste ; rien n'y est spécifique à l'habillage d'une ligne de commande ; s'en servir pour ça revient à construire chaque champ à la main.

**Le `--help` natif de Typer** n'est pas vraiment un concurrent, c'est plutôt la raison pour laquelle la colonne « aucune dépendance ajoutée » compte : Typer offre déjà une excellente ergonomie de terminal gratuitement, mais ne produit jamais de formulaire cliquable pour une personne qui n'ouvre pas de terminal.

**click-web** est l'outil le plus proche : il lit lui aussi la structure propre d'une application Click et sert un formulaire web à partir de là, mais sous la forme d'un serveur Flask qui doit rester actif (d'où sa faible note en sortie statique), et, à la différence du repli `--from-help` de sprezzature-cli-gui, n'a aucune voie pour un outil qu'il ne peut pas importer directement.

## Positionnement de sprezzature-cli-gui

Son atout distinctif est de produire un **seul fichier HTML statique** à partir de l'objet parseur d'un outil, sans aucun serveur à faire tourner et sans rien changer à l'outil lui-même : on le pointe vers un parseur `argparse`, Click ou Typer déjà existant (ou, avec une fidélité moindre, vers le texte `--help` de n'importe quel outil, Python ou non) et on récupère un fichier qui assemble la ligne de commande exacte sous forme de texte, prête à transmettre à ce qui l'exécutera pour de vrai.
