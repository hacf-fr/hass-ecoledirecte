"""Module to help communication with Ecole Directe API"""

from datetime import datetime
import json
import operator
import re
import logging
import urllib
import base64
import requests

from .const import (
    VIE_SCOLAIRE_TO_DISPLAY,
    EVENT_TYPE,
    GRADES_TO_DISPLAY,
    INTEGRATION_PATH,
)

_LOGGER = logging.getLogger(__name__)

APIURL = "https://api.ecoledirecte.com/v3"
APIVERSION = "4.56.0"


def get_response(token, url, payload, file_path):
    """send a request to API and return a json if possible or raise an error"""

    if payload is None:
        payload = "data={}"

    _LOGGER.debug("URL: [%s] - Payload: [%s]", url, payload)
    response = requests.post(url, data=payload, headers=get_headers(token), timeout=120)

    try:
        resp_json = response.json()
        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(resp_json, f, ensure_ascii=False, indent=4)

    except Exception as ex:
        raise RequestError(f"Error with URL:[{url}]: {response.content}") from ex

    if "code" not in resp_json:
        raise RequestError(f"Error with URL:[{url}]: json:[{resp_json}]")

    if resp_json["code"] == 250 and token is None:
        _LOGGER.debug("%s", resp_json)
        return resp_json

    if resp_json["code"] != 200:
        raise RequestError(
            f"Error with URL:[{url}] - Code {resp_json["code"]}: {resp_json["message"]}"
        )

    _LOGGER.debug("%s", resp_json)
    return resp_json


class RequestError(Exception):
    """Request error from API"""

    def __init__(self, message):
        super(RequestError, self).__init__(message)


class QCMError(Exception):
    """QCM error on double autentication from API"""

    def __init__(self, message):
        super(QCMError, self).__init__(message)


class EDSession:
    """Ecole Directe session with Token"""

    def __init__(self, data):
        self.token = data["token"]
        self.id = data["data"]["accounts"][0]["id"]
        self.identifiant = data["data"]["accounts"][0]["identifiant"]
        self._id_login = data["data"]["accounts"][0]["idLogin"]
        self._account_type = data["data"]["accounts"][0]["typeCompte"]
        self.modules = []
        for module in data["data"]["accounts"][0]["modules"]:
            if module["enable"]:
                self.modules.append(module["code"])
        self.eleves = []
        if self._account_type == "E":
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
        else:
            if "eleves" in data["data"]["accounts"][0]["profile"]:
                for eleve in data["data"]["accounts"][0]["profile"]["eleves"]:
                    self.eleves.append(
                        EDEleve(eleve, data["data"]["accounts"][0]["nomEtablissement"])
                    )


class EDEleve:
    """Student information"""

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
    ):
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
        """Student fullname lowercase"""
        return f"{re.sub("[^A-Za-z]", "_",
                         self.eleve_firstname.lower())
                         }_{
                             re.sub("[^A-Za-z]", "_", self.eleve_lastname.lower())}"

    def get_fullname(self) -> str | None:
        """Student fullname"""
        return f"{self.eleve_firstname} {self.eleve_lastname}"


class EDHomework:
    """Homework information"""

    def __init__(self, data, pour_le):
        self.matiere = data.get("matiere")
        self.pour_le = pour_le
        self.effectue = data.get("effectue")
        self.interrogation = data.get("interrogation")
        self.contenu = data.get("contenu")

    def __getitem__(self, key):
        return self

    def __lt__(self, other):
        return self.pour_le < other

    def __gt__(self, other):
        return self.pour_le > other

    def __repr__(self):
        """Allow seeing value instead of object description"""
        return str(self.pour_le + " - " + self.matiere)


class EDGrade:
    """Grade information"""

    def __init__(self, data):
        self.devoir = data.get("devoir")
        self.libelle_matiere = data.get("libelleMatiere")
        self.coef = data.get("coef")
        self.note_sur = data.get("noteSur")
        self.valeur = data.get("valeur")
        self.date = data.get("date")
        self.date_saisie = data.get("dateSaisie")
        self.moyenne_classe = data.get("moyenneClasse")
        self.min_classe = data.get("minClasse")
        self.max_classe = data.get("maxClasse")
        self.elements_programme = []
        if "elementsProgramme" in data:
            for element in data["elementsProgramme"]:
                self.elements_programme.append(EDCompetence(element))


class EDCompetence:
    """Evaluation information"""

    def __init__(self, data):
        self.descriptif = data.get("descriptif")
        self.libelle_competence = data.get("libelleCompetence")
        self.valeur = data.get("valeur")
        match self.valeur:
            case "1":
                self.level = "Maîtrise insuffisante"
            case "2":
                self.level = "Maîtrise fragile"
            case "3":
                self.level = "Maîtrise satisfaisante"
            case "4":
                self.level = "Très bonne maîtrise"
            case _:
                self.level = "Unknown"


