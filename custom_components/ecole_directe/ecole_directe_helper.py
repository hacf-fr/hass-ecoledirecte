"""Module to help communication with Ecole Directe API."""

import base64
import json
import logging
import operator
import re
from datetime import datetime, time
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import anyio
from ecoledirecte_api.client import EDClient, QCMException
from homeassistant.core import HomeAssistant
from unidecode import unidecode

from .const import (
    EVENT_TYPE,
    FAKE_ON,
    GRADES_TO_DISPLAY,
    HOMEWORK_DESC_MAX_LENGTH,
    INTEGRATION_PATH,
    VIE_SCOLAIRE_TO_DISPLAY,
)

# as per recommendation from @freylis, compile once only
CLEANR = re.compile("<.*?>")

LOGGER = logging.getLogger(__name__)


async def load_json_file(file_path: str) -> dict:
    """Load JSON file."""
    async with await anyio.open_file(file_path, "r") as f:
        return json.loads(await f.read())


async def save_json_file(json_content: Any, file_path: str) -> None:
    """Save JSON file."""
    async with await anyio.open_file(file_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(json_content, indent=4, ensure_ascii=False))


class EDEleve:
    """Student information."""

    def __init__(
        self,
        modules: list[str],
        data: Any = None,
        establishment: str = "",
        eleve_id: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        classe_id: str | None = None,
        classe_name: str | None = None,
    ) -> None:
        """Save student information."""
        if data is None:
            self.classe_id = classe_id
            self.classe_name: str = str({classe_name: ""})
            self.eleve_id: str = str({eleve_id: ""})
            self.eleve_lastname: str = str({last_name: ""})
            self.eleve_firstname: str = str({first_name: ""})
            self.modules: list[str] = modules
            self.establishment = establishment
        else:
            if "classe" in data:
                self.classe_id = data["classe"]["id"]
                self.classe_name = data["classe"]["libelle"]
            else:
                self.classe_id = ""
                self.classe_name = ""
            self.eleve_id: str = str(data["id"])
            self.eleve_lastname = data["nom"]
            self.eleve_firstname = data["prenom"]

            self.establishment = establishment
            self.modules = []
            for module in data["modules"]:
                if module["enable"]:
                    self.modules.append(module["code"])

    def get_fullname_lower(self) -> str:
        """Student fullname lowercase."""
        return get_unique_id(f"{self.get_fullname()}")

    def get_fullname(self) -> str:
        """Student fullname."""
        return f"{self.eleve_firstname} {self.eleve_lastname}"


