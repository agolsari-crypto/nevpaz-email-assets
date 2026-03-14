#!/usr/bin/env python3
"""
NEVPAZ Arztbericht-Generator
Generiert Arztberichte mit Claude Sonnet 4.6 via AWS Bedrock EU (Frankfurt).
Inkl. Pseudonymisierung fuer DSGVO-Konformitaet.
"""

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field

import boto3
from dotenv import load_dotenv

load_dotenv()

# --- Konfiguration ---

AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "eu.anthropic.claude-sonnet-4-6-20260214-v1:0"
)
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))


# --- Pseudonymisierung ---

@dataclass
class Pseudonymisierer:
    """Ersetzt personenbezogene Daten durch Platzhalter und umgekehrt."""

    zuordnung: dict = field(default_factory=dict)
    _rueck_zuordnung: dict = field(default_factory=dict)
    _zaehler: dict = field(default_factory=dict)

    def _naechster_platzhalter(self, kategorie: str) -> str:
        self._zaehler[kategorie] = self._zaehler.get(kategorie, 0) + 1
        return f"[{kategorie}_{self._zaehler[kategorie]:03d}]"

    def pseudonymisieren(self, text: str, patientendaten: dict) -> str:
        """Ersetzt personenbezogene Daten im Text durch Platzhalter.

        Args:
            text: Der Originaltext mit echten Patientendaten.
            patientendaten: Dict mit Kategorien und Werten, z.B.:
                {
                    "PATIENT": ["Hans Mueller"],
                    "GEBURTSDATUM": ["12.03.1985"],
                    "ADRESSE": ["Hauptstr. 5, 80331 Muenchen"],
                    "TELEFON": ["089-12345678"],
                    "VERSICHERTENNR": ["A123456789"]
                }

        Returns:
            Text mit Platzhaltern statt echten Daten.
        """
        ergebnis = text
        for kategorie, werte in patientendaten.items():
            for wert in werte:
                if wert and wert in ergebnis:
                    platzhalter = self._naechster_platzhalter(kategorie)
                    self.zuordnung[platzhalter] = wert
                    self._rueck_zuordnung[wert] = platzhalter
                    ergebnis = ergebnis.replace(wert, platzhalter)
        return ergebnis

    def re_identifizieren(self, text: str) -> str:
        """Ersetzt Platzhalter zurueck durch echte Daten.

        Args:
            text: Text mit Platzhaltern.

        Returns:
            Text mit echten Patientendaten.
        """
        ergebnis = text
        for platzhalter, wert in self.zuordnung.items():
            ergebnis = ergebnis.replace(platzhalter, wert)
        return ergebnis

    def zuordnung_anzeigen(self):
        """Gibt die Zuordnungstabelle aus (nur fuer Debugging)."""
        print("\n--- Zuordnungstabelle (VERTRAULICH) ---")
        for platzhalter, wert in self.zuordnung.items():
            print(f"  {platzhalter} → {wert}")
        print("--- Ende Zuordnungstabelle ---\n")


# --- Berichtsvorlagen ---

VORLAGEN = {
    "arztbrief": """Du bist ein erfahrener Facharzt fuer {fachgebiet}.
Erstelle einen professionellen Arztbrief (Befundbericht) an den weiterbehandelnden Arzt.

Patientendaten: {patient_info}
Diagnose: {diagnose}
Befund/Anamnese: {befund}
Therapie: {therapie}

Formatierung:
- Formelle Anrede
- Strukturierte Gliederung (Anamnese, Befund, Diagnose, Therapie, Empfehlung)
- Professioneller medizinischer Stil
- Abschluss mit Grussformel
- Praxis: Privatpraxis NEVPAZ""",

    "entlassungsbericht": """Du bist ein erfahrener Facharzt fuer {fachgebiet}.
Erstelle einen Entlassungsbericht.

Patientendaten: {patient_info}
Aufnahmedatum: {aufnahmedatum}
Entlassungsdatum: {entlassungsdatum}
Diagnosen: {diagnose}
Verlauf: {befund}
Therapie bei Entlassung: {therapie}

Formatierung:
- Strukturierter Entlassungsbericht
- Aufnahmegrund, Verlauf, Diagnosen, Therapie, Empfehlungen
- Medikamentenplan bei Entlassung
- Nachsorgeempfehlungen
- Praxis: Privatpraxis NEVPAZ""",

    "befundbericht": """Du bist ein erfahrener Facharzt fuer {fachgebiet}.
Erstelle einen detaillierten Befundbericht.

Patientendaten: {patient_info}
Untersuchung: {untersuchung}
Befund: {befund}
Diagnose: {diagnose}

Formatierung:
- Untersuchungsmethode und -datum
- Detaillierte Befundbeschreibung
- Beurteilung und Diagnose
- Empfehlung zum weiteren Vorgehen
- Praxis: Privatpraxis NEVPAZ""",
}


# --- Bedrock Client ---

