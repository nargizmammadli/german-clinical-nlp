"""
German Clinical Sample Data Generation Script

Development-only script to create synthetic German clinical text samples.
Outputs static JSON file committed to repository.

DEVIATION NOTE: Originally planned to use GGPONC 2.0 dataset via HuggingFace,
but bigbio/ggponc2 uses deprecated loading scripts (RuntimeError in datasets >= 3.0).
Generated synthetic samples instead to demonstrate German clinical NLP capabilities.

Usage:
    python scripts/extract_samples.py
"""

import json
from pathlib import Path


def generate_synthetic_samples(num_samples: int = 15) -> list:
    """
    Generate synthetic German clinical text samples.

    Args:
        num_samples: Number of samples to generate (default: 15, per D-04: 10-20)

    Returns:
        List of sample dictionaries with id, text, source, and entity annotations
    """
    print(f"Generating {num_samples} synthetic German clinical samples...")

    # Synthetic German clinical notes with entity annotations
    # These demonstrate typical clinical NLP tasks: dates, diagnoses, medications, procedures
    synthetic_data = [
        {
            "text": "Aufnahme am 15.03.2025. Patient klagt über chronische Rückenschmerzen seit 6 Monaten. Diagnose: Lumbalgie (M54.5). Therapie: Ibuprofen 600mg 3x täglich.",
            "entities": [
                {"type": "Date", "text": "15.03.2025", "start": 11, "end": 21},
                {"type": "Symptom", "text": "chronische Rückenschmerzen", "start": 41, "end": 67},
                {"type": "Diagnosis", "text": "Lumbalgie", "start": 92, "end": 101},
                {"type": "Medication", "text": "Ibuprofen 600mg", "start": 121, "end": 136}
            ]
        },
        {
            "text": "Entlassungsbericht vom 22.01.2025. Die Patientin wurde am 18.01.2025 mit akutem Myokardinfarkt (I21.9) aufgenommen. Therapie umfasste Aspirin 100mg, Atorvastatin 40mg. Verweildauer: 4 Tage.",
            "entities": [
                {"type": "Date", "text": "22.01.2025", "start": 23, "end": 33},
                {"type": "Date", "text": "18.01.2025", "start": 59, "end": 69},
                {"type": "Diagnosis", "text": "akutem Myokardinfarkt", "start": 74, "end": 95},
                {"type": "Medication", "text": "Aspirin 100mg", "start": 136, "end": 149},
                {"type": "Medication", "text": "Atorvastatin 40mg", "start": 151, "end": 168},
                {"type": "LOS", "text": "4 Tage", "start": 184, "end": 190}
            ]
        },
        {
            "text": "Aufnahmedatum: 08.12.2024. Diagnose: Diabetes mellitus Typ 2 (E11.9), arterielle Hypertonie (I10). Medikation: Metformin 1000mg 2x täglich, Ramipril 5mg 1x täglich.",
            "entities": [
                {"type": "Date", "text": "08.12.2024", "start": 15, "end": 25},
                {"type": "Diagnosis", "text": "Diabetes mellitus Typ 2", "start": 37, "end": 60},
                {"type": "Diagnosis", "text": "arterielle Hypertonie", "start": 71, "end": 92},
                {"type": "Medication", "text": "Metformin 1000mg", "start": 113, "end": 129},
                {"type": "Medication", "text": "Ramipril 5mg", "start": 143, "end": 155}
            ]
        },
        {
            "text": "Chirurgischer Eingriff am 05.06.2025: Laparoskopische Cholezystektomie bei Cholelithiasis (K80.2). OP-Dauer: 90 Minuten. Postoperative Analgesie mit Metamizol 1g i.v.",
            "entities": [
                {"type": "Date", "text": "05.06.2025", "start": 26, "end": 36},
                {"type": "Procedure", "text": "Laparoskopische Cholezystektomie", "start": 38, "end": 70},
                {"type": "Diagnosis", "text": "Cholelithiasis", "start": 75, "end": 89},
                {"type": "Medication", "text": "Metamizol 1g", "start": 152, "end": 164}
            ]
        },
        {
            "text": "Notaufnahme 12.04.2025, 14:30 Uhr. Verdacht auf Apoplexie. CT-Schädel ohne Nachweis einer Blutung. Diagnose: Transitorische ischämische Attacke (G45.9). Thrombozytenaggregationshemmung mit Clopidogrel 75mg.",
            "entities": [
                {"type": "Date", "text": "12.04.2025", "start": 12, "end": 22},
                {"type": "Symptom", "text": "Apoplexie", "start": 49, "end": 58},
                {"type": "Procedure", "text": "CT-Schädel", "start": 60, "end": 70},
                {"type": "Diagnosis", "text": "Transitorische ischämische Attacke", "start": 111, "end": 145},
                {"type": "Medication", "text": "Clopidogrel 75mg", "start": 192, "end": 208}
            ]
        },
        {
            "text": "Ambulante Vorstellung am 19.02.2025. Patient berichtet Besserung der depressiven Symptomatik unter Sertralin 50mg. Diagnose: Rezidivierende depressive Störung (F33.1). Fortführung der Therapie empfohlen.",
            "entities": [
                {"type": "Date", "text": "19.02.2025", "start": 25, "end": 35},
                {"type": "Symptom", "text": "depressiven Symptomatik", "start": 70, "end": 93},
                {"type": "Medication", "text": "Sertralin 50mg", "start": 100, "end": 114},
                {"type": "Diagnosis", "text": "Rezidivierende depressive Störung", "start": 127, "end": 160}
            ]
        },
        {
            "text": "Stationäre Aufnahme 28.11.2024 wegen akuter Exazerbation einer COPD (J44.1). Sauerstoffgabe 2l/min, Prednisolon 40mg i.v., Antibiotikatherapie mit Amoxicillin 1g 3x täglich. Klinische Besserung nach 5 Tagen.",
            "entities": [
                {"type": "Date", "text": "28.11.2024", "start": 20, "end": 30},
                {"type": "Diagnosis", "text": "akuter Exazerbation einer COPD", "start": 37, "end": 68},
                {"type": "Medication", "text": "Prednisolon 40mg", "start": 102, "end": 118},
                {"type": "Medication", "text": "Amoxicillin 1g", "start": 149, "end": 163},
                {"type": "LOS", "text": "5 Tagen", "start": 200, "end": 207}
            ]
        },
        {
            "text": "Kardiologische Kontrolle vom 14.09.2024. EKG zeigt Sinusrhythmus, RR 135/85 mmHg. Diagnose: Arterielle Hypertonie Grad 1 (I10). Fortführung Betablocker Bisoprolol 5mg.",
            "entities": [
                {"type": "Date", "text": "14.09.2024", "start": 29, "end": 39},
                {"type": "Procedure", "text": "EKG", "start": 41, "end": 44},
                {"type": "Diagnosis", "text": "Arterielle Hypertonie Grad 1", "start": 93, "end": 121},
                {"type": "Medication", "text": "Bisoprolol 5mg", "start": 154, "end": 168}
            ]
        },
        {
            "text": "Entlassung am 07.07.2025 nach erfolgreicher Hüft-TEP links bei Coxarthrose (M16.1). Mobilisation mit Gehstützen, Analgesie Ibuprofen 400mg bei Bedarf. Nachkontrolle in 6 Wochen.",
            "entities": [
                {"type": "Date", "text": "07.07.2025", "start": 14, "end": 24},
                {"type": "Procedure", "text": "Hüft-TEP links", "start": 45, "end": 59},
                {"type": "Diagnosis", "text": "Coxarthrose", "start": 64, "end": 75},
                {"type": "Medication", "text": "Ibuprofen 400mg", "start": 125, "end": 140}
            ]
        },
        {
            "text": "Laborwerte vom 03.08.2024: HbA1c 7.2%, Kreatinin 1.1 mg/dl. Diagnose: Diabetes mellitus Typ 2 mit befriedigender Stoffwechsellage. Ernährungsberatung durchgeführt.",
            "entities": [
                {"type": "Date", "text": "03.08.2024", "start": 15, "end": 25},
                {"type": "Diagnosis", "text": "Diabetes mellitus Typ 2", "start": 71, "end": 94}
            ]
        },
        {
            "text": "Pneumonologische Untersuchung 21.10.2024. Spirometrie zeigt obstruktive Ventilationsstörung. Diagnose: Asthma bronchiale (J45.0). Inhalative Therapie: Budesonid 400µg 2x täglich.",
            "entities": [
                {"type": "Date", "text": "21.10.2024", "start": 30, "end": 40},
                {"type": "Procedure", "text": "Spirometrie", "start": 42, "end": 53},
                {"type": "Diagnosis", "text": "Asthma bronchiale", "start": 105, "end": 122},
                {"type": "Medication", "text": "Budesonid 400µg", "start": 153, "end": 168}
            ]
        },
        {
            "text": "Orthopädische Vorstellung am 16.05.2025. Verdacht auf Meniskusläsion rechtes Knie. MRT geplant für 23.05.2025. Zunächst konservative Therapie mit Diclofenac 75mg retard.",
            "entities": [
                {"type": "Date", "text": "16.05.2025", "start": 29, "end": 39},
                {"type": "Diagnosis", "text": "Meniskusläsion", "start": 55, "end": 69},
                {"type": "Date", "text": "23.05.2025", "start": 101, "end": 111},
                {"type": "Procedure", "text": "MRT", "start": 84, "end": 87},
                {"type": "Medication", "text": "Diclofenac 75mg retard", "start": 149, "end": 171}
            ]
        },
        {
            "text": "Gynäkologischer Befund vom 11.01.2025: Mammographie unauffällig. Empfehlung: Kontrolle in 2 Jahren. Keine akuten Beschwerden.",
            "entities": [
                {"type": "Date", "text": "11.01.2025", "start": 27, "end": 37},
                {"type": "Procedure", "text": "Mammographie", "start": 39, "end": 51}
            ]
        },
        {
            "text": "Dermatologische Konsultation 04.03.2025. Diagnose: Psoriasis vulgaris (L40.0). Topische Behandlung mit Betamethason-Salbe. Systemtherapie vorerst nicht indiziert.",
            "entities": [
                {"type": "Date", "text": "04.03.2025", "start": 29, "end": 39},
                {"type": "Diagnosis", "text": "Psoriasis vulgaris", "start": 52, "end": 70},
                {"type": "Medication", "text": "Betamethason-Salbe", "start": 104, "end": 122}
            ]
        },
        {
            "text": "Neurologische Untersuchung am 29.06.2024. Patient mit bekannter Epilepsie. Letzte Anfälle vor 3 Monaten. Antiepileptische Therapie: Levetiracetam 1000mg 2x täglich. EEG-Kontrolle geplant.",
            "entities": [
                {"type": "Date", "text": "29.06.2024", "start": 30, "end": 40},
                {"type": "Diagnosis", "text": "Epilepsie", "start": 65, "end": 74},
                {"type": "Medication", "text": "Levetiracetam 1000mg", "start": 134, "end": 154},
                {"type": "Procedure", "text": "EEG-Kontrolle", "start": 169, "end": 182}
            ]
        }
    ]

    samples = []
    for i, data in enumerate(synthetic_data[:num_samples]):
        sample = {
            "id": f"synthetic_{i:03d}",
            "text": data["text"],
            "source": "Synthetic German Clinical Data",
            "entities": data.get("entities", [])
        }
        samples.append(sample)

    print(f"Generated {len(samples)} synthetic samples")
    return samples


def main():
    """Main generation workflow."""
    # Generate samples (15 is middle of 10-20 range per D-04)
    samples = generate_synthetic_samples(num_samples=15)

    # Write to static JSON file
    output_path = Path("data/samples/ggponc_samples.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Successfully extracted {len(samples)} samples")
    print(f"✓ Written to: {output_path}")
    print(f"✓ File size: {output_path.stat().st_size / 1024:.1f} KB")

    # Validate output
    if len(samples) < 10 or len(samples) > 20:
        print(f"\nWARNING: Sample count {len(samples)} outside D-04 requirement (10-20)")

    if output_path.stat().st_size < 5000:
        print(f"\nWARNING: File size < 5KB, may not contain substantial German text")


if __name__ == "__main__":
    main()