class EDSession:
    """Ecole Directe session with Token and cookie."""

    def __init__(
        self,
        user: str,
        pwd: str,
        qcm_path: str,
        hass: HomeAssistant,
    ) -> None:
        """Save some information needed to login the session."""
        self.hass = hass
        self.username = user
        self.password = pwd
        self.qcm_path = qcm_path
        self.log_folder = self.hass.config.config_dir + INTEGRATION_PATH + "logs/"
        self.test_folder = self.hass.config.config_dir + INTEGRATION_PATH + "test/"
        Path(self.log_folder).mkdir(parents=True, exist_ok=True)

    async def __aenter__(self) -> Self:
        """Enter the session context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the session context."""
        await self.close()

    async def close(self) -> None:
        """Close the session."""
        if self.ed_client is not None:
            await self.ed_client.close()

    async def save_question(self, qcm_json: Any) -> None:
        """Save questions to file."""
        await save_json_file(qcm_json, self.qcm_path)
        event_data = {
            "child_name": None,
            "type": "new_qcm",
        }
        self.hass.bus.fire(EVENT_TYPE, event_data)
        LOGGER.debug("Saved question to file")

    async def login(self) -> Any:
        """Login to Ecole Directe."""
        LOGGER.debug("loading QCM file")
        self.qcm = await load_json_file(self.qcm_path)
        self.ed_client: EDClient = EDClient(
            username=self.username,
            password=self.password,
            qcm_json=self.qcm,
        )
        self.ed_client.on_new_question(self.save_question)
        login = await self.ed_client.login()
        LOGGER.debug(login)
        LOGGER.info(
            "Connection OK - identifiant: [{%s}]",
            login["data"]["accounts"][0]["identifiant"],
        )
        self.data = login["data"]
        self.id = self.data["accounts"][0]["id"]
        self.identifiant = self.data["accounts"][0]["identifiant"]
        self.id_login = self.data["accounts"][0]["idLogin"]
        self.account_type = self.data["accounts"][0]["typeCompte"]
        self.modules = []
        for module in self.data["accounts"][0]["modules"]:
            if module["enable"]:
                self.modules.append(module["code"])
        self.eleves = []
        if self.account_type == "E":
            self.eleves.append(
                EDEleve(
                    self.modules,
                    None,
                    self.data["accounts"][0]["nomEtablissement"],
                    self.id,
                    self.data["accounts"][0]["prenom"],
                    self.data["accounts"][0]["nom"],
                    self.data["accounts"][0]["profile"]["classe"]["id"],
                    self.data["accounts"][0]["profile"]["classe"]["libelle"],
                )
            )
        elif "eleves" in self.data["accounts"][0]["profile"]:
            for eleve in self.data["accounts"][0]["profile"]["eleves"]:
                self.eleves.append(
                    EDEleve(
                        [],
                        eleve,
                        self.data["accounts"][0]["nomEtablissement"],
                    )
                )

    async def get_messages(
        self,
        family_id: str | None,
        eleve: EDEleve | None,
        annee_scolaire: str,
    ) -> Any | None:
        """Get messages from Ecole Directe."""
        if FAKE_ON:
            json_resp = await load_json_file(self.test_folder + "test_messages.json")
        elif eleve is None:
            json_resp = await self.ed_client.get_messages(
                family_id, None, annee_scolaire
            )
            await save_json_file(
                json_resp, self.log_folder + "get_messages_famille.json"
            )
        else:
            json_resp = await self.ed_client.get_messages(
                None, eleve.eleve_id, annee_scolaire
            )
            await save_json_file(
                json_resp, self.log_folder + f"{eleve.eleve_id}_get_messages_eleve.json"
            )

        if "data" not in json_resp:
            LOGGER.warning("get_messages: [%s]", json_resp)
            return None

        return json_resp["data"]["pagination"]

    async def get_homeworks_by_date(self, eleve: EDEleve, date: str) -> dict:
        """Get homeworks by date."""
        if FAKE_ON:
            json_resp = await load_json_file(
                self.test_folder + "test_homeworks_" + date + ".json"
            )
            return json_resp["data"]

        json_resp = await self.ed_client.get_homeworks_by_date(
            eleve.eleve_id,
            date,
        )
        await save_json_file(
            json_resp,
            self.log_folder + f"{eleve.eleve_id}_get_homeworks_by_date_{date}.json",
        )
        if "data" in json_resp:
            return json_resp["data"]
        LOGGER.warning("get_homeworks_by_date: [%s]", json_resp)
        return {}

    async def get_homeworks(self, eleve: EDEleve, decode_html: bool) -> list[Any]:
        """Get homeworks."""
        if FAKE_ON:
            json_resp = await load_json_file(self.test_folder + "test_homeworks.json")
        else:
            json_resp = await self.ed_client.get_homeworks(eleve_id=eleve.eleve_id)
            await save_json_file(
                json_resp,
                self.log_folder + f"{eleve.eleve_id}_get_homeworks.json",
            )

        homeworks = []
        if "data" not in json_resp:
            LOGGER.warning("get_homeworks: [%s]", json_resp)
        else:
            data = json_resp["data"]
            for key in data.keys():
                for homework_json in data[key]:
                    homeworks_by_date_json = await self.get_homeworks_by_date(
                        eleve, key
                    )
                    for matiere in homeworks_by_date_json["matieres"]:
                        if (
                            "aFaire" in matiere
                            and matiere["id"] == homework_json["idDevoir"]
                        ):
                            hw = self.get_homework(matiere, key, decode_html)
                            homeworks.append(hw)
            if homeworks is not None:
                homeworks.sort(key=operator.itemgetter("date"))

        return homeworks

    def get_homework(self, data: dict, pour_le: str, clean_content: bool) -> dict:
        """Get homework information."""
        if "contenu" in data["aFaire"]:
            contenu = base64.b64decode(data["aFaire"]["contenu"]).decode("utf-8")
        else:
            contenu = ""
        if clean_content:
            contenu = re.sub(CLEANR, "", contenu)
        return {
            "date": datetime.strptime(pour_le, "%Y-%m-%d"),
            "subject": data.get("matiere"),
            "short_description": contenu[0:HOMEWORK_DESC_MAX_LENGTH],
            "description": contenu,
            "done": data["aFaire"].get("effectue", False),
            "interrogation": data.get("interrogation", False),
        }

    async def get_grades_evaluations(
        self,
        eleve: EDEleve,
        annee_scolaire: str,
        grades_display: int = GRADES_TO_DISPLAY,
    ) -> dict:
        """Get grades."""
        if FAKE_ON:
            json_resp = await load_json_file(self.test_folder + "test_grades.json")
        else:
            json_resp = await self.ed_client.get_grades_evaluations(
                eleve_id=eleve.eleve_id,
                annee_scolaire=annee_scolaire,
            )
            await save_json_file(
                json_resp,
                self.log_folder + f"{eleve.eleve_id}_get_grades_evaluations.json",
            )

        if "data" not in json_resp:
            LOGGER.warning("get_grades_evaluations: [%s]", json_resp)
            return {}

        response = {}
        response["grades"] = []
        response["moyenne_generale"] = {}
        response["evaluations"] = []
        response["disciplines"] = []
        data = json_resp["data"]
        index1 = 0
        index2 = 0
        if "periodes" in data:
            data["periodes"].sort(key=operator.itemgetter("dateDebut"))
            for periode_json in data["periodes"]:
                if periode_json["cloture"]:
                    continue
                if (
                    "trimestre" not in periode_json["periode"].lower()
                    and "semestre" not in periode_json["periode"].lower()
                ):
                    continue
                if datetime.now() < datetime.strptime(
                    periode_json["dateDebut"], "%Y-%m-%d"
                ):
                    continue
                if datetime.now() > datetime.strptime(
                    periode_json["dateFin"], "%Y-%m-%d"
                ):
                    continue
                response["disciplines"] = get_disciplines_periode(periode_json)
                if "ensembleMatieres" in periode_json:
                    response["moyenne_generale"] = {
                        "moyenneGenerale": (
                            periode_json["ensembleMatieres"].get("moyenneGenerale")
                            or ""
                        ).replace(",", "."),
                        "moyenneClasse": (
                            periode_json["ensembleMatieres"].get("moyenneClasse") or ""
                        ).replace(",", "."),
                        "moyenneMin": (
                            periode_json["ensembleMatieres"].get("moyenneMin") or ""
                        ).replace(",", "."),
                        "moyenneMax": (
                            periode_json["ensembleMatieres"].get("moyenneMax") or ""
                        ).replace(",", "."),
                        "dateCalcul": (
                            periode_json["ensembleMatieres"].get("dateCalcul") or ""
                        ),
                    }
                break

        if "notes" in data:
            data["notes"].sort(key=operator.itemgetter("dateSaisie"))
            data["notes"].reverse()
            for grade_json in data["notes"]:
                if grade_json["noteSur"] == "0":
                    index1 += 1
                    if index1 > grades_display:
                        continue
                    evaluation = get_evaluation(grade_json)
                    response["evaluations"].append(evaluation)
                else:
                    index2 += 1
                    if index2 > grades_display:
                        continue
                    grade = get_grade(grade_json)
                    response["grades"].append(grade)
        return response

    async def get_vie_scolaire(self, eleve: EDEleve) -> dict:
        """Get vie scolaire (absences, retards, etc.)."""
        if FAKE_ON:
            json_resp = await load_json_file(
                self.test_folder + "test_vie_scolaire.json"
            )
        else:
            json_resp = await self.ed_client.get_vie_scolaire(
                eleve_id=eleve.eleve_id,
            )
            await save_json_file(
                json_resp,
                self.log_folder + f"{eleve.eleve_id}_get_vie_scolaire.json",
            )

        if "data" not in json_resp:
            LOGGER.warning("get_vie_scolaire: [%s]", json_resp)
            return {}

        response = {}
        response["absences"] = []
        response["retards"] = []
        response["sanctions"] = []
        response["encouragements"] = []
        data = json_resp["data"]
        index1 = 0
        index2 = 0
        if "absencesRetards" in data:
            data["absencesRetards"].sort(key=operator.itemgetter("date"))
            data["absencesRetards"].reverse()
            for data_json in data["absencesRetards"]:
                if data_json["typeElement"] == "Absence":
                    index1 += 1
                    if index1 > VIE_SCOLAIRE_TO_DISPLAY:
                        continue
                    absence = get_vie_scolaire_element(data_json)
                    response["absences"].append(absence)
                else:
                    index2 += 1
                    if index2 > VIE_SCOLAIRE_TO_DISPLAY:
                        continue
                    retard = get_vie_scolaire_element(data_json)
                    response["retards"].append(retard)

        index1 = 0
        index2 = 0
        if "sanctionsEncouragements" in data:
            data["sanctionsEncouragements"].sort(key=operator.itemgetter("date"))
            data["sanctionsEncouragements"].reverse()
            for data_json in data["sanctionsEncouragements"]:
                if data_json["typeElement"] == "Punition":
                    index1 += 1
                    if index1 > VIE_SCOLAIRE_TO_DISPLAY:
                        continue
                    sanction = get_vie_scolaire_element(data_json)
                    response["sanctions"].append(sanction)
                else:
                    index2 += 1
                    if index2 > VIE_SCOLAIRE_TO_DISPLAY:
                        continue
                    encouragement = get_vie_scolaire_element(data_json)
                    response["encouragements"].append(encouragement)

        return response

    async def get_lessons(
        self, eleve: EDEleve, date_debut: str, date_fin: str, lunch_break_time: time
    ) -> list[Any]:
        """Get lessons."""
        if FAKE_ON:
            json_resp = await load_json_file(self.test_folder + "test_lessons.json")
        else:
            json_resp = await self.ed_client.get_lessons(
                eleve_id=eleve.eleve_id,
                date_debut=date_debut,
                date_fin=date_fin,
            )
            await save_json_file(
                json_resp,
                self.log_folder + f"{eleve.eleve_id}_get_lessons.json",
            )

        response = []
        if "data" not in json_resp:
            LOGGER.warning("get_lessons: [%s]", json_resp)
        else:
            data = json_resp["data"]
            for lesson_json in data:
                response.append(get_lesson(lesson_json, lunch_break_time))
            if response is not None:
                response.sort(key=operator.itemgetter("start"))

        return response

    async def get_all_wallet_balances(self) -> dict | None:
        """Get all wallet balances from Ecole Directe."""
        if FAKE_ON:
            json_resp = await load_json_file(self.test_folder + "test_wallet.json")
        else:
            json_resp = await self.ed_client.get_all_wallet_balances()

        await save_json_file(
            json_resp,
            self.log_folder + "get_all_wallet_balances.json",
        )

        balances = {}
        if "data" in json_resp and "comptes" in json_resp["data"]:
            for compte in json_resp["data"]["comptes"]:
                if compte.get("id"):
                    compte_id = str(compte["id"])
                    if compte_id not in balances:
                        balances[compte_id] = []
                    balances[compte_id].append(
                        {
                            "solde": compte.get("solde"),
                            "libelle": compte.get("libelle"),
                        }
                    )
            return balances

        LOGGER.warning(
            "get_all_wallet_balances: No data found in response: [%s]", json_resp
        )
        return None

    async def get_sondages(self) -> dict:
        """Get sondages."""
        json_resp = await self.ed_client.get_sondages()
        await save_json_file(
            json_resp,
            self.log_folder + "get_sondages.json",
        )
        return json_resp

    async def get_formulaires(self, account_type: str, id_entity: str) -> list[Any]:
        """Get formulaires."""
        json_resp = await self.ed_client.get_formulaires(account_type, id_entity)
        await save_json_file(
            json_resp,
            self.log_folder + "get_formulaires.json",
        )

        response = []
        if "data" not in json_resp:
            LOGGER.warning("get_formulaires: [%s]", json_resp)
        else:
            data = json_resp["data"]
            for form_json in data:
                response.append(get_formulaire(form_json))

        return response

    async def get_classe(self, classe_id: str) -> None:
        """Get classe."""
        await self.ed_client.get_classe(classe_id=classe_id)