class EDVieScolaire:
    """Vie scolaire information"""

    def __init__(self, data):
        self.type_element = data.get("typeElement")
        self.date = data.get("date")
        self.display_date = data.get("displayDate")
        self.justifie = data.get("justifie")
        self.libelle = data.get("libelle")
        self.motif = data.get("motif")
        self.commentaire = data.get("commentaire")


class EDLesson:
    """Lesson information"""

    def __init__(self, data):
        self.id = data.get("id")
        self.text = data.get("text")
        self.matiere = data.get("matiere")
        self.code_matiere = data.get("codeMatiere")
        self.type_cours = data["typeCours"]
        self.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d %H:%M")
        self.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d %H:%M")
        self.color = data["color"]
        self.dispensable = data.get("dispensable", False)
        self.dispense = data["dispense"]
        self.prof = data["prof"]
        self.salle = data["salle"]
        self.classe = data["classe"]
        self.classe_id = data["classeId"]
        self.classe_code = data["classeCode"]
        self.groupe = data["groupe"]
        self.groupe_code = data["groupeCode"]
        self.groupe_id = data["groupeId"]
        self.icone = data["icone"]
        self.is_flexible = data.get("isFlexible", False)
        self.is_modifie = data.get("isModifie", False)
        self.contenu_de_seance = data.get("contenuDeSeance", False)
        self.devoir_a_faire = data.get("devoirAFaire", False)
        self.is_annule = data.get("isAnnule", False)

    def __getitem__(self, key):
        return self

    def __lt__(self, other):
        return self.start_date < other

    def __gt__(self, other):
        return self.start_date > other

    def __repr__(self):
        """Allow seeing value instead of object description"""
        return str(self.start_date.strftime("%Y-%m-%d %H:%M") + " - " + self.matiere)


def check_ecoledirecte_session(data, config_path, hass) -> bool:
    """check if credentials to Ecole Directe are ok"""
    try:
        session = get_ecoledirecte_session(data, config_path, hass)
    except QCMError:
        return True

    return session is not None


