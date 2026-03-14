# NEVPAZ Corporate LLM - Architektur & Setup-Guide

## Uebersicht

Corporate LLM-Loesung fuer die Privatpraxis NEVPAZ basierend auf:
- **Claude Sonnet 4.6** via AWS Bedrock EU (Frankfurt)
- **Hostinger VPS** (Deutschland) als Web-Frontend
- **DSGVO-konforme** Datenverarbeitung mit Pseudonymisierung

---

## Architektur

```
┌──────────────────────────────────────────────────┐
│        Hostinger VPS (Deutschland)               │
│        Docker + FastAPI Web-App                  │
│                                                  │
│  ┌─────────────┐    ┌─────────────────────────┐ │
│  │  Web-UI     │    │  Arztbericht-Generator  │ │
│  │  (Browser)  │───▶│  + Pseudonymisierung    │ │
│  │             │    │  + Template-System       │ │
│  └─────────────┘    └────────────┬────────────┘ │
│                                  │               │
│  ┌─────────────────────────────────────────────┐ │
│  │  Pseudonymisierungs-Schicht                 │ │
│  │  Patient Neff → [PATIENT_001]               │ │
│  │  12.03.1985 → [GEBURTSDATUM_001]            │ │
│  └──────────────────────┬──────────────────────┘ │
└─────────────────────────┼────────────────────────┘
                          │ HTTPS (TLS 1.3)
                          ▼
               ┌──────────────────┐
               │  AWS Bedrock EU  │
               │  eu-central-1    │
               │  (Frankfurt)     │
               │                  │
               │  Claude Sonnet   │
               │  4.6             │
               └──────────────────┘
```

---

## Schritt-fuer-Schritt Setup

### Schritt 1: AWS-Konto einrichten

1. **AWS-Konto erstellen**: https://aws.amazon.com/de/
2. **Region auf eu-central-1 (Frankfurt) setzen**
3. **Bedrock aktivieren**:
   - AWS Console → Amazon Bedrock → Model access
   - "Anthropic" auswaehlen → Claude Sonnet 4.6 aktivieren
   - Warten auf Genehmigung (~Minuten)
4. **IAM-Benutzer erstellen** (fuer API-Zugriff):
   - IAM → Users → Add user
   - Programmatic access aktivieren
   - Policy: `AmazonBedrockFullAccess`
   - Access Key ID und Secret Access Key notieren
5. **AVV (Auftragsverarbeitungsvertrag) abschliessen**:
   - AWS Artifact → AWS GDPR DPA akzeptieren
   - Dokumentiert die DSGVO-konforme Verarbeitung

### Schritt 2: Hostinger VPS einrichten

1. **VPS bestellen**: https://www.hostinger.de/vps-hosting
   - Plan: KVM 1 oder KVM 2 (ab ~5 EUR/Monat)
   - **Standort: Deutschland** auswaehlen
   - Template: Ubuntu 24.04 mit Docker
2. **Domain verbinden** (optional):
   - z.B. `llm.nevpaz.de` oder `ai.nevpaz.de`
   - SSL via Let's Encrypt (kostenlos)
3. **Firewall konfigurieren**:
   - Port 443 (HTTPS) oeffnen
   - Port 22 (SSH) auf Praxis-IP beschraenken
   - Alle anderen Ports schliessen
4. **Docker pruefen**:
   ```bash
   docker --version
   docker compose version
   ```

### Schritt 3: Anwendung deployen

```bash
# Repository klonen
git clone <repo-url> /opt/nevpaz-llm
cd /opt/nevpaz-llm/corporate-llm

# Umgebungsvariablen konfigurieren
cp .env.example .env
nano .env  # AWS-Credentials eintragen

# Container starten
docker compose up -d

# Status pruefen
docker compose logs -f
```

### Schritt 4: Testen

```bash
# Verbindungstest
python test_bedrock.py

# Demo-Arztbericht generieren
python arztbericht_generator.py --demo
```

---

## DSGVO-Checkliste fuer Arztpraxis

### Technische Massnahmen:
- [x] Datenverarbeitung in EU (AWS eu-central-1 Frankfurt)
- [x] Pseudonymisierung vor API-Aufruf
- [x] Verschluesselung in Transit (TLS 1.3)
- [x] Verschluesselung at Rest (AWS Standard)
- [x] Kein Modelltraining mit Praxisdaten (Bedrock Standard)
- [x] Zugriffskontrolle (API-Keys, Firewall)

### Organisatorische Massnahmen:
- [ ] AVV mit AWS abschliessen (AWS Artifact)
- [ ] Datenschutz-Folgenabschaetzung (DSFA) erstellen
- [ ] Verzeichnis der Verarbeitungstaetigkeiten aktualisieren
- [ ] Mitarbeiter in Pseudonymisierung schulen
- [ ] Einwilligung der Patienten einholen (falls noetig)
- [ ] Datenschutzbeauftragten informieren

### Pseudonymisierungskonzept:
```
VORHER (Praxisdaten):
  "Patient Hans Mueller, geb. 12.03.1985, Hauptstr. 5, 80331 Muenchen"

AN CLAUDE GESENDET:
  "Patient [PATIENT_001], geb. [DATUM_001], [ADRESSE_001]"

CLAUDE GENERIERT:
  "Sehr geehrte Kollegin, ich berichte ueber [PATIENT_001]..."

ZURUECK IN PRAXIS (re-identifiziert):
  "Sehr geehrte Kollegin, ich berichte ueber Hans Mueller..."
```

Die Zuordnungstabelle (Platzhalter → echte Daten) bleibt **ausschliesslich
auf dem Hostinger VPS** und wird **nie** an AWS/Claude gesendet.

---

## Kostenueberblick

| Posten | Kosten/Monat |
|--------|-------------|
| Hostinger VPS KVM 1 (Deutschland) | ~5 EUR |
| AWS Bedrock Claude Sonnet 4.6 | ~20-80 EUR* |
| Domain + SSL | 0-2 EUR |
| **Gesamt** | **~25-90 EUR** |

*Token-Kosten haengen von der Nutzung ab:
- 1 Arztbericht (~2000 Woerter) ≈ ~3000 Input + ~3000 Output Tokens
- Bei 100 Berichten/Monat ≈ ~$2-3 (sehr guenstig)
- Kosten steigen nur bei intensiver Chat-Nutzung

---

## Sicherheitshinweise

1. **NIEMALS** echte Patientendaten ohne Pseudonymisierung an Claude senden
2. **AWS-Credentials** sicher aufbewahren (nicht im Git-Repository!)
3. **Firewall** restriktiv konfigurieren (nur Praxis-IP)
4. **Regelmaessige Updates** des Hostinger VPS
5. **Audit-Logs** regelmaessig pruefen
6. **Backup** der Konfiguration (nicht der Patientendaten!)
