#!/bin/sh
# install_hooks.sh — installe les hooks de sécurité Quintessences.
#
# Usage :
#   sh tools/install_hooks.sh             # repo parent uniquement
#   sh tools/install_hooks.sh --all       # parent + repos externes connus
#   sh tools/install_hooks.sh <repo>      # un repo externe précis
#
# Les sources des hooks sont versionnées dans tools/hooks/. Les repos
# externes reçoivent des variantes qui délèguent au diagnostic partagé
# du parent via un chemin relatif (repli grep minimal si absent).

set -u

ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$ROOT" ]; then
  echo "Erreur : pas dans un dépôt git." >&2
  exit 1
fi

install_parent() {
  for h in pre-commit post-commit pre-push; do
    cp "$ROOT/tools/hooks/$h" "$ROOT/.git/hooks/$h"
    chmod +x "$ROOT/.git/hooks/$h" 2>/dev/null || true
    echo "✔ $ROOT/.git/hooks/$h installé"
  done
}

install_external() {
  REPO="$1"
  if [ ! -d "$REPO/.git" ]; then
    echo "✘ $REPO : pas de .git — ignoré" >&2
    return 1
  fi
  REL=$(python -c "import os.path,sys; print(os.path.relpath(sys.argv[1],sys.argv[2]).replace('\\\\','/'))" \
        "$ROOT/tools/security_diag.py" "$REPO")
  for h in pre-commit post-commit pre-push; do
    sed "s|__DIAG_RELPATH__|$REL|g" "$ROOT/tools/hooks/$h-external" \
      > "$REPO/.git/hooks/$h"
    chmod +x "$REPO/.git/hooks/$h" 2>/dev/null || true
  done
  # Les rapports du diag atterrissent dans <repo>/output/ — ignorer.
  if [ -f "$REPO/.gitignore" ] && ! grep -qx 'output/' "$REPO/.gitignore"; then
    printf '\n# Rapports security_diag (hooks Quintessences)\noutput/\n' \
      >> "$REPO/.gitignore"
    echo "  → output/ ajouté au .gitignore de $REPO"
  elif [ ! -f "$REPO/.gitignore" ]; then
    printf '# Rapports security_diag (hooks Quintessences)\noutput/\n' \
      > "$REPO/.gitignore"
    echo "  → .gitignore créé dans $REPO (output/)"
  fi
  echo "✔ hooks installés dans $REPO (diag: $REL)"
}

install_parent

case "${1:-}" in
  --all)
    install_external "$ROOT/apps/GeoSylva" || true
    install_external "$ROOT/apps/QGISIA" || true
    install_external "$ROOT/Forge" || true
    ;;
  "") ;;
  *) install_external "$1" ;;
esac
