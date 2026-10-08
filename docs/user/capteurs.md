# Capteurs Ecole Directe

Cette page décrit les capteurs créés par l'intégration, leurs états et leurs attributs d'état. Les clés des attributs sont sensibles à la casse et sont reproduites telles qu'elles apparaissent dans Home Assistant.

## Disponibilité

Les capteurs associés à un élève sont créés selon les modules accessibles à son compte : `CAHIER_DE_TEXTES` pour les devoirs, `EDT` pour l'emploi du temps, `NOTES` pour les notes et moyennes, `VIE_SCOLAIRE` pour la vie scolaire et `MESSAGERIE` pour la messagerie. Les formulaires nécessitent le module `EDFORMS`. L'option de forçage des modules peut activer les modules Notes, Emploi du temps et Vie scolaire même si l'établissement les a désactivés.

Le profil de chaque élève est toujours créé. Les portefeuilles apparaissent lorsqu'un solde est renvoyé par Ecole Directe. Certains capteurs existent au niveau du compte, d'autres pour chaque élève. Les variantes non applicables à un compte ou à un élève ne sont pas créées.

Sauf indication contraire, les capteurs liés à un élève ont aussi l'attribut `prenom`. Les capteurs de compteur affichent `0` lorsque leur liste est vide. Un capteur dont la donnée n'est pas disponible est indisponible dans Home Assistant.

## Profil et portefeuille

| Capteur | État | Attributs supplémentaires |
| --- | --- | --- |
| Profil de l'élève (`sensor.ed_PRENOM_NOM`) | Nom complet | `prenom`, `nom`, `nom complet`, `classe`, `etablissement`, `via_parent_account` |
| Portefeuille, un par compte et libellé disponible | Solde en EUR | `prenom` pour un portefeuille associé à un élève ; aucun attribut ajouté pour le portefeuille du compte |

`via_parent_account` vaut `true` lorsque la connexion est un compte parent. Le solde est une valeur monétaire ; le nom du capteur reprend le libellé du portefeuille.

## Devoirs et emploi du temps

Les capteurs de devoirs sont créés pour la période complète, aujourd'hui, demain, le prochain jour de cours, la semaine en cours, la semaine suivante et la semaine après suivante. Leur état est le nombre de devoirs de la période.

| Attribut | Contenu |
| --- | --- |
| `Devoirs` | Liste de devoirs, triée par date |
| `A faire` | Nombre de devoirs dont `effectue` vaut `false` |

Chaque élément de `Devoirs` contient les clés suivantes : `devoir_id`, `date`, `matiere`, `short_description`, `description`, `effectue`, `interrogation` et `documents`. `short_description` est tronquée à 125 caractères. Les contenus et documents disponibles dépendent des données retournées par Ecole Directe.

Les capteurs d'emploi du temps couvrent aujourd'hui, demain, le prochain jour de cours, la semaine en cours, la semaine suivante et la semaine après suivante. Leur état est le nombre de cours.

| Attribut | Contenu |
| --- | --- |
| `Emploi du temps` | Liste des cours |
| `Cours annulés` | Nombre de cours annulés |
| `Cours modifiés` | Nombre de cours modifiés |
| `Déjeuner début` | Heure de fin du dernier cours avant la pause déjeuner (capteurs journaliers uniquement) |
| `Déjeuner fin` | Heure de début du premier cours après la pause déjeuner (capteurs journaliers uniquement) |
| `Journée début` | Heure du premier cours de la journée (capteurs journaliers uniquement) |
| `Journée fin` | Heure du dernier cours de la journée (capteurs journaliers uniquement) |
| `Date` | Date des cours (capteurs journaliers uniquement) |

Chaque cours peut contenir : `start`, `end`, `start_at`, `end_at`, `start_time`, `end_time`, `lesson`, `salle`, `is_annule`, `is_modifie`, `background_color`, `prof`, `dispense`, `is_morning` et `is_afternoon`.

Pour les attributs volumineux des devoirs et des emplois du temps, Home Assistant peut ne recevoir qu'une référence au Store : `stored_in_store` vaut `true` et `store_key` indique la clé de stockage.

## Notes et moyennes

| Capteur | État | Attributs supplémentaires |
| --- | --- | --- |
| Notes | Nombre de notes | `notes` : liste des notes |
| Évaluations | Nombre d'évaluations | `Evaluations` : liste des évaluations ; `level_mapping` : correspondance entre niveaux et libellés |
| Discipline (un capteur par matière) | Moyenne de la matière | `Code`, `Nom`, `Moyenne classe`, `Moyenne minimum`, `Moyenne maximum`, `Appréciations` |
| Moyenne générale | Moyenne générale de la période courante | `Moyenne classe`, `Moyenne minimum`, `Moyenne maximum`, `Date de calcul`, `Disciplines` |
| Moyennes par période | Nombre de périodes disponibles | `periodes` : liste des périodes et de leurs moyennes |

Chaque élément de `notes` contient : `date`, `matiere`, `commentaire`, `note`, `sur`, `note_sur`, `coefficient`, `moyenne_classe`, `max`, `min`, `non_significatif`, `date_saisie` et `elements_programme`. Les éléments de programme contiennent `competence`, `descriptif`, `valeur` et `level`.

Chaque élément de `Evaluations` peut contenir `devoir`, `date`, `date_saisie`, `matiere` et `elements_programme`. Chaque élément de programme d'une évaluation contient `competence`, `descriptif`, `valeur` et `level`. La correspondance `level_mapping` associe `1` à « Non atteint », `2` à « Partiellement atteint », `3` à « Atteint » et `4` à « Dépassé ».

Les attributs `Disciplines` de la moyenne générale contiennent les matières avec `code`, `nom`, `moyenne`, `moyenneClasse`, `moyenneMin`, `moyenneMax` et `appreciations`.

Chaque élément de `periodes` contient `idPeriode`, `codePeriode`, `nomPeriode`, `annuel`, `examenBlanc`, `cloture`, `dateDebut`, `dateFin` et `moyenne_generale`. Cette dernière contient `moyenneGenerale`, `moyenneClasse`, `moyenneMin`, `moyenneMax` et `dateCalcul`.

## Vie scolaire

Les quatre capteurs suivants ont pour état le nombre d'éléments correspondants :

| Capteur | Attribut de liste |
| --- | --- |
| Absences | `Absences` |
| Retards | `Retards` |
| Sanctions | `Sanctions` |
| Encouragements | `Encouragements` |

Chaque élément de ces listes contient `date`, `type_element`, `display_date`, `justifie`, `motif`, `libelle` et `commentaire`. Le nombre d'éléments remontés dépend de la disponibilité des données Ecole Directe.

## Messagerie et formulaires

| Capteur | État | Attributs supplémentaires |
| --- | --- | --- |
| Messagerie (compte ou élève) | Texte au format `non lus/reçus` | `Reçus`, `Envoyés`, `Archivés`, `Non lu`, `Brouillons` ; `prenom` pour le capteur d'un élève |
| Formulaires (compte) | Nombre de formulaires | `Formulaires` : liste des formulaires |

Chaque formulaire contient `titre` et `created`. Les compteurs de messagerie correspondent respectivement aux messages reçus, envoyés, archivés, reçus non lus et brouillons.
