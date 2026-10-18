#!/usr/bin/env python3
"""
Génère un fichier de planning au format get_lessons, pour la semaine en cours et les 2 semaines suivantes, à partir d'un fichier source.

- Les dates sont recalées sur la semaine de référence (aujourd'hui par défaut).
- Les semaines de la source servent de modèle, cycliquement (semaine 1 -> S+0,
  semaine 2 -> S+1, semaine 3 -> S+2), en conservant jour et horaires.
- Les noms des professeurs sont remplacés par "Professeur 01", "Professeur 02"...
  (le même professeur garde le même pseudonyme dans tout le fichier).

Usage :
    python generer_planning.py 2232_get_lessons.json
    python generer_planning.py source.json -o planning.json --date 2026-10-19
    python generer_planning.py source.json --sans-conges
"""

import argparse
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

DATE_FMT = "%Y-%m-%d %H:%M"
NB_SEMAINES = 3  # semaine en cours + 2 semaines suivantes


def charger_source(chemin):
    with Path.open(chemin, encoding="utf-8") as f:
        obj = json.load(f)
    # Accepte aussi l'enveloppe {"stdout": "<json>", ...} si elle est présente
    if "data" not in obj and isinstance(obj.get("stdout"), str):
        obj = json.loads(obj["stdout"])
    if "data" not in obj:
        raise ValueError("Clé 'data' introuvable dans le fichier source.")
    return obj


def lundi_de(d: date) -> date:
    return d - timedelta(days=d.weekday())


def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, DATE_FMT)


def semaines_source(cours):
    """Lundis des semaines présentes dans la source, triés."""
    return sorted({lundi_de(parse_dt(c["start_date"]).date()) for c in cours})


def pseudonymes(cours):
    """Associe chaque professeur réel à un pseudonyme stable."""
    noms = sorted({c["prof"].strip() for c in cours if c["prof"].strip()})
    return {nom: f"Professeur {i:02d}" for i, nom in enumerate(noms, start=1)}


def generer(source, date_ref: date, sans_conges=False):
    cours = source["data"]
    if sans_conges:
        cours = [c for c in cours if c.get("typeCours") != "CONGE"]

    semaines = semaines_source(cours)
    if not semaines:
        raise ValueError("Aucun cours trouvé dans la source.")

    anonymes = pseudonymes(cours)
    lundi_cible = lundi_de(date_ref)
    resultat = []
    prochain_id = 1

    for i in range(NB_SEMAINES):
        lundi_modele = semaines[i % len(semaines)]
        lundi_nouveau = lundi_cible + timedelta(weeks=i)
        decalage = timedelta(days=(lundi_nouveau - lundi_modele).days)

        for c in cours:
            debut = parse_dt(c["start_date"])
            if lundi_de(debut.date()) != lundi_modele:
                continue
            fin = parse_dt(c["end_date"])

            nouveau = dict(c)
            nouveau["id"] = prochain_id
            prochain_id += 1
            nouveau["start_date"] = (debut + decalage).strftime(DATE_FMT)
            nouveau["end_date"] = (fin + decalage).strftime(DATE_FMT)
            nouveau["prof"] = anonymes.get(c["prof"].strip(), "")
            resultat.append(nouveau)

    resultat.sort(key=lambda c: c["start_date"])
    return {
        "code": 200,
        "token": str(uuid.uuid4()),
        "host": source.get("host", "HTTP"),
        "data": resultat,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("source", help="Fichier JSON source (format get_lessons)")
    parser.add_argument(
        "-o",
        "--sortie",
        help="Fichier de sortie (défaut : <source>_anonymise_<lundi>.json)",
    )
    parser.add_argument(
        "--date", help="Date de référence AAAA-MM-JJ (défaut : aujourd'hui)"
    )
    parser.add_argument(
        "--sans-conges",
        action="store_true",
        help="Exclure les lignes CONGE (jours fériés, vacances)",
    )
    args = parser.parse_args()

    date_ref = date.fromisoformat(args.date) if args.date else date.today()
    source = charger_source(args.source)
    planning = generer(source, date_ref, sans_conges=args.sans_conges)

    sortie = (
        Path(args.sortie)
        if args.sortie
        else Path(args.source).with_name(
            f"{Path(args.source).stem}_anonymise_{lundi_de(date_ref).isoformat()}.json"
        )
    )
    with Path.open(sortie, "w", encoding="utf-8") as f:
        json.dump(planning, f, ensure_ascii=False, indent=4)

    print(f"Fichier écrit : {sortie}")
    print(f"Nombre de cours : {len(planning['data'])}")
    print(f"Semaines : du {lundi_de(date_ref)} sur {NB_SEMAINES} semaines")


if __name__ == "__main__":
    main()
