# SITE — Site public Quintessences 1.0.0

| Champ | Valeur |
|---|---|
| **Identifiant** | SITE-001 |
| **Statut** | Validé |
| **Version** | 1.0.0 |
| **Date** | 2026-08-09 |
| **Auteur** | Fondateur — proposition instruite par Claude (Anthropic) |
| **Décision** | DEC-000057 |
| **Dépend de** | `IDENTITE-001` (compte), `DEC-000056` (icônes des 9 apps), `GSIE-DIR-0009` §3/§227 (Terra/Aeris/Atlas) |
| **Voir aussi** | `SITE-002` — direction créative et expérience |

## 1. Résumé

Cette spécification définit les exigences du **site public unifié**
`quintessences-platform.com`, qui remplace et étend la landing page
statique actuelle (`landing-quintessences/`). Le site regroupe cinq
zones : landing page, compte utilisateur, actualités, galerie et
contact. L'ambition est un site au niveau des références du secteur
(voir `SITE-002` pour les inspirations et la direction créative),
sobre et scientifique dans le ton (CLAUDE.md §8), sans jargon
commercial.

Cette spécification ne décrit pas l'implémentation (composants,
librairies, code) — voir `SITE-002` pour la direction d'expérience et
une future architecture technique pour l'implémentation.

## 2. Périmètre

### 2.1 Zones couvertes

1. **Landing** (`/`) — présentation de Quintessences, GSIE, des 9
   applications, des principes fondateurs.
2. **Compte** (`/compte/`) — connexion, inscription, profil, sécurité,
   sessions, suppression de compte. Consomme `IDENTITE-001` sans le
   dupliquer.
3. **Actualités** (`/actualites/`) — fil public des avancées produit.
4. **Galerie** (`/galerie/`) — médias sélectionnés (images/vidéos de
   démonstration, notamment drones Ignis).
5. **Contact** (`/contact`) — formulaire déjà protégé par Turnstile
   (existant, à faire évoluer).

### 2.2 Hors périmètre (voir §10)

- Boutique, paiement, abonnement.
- Blog long-format ou CMS éditorial complexe (l'actualité reste un
  fil court, pas un blog).
- Multilingue au lancement (architecture prête pour l'anglais, contenu
  français uniquement en v1).
- Modération communautaire (commentaires, réactions).
- Upload public de médias par les utilisateurs pour la galerie.

## 3. Exigences fonctionnelles

### 3.1 Landing

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| SITE-F-001 | La page d'accueil présente Quintessences et GSIE en une vue de tête (hero) | P0 | Titre, sous-titre et appel à l'action visibles sans défilement sur desktop et mobile |
| SITE-F-002 | La page présente la chaîne d'intelligence GSIE (Evidence → … → Validation) | P0 | Les 7 moteurs de la chaîne principale sont nommés et ordonnés correctement |
| SITE-F-003 | La page présente les 9 applications avec leur icône réelle | P0 | GeoSylva, Ignis, Hydro, Flora, Artemis, QGISIA, Terra, Aeris, Atlas apparaissent avec l'icône intégrée par `DEC-000056` |
| SITE-F-004 | Chaque application affiche son domaine et un résumé court | P0 | Le texte reprend le domaine déclaré dans `CLAUDE.md` §10 sans invention |
| SITE-F-005 | La page présente les principes fondateurs du projet | P0 | Reprend au minimum GSIE-CON-001 (le forestier décide) et CON-002 (traçabilité) sans les reformuler de façon inexacte |
| SITE-F-006 | La page affiche des indicateurs publics réels (ex. connaissances validées, datasets catalogués) | P1 | Chaque indicateur est lu depuis un endpoint public de l'API GSIE, jamais une valeur codée en dur qui devient fausse avec le temps |
| SITE-F-007 | Un indicateur dont la source est indisponible affiche un état dégradé explicite, jamais une valeur périmée silencieuse | P0 | Message « donnée indisponible » visible, aucune valeur mise en cache présentée comme actuelle |
| SITE-F-008 | La page relie vers la documentation, l'API et le statut existants | P0 | Liens vers `docs.`, `api.`/docs et `status.quintessences-platform.com` fonctionnels |
| SITE-F-009 | La page relie vers le compte (connexion/inscription) | P0 | Lien visible en en-tête vers `/compte/` |

