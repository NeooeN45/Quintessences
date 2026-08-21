# RFC-0014 — POC Azure frugal et financement Microsoft for Startups

| Champ | Valeur |
|---|---|
| **ID** | RFC-0014 |
| **Statut** | Proposé — à valider avant création de ressources Azure |
| **Phase** | 4 — Implémentation |
| **Créé le** | 2026-07-22 |
| **Auteur** | Camille Perraudeau (Fondateur) |
| **Impact** | `GSIE/API/`, future infrastructure Azure, `18_FINANCING/` |
| **Décision liée** | À créer uniquement après validation de cette RFC |
| **RFC liées** | RFC-0012 (migration API), RFC-0013 (ingestion de données) |

---

## 1. Objet

Cette RFC propose un usage **limité, réversible et mesurable** de
Microsoft Azure pour exposer un POC de l'API GSIE. Elle propose aussi la
préparation d'une candidature Microsoft for Startups afin de financer les
expérimentations cloud sans détourner les ressources du chemin critique :

1. stabiliser GeoSylva et sa bêta professionnelle ;
2. démontrer une interopérabilité verticale minimale GeoSylva → GSIE ;
3. commencer Artemis après validation de cette liaison ;
4. reporter l'entraînement de modèles spécialisés, les GPU permanents et
   l'infrastructure lourde tant que les données et les usages ne sont pas
   validés.

Azure n'est pas une dépendance du fonctionnement terrain de GeoSylva.
L'application conserve sa capacité offline-first et ses calculs locaux.

## 2. Motivation

Le projet a besoin d'un environnement distant pour les démonstrations, les
tests d'interopérabilité et les premiers pilotes. La contrainte principale
reste le coût. L'architecture doit donc pouvoir :

- fonctionner localement sans Azure ;
- être reproduite par infrastructure as code ;
- revenir à zéro instance quand elle n'est pas utilisée ;
- être supprimée et redéployée sans perte de données métier ;
- séparer les données terrain, les sauvegardes et les services éphémères ;
- rendre chaque dépense attribuable et contrôlable.

Le programme Microsoft for Startups annonce des crédits Azure progressifs
pouvant atteindre 150 000 USD pour les entreprises admissibles. Ce montant
est un plafond, pas une attribution garantie. Le parcours avec code de
recommandation d'un membre du Microsoft Investor Network est le chemin prévu
par Microsoft pour accéder aux niveaux supérieurs.

## 3. Architecture proposée

### 3.1 Périmètre initial

| Besoin | Service proposé | Règle |
|---|---|---|
| API GSIE de démonstration | Azure Container Apps Consumption | `minReplicas=0`, plafond de réplicas explicite |
| Image de l'API | Azure Container Registry | Une image versionnée par livraison |
| Données structurées | PostgreSQL Flexible Server + PostGIS | Créé seulement au jalon de synchronisation |
| Capsules et petits artefacts | Azure Blob Storage | Rétention et cycle de vie configurés |
| Secrets | Managed Identity puis Key Vault | Aucun secret durable dans Git ou l'image |
| Journaux | Azure Monitor, rétention courte | Pas d'ingestion illimitée par défaut |

Avant le premier flux de synchronisation, PostgreSQL/PostGIS reste local dans
l'environnement de développement. Redis, Kubernetes, GPU, moteur vectoriel
managé et entrepôt analytique sont exclus du POC tant qu'un besoin mesuré ne
les justifie pas.

### 3.2 Frontière offline-first

GeoSylva reste l'autorité opérationnelle sur le terrain : saisie, calculs
déterministes, catalogue d'essences nécessaire au chantier et file de
synchronisation sont locaux. GSIE reçoit ensuite des paquets versionnés et
traçables. Une indisponibilité d'Azure ne doit empêcher ni une mesure, ni un
calcul, ni l'export local d'un chantier.

### 3.3 Contrat de synchronisation minimal

Le premier parcours accepté est volontairement étroit :

1. création ou modification d'un chantier dans GeoSylva ;
2. constitution locale d'une capsule versionnée avec identifiant stable ;
3. synchronisation manuelle ou différée vers un endpoint GSIE idempotent ;
4. validation de schéma, provenance et horodatage côté GSIE ;
5. accusé de réception local sans suppression prématurée de la source ;
6. reprise vérifiée après coupure réseau et absence de doublon.

## 4. Garde-fous financiers obligatoires

Avant toute ressource payante :

- une souscription et un groupe de ressources dédiés au POC ;
- des étiquettes `project`, `environment`, `owner`, `expiry` et
  `cost_center` sur chaque ressource ;
