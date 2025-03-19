"""Module to help communication with Ecole Directe API."""

import base64
from datetime import datetime
import json
import operator
from pathlib import Path
import re
from typing import Any
import urllib

from custom_components.ecole_directe.config_flow import InvalidAuthError
import requests

from homeassistant.components.persistent_notification import async_create

from .const import (
    DEBUG_ON,
    EDMFA,
    EDOK,
    EVENT_TYPE,
    GRADES_TO_DISPLAY,
    HOMEWORK_DESC_MAX_LENGTH,
    INTEGRATION_PATH,
    LOGGER,
    VIE_SCOLAIRE_TO_DISPLAY,
)

APIURL = "https://api.ecoledirecte.com/v3"
APIVERSION = "4.70.0"

# as per recommendation from @freylis, compile once only
CLEANR = re.compile("<.*?>")


def get_headers(token: str | None) -> dict:
    """Return headers needed from Ecole Directe API."""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "DNT": "1",
        "Host": "api.ecoledirecte.com",
        "Origin": "https://www.ecoledirecte.com",
        "Referer": "https://www.ecoledirecte.com/",
        "Sec-fetch-dest": "empty",
        "Sec-fetch-mode": "cors",
        "Sec-fetch-site": "same-site",
        "Sec-GPC": "1",
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    }
    if token is not None:
        headers["X-Token"] = token

    return headers


def get_response(token: str | None, url: str, payload: Any, file_path: str) -> dict:
    """Send a request to API and return a json if possible or raise an error."""
    if payload is None:
        payload = "data={}"

    LOGGER.debug("URL: [%s] - Payload: [%s]", url, payload)
    response = requests.post(url, data=payload, headers=get_headers(token), timeout=120)

    try:
        resp_json = response.json()
        with Path.open(
            file_path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(resp_json, f, ensure_ascii=False, indent=4)

    except Exception as ex:
        msg = f"Error with URL:[{url}]: {response.content}"
        raise RequestError(msg) from ex

    if "code" not in resp_json:
        msg = f"Error with URL:[{url}]: json:[{resp_json}]"
        raise RequestError(msg)

    if resp_json["code"] == EDMFA and token is None:
        LOGGER.debug("%s", resp_json)
        return resp_json

    if resp_json["code"] != EDOK:
        msg = (
            f"Error with URL:[{url}] - Code {resp_json['code']}: {resp_json['message']}"
        )
        raise RequestError(msg)

    LOGGER.debug("%s", resp_json)
    return resp_json


class RequestError(Exception):
    """Request error from API."""

    def __init__(self, message: str) -> None:
        """Initialize RequestError."""
        super().__init__(message)


class QCMError(Exception):
    """QCM error on double autentication from API."""

    def __init__(self, message: str) -> None:
        """Initialize QCMError."""
        super().__init__(message)


class EDSession:
    """Ecole Directe session with Token."""

    def __init__(self, data: Any) -> None:
        """Initialize EDSession."""
        self.token = data["token"]
        self.id = data["data"]["accounts"][0]["id"]
        self.identifiant = data["data"]["accounts"][0]["identifiant"]
        self._id_login = data["data"]["accounts"][0]["idLogin"]
        self.account_type = data["data"]["accounts"][0]["typeCompte"]
        self.modules = []
        for module in data["data"]["accounts"][0]["modules"]:
            if module["enable"]:
                self.modules.append(module["code"])
        self.eleves = []
        if self.account_type == "E":
            self.eleves.append(
                EDEleve(
                    None,
                    data["data"]["accounts"][0]["nomEtablissement"],
                    self.id,
                    data["data"]["accounts"][0]["prenom"],
                    data["data"]["accounts"][0]["nom"],
                    data["data"]["accounts"][0]["profile"]["classe"]["id"],
                    data["data"]["accounts"][0]["profile"]["classe"]["libelle"],
                    self.modules,
                )
            )
        elif "eleves" in data["data"]["accounts"][0]["profile"]:
            for eleve in data["data"]["accounts"][0]["profile"]["eleves"]:
                self.eleves.append(
                    EDEleve(eleve, data["data"]["accounts"][0]["nomEtablissement"])
                )


class EDEleve:
    """Student information."""

    def __init__(
        self,
        data=None,
        establishment=None,
        eleve_id=None,
        first_name=None,
        last_name=None,
        classe_id=None,
        classe_name=None,
        modules=None,
    ) -> None:
        """Initialize EDEleve."""
        if data is None:
            self.classe_id = classe_id
            self.classe_name = classe_name
            self.eleve_id = eleve_id
            self.eleve_lastname = last_name
            self.eleve_firstname = first_name
            self.modules = modules
            self.establishment = establishment
        else:
            if "classe" in data:
                self.classe_id = data["classe"]["id"]
                self.classe_name = data["classe"]["libelle"]
            self.eleve_id = data["id"]
            self.eleve_lastname = data["nom"]
            self.eleve_firstname = data["prenom"]
            self.establishment = establishment
            self.modules = []
            for module in data["modules"]:
                if module["enable"]:
                    self.modules.append(module["code"])

    def get_fullname_lower(self) -> str | None:
        """Student fullname lowercase."""
        return f"{re.sub('[^A-Za-z]', '_', self.eleve_firstname.lower())}_{
            re.sub('[^A-Za-z]', '_', self.eleve_lastname.lower())
        }"

    def get_fullname(self) -> str | None:
        """Student fullname."""
        return f"{self.eleve_firstname} {self.eleve_lastname}"


