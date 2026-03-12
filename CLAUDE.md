# NEVPAZ Projektanweisungen

## Automatische Skill-Aktivierung

### Scientific Analysis Skill
Der Skill `.claude/skills/scientific-analysis.md` wird **automatisch** bei folgenden Anfragen verwendet:
- Erstellung von PowerPoint-Präsentationen (PPTX)
- Analyse wissenschaftlicher PDFs und Paper
- Erstellung von Diagrammen, Grafiken, Tabellen oder Charts
- Visualisierung medizinischer/neurowissenschaftlicher Zusammenhänge
- Pathophysiologie-Darstellungen und Neurotransmitter-Systeme
- Studienanalysen und Meta-Analysen
- Jede Anfrage die wissenschaftliche Daten visuell aufbereiten soll

### Verfügbare Tools
- **Python Toolkit**: `scripts/scientific_viz.py` — Wissenschaftliche Visualisierungen
  - Forest Plots, PRISMA-Diagramme, Neurotransmitter-Pathways
  - Rezeptor-Bindungsprofile, Dosis-Wirkungs-Kurven
  - Synaptischer Spalt, Heatmaps, Studienvergleiche
  - PowerPoint-Generierung mit NEVPAZ-Design
  - Demo: `python scripts/scientific_viz.py --demo`

### Design-Standards
- NEVPAZ Farben: `#1a5276` (Dunkelblau), `#2980b9` (Mittelblau)
- Mindestens 300 DPI für alle Grafiken
- Calibri als Standard-Schriftart
- 16:9 für Präsentationen
- Quellenangaben auf jeder Grafik