- des alertes budgétaires à 50 %, 80 % et 100 % du budget mensuel, ainsi que
  des alertes absolues adaptées au budget disponible ;
- un propriétaire et une date d'expiration pour chaque ressource ;
- une politique de suppression ou d'arrêt des environnements de test ;
- une rétention courte et plafonnée des logs ;
- aucun déploiement manuel non représenté dans l'infrastructure as code ;
- un export mensuel des coûts et une revue avant changement d'échelle.

Les budgets Azure **alertent mais ne coupent pas automatiquement** les
ressources. Le crédit Azure Sponsorship peut en outre basculer vers une offre
pay-as-you-go à l'expiration ou à l'épuisement des crédits. Une carte bancaire
ne doit donc pas être considérée comme une protection de coût.

## 5. Plan d'exécution proposé

| Jalon | Livrable | Critère de sortie |
|---|---|---|
| J0 — Dossier | Candidature Microsoft for Startups complétée | Identité légale et preuves vérifiées |
| J1 — Local | API et PostGIS reproductibles localement | Tests, sauvegarde et restauration réussis |
| J2 — Infra | Infrastructure as code du POC | `plan/what-if` relisible, aucun secret |
| J3 — API | API GSIE sur Container Apps | Mise à zéro, santé, logs et coût vérifiés |
| J4 — Données | PostgreSQL/PostGIS distant | Migration et restauration testées |
| J5 — Verticale | Un chantier GeoSylva synchronisé | Reprise offline et idempotence prouvées |
| J6 — Pilote | Petit groupe de testeurs professionnels | Retours tracés et budget respecté |

L'ordre J1 → J6 est obligatoire. L'obtention de crédits ne justifie pas de
sauter les validations ni de déployer les composants exclus.

## 6. Critères d'acceptation

La proposition peut être adoptée si :

- la bêta GeoSylva reste prioritaire ;
- le coût mensuel maximal du POC est explicitement validé par le Fondateur ;
- l'environnement peut être détruit puis reconstruit depuis le dépôt ;
- une procédure d'export PostgreSQL et Blob est testée ;
- les calculs forestiers critiques restent déterministes et testables sans
  service d'IA distant ;
- aucune donnée sensible réelle n'est utilisée avant revue sécurité et RGPD.

## 7. Alternatives

### 7.1 Hébergement local uniquement

Conservé comme mode de développement et solution de repli. Il ne suffit pas
pour une démonstration distante ou un pilote multi-organisation.

### 7.2 Machine virtuelle Azure permanente

Rejetée pour le POC : coûts au repos, maintenance système et surface de
sécurité disproportionnés.

### 7.3 Kubernetes managé

Rejeté pour le POC : complexité inutile avant preuve de charge et d'équipe
d'exploitation.

### 7.4 GPU et entraînement de LLM

Reportés : la priorité est la qualité des données, les algorithmes
déterministes et la validation métier. Les GPU serverless pourront être
évalués plus tard pour des expériences bornées et mesurées.

## 8. Risques et réversibilité

| Risque | Réduction |
|---|---|
| Dépassement de crédits | Plafonds de capacité, alertes, dates d'expiration, revue hebdomadaire |
| Verrouillage fournisseur | Conteneurs OCI, PostgreSQL/PostGIS, export Blob standard |
| Dispersion du développement | Un seul parcours vertical avant tout nouveau service |
| Fuite de données | Données synthétiques au POC, identités managées, revue RGPD |
| Surarchitecture | Liste d'exclusion explicite et preuves de besoin |

La sortie d'Azure doit rester possible par export PostgreSQL, copie des objets
et redéploiement des conteneurs sur un autre hébergeur compatible.

## 9. Références officielles

- [Candidature Microsoft for Startups](https://learn.microsoft.com/fr-fr/startups/microsoft-for-startups/application)
- [Vue d'ensemble Microsoft for Startups](https://learn.microsoft.com/en-us/startups/microsoft-for-startups/overview)
- [Azure Container Apps et allocation gratuite](https://azure.microsoft.com/en-us/products/container-apps)
- [Mise à l'échelle de Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/scale-app)
- [Extensions PostgreSQL prises en charge](https://learn.microsoft.com/en-us/azure/postgresql/extensions/concepts-extensions-versions)
- [Budgets Azure Cost Management](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)

## 10. Validation demandée

Cette RFC ne crée aucune ressource Azure. Après validation du Fondateur, une
décision dédiée pourra autoriser J1 et J2. J3 nécessitera en plus un plafond
mensuel écrit et une vérification des garde-fous financiers.
