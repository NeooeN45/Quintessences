#!/usr/bin/env node
/**
 * GSIE — Garde-fou constitutionnel.
 *
 * Hook PreToolUse : bloque toute écriture (Edit/Write/MultiEdit) sur un
 * document VERROUILLÉ (`Locked`). Un `Locked` ne se modifie QUE par un RFC.
 * Voir CLAUDE.md §2 et GSIE-CON-000 (Primauté de la Constitution).
 *
 * Détection :
 *   1. Liste explicite des fondateurs verrouillés (fiable).
 *   2. En-tête auto-déclaré : une des 15 premières lignes contient
 *      « statut … Locked » ou « status: Locked ».
 *
 * Blocage : sortie stderr + exit code 2 (Claude reçoit le refus).
 */
import { readFileSync } from 'node:fs';
import { basename } from 'node:path';

const LOCKED_BASENAMES = new Set([
  'GSIE-FND-001.md',
  'GSIE-FND-002.md',
  'GSIE-CON-000.md',
]);

function readStdin() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function isSelfDeclaredLocked(filePath) {
  try {
    const head = readFileSync(filePath, 'utf8').split(/\r?\n/, 15).join('\n');
    return /(statut|status)\b[^\n]{0,40}\blocked\b/i.test(head);
  } catch {
    return false; // fichier inexistant (création) => pas verrouillé
  }
}

const raw = readStdin();
let payload = {};
try { payload = JSON.parse(raw || '{}'); } catch { process.exit(0); }

const tool = payload.tool_name || '';
if (!/^(Edit|Write|MultiEdit|NotebookEdit)$/.test(tool)) process.exit(0);

const input = payload.tool_input || {};
const filePath = input.file_path || input.notebook_path || '';
if (!filePath) process.exit(0);

const locked = LOCKED_BASENAMES.has(basename(filePath)) || isSelfDeclaredLocked(filePath);

if (locked) {
  process.stderr.write(
    `⛔ GSIE — Document VERROUILLÉ (Locked) : ${basename(filePath)}\n` +
    `Un document Locked ne se modifie QUE via un RFC (02_RFC/).\n` +
    `Réf. CLAUDE.md §2 + GSIE-CON-000. Crée un RFC ou demande le déverrouillage.\n`
  );
  process.exit(2); // bloque l'outil
}
process.exit(0);
