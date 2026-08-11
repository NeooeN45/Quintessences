# todo-001 — Lancer premier cycle loop Sécurité+Perf

- **Type** : todo
- **Date** : 2026-08-08
- **Salience** : 0.9
- **Importance** : 0.9
- **Échéance** : Premier lancement de l'orchestrateur

## Tâche

Lancer le premier cycle de la loop Sécurité+Perf :
1. Audit OWASP Top 10 sur l'API GSIE
2. Enregistrer les findings dans `loop_securite_perf.md`
3. Escalader les vulnérabilités critiques
4. Mettre à jour le trust score

## Contexte

L'API GSIE a 10 clients d'API externes, auth JWT, rate limiting.
Le fichier `_test_ssrf_mutation.py` suggère qu'un test SSRF est en cours.
Vérifier la couverture sécurité.
