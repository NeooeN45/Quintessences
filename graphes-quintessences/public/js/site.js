// Interactions du site des graphes Quintessences / GSIE.
// Vanilla JS, aucune dépendance. Doit rester lisible et sans framework :
// le site est généré par generate_site.py et reste un fichier statique.

(function () {
  "use strict";

  var STOCKAGE_THEME = "graphes-quintessences-theme";
  var ECHELLE_MIN = 0.3;
  var ECHELLE_MAX = 3;
  var ECHELLE_PAS = 0.15;

  var filtreCategorieCourant = "tout";

  function themeCourant() {
    return localStorage.getItem(STOCKAGE_THEME) || "clair";
  }

  function appliquerThemeInitial() {
    var theme = themeCourant();
    document.documentElement.setAttribute("data-theme", theme);
    return theme;
  }

  function initialiserMermaid(theme) {
    var themeMermaid = theme === "sombre" ? "dark" : "base";
    mermaid.initialize({
      startOnLoad: false,
      theme: themeMermaid,
      securityLevel: "antiscript",
      fontFamily: "Space Grotesk, sans-serif",
    });
    mermaid.run({ querySelector: ".mermaid" });
  }

  function initialiserBasculeTheme() {
    var bouton = document.getElementById("bascule-theme");
    if (!bouton) return;

    var mettreAJourLibelle = function (theme) {
      bouton.textContent = theme === "sombre" ? "Thème clair" : "Thème sombre";
    };
    mettreAJourLibelle(themeCourant());

    bouton.addEventListener("click", function () {
      var nouveauTheme = themeCourant() === "sombre" ? "clair" : "sombre";
      localStorage.setItem(STOCKAGE_THEME, nouveauTheme);
      // Recharger est le choix le plus robuste : Mermaid a déjà remplacé les
      // <pre> par du SVG rendu avec l'ancien thème ; ré-initialiser proprement
      // évite les incohérences de rendu entre les diagrammes déjà transformés
      // et ceux qui ne le sont pas encore.
      window.location.reload();
    });
  }

  function appliquerFiltres() {
    var champ = document.getElementById("recherche");
    var requete = champ ? champ.value.trim().toLowerCase() : "";
    var visibles = 0;

    document.querySelectorAll(".carte").forEach(function (carte) {
      var titre = carte.getAttribute("data-titre") || "";
      var categorie = carte.getAttribute("data-categorie") || "";
      var correspondTexte = titre.indexOf(requete) !== -1;
      var correspondCategorie =
        filtreCategorieCourant === "tout" || categorie === filtreCategorieCourant;
      var visible = correspondTexte && correspondCategorie;
      carte.hidden = !visible;
      if (visible) visibles += 1;
    });

    document.querySelectorAll(".nav-groupe").forEach(function (groupe) {
      var groupeCategorie = groupe.getAttribute("data-groupe") || "";
      var groupeCorrespond =
        filtreCategorieCourant === "tout" || groupeCategorie === filtreCategorieCourant;
      var liens = groupe.querySelectorAll("li");
      var visiblesGroupe = 0;
      liens.forEach(function (li) {
        var a = li.querySelector("a");
        var titre = a ? a.getAttribute("data-titre") || "" : "";
        var visible = groupeCorrespond && titre.indexOf(requete) !== -1;
        li.hidden = !visible;
        if (visible) visiblesGroupe += 1;
      });
      groupe.classList.toggle("masque", visiblesGroupe === 0);
    });

    var aucunResultat = document.getElementById("aucun-resultat");
    if (aucunResultat) {
      aucunResultat.hidden = visibles !== 0;
    }
  }

  function initialiserRecherche() {
    var champ = document.getElementById("recherche");
    if (!champ) return;
    champ.addEventListener("input", appliquerFiltres);
  }

  function initialiserFiltresCategorie() {
    var puces = document.querySelectorAll("[data-filtre-categorie]");
    puces.forEach(function (puce) {
      puce.addEventListener("click", function () {
        filtreCategorieCourant = puce.getAttribute("data-filtre-categorie") || "tout";
        puces.forEach(function (p) {
          p.classList.toggle("actif", p === puce);
        });
        appliquerFiltres();
      });
    });
  }

  function initialiserNavigationActive() {
    var liens = {};
    document.querySelectorAll("[data-nav-id]").forEach(function (lien) {
      liens[lien.getAttribute("data-nav-id")] = lien;
    });

    var cartes = document.querySelectorAll(".carte");
    if (!cartes.length || !("IntersectionObserver" in window)) return;

    var observateur = new IntersectionObserver(
      function (entrees) {
        entrees.forEach(function (entree) {
          var lien = liens[entree.target.id];
          if (!lien) return;
          if (entree.isIntersecting) {
            Object.values(liens).forEach(function (l) {
              l.classList.remove("actif");
            });
            lien.classList.add("actif");
          }
        });
      },
      { rootMargin: "-15% 0px -70% 0px", threshold: 0.01 }
    );

    cartes.forEach(function (carte) {
      observateur.observe(carte);
    });
  }

  function lireCodeSource(id) {
    var script = document.querySelector('[data-code-source="' + id + '"]');
    if (!script) return null;
    try {
      return JSON.parse(script.textContent);
    } catch (erreur) {
      return null;
    }
  }

  function initialiserCopieCode() {
    document.querySelectorAll('[data-action="copier"]').forEach(function (bouton) {
      bouton.addEventListener("click", function () {
        var code = lireCodeSource(bouton.getAttribute("data-cible"));
        if (code === null) return;

        var succes = function () {
          var libelleInitial = bouton.textContent;
          bouton.textContent = "Copié !";
          bouton.classList.add("copie");
          setTimeout(function () {
            bouton.textContent = libelleInitial;
            bouton.classList.remove("copie");
          }, 1500);
        };

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(code).then(succes).catch(function () {
            copierAvecFallback(code, succes);
          });
        } else {
          copierAvecFallback(code, succes);
        }
      });
    });
  }

  function copierAvecFallback(texte, succes) {
    var zone = document.createElement("textarea");
    zone.value = texte;
    zone.setAttribute("readonly", "");
    zone.style.position = "fixed";
    zone.style.opacity = "0";
    document.body.appendChild(zone);
    zone.select();
    try {
      document.execCommand("copy");
      succes();
    } catch (erreur) {
      // Copie impossible dans ce navigateur — abandon silencieux.
    }
    document.body.removeChild(zone);
  }

  function initialiserBasculeCode() {
    document.querySelectorAll('[data-action="basculer-code"]').forEach(function (bouton) {
      bouton.addEventListener("click", function () {
        var id = bouton.getAttribute("data-cible");
        var bloc = document.querySelector('[data-code-affiche="' + id + '"]');
        if (!bloc) return;
        var maintenantVisible = bloc.hidden;
        bloc.hidden = !maintenantVisible;
        bouton.textContent = maintenantVisible ? "Masquer le code" : "Voir le code";
      });
    });
  }

  function initialiserTelechargementSvg() {
    document.querySelectorAll('[data-action="telecharger-svg"]').forEach(function (bouton) {
      bouton.addEventListener("click", function () {
        var id = bouton.getAttribute("data-cible");
        var svg = document.querySelector('[data-diagram-id="' + id + '"] svg');
        if (!svg) return;

        var clone = svg.cloneNode(true);
        clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        var source = new XMLSerializer().serializeToString(clone);
        var blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
        var url = URL.createObjectURL(blob);

        var lien = document.createElement("a");
        lien.href = url;
        lien.download = id + ".svg";
        document.body.appendChild(lien);
        lien.click();
        document.body.removeChild(lien);
        URL.revokeObjectURL(url);
      });
    });
  }

  function initialiserPleinEcran() {
    var modale = document.getElementById("modale-plein-ecran");
    var corps = document.getElementById("modale-corps");
    var titre = document.getElementById("modale-titre");
    var boutonFermer = document.getElementById("modale-fermer");
    if (!modale || !corps || !boutonFermer) return;

    function fermer() {
      modale.hidden = true;
      corps.innerHTML = "";
    }

    document.querySelectorAll('[data-action="plein-ecran"]').forEach(function (bouton) {
      bouton.addEventListener("click", function () {
        var id = bouton.getAttribute("data-cible");
        var svg = document.querySelector('[data-diagram-id="' + id + '"] svg');
        if (!svg) return;
        var carte = document.getElementById(id);
        var h2 = carte ? carte.querySelector("h2") : null;

        corps.innerHTML = "";
        corps.appendChild(svg.cloneNode(true));
        titre.textContent = h2 ? h2.textContent : "";
        modale.hidden = false;
      });
    });

    boutonFermer.addEventListener("click", fermer);
    modale.addEventListener("click", function (evenement) {
      if (evenement.target === modale) fermer();
    });
    window.addEventListener("keydown", function (evenement) {
      if (evenement.key === "Escape" && !modale.hidden) fermer();
    });
  }

  function initialiserRaccourcisClavier() {
    var champ = document.getElementById("recherche");
    window.addEventListener("keydown", function (evenement) {
      if (evenement.key !== "/" || !champ) return;
      var cible = evenement.target;
      var editable =
        cible && (cible.tagName === "INPUT" || cible.tagName === "TEXTAREA");
      if (editable) return;
      evenement.preventDefault();
      champ.focus();
    });
  }

  function initialiserZoom() {
    var echelles = {};

    function obtenirEchelle(id) {
      return echelles[id] || 1;
    }

    function definirEchelle(id, valeur) {
      var bornee = Math.min(ECHELLE_MAX, Math.max(ECHELLE_MIN, valeur));
      echelles[id] = bornee;
      var conteneur = document.querySelector('[data-scale="' + id + '"]');
      if (conteneur) {
        conteneur.style.transform = "scale(" + bornee + ")";
      }
    }

    document.querySelectorAll("[data-action]").forEach(function (bouton) {
      var action = bouton.getAttribute("data-action");
      if (action !== "zoom-in" && action !== "zoom-out" && action !== "zoom-reset") {
        return;
      }
      bouton.addEventListener("click", function () {
        var id = bouton.getAttribute("data-cible");
        if (action === "zoom-in") {
          definirEchelle(id, obtenirEchelle(id) + ECHELLE_PAS);
        } else if (action === "zoom-out") {
          definirEchelle(id, obtenirEchelle(id) - ECHELLE_PAS);
        } else {
          definirEchelle(id, 1);
        }
      });
    });

    // Zoom à la molette (Ctrl/Cmd + molette), pour éviter d'intercepter le
    // défilement normal de la page.
    document.querySelectorAll(".diagram-viewport").forEach(function (viewport) {
      var id = viewport.getAttribute("data-viewport");

      viewport.addEventListener(
        "wheel",
        function (evenement) {
          if (!evenement.ctrlKey && !evenement.metaKey) return;
          evenement.preventDefault();
          var delta = evenement.deltaY < 0 ? ECHELLE_PAS : -ECHELLE_PAS;
          definirEchelle(id, obtenirEchelle(id) + delta);
        },
        { passive: false }
      );

      // Glisser pour déplacer (pan) — souris uniquement, le tactile utilise
      // le défilement natif du conteneur `overflow: auto`.
      var enGlissement = false;
      var origineX = 0;
      var origineY = 0;
      var scrollInitialX = 0;
      var scrollInitialY = 0;

      viewport.addEventListener("mousedown", function (evenement) {
        enGlissement = true;
        origineX = evenement.clientX;
        origineY = evenement.clientY;
        scrollInitialX = viewport.scrollLeft;
        scrollInitialY = viewport.scrollTop;
        viewport.classList.add("saisi");
      });

      window.addEventListener("mousemove", function (evenement) {
        if (!enGlissement) return;
        viewport.scrollLeft = scrollInitialX - (evenement.clientX - origineX);
        viewport.scrollTop = scrollInitialY - (evenement.clientY - origineY);
      });

      window.addEventListener("mouseup", function () {
        enGlissement = false;
        viewport.classList.remove("saisi");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var theme = appliquerThemeInitial();
    initialiserMermaid(theme);
    initialiserBasculeTheme();
    initialiserRecherche();
    initialiserFiltresCategorie();
    initialiserNavigationActive();
    initialiserCopieCode();
    initialiserBasculeCode();
    initialiserTelechargementSvg();
    initialiserPleinEcran();
    initialiserRaccourcisClavier();
    initialiserZoom();
  });
})();
