---
name: kotlin-android
description: Conventions Kotlin + Jetpack Compose pour GeoSylva Android (NeooeN45/GeoSylva)
triggers:
  - user
  - model
---

# GeoSylva — Kotlin Android

## Repo

GitHub: NeooeN45/GeoSylva
Local: `apps/GeoSylva/` (repo git indépendant — ne pas committer dans le repo parent)

```bash
# Pour travailler sur GeoSylva
cd apps/GeoSylva/
git status  # repo indépendant
```

## Architecture (Clean Architecture + MVVM)

```
GeoSylva/
├── domain/
│   ├── model/          ← ForestPlot, Measurement, Species (data classes pures)
│   ├── repository/     ← interfaces (ForestPlotRepository)
│   └── usecase/        ← cas d'utilisation (GetForestPlotsUseCase)
├── data/
│   ├── remote/         ← Retrofit + API GSIE
│   ├── local/          ← Room Database
│   └── repository/     ← implémentations des repositories
└── presentation/
    ├── viewmodel/      ← StateFlow, pas de LiveData
    └── ui/             ← Composables Jetpack Compose
```

## Règles Kotlin absolues

```kotlin
// JAMAIS de !! (non-null assertion)
val name = plot?.name ?: return         // ✓
val name = plot!!.name                   // ✗

// Pas de Any non typé en signature publique
fun processPlot(plot: ForestPlot): Result<ForestAnalysis>  // ✓
fun process(data: Any): Any                                 // ✗

// StateFlow pour l'état UI
private val _plots = MutableStateFlow<List<ForestPlot>>(emptyList())
val plots: StateFlow<List<ForestPlot>> = _plots.asStateFlow()

// Coroutines : toujours dans viewModelScope ou lifecycleScope
viewModelScope.launch {
    repository.getPlots().collect { _plots.value = it }
}
```

## Composables

```kotlin
// Un composable = une responsabilité
@Composable
fun ForestPlotCard(plot: ForestPlot, onClick: () -> Unit) {
    // max 30 lignes, extraire si plus complexe
}

// Nommage : PascalCase, suffixe Screen/Card/Dialog/Button
ForestMapScreen, PlotSummaryCard, AddPlotDialog
```

## Intégration GSIE API

- Client : Retrofit + Kotlin Serialization (pas Gson)
- Timeout : 30s connect, 60s read pour les requêtes géospatiales
- Gestion erreurs : `Result<T>` ou `sealed class ApiResult`
- Cache : Room pour offline first

## Tests

```kotlin
// Nommage : should_[expected]_when_[condition]
@Test
fun should_return_plots_when_network_available() { ... }

// Utiliser Turbine pour les Flow
testForestPlotViewModel.plots.test {
    val item = awaitItem()
    assertThat(item).isNotEmpty()
}
```