async def check_ecoledirecte_session(
    user: str, pwd: str, qcm_file_name: str, hass: HomeAssistant
) -> bool:
    """Check if credentials to Ecole Directe are ok."""
    try:
        async with EDSession(
            user, pwd, hass.config.config_dir + "/" + qcm_file_name, hass
        ) as session:
            await session.login()
    except QCMException:
        return True
    return session is not None


def get_grade(data: Any) -> dict:
    """Get grade information."""
    elements_programme = []
    if "elementsProgramme" in data:
        for element in data["elementsProgramme"]:
            elements_programme.append(get_competence(element))

    return {
        "date": data.get("date"),
        "subject": data.get("libelleMatiere"),
        "comment": data.get("devoir"),
        "grade": data.get("valeur"),
        "out_of": data.get("noteSur").replace(".", ","),
        "default_out_of": data.get("noteSur").replace(".", ","),
        "grade_out_of": data.get("valeur") + "/" + data.get("noteSur"),
        "coefficient": (data.get("coef") or "").replace(".", ","),
        "class_average": (data.get("moyenneClasse") or "").replace(".", ","),
        "max": str(data.get("maxClasse") or "").replace(".", ","),
        "min": str(data.get("minClasse") or "").replace(".", ","),
        "is_bonus": "",
        "is_optionnal": data.get("nonSignificatif"),
        "is_out_of_20": "",
        "date_saisie": data.get("dateSaisie"),
        "elements_programme": elements_programme,
    }


