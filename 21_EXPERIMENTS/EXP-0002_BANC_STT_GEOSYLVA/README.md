# EXP-0002 — Banc d'essai reconnaissance vocale GeoSylva

| Champ | Valeur |
|---|---|
| **Identifiant** | EXP-0002 |
| **Statut** | Draft — expérimentation ouverte |
| **Date d'ouverture** | 2026-08-16 |
| **Décision d'ouverture** | Fondateur, 2026-08-16 (réponse D2 de `GSIE-VEILLE-STT-VLA-2026-08-16`) |
| **Veille amont** | `GSIE/RESEARCH/VEILLE_STT_EMBARQUE_ET_VLA_DRONE_2026-08-16.md` |
| **Sortie attendue** | Un tableau de mesures. **Pas** une intégration dans GeoSylva. |

---

## 1. Question à laquelle ce banc répond

Quel modèle de reconnaissance vocale ouvert transcrit le plus fidèlement une
**dictée de martelage en français**, hors réseau, sur un smartphone d'entrée de
gamme ?

Ce banc ne dit pas s'il faut intégrer, ni quand. Il produit des chiffres.

---

## 2. Le vrai objet du problème : ce n'est pas de la transcription libre

La dictée de martelage n'est pas de la parole continue. C'est une **énonciation
courte et structurée, une par arbre**. Exemples fournis par le Fondateur :

```
chêne rouvre 50 cm hauteur 20 m
douglas 25 m diamètre 60 cm dégât d'exploitation
```

Trois observations qui déterminent toute la conception du banc :

1. **L'ordre des champs n'est pas fixe.** Le premier exemple donne
   essence → diamètre → hauteur ; le second essence → hauteur → diamètre → défaut.
   Un parseur positionnel est donc exclu d'emblée.
2. **Ce sont les unités qui portent le sens.** `50 cm` est un diamètre, `20 m`
   une hauteur — même quand le mot « diamètre » ou « hauteur » est omis, comme
   dans le premier exemple. Le parseur doit être piloté par l'unité, avec le
   mot-clé comme confirmation quand il est présent.
3. **Le vocabulaire est fermé et hors-distribution.** « chêne rouvre »,
   « douglas », « dégât d'exploitation » sont rares dans les corpus généralistes
   dont ces modèles sont issus. C'est là que la transcription cassera, pas sur
   la syntaxe.

**Conséquence sur le classement de la veille.** Le streaming perd son statut de
critère structurant : on transcrit des énoncés de deux à quatre secondes, pas un
flux. Ce qui devient décisif, c'est la capacité à **biaiser la reconnaissance
par un lexique métier**.

---

## 3. Chaîne cible évaluée

```
audio → [1] ASR biaisé par lexique → texte
      → [2] parseur déterministe piloté par unités → champs structurés
      → [3] confirmation visuelle par l'opérateur → écriture en base
```

- **[1]** est l'objet du banc.
- **[2]** est une grammaire écrite à la main, pas un modèle. Elle est
  auditable, déterministe, gratuite en calcul et ne peut pas halluciner un
  diamètre. Aucun LLM n'a sa place ici.
- **[3]** n'est pas négociable : `GSIE-CON-001` — l'IA assiste, ne décide
  jamais. Aucune donnée dendrométrique ne s'écrit sans validation humaine.
  Un chiffre mal transcrit et non confirmé corrompt un inventaire entier.

---

## 4. Candidats

| # | Modèle | Licence | Biasing lexique | Rôle |
|---|---|---|---|---|
| 1 | Qwen3-ASR-0.6B | Apache-2.0 | **Oui** — contexte libre via `prompt` (vérifié sur la fiche officielle) | Favori |
| 2 | VibeVoice-ASR-BitNet | MIT | à qualifier | Challenger — meilleur profil embarqué |
| 3 | Nemotron-3.5-ASR-streaming-0.6b | OpenMDW-1.1 | à qualifier | Challenger |
| T1 | Whisper-small + whisper.cpp | MIT | prompt initial (mécanisme connu, effet limité) | Témoin haut |
| T2 | Vosk FR | Apache-2.0 | grammaire fermée native | Témoin bas |
| T3 | `RecognizerIntent` Android | — | aucun | **Témoin existant** — c'est lui qu'il s'agit de battre |