def check_ecoledirecte_session(data, config_path, hass) -> bool:
    """Check if credentials to Ecole Directe are ok."""
    try:
        session = get_ecoledirecte_session(data, config_path, hass)
        if session is None:
            raise InvalidAuthError
    except QCMError:
        return True

    return True


def get_ecoledirecte_session(data, config_path, hass) -> EDSession | None:
    """Function connecting to Ecole Directe."""
    try:
        payload = (
            'data={"identifiant":"'
            + urllib.parse.quote(data["username"], safe="")
            + '", "motdepasse":"'
            + urllib.parse.quote(data["password"], safe="")
            + '", "isRelogin": false}'
        )

        login = get_response(
            None,
            f"{APIURL}/login.awp?v={APIVERSION}",
            payload,
            config_path + INTEGRATION_PATH + "get_ecoledirecte_session.json",
        )

        # Si connexion initiale
        if login["code"] == EDMFA:
            with Path.open(
                config_path + "/" + data["qcm_filename"],
                encoding="utf-8",
            ) as f:
                qcm_json = json.load(f)

            try_login = 5

            while try_login > 0:
                # Obtenir le qcm de vérification et les propositions de réponse
                qcm = get_qcm_connexion(login["token"], config_path)
                question = base64.b64decode(qcm["question"]).decode("utf-8")

                if qcm_json is not None and question in qcm_json:
                    if len(qcm_json[question]) > 1:
                        try_login -= 1
                        continue
                    reponse = base64.b64encode(
                        bytes(qcm_json[question][0], "utf-8")
                    ).decode("ascii")
                    cn_et_cv = post_qcm_connexion(
                        login["token"], str(reponse), config_path
                    )
                    # Si le quiz a été raté
                    if not cn_et_cv:
                        LOGGER.warning(
                            "qcm raté pour la question [%s], vérifier le fichier %s. [%s]",
                            question,
                            data["qcm_filename"],
                            cn_et_cv,
                        )
                        continue
                    cn = cn_et_cv["cn"]
                    cv = cn_et_cv["cv"]
                    break
                rep = []
                propositions = qcm["propositions"]
                for proposition in propositions:
                    rep.append(base64.b64decode(proposition).decode("utf-8"))

                qcm_json[question] = rep

                with Path.open(
                    config_path + "/" + data["qcm_filename"],
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(qcm_json, f, ensure_ascii=False, indent=4)
                event_data = {
                    "device_id": "ED - " + data["username"],
                    "type": "new_qcm",
                    "question": question,
                }
                hass.bus.fire(EVENT_TYPE, event_data)

                if data["qcm_filename"]:
                    async_create(
                        hass,
                        "Vérifiez le fichier "
                        + data["qcm_filename"]
                        + ", et rechargez l'intégration Ecole Directe.",
                        title="Ecole Directe",
                    )
                try_login -= 1

            if try_login == 0:
                msg = "Vérifiez le fichier qcm.json, et rechargez l'intégration Ecole Directe."
                raise QCMError(msg)

            LOGGER.debug("cn: [%s] - cv: [%s]", cn, cv)

            payload = (
                'data={"identifiant":"'
                + urllib.parse.quote(data["username"], safe="")
                + '", "motdepasse":"'
                + urllib.parse.quote(data["password"], safe="")
                + '", "isRelogin": false, "fa": [{"cn": "'
                + cn
                + '", "cv": "'
                + cv
                + '"}]}'
            )

            # Renvoyer une requête de connexion avec la double-authentification réussie
            login = get_response(
                None,
                f"{APIURL}/login.awp?v={APIVERSION}",
                payload,
                config_path + INTEGRATION_PATH + "get_ecoledirecte_session2.json",
            )

        LOGGER.info(
            "Connection OK - identifiant: [{%s}]",
            login["data"]["accounts"][0]["identifiant"],
        )
        return EDSession(login)
    except QCMError as err:
        LOGGER.warning(err)
        raise
    except Exception as err:
        LOGGER.critical(err)
        return None


def get_qcm_connexion(token, config_path):
    """Obtenir le QCM donné lors d'une connexion à partir d'un nouvel appareil."""
    json_resp = get_response(
        token,
        f"{APIURL}/connexion/doubleauth.awp?verbe=get&v={APIVERSION}",
        None,
        config_path + INTEGRATION_PATH + "get_qcm_connexion.json",
    )

    if "data" in json_resp:
        return json_resp["data"]
    LOGGER.warning("get_qcm_connexion: [%s]", json_resp)
    return None


def post_qcm_connexion(token, proposition, config_path):
    """Renvoyer la réponse du QCM donné."""
    json_resp = get_response(
        token,
        f"{APIURL}/connexion/doubleauth.awp?verbe=post&v={APIVERSION}",
        f'data={{"choix": "{proposition}"}}',
        config_path + INTEGRATION_PATH + "post_qcm_connexion.json",
    )

    if "data" in json_resp:
        return json_resp["data"]
    LOGGER.warning("post_qcm_connexion: [%s]", json_resp)
    return None


def get_messages(token, id, eleve, annee_scolaire, config_path):
    """Get messages from Ecole Directe."""
    if DEBUG_ON:
        # Opening JSON file
        f = open(config_path + INTEGRATION_PATH + "test/test_messages.json")
        json_resp = json.load(f)
    else:
        payload = (
            'data={"anneeMessages":"'
            + urllib.parse.quote(annee_scolaire, safe="")
            + '"}'
        )
        if eleve is None:
            json_resp = get_response(
                token,
                f"{APIURL}/familles/{id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
                payload,
                config_path + INTEGRATION_PATH + "get_messages_famille.json",
            )
        else:
            json_resp = get_response(
                token,
                f"{APIURL}/eleves/{eleve.eleve_id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
                payload,
                f"{config_path + INTEGRATION_PATH}{eleve.eleve_id}_get_messages_eleve.json",
            )

    if "data" not in json_resp:
        LOGGER.warning("get_messages: [%s]", json_resp)
        return None

    return json_resp["data"]["pagination"]


def get_homeworks_by_date(token, eleve, date, config_path):
    """Get homeworks by date."""
    if DEBUG_ON:
        # Opening JSON file
        f = open(
            config_path + INTEGRATION_PATH + "test/test_homeworks_" + date + ".json"
        )
        data = json.load(f)
        return data["data"]

    json_resp = get_response(
        token,
        f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp?verbe=get&v={APIVERSION}",
        None,
        f"{config_path + INTEGRATION_PATH}{eleve.eleve_id}_get_homeworks_by_date_{date}.json",
    )
    if "data" in json_resp:
        return json_resp["data"]
    LOGGER.warning("get_homeworks_by_date: [%s]", json_resp)
    return None


def get_homeworks(token, eleve, config_path, decode_html):
    """Get homeworks."""
    if DEBUG_ON:
        # Opening JSON file
        f = open(config_path + INTEGRATION_PATH + "test/test_homeworks.json")
        json_resp = json.load(f)
    else:
        json_resp = get_response(
            token,
            f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte.awp?verbe=get&v={APIVERSION}",
            None,
            f"{config_path + INTEGRATION_PATH}{eleve.eleve_id}_get_homeworks.json",
        )

    if "data" not in json_resp:
        LOGGER.warning("get_homeworks: [%s]", json_resp)
        return None

    data = json_resp["data"]
    homeworks = []
    for key in data.keys():
        for idx, homework_json in enumerate(data[key]):
            homeworks_by_date_json = get_homeworks_by_date(
                token, eleve, key, config_path
            )
            for matiere in homeworks_by_date_json["matieres"]:
                if "aFaire" in matiere:
                    if matiere["id"] == homework_json["idDevoir"]:
                        hw = get_homework(matiere, key, decode_html)
                        homeworks.append(hw)
    if homeworks is not None:
        homeworks.sort(key=operator.itemgetter("date"))

    return homeworks


def get_homework(data, pour_le, clean_content):
    """Get homework information."""
    if "contenu" in data["aFaire"]:
        contenu = base64.b64decode(data["aFaire"]["contenu"]).decode("utf-8")
    else:
        contenu = ""
    if clean_content:
        contenu = clean_html(contenu)
    return {
        "date": pour_le,
        "subject": data.get("matiere"),
        "short_description": contenu[0:HOMEWORK_DESC_MAX_LENGTH],
        "description": contenu,
        "done": data["aFaire"].get("effectue"),
        "background_color": "#FFFFFF",
        "files": [],
        "interrogation": data["aFaire"].get("interrogation"),
    }


def clean_html(raw_html):
    """Clean html."""
    cleantext = re.sub(CLEANR, "", raw_html)
    return cleantext


def get_grades_evaluations(
    token, eleve, annee_scolaire, config_path, grades_dispaly=GRADES_TO_DISPLAY
):
    """Get grades."""
    if DEBUG_ON:
        # Opening JSON file
        f = open(config_path + INTEGRATION_PATH + "test/test_grades.json")
        json_resp = json.load(f)
    else:
        json_resp = get_response(
            token,
            f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp?verbe=get&v={APIVERSION}",
            f"data={{'anneeScolaire': '{annee_scolaire}'}}",
            f"{config_path + INTEGRATION_PATH}{eleve.eleve_id}_get_grades_evaluations.json",
        )

    if "data" not in json_resp:
        LOGGER.warning("get_grades_evaluations: [%s]", json_resp)
        return None

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
            if datetime.now() > datetime.strptime(periode_json["dateFin"], "%Y-%m-%d"):
                continue
            response["disciplines"] = get_disciplines_periode(periode_json)
            if "ensembleMatieres" in periode_json:
                response["moyenne_generale"] = {
                    "moyenneGenerale": (
                        periode_json["ensembleMatieres"].get("moyenneGenerale") or ""
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
                if index1 > grades_dispaly:
                    continue
                evaluation = get_evaluation(grade_json)
                response["evaluations"].append(evaluation)
            else:
                index2 += 1
                if index2 > grades_dispaly:
                    continue
                grade = get_grade(grade_json)
                response["grades"].append(grade)
    return response


def get_grade(data):
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


def get_disciplines_periode(data):
    """Get periode information."""
    try:
        disciplines = []
        if "ensembleMatieres" in data:
            if "disciplines" in data["ensembleMatieres"]:
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
                        "moyenneClasse": discipline_json.get(
                            "moyenneClasse", ""
                        ).replace(",", "."),
                        "moyenneMin": discipline_json.get("moyenneMin", "").replace(
                            ",", "."
                        ),
                        "moyenneMax": discipline_json.get("moyenneMax", "").replace(
                            ",", "."
                        ),
                        "appreciations": discipline_json.get("appreciations", ""),
                    }
                    disciplines.append(discipline)
        return disciplines
    except Exception as ex:
        LOGGER.warning("get_periode: %s", ex)
        raise


def get_evaluation(data):
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


def get_competence(data):
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


def get_vie_scolaire(token, eleve, config_path):
    """Get vie scolaire (absences, retards, etc.)."""
    if DEBUG_ON:
        # Opening JSON file
        f = open(config_path + INTEGRATION_PATH + "test/test_vie_scolaire.json")
        json_resp = json.load(f)
    else:
        json_resp = get_response(
            token,
            f"{APIURL}/eleves/{eleve.eleve_id}/viescolaire.awp?verbe=get&v={APIVERSION}",
            "data={}",
            f"{config_path + INTEGRATION_PATH}{eleve.eleve_id}_get_vie_scolaire.json",
        )

    if "data" not in json_resp:
        LOGGER.warning("get_vie_scolaire: [%s]", json_resp)
        return None

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


def get_vie_scolaire_element(viescolaire) -> dict:
    """Vie scolaire format"""
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


def get_lessons(token, eleve, date_debut, date_fin, config_path, lunch_break_time):
    """Get lessons."""
    if DEBUG_ON:
        # Opening JSON file
        f = open(config_path + INTEGRATION_PATH + "test/test_lessons.json")
        json_resp = json.load(f)
    else:
        json_resp = get_response(
            token,
            f"{APIURL}/E/{eleve.eleve_id}/emploidutemps.awp?verbe=get&v={APIVERSION}",
            f"data={{'dateDebut': '{date_debut}','dateFin': '{
                date_fin
            }','avecTrous': false}}",
            f"{config_path + INTEGRATION_PATH}{eleve.eleve_id}_get_lessons.json",
        )

    if "data" not in json_resp:
        LOGGER.warning("get_lessons: [%s]", json_resp)
        return None

    response = []
    data = json_resp["data"]
    for lesson_json in data:
        lesson = get_lesson(lesson_json, lunch_break_time)
        if not lesson["canceled"]:
            response.append(lesson)
    if response is not None:
        response.sort(key=operator.itemgetter("start"))

    return response


def get_lesson(data, lunch_break_time):
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


def get_sondages(token, config_path):
    """Get sondages."""
    return get_response(
        token,
        f"{APIURL}/rdt/sondages.awp?v={APIVERSION}",
        None,
        config_path + INTEGRATION_PATH + "get_sondages.json",
    )


def get_formulaires(token, account_type, id_entity, config_path):
    """Get formulaires."""
    payload = (
        'data={"typeEntity": "' + account_type + '","idEntity":' + str(id_entity) + "}"
    )
    json_resp = get_response(
        token,
        f"{APIURL}/edforms.awp?verbe=list&v={APIVERSION}",
        payload,
        config_path + INTEGRATION_PATH + "get_formulaires.json",
    )
    if "data" not in json_resp:
        LOGGER.warning("get_formulaires: [%s]", json_resp)
        return None

    response = []
    data = json_resp["data"]
    for form_json in data:
        response.append(get_formulaire(form_json))

    return response


def get_formulaire(data):
    """Get formulaire."""
    return {
        "titre": data["titre"],
        "created": data["created"],
    }


def get_classe(token, classe_id, config_path):
    """Get classe."""
    json_resp = get_response(
        token,
        f"{APIURL}/Classes/{classe_id}/viedelaclasse.awp?verbe=get&v={APIVERSION}",
        "data={}",
        f"{config_path + INTEGRATION_PATH}get_classe_{classe_id}.json",
    )
    LOGGER.warning("get_classe: [%s]", json_resp)

    json_resp = get_response(
        token,
        f"{APIURL}/R/{classe_id}/viedelaclasse.awp?verbe=get&v={APIVERSION}",
        "data={}",
        f"{config_path + INTEGRATION_PATH}get_classeV2_{classe_id}.json",
    )
    LOGGER.warning("get_classeV2: [%s]", json_resp)