def get_disciplines_periode(data: Any) -> list:
    """Get periode information."""
    disciplines = []
    try:
        if "ensembleMatieres" in data and "disciplines" in data["ensembleMatieres"]:
            for discipline_json in data["ensembleMatieres"]["disciplines"]:
                if (
                    "codeSousMatiere" in discipline_json
                    and len(discipline_json["codeSousMatiere"]) > 0
                ):
                    continue
                discipline = {
                    "code": discipline_json.get("codeMatiere", "").lower(),
                    "name": discipline_json.get("discipline", "").lower(),
                    "moyenne": discipline_json.get("moyenne", "").replace(",", "."),
                    "moyenneClasse": discipline_json.get("moyenneClasse", "").replace(
                        ",", "."
                    ),
                    "moyenneMin": discipline_json.get("moyenneMin", "").replace(
                        ",", "."
                    ),
                    "moyenneMax": discipline_json.get("moyenneMax", "").replace(
                        ",", "."
                    ),
                    "appreciations": discipline_json.get("appreciations", ""),
                }
                disciplines.append(discipline)
    except Exception as ex:
        LOGGER.warning("get_periode: %s", ex)
        raise
    return disciplines


def get_evaluation(data: Any) -> dict:
    """Get evaluation information."""
    try:
        elements_programme = []
        if "elementsProgramme" in data:
            for element in data["elementsProgramme"]:
                elements_programme.append(element)

        return {
            "name": data.get("devoir"),
            "date": data.get("date"),
            "subject": data.get("libelleMatiere"),
            "acquisitions": [
                {
                    "name": acquisition.get("libelleCompetence"),
                    "abbreviation": acquisition.get("valeur"),
                    "level": acquisition.get("level"),
                }
                for acquisition in elements_programme
            ],
        }
    except Exception as ex:
        LOGGER.warning("get_evaluation: %s", ex)
        raise


