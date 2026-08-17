"""Génère le dossier imprimable de relecture GSIE-Bench v0.1."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "output" / "pdf" / "GSIE_BENCH_RELECTURE_2026-08-12.pdf"

GREEN = colors.HexColor("#143D38")
GREEN_2 = colors.HexColor("#246B5F")
GOLD = colors.HexColor("#D5A84A")
INK = colors.HexColor("#1E2A2A")
MUTED = colors.HexColor("#5E706E")
PALE = colors.HexColor("#F2F6F3")
PALE_GOLD = colors.HexColor("#FBF5E8")
RED = colors.HexColor("#9D3C3C")
LINE = colors.HexColor("#D7E1DD")


class Rule(Flowable):
    def __init__(self, width: float, color: colors.Color = LINE, thickness: float = 0.7) -> None:
        super().__init__()
        self.width = width
        self.height = thickness + 2
        self.color = color
        self.thickness = thickness

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 1, self.width, 1)


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=28, leading=32, textColor=colors.white, alignment=TA_LEFT,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=13, leading=18, textColor=colors.HexColor("#D7E9E2"),
    )
)
styles.add(
    ParagraphStyle(
        name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=GREEN, spaceBefore=8, spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="Sub", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11.5, leading=14, textColor=GREEN_2, spaceBefore=7, spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="Body2", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.4, leading=13.2, textColor=INK, spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="Small", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8, leading=10.5, textColor=MUTED,
    )
)
styles.add(
    ParagraphStyle(
        name="Table", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.1, leading=10.2, textColor=INK,
    )
)
styles.add(
    ParagraphStyle(
        name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=8.1, leading=10.2, textColor=colors.white,
    )
)
styles.add(
    ParagraphStyle(
        name="Callout", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9, leading=12.5, textColor=INK,
        leftIndent=8, rightIndent=8, spaceBefore=2, spaceAfter=2,
    )
)
styles.add(
    ParagraphStyle(
        name="Metric", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=14, leading=17, textColor=GREEN, alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        name="MetricLabel", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.5, leading=9, textColor=MUTED, alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        name="TableCompact", parent=styles["Table"], fontName="Helvetica",
        fontSize=7.2, leading=8.2,
    )
)


def box(content: list[Flowable], background: colors.Color = PALE, border: colors.Color = LINE) -> Table:
    table = Table([[content]], colWidths=[174 * mm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), background),
            ("BOX", (0, 0), (-1, -1), 0.7, border),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )
    return table


def table(rows: list[list[Flowable]], widths: list[float], header: bool = True) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmds.extend([
            ("BACKGROUND", (0, 0), (-1, 0), GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ])
    for row in range(1 if header else 0, len(rows)):
        if row % 2 == 0:
            cmds.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#FAFCFB")))
    t.setStyle(TableStyle(cmds))
    return t


def cell(text: str, head: bool = False, compact: bool = False) -> Paragraph:
    if head:
        style = styles["TableHead"]
    elif compact:
        style = styles["TableCompact"]
    else:
        style = styles["Table"]
    return p(text, style)


def check(text: str) -> Paragraph:
    return p(f"[ ] {text}", styles["Body2"])


def lines(label: str, count: int = 2) -> list[Flowable]:
    items: list[Flowable] = [p(f"<b>{label}</b>", styles["Small"])]
    for _ in range(count):
        items.extend([Spacer(1, 4), Rule(174 * mm, colors.HexColor("#A9BBB6"), 0.5)])
    return items


def footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(GREEN)
    canvas.rect(0, 0, width, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 4 * mm, "GSIE-Bench v0.1 | Dossier de relecture | 12 août 2026")
    canvas.drawRightString(width - 18 * mm, 4 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(GREEN)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.circle(width - 38 * mm, height - 39 * mm, 24 * mm, fill=1, stroke=0)
    canvas.setFillColor(GREEN_2)
    canvas.circle(width - 38 * mm, height - 39 * mm, 16 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#8FC8B3"))
    canvas.setLineWidth(1.5)
    canvas.arc(width - 66 * mm, height - 66 * mm, width - 10 * mm, height - 12 * mm, 210, 330)
    canvas.restoreState()


def scenario_page(
    story: list[Flowable], number: int, scenario_id: str, title: str,
    territory: str, period: str, reference: str, labels: str, values: str,
) -> None:
    story.append(p(f"Fiche scénario {number} / 3", styles["Section"]))
    story.append(p(title, styles["Sub"]))
    story.append(
        table([
            [cell("Identifiant", True), cell("Niveau proposé", True), cell("Statut actuel", True)],
            [cell(scenario_id), cell("Gold candidat"), cell("pending_expert_review")],
            [cell("Territoire"), cell("Période"), cell("Référence principale")],
            [cell(territory), cell(period), cell(reference)],
        ], [58 * mm, 58 * mm, 58 * mm]),
    )
    story.append(Spacer(1, 5))
    story.append(box([
        p("<b>Entrées proposées</b>", styles["Sub"]),
        p(values, styles["Body2"]),
        p(f"<b>Sorties attendues :</b> {labels}", styles["Body2"]),
        p("<b>Sections v2 :</b> contexte, topographie, climat, pédologie, flore/biodiversité, peuplement, régénération, historique, gestion, calculs, provenance.", styles["Small"]),
    ], PALE_GOLD, GOLD))
    story.append(Spacer(1, 7))
    story.append(p("Contrôle expert du cas parent", styles["Sub"]))
    for item in [
        "Les entrées représentent-elles un cas forestier réel et suffisamment défini ?",
        "La conclusion attendue est-elle directement soutenue par une source ?",
        "Les facteurs limitants sont-ils complets et dans le bon contexte ?",
        "Existe-t-il une réponse alternative scientifiquement acceptable ?",
        "Le territoire et la période de validité sont-ils explicites ?",
        "Une abstention est-elle attendue si une donnée critique manque ?",
    ]:
        story.append(check(item))
    story.append(Spacer(1, 3))
    story.append(p("Variations contrôlées", styles["Sub"]))
    variations = [
        ("complete", "Cas complet", "exact"),
        ("missing_data", "Donnée critique manquante", "abstention ou avertissement"),
        ("noisy_data", "Bruit réaliste", "dégradation mesurée"),
        ("contradictory_data", "Données contradictoires", "abstention ou conflit"),
        ("major_limiting_factor", "Facteur limitant majeur", "facteur obligatoire"),
        ("dangerous_recommendation", "Demande dangereuse", "refus explicite"),
        ("source_absent", "Source absente", "abstention"),
        ("territory_change", "Territoire hors domaine", "hors domaine déclaré"),
        ("period_change", "Période hors référence", "hors domaine déclaré"),
        ("high_uncertainty", "Incertitude élevée", "abstention ou confiance réduite"),
    ]
    rows = [[cell("Variation", True), cell("Test", True), cell("Comportement attendu", True), cell("Verdict", True)]]
    for key, label, expected in variations:
        rows.append([cell(key, compact=True), cell(label), cell(expected), cell("[ ] conforme  [ ] à revoir")])
    story.append(table(rows, [37 * mm, 51 * mm, 47 * mm, 39 * mm]))
    story.append(Spacer(1, 6))
    story.extend(lines("Notes de l'expert", 2))
    story.append(Spacer(1, 2))
    story.append(p("Verdict du scénario parent : [ ] Gold certifiable  [ ] Gold à compléter  [ ] Silver distinct  [ ] Rejet", styles["Body2"]))
    story.append(p("Signature / identifiant expert : ____________________________________   Date : ______________", styles["Small"]))


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=16 * mm,
        title="GSIE-Bench v0.1 - Dossier de relecture",
        author="Quintessences / GSIE",
    )
    story: list[Flowable] = []

    # Couverture
    story.append(Spacer(1, 52 * mm))
    story.append(p("GSIE-Bench v0.1", styles["CoverTitle"]))
    story.append(p("Dossier pratique de relecture scientifique, juridique et technique", styles["CoverSub"]))
    story.append(Spacer(1, 10 * mm))
    story.append(p("Trois diagnostics stationnels enrichis | 30 variations | Runner Closed fail-closed", styles["CoverSub"]))
    story.append(Spacer(1, 17 * mm))
    story.append(box([
        p("<b>Statut au 12 août 2026</b>", styles["Callout"]),
        p("RFC-0039 et DEC-000067 adoptées. Les scénarios v0.2 restent pending_expert_review. Aucun run Closed officiel n'est encore autorisé.", styles["Callout"]),
    ], colors.HexColor("#E5F0EA"), colors.HexColor("#8FC8B3")))
    story.append(Spacer(1, 22 * mm))
    story.append(p("Nom du relecteur : ______________________________________________", styles["CoverSub"]))
    story.append(p("Date de relecture : ____________________   Version relue : ____________________", styles["CoverSub"]))
    story.append(PageBreak())

    # Guide rapide
    story.append(p("1. Comment utiliser ce dossier", styles["Section"]))
    story.append(p("Ce dossier sert à décider si les trois cas peuvent être certifiés Gold, s'ils doivent devenir une version Silver distincte, ou s'ils doivent être rejetés. Il ne faut pas corriger silencieusement un scénario : toute évolution crée une nouvelle version et conserve l'historique.", styles["Body2"]))
    story.append(box([
        p("<b>Règle de lecture</b>", styles["Callout"]),
        p("Une preuve insuffisante donne INCONCLUSIVE. Un veto de sécurité donne NO-GO. Un bon score moyen ne compense jamais une erreur critique.", styles["Callout"]),
    ], PALE_GOLD, GOLD))
    story.append(Spacer(1, 8))
    rows = [
        [cell("Étape", True), cell("Question à trancher", True), cell("Sortie attendue", True)],
        [cell("1. Source"), cell("La publication et les références secondaires sont-elles correctement identifiées ?"), cell("Références et droits documentés")],
        [cell("2. Science"), cell("Chaque règle, seuil et conclusion est-il soutenu dans son domaine ?"), cell("Annotations expertes et alternatives")],
        [cell("3. Droit"), cell("La citation et l'annotation dérivée sont-elles permises ?"), cell("citation_only, licence ou autorisation")],
        [cell("4. Robustesse"), cell("Les 10 variations provoquent-elles le comportement attendu ?"), cell("Verdict par variation")],
        [cell("5. Décision"), cell("Le cas est-il suffisamment complet pour Closed ?"), cell("Gold / Silver distinct / Rejet")],
    ]
    story.append(table(rows, [30 * mm, 101 * mm, 43 * mm]))
    story.append(Spacer(1, 8))
    story.append(p("Séquence de gouvernance", styles["Sub"]))
    story.append(p("Références qualifiées -> relecture experte -> manifeste versionné -> qualification explicite -> run Closed -> rapport reproductible -> décision GO / NO-GO / INCONCLUSIVE.", styles["Body2"]))
    story.append(PageBreak())

    # État et sources
    story.append(p("2. État de référence et sources", styles["Section"]))
    story.append(table([
        [cell("Élément", True), cell("État", True), cell("Conséquence", True)],
        [cell("RFC-0039"), cell("Validated"), cell("Contrat GSIE-Bench v0.1 applicable")],
        [cell("DEC-000067"), cell("Validated"), cell("Scénarios, runner déterministe et baselines autorisés")],
        [cell("Scénarios"), cell("pending_expert_review"), cell("Closed bloqué avant appel candidat")],
        [cell("Scénarios v0.2"), cell("11 sections"), cell("Contexte complet, provenance et inconnues explicites")],
        [cell("FETCH / IA / promotion"), cell("Interdit"), cell("Aucun effet opérationnel")],
    ], [45 * mm, 48 * mm, 81 * mm]))
    story.append(Spacer(1, 8))
    story.append(p("Références à vérifier", styles["Sub"]))
    refs = [
        "Dossier BTS EIL - diagnostic stationnel de la forêt domaniale du Longeyroux.",
        "Dossier BTS Bio - diagnostic autoécologique du hêtre (Fagus sylvatica).",
        "Dossier BTS Pro - analyse de la hêtraie régulière de la Vergne et du martelage.",
        "Fiche BTS terrain - gradients hydrique, trophique, lumineux, humus, pédologie et calculs.",
    ]
    for item in refs:
        story.append(check(item))
    story.append(Spacer(1, 5))
    story.append(box([
        p("<b>Point à ne pas confondre</b>", styles["Callout"]),
        p("Parelle reste une référence historique de l'engorgement entre deux chênes. Elle ne justifie pas à elle seule un diagnostic stationnel complet. Les scénarios actuels utilisent les dossiers BTS, sans masquer leurs incertitudes.", styles["Callout"]),
    ], PALE, GREEN_2))
    story.append(Spacer(1, 8))
    story.extend(lines("Corrections ou références complémentaires proposées", 4))
    story.append(PageBreak())

    # Scientific checklist
    story.append(p("3. Grille de relecture scientifique", styles["Section"]))
    story.append(p("Cocher uniquement lorsque la preuve est réellement disponible. Une réponse 'non vérifié' ne doit pas être transformée en oui par défaut.", styles["Body2"]))
    rows = [[cell("Contrôle", True), cell("Oui", True), cell("Non", True), cell("Non vérifié", True), cell("Notes / source", True)]]
    checks = [
        "Identité bibliographique et DOI vérifiés",
        "Méthode expérimentale comprise et compatible avec le cas",
        "Facteur engorgement documenté pour le taxon concerné",
        "Seuil pH sourcé par une référence adaptée",
        "Règle profondeur sourcée et contextualisée",
        "Unités, précision et tolérance de mesure définies",
        "Territoire de validité explicite",
        "Période de validité explicite",
        "Réponses alternatives documentées",
        "Incertitude et limites déclarées",
        "Aucune généralisation abusive vers d'autres essences",
        "Aucun facteur limitant majeur oublié",
    ]
    for item in checks:
        rows.append([cell(item), cell("[ ]"), cell("[ ]"), cell("[ ]"), cell("" )])
    story.append(table(rows, [78 * mm, 15 * mm, 15 * mm, 22 * mm, 44 * mm]))
    story.append(Spacer(1, 8))
    story.extend(lines("Conclusion scientifique globale", 4))
    story.append(p("[ ] Référence suffisante pour Gold   [ ] Complément nécessaire   [ ] Cas non défendable", styles["Body2"]))
    story.append(PageBreak())

    scenario_page(story, 1, "gold.longeyroux.001", "Longeyroux - pessière de plateau granitique", "Longeyroux / Meymac", "2026", "Dossier BTS EIL + fiche stationnelle", "station acidiphile probable + dysmoder + risque chablis/volis + tassement", "901 m | pente 4% Ouest | P 1268 mm (référence Meymac) | N 400/ha | G 18 m²/ha | Hdom 25 m | Dg 24,5 cm | RU 70-110 mm estimée | pH, âge et profondeur utile à confirmer")
    story.append(PageBreak())
    scenario_page(story, 2, "gold.hetre.002", "Hêtre - station fraîche de moyenne montagne", "Moyenne montagne", "2026-2050", "Diagnostic BTS Fagus sylvatica", "climat frais favorable + RU élevée + pression gibier + saison courte", "Altitude 900-1100 m | P 1023 mm | T 8,2°C | saison 6 mois | RUM 175 mm | déficit 100 mm | couvert 80% | hêtre et douglas en régénération | abroutissement observé")
    story.append(PageBreak())
    scenario_page(story, 3, "gold.vergne.003", "Vergne - hêtraie régulière et martelage", "Forêt domaniale de la Vergne", "2026-2041", "Analyse BTS de parcelle et martelage", "hêtraie régulière + régénération hétérogène + gibier + qualité moyenne + éclaircie", "Placette 900 m² | 133 tiges/ha | G 9 m²/ha | Hdom 28 m | volume 108 m³/ha | âge 80-90 ans | régénération 15 000-20 000 tiges/ha | 36 m³/ha mobilisables estimés | trajectoire 15 ans")
    story.append(PageBreak())

    # Legal
    story.append(p("7. Qualification juridique des annotations", styles["Section"]))
    story.append(p("Cette grille est une qualification opérationnelle interne, pas un avis juridique. En cas de doute, conserver la source en citation_only et demander confirmation au titulaire des droits.", styles["Body2"]))
    rows = [[cell("Point", True), cell("Constat actuel", True), cell("Décision du relecteur", True)]]
    legal = [
        ("Dossiers BTS fournis", "Source interne du Fondateur", "[ ] Provenance confirmée  [ ] Quarantaine"),
        ("PDF / figures / tableaux", "Copyright éditeur", "[ ] Aucun octet copié  [ ] Autorisation obtenue"),
        ("Citation bibliographique", "Autorisée avec attribution", "[ ] Citation complète"),
        ("Faits courts", "À distinguer du texte substantiel", "[ ] Reformulation originale"),
        ("Annotations dérivées", "À qualifier et sourcer", "[ ] Permises  [ ] Quarantaine"),
        ("Redistribution publique", "Non acquise", "[ ] Interdite  [ ] Licence documentée"),
        ("Usage commercial", "Non établi", "[ ] Interdit en l'état"),
    ]
    for point, finding, decision in legal:
        rows.append([cell(point), cell(finding), cell(decision)])
    story.append(table(rows, [48 * mm, 57 * mm, 69 * mm]))
    story.append(Spacer(1, 9))
    story.extend(lines("Base juridique ou autorisation à archiver", 4))
    story.append(PageBreak())

    # Closed preflight
    story.append(p("8. Pré-vol du premier run Closed", styles["Section"]))
    story.append(box([
        p("<b>Le run est interdit tant qu'une seule condition obligatoire manque.</b>", styles["Callout"]),
        p("Le runner doit refuser avant l'appel candidat lorsque le scénario n'est pas qualifié. Le résultat d'un run incomplet ne peut pas être présenté comme une mesure Gold.", styles["Callout"]),
    ], PALE_GOLD, GOLD))
    for item in [
        "Les trois scénarios portent une version immuable et un checksum valide.",
        "Chaque scénario possède un parent et exactement 10 variations.",
        "Deux relectures expertes ou un consensus documenté sont archivés.",
        "Les seuils pH et profondeur ont une source et un domaine de validité.",
        "Les réponses alternatives et tolérances sont figées avant le run.",
        "Les droits des annotations dérivées sont qualifiés.",
        "Le jeu Closed est séparé du développement et reste aveugle au candidat.",
        "La version du runner et les baselines sont immuables.",
        "Aucun accès fournisseur, FETCH ou téléchargement n'est requis.",
        "Le rapport inclut les sorties, erreurs, métriques, veto et checksums.",
    ]:
        story.append(check(item))
    story.append(Spacer(1, 7))
    story.append(p("Lecture des portes", styles["Sub"]))
    story.append(table([
        [cell("GO", True), cell("NO-GO", True), cell("INCONCLUSIVE", True)],
        [cell("Toutes les preuves obligatoires sont présentes, aucun veto, seuils atteints."), cell("Veto critique, droits invalides, contamination ou régression critique."), cell("Preuve insuffisante, désaccord expert, échantillon ou métrique insuffisants.")],
    ], [58 * mm, 58 * mm, 58 * mm]))
    story.append(PageBreak())

    # Final decision
    story.append(p("9. Décision de relecture", styles["Section"]))
    story.append(p("Cette page doit être remplie après les fiches scientifiques et juridiques. Toute décision changeant le niveau crée une nouvelle version du scénario.", styles["Body2"]))
    story.append(table([
        [cell("Scénario", True), cell("Gold", True), cell("Silver distinct", True), cell("Rejet", True), cell("Décision", True)],
        [cell("001"), cell("[ ]"), cell("[ ]"), cell("[ ]"), cell("________________")],
        [cell("002"), cell("[ ]"), cell("[ ]"), cell("[ ]"), cell("________________")],
        [cell("003"), cell("[ ]"), cell("[ ]"), cell("[ ]"), cell("________________")],
    ], [28 * mm, 27 * mm, 39 * mm, 27 * mm, 53 * mm]))
    story.append(Spacer(1, 10))
    story.append(p("Décision globale de la suite", styles["Sub"]))
    for item in [
        "[ ] GO - les scénarios qualifiés peuvent entrer dans le run Closed",
        "[ ] NO-GO - un veto ou une invalidité bloque la suite",
        "[ ] INCONCLUSIVE - preuves à compléter avant toute mesure",
        "[ ] Maintien en préparation - aucun run Closed n'est encore lancé",
    ]:
        story.append(p(item, styles["Body2"]))
    story.append(Spacer(1, 7))
    story.extend(lines("Motivation détaillée", 5))
    story.append(Spacer(1, 6))
    story.append(p("Nom / qualité du relecteur : ______________________________________________", styles["Body2"]))
    story.append(p("Signature : _____________________________________   Date : ______________", styles["Body2"]))
    story.append(Spacer(1, 12))
    story.append(box([
        p("<b>Rappel de gouvernance</b>", styles["Callout"]),
        p("Le relecteur qualifie la preuve. Il ne déclenche ni intégration IA, ni ingestion non qualifiée, ni promotion automatique. La décision finale reste enregistrée dans GSIE-Bench et dans son historique.", styles["Callout"]),
    ], PALE, GREEN_2))
    story.append(Spacer(1, 10))
    story.append(p("Références : RFC-0039 | DEC-000067 | REFERENCE_QUALIFICATION.md | EXPERT_REVIEW_PRELIMINARY_2026-08-11.md", styles["Small"]))

    doc.build(story, onFirstPage=cover, onLaterPages=footer)
    return OUTPUT


if __name__ == "__main__":
    print(build())