### 3.2 Compte

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| SITE-F-010 | Le site expose les écrans requis par `IDENTITE-001` (ID-F-002 à ID-F-020) sur le web | P0 | Connexion, inscription, Google OIDC, profil, vérification e-mail, récupération, sessions, suppression fonctionnent via le même compte que GeoSylva |
| SITE-F-011 | L'espace compte partage l'identité visuelle du reste du site | P0 | Pas de redirection vers une interface visuellement disjointe (ex. écran Keycloak par défaut non habillé) |
| SITE-F-012 | Un utilisateur connecté voit un état de connexion persistant en navigation | P1 | Le nom/avatar apparaît dans l'en-tête sur toutes les zones du site, pas seulement `/compte/` |

Le détail fonctionnel et sécurité du compte (mots de passe, MFA,
anti-énumération, jetons) reste normatif dans `IDENTITE-001` — cette
spécification n'en crée pas de version parallèle.

### 3.3 Actualités

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| SITE-F-013 | Le site publie un fil chronologique des avancées produit | P0 | Liste triée par date décroissante, une entrée = un titre, une date, un résumé court |
| SITE-F-014 | Chaque entrée est reformulée en langage clair, sans détail technique interne | P0 | Aucun chemin de fichier, nom de variable, secret ou détail d'infrastructure interne dans le texte publié |
| SITE-F-015 | Chaque entrée peut être filtrée par application ou domaine concerné | P1 | Un filtre par app (GeoSylva, Ignis, …) réduit la liste sans rechargement complet |
| SITE-F-016 | Une entrée peut être retrouvée par une URL stable | P1 | Chaque entrée a une URL dédiée partageable |
| SITE-F-017 | Le contenu des actualités est versionné dans le dépôt, pas dans une base tierce | P0 | Les entrées sont des fichiers texte sous contrôle de version (cohérent avec CON-002 traçabilité) |

### 3.4 Galerie

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| SITE-F-018 | La galerie affiche des médias sélectionnés manuellement par le Fondateur | P0 | Aucun média n'apparaît sans une étape de publication explicite et tracée |
| SITE-F-019 | Chaque média porte une légende, une date et un contexte (mission/app d'origine) | P0 | Aucun média sans métadonnée minimale |
| SITE-F-020 | Chaque média porte une mention explicite « vol de test / démonstration » ou équivalent lorsque ce n'est pas une opération réelle | P0 | Aucune ambiguïté entre contenu de démonstration et intervention réelle |
| SITE-F-021 | Un média contenant une personne, un véhicule ou une propriété identifiable n'est publié qu'après vérification qu'aucun consentement ou anonymisation n'est requis | P0 | Vérifié manuellement avant publication (processus hors code, voir §9 risques) |
| SITE-F-022 | La galerie peut être filtrée par application ou type de média | P1 | Filtre fonctionnel sans rechargement complet |

### 3.5 Contact

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| SITE-F-023 | Le formulaire de contact reste protégé par Cloudflare Turnstile | P0 | Aucune soumission n'aboutit sans jeton Turnstile valide (comportement existant, DEC-000055) |
| SITE-F-024 | Le formulaire permet de catégoriser la demande (partenariat, presse, sécurité, support, autre) | P1 | Le message reçu porte la catégorie choisie |
| SITE-F-025 | Une demande de catégorie « sécurité » est signalée distinctement | P1 | Le canal de réception distingue visuellement les signalements de sécurité |

## 4. Exigences d'expérience et non fonctionnelles

| ID | Exigence | Critère d'acceptation |
|---|---|---|
| SITE-X-001 | Chargement perçu rapide sur connexion mobile courante | LCP < 2,5 s, INP < 200 ms, CLS < 0,1 (mesuré en conditions réalistes, pas seulement en local) |
| SITE-X-002 | Le site respecte la préférence système de réduction des animations | `prefers-reduced-motion` désactive ou réduit toute animation non essentielle |
| SITE-X-003 | Le site est utilisable entièrement au clavier | Toute action réalisable à la souris l'est aussi au clavier, focus visible en permanence |
| SITE-X-004 | Le site respecte un niveau d'accessibilité reconnu | Conforme WCAG 2.1 niveau AA sur les parcours principaux |
| SITE-X-005 | Le site est utilisable sans JavaScript pour le contenu essentiel (landing, actualités, contact) | Le contenu textuel principal reste lisible si le JavaScript échoue à charger |
| SITE-X-006 | Le site est responsive de la taille mobile à la taille bureau | Aucune rupture de mise en page entre 320 px et 2560 px de large |
| SITE-X-007 | Le site est en thème clair exclusivement (amendé par SITE-002 v1.1.0, décision Fondateur) | Aucune bascule sombre proposée ; contraste AA vérifié sur fond clair (`SITE-X-004`) |
| SITE-X-008 | Le site est référencé correctement par les moteurs de recherche | Métadonnées, `sitemap.xml`, balises Open Graph présentes et correctes sur chaque zone publique |
| SITE-X-009 | Une indisponibilité de l'API GSIE ne bloque pas la consultation du contenu statique | Landing, actualités et galerie restent consultables même si l'API est indisponible (seuls les indicateurs live et le compte sont affectés) |

## 5. Exigences de sécurité

| ID | Exigence | Critère d'acceptation |
|---|---|---|
| SITE-S-001 | Le site applique une politique de sécurité de contenu stricte (CSP) | Aucun script tiers non déclaré ne peut s'exécuter |
| SITE-S-002 | Tout formulaire public est protégé contre les soumissions automatisées | Turnstile ou équivalent sur chaque formulaire (contact au minimum) |
| SITE-S-003 | Tout endpoint public consommé par le site est en lecture seule et ne renvoie aucune donnée sensible | Aucune donnée personnelle, secret ou détail d'infrastructure interne dans les réponses consommées par la landing page |
| SITE-S-004 | Les sessions de compte suivent les mêmes règles que `IDENTITE-001` | Aucune règle de session parallèle ou affaiblie créée côté web |
| SITE-S-005 | Le site est servi exclusivement en HTTPS avec HSTS | Toute requête HTTP est redirigée, HSTS actif (cohérent avec le bootstrap Cloudflare existant) |

## 6. Exigences de données

| ID | Exigence |
|---|---|
| SITE-D-001 | Le contenu des actualités et de la galerie est stocké sous forme de fichiers versionnés dans le dépôt (pas de base de données de contenu tierce) |
| SITE-D-002 | Les médias volumineux (images/vidéos) sont servis depuis un stockage objet, pas committés bruts dans l'historique Git s'ils dépassent une taille raisonnable |
| SITE-D-003 | Les indicateurs publics de la landing page proviennent d'un endpoint API GSIE dédié, distinct des endpoints internes/admin |
| SITE-D-004 | Aucune donnée personnelle n'est collectée par la landing, les actualités ou la galerie — seule la zone Compte traite des données personnelles, sous le régime déjà défini par `IDENTITE-001` |

## 7. Exigences d'interface

- Une seule identité visuelle cohérente entre les cinq zones — aucune
  zone ne doit paraître être un site ou un produit différent.
- La zone Compte reprend les mêmes composants d'interface (typographie,
  couleurs, espacement) que le reste du site, même si son contrat
  fonctionnel vient de `IDENTITE-001`.
