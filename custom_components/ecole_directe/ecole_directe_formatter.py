"""Data Formatter for the Ecole Directe integration."""

import base64
import logging

from .const import HOMEWORK_DESC_MAX_LENGTH

_LOGGER = logging.getLogger(__name__)


def format_homework(homework):
    """format homework"""
    try:
        if homework.contenu is not None:
            contenu = base64.b64decode(homework.contenu).decode("utf-8")
        else:
            contenu = ""
        return {
            "date": homework.pour_le,
            "subject": homework.matiere,
            "short_description": contenu[0:HOMEWORK_DESC_MAX_LENGTH],
            "description": contenu,
            "done": homework.effectue,
            "background_color": None,
            "files": [],
            "interrogation": homework.interrogation,
        }
    except Exception as ex:
        _LOGGER.warning("Error: %s - format_homework: %s", ex, homework)
        return {}


def format_grade(grade) -> dict:
    """grade format"""
    try:
        return {
            "date": grade.date,
            "subject": grade.libelle_matiere,
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
            "date_saisie": grade.date_saisie,
        }
    except Exception as ex:
        _LOGGER.warning("Error: %s - format_grade: %s", ex, grade)
        return {}


def format_lesson(lesson, lunch_break_time) -> dict:
    """lesson format"""
    try:
        return {
            "start_at": lesson.start_date,
            "end_at": lesson.end_date,
            "start_time": lesson.start_date.strftime("%H:%M"),
            "end_time": lesson.end_date.strftime("%H:%M"),
            "lesson": lesson.text,
            "classroom": lesson.get("salle", ""),
            "canceled": lesson.get("isAnnule", False),
            "status": None,
            "background_color": lesson.get("color", ""),
            "teacher_name": lesson.get("prof", ""),
            "teacher_names": None,
            "classrooms": None,
            "outing": None,
            "memo": None,
            "group_name": None,
            "group_names": None,
            "exempted": lesson.dispense,
            "virtual_classrooms": None,
            "num": lesson.color,
            "detention": None,
            "test": None,
            "is_morning": lesson.start.time() < lunch_break_time,
            "is_afternoon": lesson.start.time() >= lunch_break_time,
            "subject": lesson.get("matiere", ""),
            "subject_code": lesson.get("codeMatiere", ""),
            "course_type": lesson.get("typeCours", ""),
            "is_mandatory": not lesson.get("dispensable", False),
            "exemption": lesson.get("dispense", 0),
            "class": lesson.get("classe", ""),
            "class_id": lesson.get("classeId", 0),
            "class_code": lesson.get("classeCode", ""),
            "group": lesson.get("groupe", ""),
            "group_code": lesson.get("groupeCode", ""),
            "is_flexible": lesson.get("isFlexible", False),
            "group_id": lesson.get("groupeId", 0),
            "icon": lesson.get("icone", ""),
            "is_modified": lesson.get("isModifie", False),
            "session_content_available": lesson.get("contenuDeSeance", False),
            "homework_due": lesson.get("devoirAFaire", False),
        }
    except Exception as ex:
        _LOGGER.warning("Error: %s - format_lesson: %s", ex, lesson)
        return {}


def format_evaluation(evaluation) -> dict:
    """evaluation format"""
    return {
        "name": evaluation.libelle_matiere,
        "domain": None,
        "date": evaluation.date,
        "subject": evaluation.devoir,
        "description": None,
        "coefficient": None,
        "paliers": None,
        "teacher": None,
        "acquisitions": [
            {
                "order": None,
                "name": acquisition.libelle_competence,
                "abbreviation": None,
                "level": acquisition.valeur,
                "domain": acquisition.descriptif,
                "pillar": None,
                "pillar_prefix": None,
            }
            for acquisition in evaluation.elements_programme
        ],
    }


def format_vie_scolaire(viescolaire) -> dict:
    """vie scolaire format"""
    try:
        return {
            "date": viescolaire.date,
            "type": viescolaire.type_element,
            "display_date": viescolaire.display_date,
            "justified": viescolaire.justifie,
        }
    except Exception as ex:
        _LOGGER.warning("Error: %s - format_viescolaire: %s", ex, viescolaire)
        return {}
