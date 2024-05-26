"""Data Formatter for the Ecole Directe integration."""

import base64
import logging
import re

# as per recommendation from @freylis, compile once only
CLEANR = re.compile("<.*?>")

from .const import HOMEWORK_DESC_MAX_LENGTH

_LOGGER = logging.getLogger(__name__)


def format_homework(homework, clean_content):
    """format homework"""
    try:
        if homework.contenu is not None:
            contenu = base64.b64decode(homework.contenu).decode("utf-8")
        else:
            contenu = ""
        if clean_content:
            contenu = clean_html(contenu)
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


def clean_html(raw_html):
    """clean html"""
    cleantext = re.sub(CLEANR, "", raw_html)
    return cleantext


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
            "start_at": lesson.start_date.strftime("%Y-%m-%d"),
            "end_at": lesson.end_date.strftime("%Y-%m-%d"),
            "start_time": lesson.start_date.strftime("%H:%M"),
            "end_time": lesson.end_date.strftime("%H:%M"),
            "lesson": lesson.text,
            "classroom": lesson.salle,
            "canceled": lesson.is_annule,
            "background_color": lesson.color,
            "teacher_name": lesson.prof,
            "exempted": lesson.dispense,
            "is_morning": lesson.start_date.time() < lunch_break_time,
            "is_afternoon": lesson.start_date.time() >= lunch_break_time,
        }
    except Exception as ex:
        _LOGGER.warning("Error: %s - format_lesson: %s", ex, lesson)
        return {}


def format_evaluation(evaluation) -> dict:
    """evaluation format"""
    return {
        "name": evaluation.devoir,
        "date": evaluation.date,
        "subject": evaluation.libelle_matiere,
        "acquisitions": [
            {
                "name": acquisition.libelle_competence,
                "abbreviation": acquisition.valeur,
                "level": acquisition.level,
            }
            for acquisition in evaluation.elements_programme
        ],
    }


def format_vie_scolaire(viescolaire) -> dict:
    """vie scolaire format"""
    try:
        return {
            "date": viescolaire.date,
            "type_element": viescolaire.type_element,
            "display_date": viescolaire.display_date,
            "justified": viescolaire.justifie,
            "motif": viescolaire.motif,
            "commentaire": viescolaire.commentaire,
        }
    except Exception as ex:
        _LOGGER.warning("Error: %s - format_viescolaire: %s", ex, viescolaire)
        return {}
