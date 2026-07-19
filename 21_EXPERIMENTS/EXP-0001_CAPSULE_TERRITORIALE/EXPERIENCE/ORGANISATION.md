# Organisation de l'incrément démontrable

| Champ | Valeur |
|---|---|
| **Statut** | Draft opérationnel |
| **Horizon** | 3 incréments courts |
| **Objet** | territoire de référence + capsule signée + Golden Bench |

## Objectif produit

À la fin de l'incrément, un partenaire, un forestier ou un développeur doit
pouvoir voir en cinq minutes que GSIE sait :

1. transporter un contexte territorial complet ;
2. vérifier son origine et son intégrité sans réseau ;
3. exécuter un calcul reproductible ;
4. rendre visible la provenance, la tolérance et le statut de revue ;
5. refuser une donnée altérée au lieu de produire silencieusement un résultat.

## Résultat de chaque incrément

| Incrément | Résultat démontrable | Gate de sortie |
|---|---|---|
| **I0 — Preuve locale** | CLI Python, capsule synthétique, signature, Golden Bench, tests | `make demo` et `make test` verts |
| **I1 — Contrat partagé** | fixtures figées, API de distribution, vérificateur Kotlin | mêmes capsules acceptées/rejetées par Python et Android |
| **I2 — Usage terrain** | téléchargement résumable, installation atomique, écran GeoSylva, rapport dans le Hub | démonstration mode avion sur appareil réel |

I0 est le périmètre du présent code. I1 et I2 restent planifiés.

## Chantiers et responsabilités

| Chantier | Responsable attendu | Relecteur obligatoire | Livrable |
|---|---|---|---|
| Produit et arbitrages | Fondateur / Product Owner | utilisateur professionnel | scénario et priorités |
| Science forestière | référent dendrométrie/sylviculture | second expert indépendant | cas Golden Bench validés |
| Données et licences | Data Steward | juridique/RGPD | data cards et matrice de droits |
| Backend GSIE | développeur Python | sécurité + QA | builder, registre et API |
| GeoSylva | développeur Kotlin | utilisateur terrain | vérification et installation |
| Hub UE 5.8 | développeur C++/Blueprint | UX + opérateur | lecture et visualisation |
| Sécurité | référent AppSec | mainteneur Android/backend | clés, menaces, rollback |
| Qualité | QA | expert métier | tests, rapports et gates |

Une même personne peut tenir plusieurs rôles, mais ne doit pas valider seule
un cas scientifique qu'elle a écrit.

## Backlog ordonné

| ID | Priorité | Élément | État après I0 |
|---|---|---|---|
| CAP-001 | P0 | Manifeste canonique et schéma JSON | Implémenté expérimental |
| CAP-002 | P0 | Signature/vérification Ed25519 | Implémenté expérimental |
| CAP-003 | P0 | Contrôle SHA-256 de chaque membre | Implémenté expérimental |
| CAP-004 | P0 | Défenses Zip Slip, doublons et budgets | Implémenté expérimental |
| BENCH-001 | P0 | Format de cas attendu/obtenu/tolérance | Implémenté expérimental |
| BENCH-002 | P0 | Rapport JSON et états de revue | Implémenté expérimental |
| DATA-001 | P0 | Fixture territoriale sans droits tiers | Implémenté synthétique |
| SCI-001 | P0 | Revue des formules et tolérances | À faire par expert |
| API-001 | P1 | Endpoint catalogue/téléchargement | Planifié I1 |
| SDK-001 | P1 | Vérificateur Kotlin contractuel | Planifié I1 |
| SEC-001 | P1 | Rotation/révocation/protection rollback | Planifié I1 |
| GEO-001 | P1 | Installation atomique dans GeoSylva | Planifié I2 |
| UX-001 | P1 | Écran stockage, périmètre, fraîcheur, confiance | Planifié I2 |
| HUB-001 | P2 | Lecture de la même capsule dans UE 5.8 | Planifié I2 |

## Definition of Ready

Un élément peut entrer en développement si :

- son utilisateur et son bénéfice sont identifiés ;
- les données d'entrée et de sortie sont décrites ;
- la licence et la provenance des données sont connues ;
- un exemple positif et un exemple de rejet existent ;
- les contraintes offline, sécurité et taille sont explicites ;
- le statut scientifique attendu est défini.

## Definition of Done

Un élément n'est terminé que si :

- code, documentation et contrat sont cohérents ;
- tests de succès et d'échec existent ;
- aucun accès réseau n'est nécessaire sur le chemin offline ;
- les erreurs sont explicites et ne masquent pas une incertitude ;
- les rapports sont lisibles par une machine et par un humain ;
- sécurité, licence et provenance ont été revues ;
- la mémoire, la roadmap et le changelog sont mis à jour.

Pour une règle ou formule scientifique s'ajoutent : source vérifiable,
version, domaine de validité, unité, tolérance, cas limites, auteur et double
revue.

## Rythme de pilotage

- Début d'incrément : choisir un seul scénario démontrable et ses gates.
- Chaque changement : conserver une fixture acceptée et au moins une fixture
  rejetée.
- Fin d'incrément : rejouer la démonstration depuis un environnement propre,
  conserver le rapport, mesurer temps et taille, puis décider de promouvoir,
  corriger ou abandonner.

## Indicateurs I0

| Indicateur | Cible |
|---|---|
| Commandes nécessaires pour la démo | 1 |
| Accès réseau durant la démo | 0 |
| Fichiers du payload vérifiés | 100 % |
| Altérations silencieusement acceptées | 0 |
| Cas numériques avec attendu/obtenu/tolérance | 100 % |
| Cas présentés comme validés sans revue | 0 |
| Durée cible sur poste de développement | moins de 60 s |

