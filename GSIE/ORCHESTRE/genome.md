# Genome — ORCHESTRE GSIE

> Stratégie versionnée, auto-évolutive. L'orchestrateur lit ce fichier
> au démarrage de chaque cycle et le réécrit quand il apprend quelque
> chose. Inspiré du pattern azena-ai genome + NOOA ReflectionEngine.

---

## Mission

Orchestrer les loops spécialisées pour faire avancer GSIE Phase 4
sans intervention humaine, sauf pour les décisions critiques.
L'orchestrateur remplace le Fondateur pour la gestion opérationnelle
des tâches, mais le Fondateur garde l'autorité finale sur toute
décision structurante (RFC, breaking change, sécurité).

## Stratégie courante

### Priorités (ordre d'exécution)

1. **Sécurité + Perf** — audit continu de l'API GSIE
   - OWASP Top 10, dépendances CVE, benchmarks, profiling, secrets
2. **QA** — couverture et qualité des moteurs implémentés
   - Couverture 100%, mutation, revue de code, dette technique
3. **Veille** — surveillance technologique
   - NVIDIA, publications scientifiques, outils forestiers/géospatiaux

### Règles d'activation

- Une loop tourne en background (sub-agent SWE 1.7 max)
- Maximum 3 loops simultanées (limite de parallélisme)
- Une loop se met en pause si elle touche une escalade critique
- L'orchestrateur surveille les loops et synthétise les résultats

### Gating hérité

Le gating adaptatif du consortium existant s'applique toujours :
- LÉGER (< 5 fichiers, pas de risque) → 1 agent, micro-boucle
- STANDARD (5-15 fichiers) → 1 implémenteur + 1 reviewer
- LOURD (> 15 fichiers, breaking, sécurité) → 4 agents, 9 phases

L'orchestrateur utilise ce gating pour décider du niveau de cérémonie
de chaque tâche produite par une loop.

## Levers d'amélioration (backlog)

> Liste priorisée d'améliorations que l'orchestrateur peut activer
> quand il détecte un pattern récurrent ou une opportunité.

1. [ ] Ajouter loop Implémentation moteurs (14 moteurs GSIE en parallèle)
2. [ ] Paralleliser audit OWASP + dépendances dans la loop sécu
3. [ ] Auto-résolution des conflits mineurs sans consensus
4. [ ] Ajouter loop Documentation (mise à jour automatique docs)
5. [ ] Ajouter loop Refactoring (dette technique détectée par QA)
6. [ ] Benchmark automatique après chaque commit de moteur
7. [ ] Détection de régression de performance en continu

## Leçons apprises

> Règles auto-apprises, numérotées. L'orchestrateur les ajoute
> après chaque cycle où il a appris quelque chose.

<!-- Les leçons sont ajoutées automatiquement par l'orchestrateur -->
<!-- Format: - [lesson-NNN] description courte -->

- [lesson-001] Toujours exécuter ruff format avant de committer
- [lesson-002] mypy strict sur tout nouveau code — pas de Any
- [lesson-003] Ne pas committer dans les repos externes (GeoSylva, QGISIA, Forge)
- [lesson-004] Les tests de mutation doivent couvrir chaque nouvelle garde
- [lesson-005] numpy.corrcoef est 326x-1521x plus rapide que scipy pairwise

## Évolution du genome

> L'orchestrateur réécrit cette section après chaque évolution.

- **Version** : 0.9.0
- **Date création** : 2026-08-08
- **Dernière évolution** : 2026-08-09 (upgrade FastAPI/Starlette validé)
- **Cycles total** : 7
- **Évolutions total** : 8
- **Prochaine révision** : après revalidation pip-audit et traitement des warnings

## Métriques de santé

> L'orchestrateur met à jour ces métriques après chaque cycle.

| Métrique | Valeur | Tendance |
|---|---|---|
| Cycles complétés | 7 | +1 |
| Tâches réussies | 7 | +1 |
| Tâches échouées | 0 | — |
| Escalades générées | 2 | — |
| Escalades résolues | 2 | +1 |
| Consensus atteints | 0 | — |
| Consensus échoués | 0 | — |
| Leçons apprises | 5 | — |
| Couverture moyenne | 100 % | — |
| Vulnérabilités ouvertes | Audit en ligne bloqué TLS ; warnings à traiter | stable |
