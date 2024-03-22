"""Data Formatter for the Ecole Directe integration."""

from .const import HOMEWORK_DESC_MAX_LENGTH


def format_homework(homework):
    """format homework"""
    try:
        return {
            "date": homework.pour_le,
            "subject": homework.matiere,
            "short_description": homework.contenu[0:HOMEWORK_DESC_MAX_LENGTH],
            "description": homework.contenu,
            "done": homework.effectue,
            "background_color": None,
            "files": None,
            "matiere": homework.matiere,
            "codeMatiere": homework.code_matiere,
            "aFaire": homework.a_faire,
            "idDevoir": homework.id_devoir,
            "documentsAFaire": homework.documents_a_faire,
            "donneLe": homework.donne_le,
            "pourLe": homework.pour_le,
            "effectue": homework.effectue,
            "interrogation": homework.interrogation,
            "rendreEnLigne": homework.rendre_en_ligne,
            "nbJourMaxRenduDevoir": homework.nb_jour_max_rendu_devoir,
            "contenu": homework.contenu,
        }
    except Exception:
        return {}


def format_grade(grade):
    """grade fromat"""
    try:
        return {
            "date": grade.date,
            "subject": grade.code_matiere,
            "comment": grade.devoir,
            "grade": grade.valeur,
            "out_of": str(grade.note_sur).replace(".", ","),
            "default_out_of": str(grade.note_sur).replace(".", ","),
            "grade_out_of": grade.valeur + "/" + grade.note_sur,
            "coefficient": str(grade.coef).replace(".", ","),
            "class_average": str(grade.moyenne_classe).replace(".", ","),
            "max": str(grade.max_classe).replace(".", ","),
            "min": str(grade.min_classe).replace(".", ","),
            "is_bonus": None,
            "is_optionnal": None,
            "is_out_of_20": None,
            "id": grade.id,
            "devoir": grade.devoir,
            "codePeriode": grade.code_periode,
            "codeMatiere": grade.code_matiere,
            "libelleMatiere": grade.libelle_matiere,
            "codeSousMatiere": grade.code_sous_matiere,
            "typeDevoir": grade.type_devoir,
            "enLettre": grade.en_lettre,
            "commentaire": grade.commentaire,
            "uncSujet": grade.unc_sujet,
            "uncCorrige": grade.unc_corrige,
            "coef": grade.coef,
            "noteSur": grade.note_sur,
            "valeur": grade.valeur,
            "nonSignificatif": grade.non_significatif,
            "dateSaisie": grade.date_saisie,
            "valeurisee": grade.valeurisee,
            "moyenneClasse": grade.moyenne_classe,
            "minClasse": grade.min_classe,
            "maxClasse": grade.max_classe,
            "elementsProgramme": grade.elements_programme,
        }
    except Exception:
        return {}