def get_ecoledirecte_session(data, config_path, hass) -> EDSession | None:
    """Function connecting to Ecole Directe"""
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
        if login["code"] == 250:
            with open(
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
                        _LOGGER.warning(
                            "qcm raté pour la question [%s], vérifier le fichier %s. [%s]",
                            question,
                            data["qcm_filename"],
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

                    with open(
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
                        hass.components.persistent_notification.async_create(
                            "Vérifiez le fichier "
                            + data["qcm_filename"]
                            + ", et rechargez l'intégration Ecole Directe.",
                            title="Ecole Directe",
                        )
                try_login -= 1

            if try_login == 0:
                raise QCMError(
                    "Vérifiez le fichier qcm.json, et rechargez l'intégration Ecole Directe."
                )

            _LOGGER.debug("cn: [%s] - cv: [%s]", cn, cv)

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

        _LOGGER.info(
            "Connection OK - identifiant: [{%s}]",
            login["data"]["accounts"][0]["identifiant"],
        )
        return EDSession(login)
    except QCMError as err:
        _LOGGER.warning(err)
        raise
    except Exception as err:
        _LOGGER.critical(err)
        return None


def get_qcm_connexion(token, config_path):
    """Obtenir le QCM donné lors d'une connexion à partir d'un nouvel appareil"""

    json_resp = get_response(
        token,
        f"{APIURL}/connexion/doubleauth.awp?verbe=get&v={APIVERSION}",
        None,
        config_path + INTEGRATION_PATH + "get_qcm_connexion.json",
    )

    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_qcm_connexion: [%s]", json_resp)
    return None


def post_qcm_connexion(token, proposition, config_path):
    """Renvoyer la réponse du QCM donné"""

    json_resp = get_response(
        token,
        f"{APIURL}/connexion/doubleauth.awp?verbe=post&v={APIVERSION}",
        f'data={{"choix": "{proposition}"}}',
        config_path + INTEGRATION_PATH + "post_qcm_connexion.json",
    )

    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("post_qcm_connexion: [%s]", json_resp)
    return None


def get_messages(session, eleve, annee_scolaire, config_path):
    """Get messages from Ecole Directe"""
    payload = (
        'data={"anneeMessages":"' + urllib.parse.quote(annee_scolaire, safe="") + '"}'
    )
    if eleve is None:
        return get_response(
            session,
            f"{APIURL}/familles/{session.id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
            payload,
            config_path + INTEGRATION_PATH + "get_messages_famille.json",
        )
    return get_response(
        session,
        f"{APIURL}/eleves/{eleve.eleve_id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
        payload,
        config_path + INTEGRATION_PATH + "get_messages_eleve.json",
    )


def get_homeworks_by_date(token, eleve, date, config_path, idx):
    """get homeworks by date"""

    json_resp = get_response(
        token,
        f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp?verbe=get&v={APIVERSION}",
        None,
        config_path + INTEGRATION_PATH + "get_homeworks_by_date_" + str(idx) + ".json",
    )
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_homeworks_by_date: [%s]", json_resp)
    return None

    # Opening JSON file
    # f = open(
    #     config_path + INTEGRATION_PATH + "test/test_homeworks_" + str(idx) + ".json"
    # )
    # data = json.load(f)
    # return data["data"]


def get_homeworks(token, eleve, config_path):
    """get homeworks"""

    json_resp = get_response(
        token,
        f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte.awp?verbe=get&v={APIVERSION}",
        None,
        config_path + INTEGRATION_PATH + "get_homeworks.json",
    )
    if "data" not in json_resp:
        _LOGGER.warning("get_homeworks: [%s]", json_resp)
        return None

    # Opening JSON file
    # f = open(config_path + INTEGRATION_PATH + "test/test_homeworks.json")
    # json_resp = json.load(f)

    data = json_resp["data"]
    homeworks = []
    for key in data.keys():
        for idx, homework_json in enumerate(data[key]):
            homeworks_by_date_json = get_homeworks_by_date(
                token, eleve, key, config_path, idx
            )
            for matiere in homeworks_by_date_json["matieres"]:
                for homework in data[key]:
                    if matiere["id"] == homework["idDevoir"]:
                        homework["nbJourMaxRenduDevoir"] = matiere[
                            "nbJourMaxRenduDevoir"
                        ]
                        homework["contenu"] = matiere["aFaire"]["contenu"]

            hw = EDHomework(homework_json, key)
            if not hw.effectue:
                homeworks.append(hw)
    if homeworks is not None:
        homeworks.sort(key=operator.itemgetter("pourLe"))

    return homeworks


def get_grades_evaluations(token, eleve, annee_scolaire, config_path):
    """get grades"""
    json_resp = get_response(
        token,
        f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp?verbe=get&v={APIVERSION}",
        f"data={{'anneeScolaire': '{annee_scolaire}'}}",
        config_path + INTEGRATION_PATH + "get_grades_evaluations.json",
    )
    if "data" not in json_resp:
        _LOGGER.warning("get_grades_evaluations: [%s]", json_resp)
        return None

    # Opening JSON file
    # f = open(config_path + INTEGRATION_PATH + "test/test_grades.json")
    # json_resp = json.load(f)

    response = {}
    response["grades"] = []
    response["evaluations"] = []
    data = json_resp["data"]
    index1 = 0
    index2 = 0
    if "notes" in data:
        data["notes"].sort(key=operator.itemgetter("date"))
        data["notes"].reverse()
        for grade_json in data["notes"]:
            if grade_json["noteSur"] == "0":
                index1 += 1
                if index1 > GRADES_TO_DISPLAY:
                    continue
                evaluation = EDGrade(grade_json)
                response["evaluations"].append(evaluation)
            else:
                index2 += 1
                if index2 > GRADES_TO_DISPLAY:
                    continue
                grade = EDGrade(grade_json)
                response["grades"].append(grade)
    return response


def get_vie_scolaire(token, eleve, config_path):
    """get vie scolaire (absences, retards, etc.)"""
    json_resp = get_response(
        token,
        f"{APIURL}/eleves/{eleve.eleve_id}/viescolaire.awp?verbe=get&v={APIVERSION}",
        "data={}",
        config_path + INTEGRATION_PATH + "get_vie_scolaire.json",
    )
    if "data" not in json_resp:
        _LOGGER.warning("get_vie_scolaire: [%s]", json_resp)
        return None
    # Opening JSON file
    # f = open(config_path + INTEGRATION_PATH + "test/test_vie_scolaire.json")
    # json_resp = json.load(f)

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
                absence = EDVieScolaire(data_json)
                response["absences"].append(absence)
            else:
                index2 += 1
                if index2 > VIE_SCOLAIRE_TO_DISPLAY:
                    continue
                retard = EDVieScolaire(data_json)
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
                sanction = EDVieScolaire(data_json)
                response["sanctions"].append(sanction)
            else:
                index2 += 1
                if index2 > VIE_SCOLAIRE_TO_DISPLAY:
                    continue
                encouragement = EDVieScolaire(data_json)
                response["encouragements"].append(encouragement)

    return response


def get_lessons(token, eleve, date_debut, date_fin, config_path):
    """get lessons"""
    json_resp = get_response(
        token,
        f"{APIURL}/E/{eleve.eleve_id}/emploidutemps.awp?verbe=get&v={APIVERSION}",
        f"data={{'dateDebut': '{date_debut}','dateFin': '{date_fin}','avecTrous': false}}",
        config_path + INTEGRATION_PATH + "get_lessons.json",
    )
    if "data" not in json_resp:
        _LOGGER.warning("get_lessons: [%s]", json_resp)
        return None
    # Opening JSON file
    # f = open(config_path + INTEGRATION_PATH + "test/test_lessons.json")
    # json_resp = json.load(f)

    response = []
    data = json_resp["data"]
    for lesson_json in data:
        lesson = EDLesson(lesson_json)
        if not lesson.is_annule:
            response.append(lesson)
    if response is not None:
        response.sort(key=operator.itemgetter("start_date"))

    return response


def get_headers(token):
    """return headers needed from Ecole Directe API"""
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