def get_competence(data: Any) -> dict:
    """Get grade information."""
    valeur = data.get("valeur")
    match valeur:
        case "1":
            level = "Maîtrise insuffisante"
        case "2":
            level = "Maîtrise fragile"
        case "3":
            level = "Maîtrise satisfaisante"
        case "4":
            level = "Très bonne maîtrise"
        case _:
            level = "Unknown"

    return {
        "descriptif": data.get("descriptif"),
        "libelle_competence": data.get("libelleCompetence"),
        "valeur": valeur,
        "level": level,
    }


def get_vie_scolaire_element(viescolaire: Any) -> dict:
    """Vie scolaire format."""
    try:
        return {
            "date": viescolaire["date"],
            "type_element": viescolaire["typeElement"],
            "display_date": viescolaire["displayDate"],
            "justified": viescolaire["justifie"],
            "motif": viescolaire["motif"],
            "libelle": viescolaire["libelle"],
            "commentaire": viescolaire["commentaire"],
        }
    except Exception as ex:
        LOGGER.warning("Error: %s - format_viescolaire: %s", ex, viescolaire)
        return {}


def get_lesson(data: Any, lunch_break_time: time) -> dict:
    """Get lesson information."""
    start_date = datetime.strptime(data["start_date"], "%Y-%m-%d %H:%M")
    end_date = datetime.strptime(data["end_date"], "%Y-%m-%d %H:%M")
    return {
        "start": start_date,
        "end": end_date,
        "start_at": start_date.strftime("%Y-%m-%d %H:%M"),
        "end_at": end_date.strftime("%Y-%m-%d %H:%M"),
        "start_time": start_date.strftime("%H:%M"),
        "end_time": end_date.strftime("%H:%M"),
        "lesson": data["text"],
        "classroom": data["salle"],
        "canceled": data["isAnnule"],
        "background_color": data["color"],
        "teacher_name": data["prof"],
        "exempted": data["dispense"],
        "is_morning": start_date.time() < lunch_break_time,
        "is_afternoon": start_date.time() >= lunch_break_time,
    }


def get_formulaire(data: Any) -> dict:
    """Get formulaire."""
    return {
        "titre": data["titre"],
        "created": data["created"],
    }


def get_unique_id(data: str) -> str:
    """Get unique id."""
    return unidecode(data).lower().replace(" ", "_")
