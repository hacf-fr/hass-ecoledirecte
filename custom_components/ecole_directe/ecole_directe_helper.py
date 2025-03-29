"""Module to help communication with Ecole Directe API."""

import base64
from datetime import datetime
import json
import operator
from pathlib import Path
import re
from typing import Any
import urllib
from urllib.parse import urlparse

import requests

from homeassistant.components.persistent_notification import async_create
from homeassistant.core import HomeAssistant

from .const import (
    FAKE_ON,
    EVENT_TYPE,
    GRADES_TO_DISPLAY,
    HOMEWORK_DESC_MAX_LENGTH,
    INTEGRATION_PATH,
    LOGGER,
    VIE_SCOLAIRE_TO_DISPLAY,
)

APIURL = "https://api.ecoledirecte.com/v3"
APIVERSION = "4.75.0"

# as per recommendation from @freylis, compile once only
CLEANR = re.compile("<.*?>")


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
    """Ecole Directe session with Token and cookie."""

    def __init__(
        self,
        user: str,
        pwd: str,
        qcm: str,
        hass: HomeAssistant,
    ) -> None:
        """Save some information needed to login the session."""
        self.hass = hass
        self.username = user
        self.password = pwd
        self.qcm = qcm
        self.log_folder = self.hass.config.config_dir + INTEGRATION_PATH + "logs/"
        Path(self.log_folder).mkdir(parents=True, exist_ok=True)
        self.loginUrl = f"{APIURL}/login.awp"

        self.full_login_flow()

    def full_login_flow(self) -> None:
        """Login to a session."""
        self.session: requests.Session = requests.Session()
        self.session.headers.update({"accept": "application/json, text/plain, */*"})
        self.session.headers.update({"accept-encoding": "gzip, deflate, br, zstd"})
        self.session.headers.update({"accept-language": "fr-FR,fr;q=0.9"})
        self.session.headers.update({"Connection": "keep-alive"})
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded"
        })
        self.session.headers.update({"dnt": "1"})
        self.session.headers.update({"Origin": "https://www.ecoledirecte.com"})
        self.session.headers.update({"priority": "1"})
        self.session.headers.update({"Referer": "https://www.ecoledirecte.com/"})
        self.session.headers.update({
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"'
        })
        self.session.headers.update({"sec-ch-ua-mobile": "?0"})
        self.session.headers.update({"sec-ch-ua-platform": "Windows"})
        self.session.headers.update({"Sec-fetch-dest": ""})
        self.session.headers.update({"accept": "empty"})
        self.session.headers.update({"Sec-fetch-mode": "cors"})
        self.session.headers.update({"Sec-fetch-site": "same-site"})
        self.session.headers.update({
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        })

        try:
            login = self.login(None, None)

            # Si connexion initiale
            if login["code"] == 250:
                with Path(self.hass.config.config_dir + "/" + self.qcm).open(
                    "r",
                    encoding="utf-8",
                ) as fp:
                    qcm_json = json.load(fp)

                try_login = 5

                while try_login > 0:
                    # Obtenir le qcm de vérification et les propositions de réponse
                    qcm = self.get_qcm_connexion()
                    question = base64.b64decode(qcm["question"]).decode("utf-8")

                    if qcm_json is not None and question in qcm_json:
                        if len(qcm_json[question]) > 1:
                            try_login -= 1
                            continue
                        reponse = base64.b64encode(
                            bytes(qcm_json[question][0], "utf-8")
                        ).decode("ascii")
                        cn_et_cv = self.post_qcm_connexion(
                            str(reponse),
                        )
                        # Si le quiz a été raté
                        if not cn_et_cv:
                            LOGGER.warning(
                                "qcm raté pour la question [%s], vérifier le fichier %s. [%s]",
                                question,
                                self.qcm,
                                cn_et_cv,
                            )
                            continue
                        cn = cn_et_cv["cn"]
                        cv = cn_et_cv["cv"]
                        break
                    else:
                        rep = []
                        propositions = qcm["propositions"]
                        for proposition in propositions:
                            rep.append(base64.b64decode(proposition).decode("utf-8"))

                        qcm_json[question] = rep

                        with Path(self.hass.config.config_dir + "/" + self.qcm).open(
                            "w",
                            encoding="utf-8",
                        ) as f:
                            json.dump(qcm_json, f, ensure_ascii=False, indent=4)
                        event_data = {
                            "device_id": "ED - " + self.username,
                            "type": "new_qcm",
                            "question": question,
                        }
                        self.hass.bus.fire(EVENT_TYPE, event_data)

                        if self.qcm:
                            async_create(
                                self.hass,
                                "Vérifiez le fichier "
                                + self.qcm
                                + ", et rechargez l'intégration Ecole Directe.",
                                title="Ecole Directe",
                            )
                    try_login -= 1

                if try_login == 0:
                    raise QCMError(
                        "Vérifiez le fichier qcm.json, et rechargez l'intégration Ecole Directe."
                    )

                LOGGER.debug("cn: [%s] - cv: [%s]", cn, cv)

                # Renvoyer une requête de connexion avec la double-authentification réussie
                login = self.login(cn, cv)

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
                            None,
                            self.data["accounts"][0]["nomEtablissement"],
                            self.id,
                            self.data["accounts"][0]["prenom"],
                            self.data["accounts"][0]["nom"],
                            self.data["accounts"][0]["profile"]["classe"]["id"],
                            self.data["accounts"][0]["profile"]["classe"]["libelle"],
                            self.modules,
                        )
                    )
                elif "eleves" in self.data["accounts"][0]["profile"]:
                    for eleve in self.data["accounts"][0]["profile"]["eleves"]:
                        self.eleves.append(
                            EDEleve(
                                eleve,
                                self.data["accounts"][0]["nomEtablissement"],
                            )
                        )

        except QCMError as err:
            LOGGER.warning(err)
            raise
        except Exception as err:
            LOGGER.critical(err)

    def login(self, cn: str | None, cv: str | None) -> Any:
        """Login to a session."""
        # first call to get a cookie
        if "x-gtk" in self.session.headers:
            self.session.headers.pop("x-gtk")
        response = self.session.get(
            f"{APIURL}/login.awp",
            params={"v": APIVERSION, "gtk": 1},
            data=None,
            timeout=120,
        )

        cookies = self.session.cookies.get_dict()
        if "GTK" in cookies:
            self.session.headers.update({"x-gtk": cookies["GTK"]})

        if cn is not None and cv is not None:
            payload = (
                'data={"identifiant":"'
                + self.username
                + '", "motdepasse":"'
                + self.password
                + '", "isRelogin": false, "cn":"'
                + cn
                + '", "cv":"'
                + cv
                + '", "uuid": "", "fa": [{"cn": "'
                + cn
                + '", "cv": "'
                + cv
                + '"}]}'
            )
            file_name = self.log_folder + "post_login2.json"
        else:
            payload = (
                'data={"identifiant":"'
                + self.username
                + '", "motdepasse":"'
                + self.password
                + '", "isRelogin": false}'
            )
            file_name = self.log_folder + "post_login.json"
        # Post credentials to get a token
        response = self.session.post(
            f"{APIURL}/login.awp",
            params={"v": APIVERSION},
            data=payload,
            timeout=120,
        )

        login = response.json()
        with Path(file_name).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(login, f, ensure_ascii=False, indent=4)

        self.token = response.headers["x-token"]
        self.session.headers.update({"x-token": self.token})
        return login

    def get_response(self, is_get: bool, url, params, payload, file_name) -> Any:
        """Send a request to API and return a json if possible or raise an error."""
        if is_get:
            LOGGER.debug(
                "URL: [%s] - GET - params: [%s] - Payload: [%s] - file_name: [%s]",
                url,
                params,
                payload,
                file_name,
            )
            response = self.session.get(url, params=params, data=payload, timeout=120)
        else:
            if payload is None:
                payload = "data={}"
            LOGGER.debug(
                "URL: [%s] - POST - params: [%s] - Payload: [%s] - file_name: [%s]",
                url,
                params,
                payload,
                file_name,
            )
            response = self.session.post(
                url,
                params=params,
                data=payload,
                timeout=120,
            )

        try:
            resp_json = response.json()
            with Path(self.log_folder + file_name).open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(resp_json, f, ensure_ascii=False, indent=4)

        except Exception as ex:
            raise RequestError(f"Error with URL:[{url}]: {response.content}") from ex

        if "code" not in resp_json:
            raise RequestError(f"Error with URL:[{url}]: json:[{resp_json}]")

        if resp_json["code"] == 250:
            LOGGER.debug("%s", resp_json)
            return resp_json

        if resp_json["code"] != 200:
            raise RequestError(
                f"Error with URL:[{url}] - Code {resp_json['code']}: {resp_json['message']}"
            )

        LOGGER.debug("%s", resp_json)
        return resp_json

    def get_qcm_connexion(self) -> dict:
        """Obtenir le QCM donné lors d'une connexion à partir d'un nouvel appareil."""
        response = self.session.post(
            url=f"{APIURL}/connexion/doubleauth.awp",
            params={"verbe": "get", "v": APIVERSION},
            data="data={}",
            timeout=120,
        )
        try:
            json_resp = response.json()
            with open(
                self.log_folder + "get_qcm_connexion.json",
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(json_resp, f, ensure_ascii=False, indent=4)

        except Exception as ex:
            raise RequestError(
                f"Error with URL:[{f'{APIURL}/connexion/doubleauth.awp'}]: {response.content}"
            ) from ex

        if json_resp["code"] != 200:
            LOGGER.warning("get_qcm_connexion: [%s]", json_resp)
            raise QCMError(json_resp)

        if "data" in json_resp:
            self.token = response.headers["x-token"]
            self.session.headers.update({"x-token": self.token})
            return json_resp["data"]

        LOGGER.warning("get_qcm_connexion: [%s]", json_resp)
        raise QCMError(json_resp)

    def post_qcm_connexion(self, proposition) -> dict:
        """Renvoyer la réponse du QCM donné."""
        response = self.session.post(
            url=f"{APIURL}/connexion/doubleauth.awp",
            params={"verbe": "post", "v": APIVERSION},
            data=f'data={{"choix": "{proposition}"}}',
            timeout=120,
        )
        json_resp = response.json()
        with open(
            self.log_folder + "post_qcm_connexion.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(json_resp, f, ensure_ascii=False, indent=4)

        if "data" in json_resp:
            self.token = response.headers["x-token"]
            LOGGER.debug("post_qcm_connexion token: %s", self.token)
            self.session.headers.update({"x-token": self.token})
            return json_resp["data"]
        LOGGER.warning("post_qcm_connexion: [%s]", json_resp)
        raise QCMError(json_resp)

    def get_messages(self, id, eleve, annee_scolaire, config_path):
        """Get messages from Ecole Directe"""

        if FAKE_ON:
            # Opening JSON file
            f = open(config_path + INTEGRATION_PATH + "test/test_messages.json")
            json_resp = json.load(f)
        else:
            payload = 'data={"anneeMessages":"' + annee_scolaire + '"}'
            if eleve is None:
                json_resp = self.get_response(
                    is_get=False,
                    url=f"{APIURL}/familles/{id}/messages.awp",
                    params={
                        "force": "false",
                        "typeRecuperation": "received",
                        "idClasseur": "0",
                        "orderBy": "date",
                        "order": "desc",
                        "query": "",
                        "onlyRead": "",
                        "page": "0",
                        "itemsPerPage": "100",
                        "getAll": "0",
                        "verbe": "get",
                        "v": APIVERSION,
                    },
                    payload=payload,
                    file_name="get_messages_famille.json",
                )
            else:
                json_resp = self.get_response(
                    is_get=False,
                    url=f"{APIURL}/eleves/{eleve.eleve_id}/messages.awp",
                    payload=payload,
                    params={
                        "force": "false",
                        "typeRecuperation": "received",
                        "idClasseur": "0",
                        "orderBy": "date",
                        "order": "desc",
                        "query": "",
                        "onlyRead": "",
                        "page": "0",
                        "itemsPerPage": "100",
                        "getAll": "0",
                        "verbe": "get",
                        "v": APIVERSION,
                    },
                    file_name=f"{eleve.eleve_id}_get_messages_eleve.json",
                )

        if "data" not in json_resp:
            LOGGER.warning("get_messages: [%s]", json_resp)
            return None

        return json_resp["data"]["pagination"]

    def get_homeworks_by_date(self, eleve, date, config_path) -> dict:
        """get homeworks by date."""
        if FAKE_ON:
            # Opening JSON file
            f = open(
                config_path + INTEGRATION_PATH + "test/test_homeworks_" + date + ".json"
            )
            data = json.load(f)
            return data["data"]

        json_resp = self.get_response(
            is_get=False,
            url=f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload=None,
            file_name=f"{eleve.eleve_id}_get_homeworks_by_date_{date}.json",
        )
        if "data" in json_resp:
            return json_resp["data"]
        LOGGER.warning("get_homeworks_by_date: [%s]", json_resp)
        return {}

    def get_homeworks(self, eleve, config_path, decode_html):
        """get homeworks."""
        if FAKE_ON:
            # Opening JSON file
            f = open(config_path + INTEGRATION_PATH + "test/test_homeworks.json")
            json_resp = json.load(f)
        else:
            json_resp = self.get_response(
                is_get=False,
                url=f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte.awp",
                params={"verbe": "get", "v": APIVERSION},
                payload=None,
                file_name=f"{eleve.eleve_id}_get_homeworks.json",
            )

        if "data" not in json_resp:
            LOGGER.warning("get_homeworks: [%s]", json_resp)
            return None

        data = json_resp["data"]
        homeworks = []
        for key in data.keys():
            for idx, homework_json in enumerate(data[key]):
                homeworks_by_date_json = self.get_homeworks_by_date(
                    eleve, key, config_path
                )
                for matiere in homeworks_by_date_json["matieres"]:
                    if "aFaire" in matiere:
                        if matiere["id"] == homework_json["idDevoir"]:
                            hw = self.get_homework(matiere, key, decode_html)
                            homeworks.append(hw)
        if homeworks is not None:
            homeworks.sort(key=operator.itemgetter("date"))

        return homeworks

    def get_homework(self, data, pour_le, clean_content):
        """get homework information"""

        if "contenu" in data["aFaire"]:
            contenu = base64.b64decode(data["aFaire"]["contenu"]).decode("utf-8")
        else:
            contenu = ""
        if clean_content:
            contenu = re.sub(CLEANR, "", contenu)
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

    def get_grades_evaluations(
        self,
        eleve,
        annee_scolaire,
        config_path,
        grades_dispaly=GRADES_TO_DISPLAY,
    ):
        """Get grades."""
        if FAKE_ON:
            # Opening JSON file
            f = open(config_path + INTEGRATION_PATH + "test/test_grades.json")
            json_resp = json.load(f)
        else:
            json_resp = self.get_response(
                is_get=False,
                url=f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp",
                params={"verbe": "get", "v": APIVERSION},
                payload=f"data={{'anneeScolaire': '{annee_scolaire}'}}",
                file_name=f"{eleve.eleve_id}_get_grades_evaluations.json",
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
                if periode_json["cloture"] == True:
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

    def get_vie_scolaire(self, eleve, config_path):
        """get vie scolaire (absences, retards, etc.)"""

        if FAKE_ON:
            # Opening JSON file
            f = open(config_path + INTEGRATION_PATH + "test/test_vie_scolaire.json")
            json_resp = json.load(f)
        else:
            json_resp = self.get_response(
                is_get=False,
                url=f"{APIURL}/eleves/{eleve.eleve_id}/viescolaire.awp",
                params={"verbe": "get", "v": APIVERSION},
                payload="data={}",
                file_name=f"{eleve.eleve_id}_get_vie_scolaire.json",
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

    def get_lessons(self, eleve, date_debut, date_fin, config_path, lunch_break_time):
        """get lessons"""

        if FAKE_ON:
            # Opening JSON file
            f = open(config_path + INTEGRATION_PATH + "test/test_lessons.json")
            json_resp = json.load(f)
        else:
            json_resp = self.get_response(
                is_get=False,
                url=f"{APIURL}/E/{eleve.eleve_id}/emploidutemps.awp",
                params={"verbe": "get", "v": APIVERSION},
                payload=f"data={{'dateDebut': '{date_debut}','dateFin': '{
                    date_fin
                }','avecTrous': false}}",
                file_name=f"{eleve.eleve_id}_get_lessons.json",
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

    def get_sondages(self):
        """Get sondages"""

        return self.get_response(
            is_get=True,
            url=f"{APIURL}/rdt/sondages.awp?v={APIVERSION}",
            params={"v": APIVERSION},
            payload=None,
            file_name="get_sondages.json",
        )

    def get_formulaires(self, account_type, id_entity):
        """Get formulaires"""

        payload = (
            'data={"typeEntity": "'
            + account_type
            + '","idEntity":'
            + str(id_entity)
            + "}"
        )
        json_resp = self.get_response(
            is_get=False,
            url=f"{APIURL}/edforms.awp",
            params={"verbe": "list", "v": APIVERSION},
            payload=payload,
            file_name="get_formulaires.json",
        )
        if "data" not in json_resp:
            LOGGER.warning("get_formulaires: [%s]", json_resp)
            return None

        response = []
        data = json_resp["data"]
        for form_json in data:
            response.append(get_formulaire(form_json))

        return response

    def get_classe(self, classe_id):
        """Get classe"""

        json_resp = self.get_response(
            is_get=True,
            url=f"{APIURL}/Classes/{classe_id}/viedelaclasse.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
            file_name=f"get_classe_{classe_id}.json",
        )
        LOGGER.warning("get_classe: [%s]", json_resp)

        json_resp = self.get_response(
            is_get=True,
            url=f"{APIURL}/R/{classe_id}/viedelaclasse.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
            file_name=f"get_classeV2_{classe_id}.json",
        )
        LOGGER.warning("get_classeV2: [%s]", json_resp)

        return None


class EDEleve:
    """Student information."""

    def __init__(
        self,
        data: Any | None=None,
        establishment: Any | None=None,
        eleve_id: Any | None =None,
        first_name: str | None = None,
        last_name: str | None = None,
        classe_id: str | None = None,
        classe_name: str | None = None,
        modules: list = [],
    )-> None:
        """Initialize EDEleve."""
        if data is None:
            self.classe_id = classe_id
            self.classe_name: str = str({classe_name: ""})
            self.eleve_id = eleve_id
            self.eleve_lastname: str = str({last_name: ""})
            self.eleve_firstname: str = str({first_name: ""})
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


def check_ecoledirecte_session(data: Any, config_path: Any, hass: Any) -> bool:
    """Check if credentials to Ecole Directe are ok."""
    try:
        session = get_ecoledirecte_session(data, config_path, hass)
        if session is None:
            raise InvalidAuthError
    except QCMError:
        return True

    return True


def get_ecoledirecte_session(user, pwd, qcm, hass: HomeAssistant) -> EDSession | None:
    """Return ecole directe session connecting to Ecole Directe."""
    try:
        return EDSession(user, pwd, qcm, hass)
    except QCMError:
        raise
    except Exception as err:
        LOGGER.critical(err)
        return None


def get_grade(data):
    """get grade information"""

    elements_programme = []
    if "elementsProgramme" in data:
        elements_programme = [
            get_competence(element) for element in data["elementsProgramme"]
        ]

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


def get_disciplines_periode(data: Any) -> dict:
    """Get periode information."""
    try:
        disciplines = []
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
    else:
        return disciplines


def get_evaluation(data: Any) -> dict:
    """Get evaluation information."""
    try:
        elements_programme = []
        if "elementsProgramme" in data:
            elements_programme = [
                get_competence(element) for element in data["elementsProgramme"]
            ]

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


def get_vie_scolaire_element(viescolaire) -> dict:
    """vie scolaire format"""
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


def get_lesson(data, lunch_break_time):
    """get lesson information"""

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


def get_formulaire(data):
    """Get formulaire"""
    return {
        "titre": data["titre"],
        "created": data["created"],
    }