- Voir `SITE-002` pour la direction créative détaillée (palette,
  typographie, moments d'interaction).

## 8. Critères d'acceptation de la spécification

1. Les cinq zones sont couvertes par au moins une exigence
   fonctionnelle testable.
2. Aucune exigence ne décrit une technologie ou un composant précis
   (rôle de l'architecture).
3. La zone Compte ne duplique aucune exigence déjà normative dans
   `IDENTITE-001`.
4. Les risques identifiés (§9) ont chacun une exigence associée qui
   les atténue, ou sont explicitement laissés ouverts.

## 9. Risques et points ouverts

- **Galerie et vie privée** : un média drone peut capturer des
  personnes, véhicules ou propriétés identifiables. `SITE-F-021` pose
  une exigence de vérification, mais le processus de vérification
  lui-même (qui valide, avec quel outil) reste à définir avant toute
  implémentation.
- **Source des indicateurs live** (`SITE-F-006`) : aucun endpoint
  public d'agrégats non sensibles n'existe aujourd'hui dans l'API
  GSIE — sa conception est un prérequis, pas un acquis.
- **Hébergement du compte web** : `IDENTITE-001` a été conçue avec
  GeoSylva comme premier client ; exposer le même contrat sur le web
  peut révéler des hypothèses implicites (stockage de jeton en
  navigateur, CSRF) non couvertes par `IDENTITE-001` telle qu'écrite —
  à vérifier avant l'architecture technique.
- **Contenu des actualités** : la reformulation « langage clair, sans
  détail technique interne » (`SITE-F-014`) suppose un jugement humain
  à chaque publication ; aucune règle automatique ne peut garantir
  l'absence de fuite d'information interne.

## 10. Hors périmètre

- Boutique, paiement, abonnement, espace partenaire authentifié
  distinct du compte utilisateur.
- Blog long-format, CMS éditorial avec rôles de rédaction multiples.
- Multilingue au lancement (l'architecture ne doit pas l'exclure,
  mais le contenu anglais n'est pas requis en v1).
- Modération communautaire, commentaires, réactions.
- Upload public de médias par les utilisateurs.
- Application mobile dédiée au site (le site reste responsive web).