Écartés en amont, motifs dans la veille : Audio8-ASR (CC-BY-NC),
CrisperWhisper 2.0 (poids sous licence de recherche non commerciale),
Voxtral-Mini et cohere-transcribe (gabarit serveur).

---

## 5. Corpus

**C'est le livrable le plus coûteux et le plus durable du banc.** Le corpus
survivra à tous les modèles testés.

| Paramètre | Cible |
|---|---|
| Volume | 200 énoncés minimum, 400 souhaitable |
| Locuteurs | 3 au moins, dont un non-Fondateur — le banc ne doit pas mesurer une seule voix |
| Conditions | Calme, vent, pluie, marche, distance micro variable — chaque énoncé étiqueté par sa condition |
| Essences | Couverture du référentiel GeoSylva, avec sur-représentation des noms composés (chêne rouvre, chêne pédonculé, pin sylvestre) qui sont les plus fragiles |
| Valeurs | Diamètres et hauteurs couvrant la plage réelle, avec les nombres phonétiquement ambigus en français : 2/12, 6/16, 13/30, 60/70 |
| Défauts | Vocabulaire de défauts et dégâts tel qu'employé sur le terrain |
| Référence | Transcription manuelle **et** champs structurés attendus, saisis séparément |

Chaque entrée porte : audio, transcription de référence, champs attendus,
locuteur, condition, terminal d'enregistrement.

---

## 6. Métriques

| Métrique | Définition | Statut |
|---|---|---|
| **Taux d'énoncés exacts** | Part des énoncés dont **tous** les champs sortent justes après parsing | **Décisionnelle** |
| **Erreur sur les nombres** | Taux d'erreur sur les seules valeurs numériques | **Décisionnelle** — une hauteur fausse est pire qu'un mot faux |
| Erreur sur les essences | Taux d'erreur sur le nom d'essence | Décisionnelle |
| WER global | Taux d'erreur mot classique | Indicative — comparabilité externe uniquement |
| Latence | Fin de parole → champs affichés | Contrainte |
| Énergie | Consommation sur 30 min de dictée continue | Contrainte |
| Empreinte | Taille du paquet embarqué | Contrainte |

Le WER global **n'est pas** le critère de décision. Un modèle peut avoir un WER
flatteur et se tromper systématiquement sur « 60 » contre « 70 ».

---

## 7. Terminaux

Au moins deux, dont **un terminal d'entrée de gamme** — c'est lui la contrainte
réelle du terrain, pas le haut de gamme du développeur.

---

## 8. Critère de bascule

Un candidat ne remplace l'existant que s'il satisfait **les trois** conditions :

1. taux d'énoncés exacts strictement supérieur au témoin T3 (`RecognizerIntent`) ;
2. latence compatible avec un rythme de martelage soutenu ;
3. fonctionnement vérifié **en mode avion**, appareil coupé du réseau.

Un candidat qui gagne sur la qualité mais échoue en mode avion ne gagne pas :
il ne répond pas au besoin.

---

## 9. Ce que ce banc ne fait pas

- Il ne modifie aucune ligne de GeoSylva.
- Il ne tranche pas l'architecture d'intégration.
- Il ne qualifie aucun modèle pour la production : cela relèverait d'une
  décision tracée dans `03_DECISIONS/`, sur la base de ses résultats.

---

## 10. Historique

| Version | Date | Auteur | Modification |
|---|---|---|---|
| 0.1.0 | 2026-08-16 | Claude | Ouverture du banc, protocole initial |