def bedrock_client():
    """Erstellt einen Bedrock Runtime Client fuer eu-central-1."""
    return boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def claude_anfrage(prompt: str, stream: bool = True) -> str:
    """Sendet eine Anfrage an Claude Sonnet 4.6 via Bedrock EU.

    Args:
        prompt: Der (pseudonymisierte!) Prompt.
        stream: Ob die Antwort gestreamt werden soll.

    Returns:
        Die generierte Antwort.
    """
    client = bedrock_client()

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
    })

    if stream:
        response = client.invoke_model_with_response_stream(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        ergebnis = []
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk["type"] == "content_block_delta":
                text = chunk["delta"].get("text", "")
                print(text, end="", flush=True)
                ergebnis.append(text)
        print()  # Newline am Ende
        return "".join(ergebnis)
    else:
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]


# --- Arztbericht generieren ---

def arztbericht_erstellen(
    berichtstyp: str,
    patientendaten: dict,
    klinische_daten: dict,
) -> str:
    """Erstellt einen Arztbericht mit Pseudonymisierung.

    Args:
        berichtstyp: "arztbrief", "entlassungsbericht", oder "befundbericht"
        patientendaten: Dict mit personenbezogenen Daten fuer Pseudonymisierung
        klinische_daten: Dict mit klinischen Angaben fuer die Vorlage

    Returns:
        Der fertige (re-identifizierte) Arztbericht.
    """
    if berichtstyp not in VORLAGEN:
        raise ValueError(
            f"Unbekannter Berichtstyp: {berichtstyp}. "
            f"Verfuegbar: {', '.join(VORLAGEN.keys())}"
        )

    # 1. Vorlage befuellen
    vorlage = VORLAGEN[berichtstyp]
    prompt = vorlage.format(**klinische_daten)

    # 2. Pseudonymisieren
    pseudo = Pseudonymisierer()
    prompt_pseudo = pseudo.pseudonymisieren(prompt, patientendaten)

    print(f"\n{'='*60}")
    print(f"Berichtstyp: {berichtstyp}")
    print(f"Modell: {BEDROCK_MODEL_ID}")
    print(f"Region: {AWS_REGION}")
    print(f"{'='*60}")
    print("\n--- Generiere Bericht (gestreamt) ---\n")

    # 3. Claude aufrufen (mit pseudonymisiertem Prompt)
    antwort_pseudo = claude_anfrage(prompt_pseudo)

    # 4. Re-identifizieren
    antwort = pseudo.re_identifizieren(antwort_pseudo)

    return antwort


# --- Demo ---

def demo():
    """Demonstriert die Arztbericht-Generierung mit Beispieldaten."""
    print("\n" + "=" * 60)
    print("NEVPAZ Arztbericht-Generator - DEMO")
    print("=" * 60)

    # Beispiel-Patientendaten (werden pseudonymisiert)
    patientendaten = {
        "PATIENT": ["Maria Schmidt"],
        "GEBURTSDATUM": ["15.06.1978"],
        "ADRESSE": ["Leopoldstr. 42, 80802 Muenchen"],
        "VERSICHERTENNR": ["T987654321"],
    }

    # Klinische Daten fuer die Vorlage
    klinische_daten = {
        "fachgebiet": "Neurologie und Psychiatrie",
        "patient_info": (
            "Maria Schmidt, geb. 15.06.1978, "
            "Leopoldstr. 42, 80802 Muenchen, "
            "Versichertennr. T987654321"
        ),
        "diagnose": "F33.1 Rezidivierende depressive Stoerung, gegenwärtig mittelgradige Episode",
        "befund": (
            "Die Patientin Maria Schmidt stellt sich aufgrund zunehmender "
            "depressiver Symptomatik vor. Seit ca. 6 Wochen bestehen "
            "Antriebsminderung, Schlafstörungen und Konzentrationsprobleme. "
            "BDI-II Score: 24 (mittelgradig)."
        ),
        "therapie": (
            "Sertralin 50mg 1-0-0, Steigerung auf 100mg nach 2 Wochen. "
            "KVT-Psychotherapie 1x/Woche empfohlen."
        ),
    }

    print("\n1. PSEUDONYMISIERUNG:")
    pseudo = Pseudonymisierer()
    test_text = klinische_daten["patient_info"]
    pseudo_text = pseudo.pseudonymisieren(test_text, patientendaten)
    print(f"   Original:       {test_text}")
    print(f"   Pseudonymisiert: {pseudo_text}")
    print(f"   Re-identifiziert: {pseudo.re_identifizieren(pseudo_text)}")

    print("\n2. BERICHT-GENERIERUNG:")
    print("   (Verbindung zu AWS Bedrock EU Frankfurt...)")

    try:
        bericht = arztbericht_erstellen(
            berichtstyp="arztbrief",
            patientendaten=patientendaten,
            klinische_daten=klinische_daten,
        )
        print("\n--- Fertiger Bericht (re-identifiziert) ---\n")
        print(bericht)
    except Exception as e:
        print(f"\n   FEHLER bei Bedrock-Verbindung: {e}")
        print("   Stellen Sie sicher, dass die AWS-Credentials in .env korrekt sind.")
        print("   Fuer den reinen Pseudonymisierungs-Test war der obige Test erfolgreich.")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        print("Nutzung: python arztbericht_generator.py --demo")
        print("Oder importieren Sie die Funktionen in Ihre eigene Anwendung.")
