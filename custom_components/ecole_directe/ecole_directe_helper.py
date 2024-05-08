"""Module to help communication with Ecole Directe API"""

import json
import re
import logging
import urllib
import base64
import requests

from .const import EVENT_TYPE, INTEGRATION_PATH

_LOGGER = logging.getLogger(__name__)

APIURL = "https://api.ecoledirecte.com/v3"
APIVERSION = "4.55.0"


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
        if "matiere" in data:
            self.matiere = data["matiere"]
        else:
            self.matiere = ""
        if "codeMatiere" in data:
            self.code_matiere = data["codeMatiere"]
        else:
            self.code_matiere = ""
        if "aFaire" in data:
            self.a_faire = data["aFaire"]
        else:
            self.a_faire = ""
        if "idDevoir" in data:
            self.id_devoir = data["idDevoir"]
        else:
            self.id_devoir = ""
        if "documentsAFaire" in data:
            self.documents_a_faire = data["documentsAFaire"]
        else:
            self.documents_a_faire = ""
        if "donneLe" in data:
            self.donne_le = data["donneLe"]
        else:
            self.donne_le = ""
        self.pour_le = pour_le
        if "effectue" in data:
            self.effectue = data["effectue"]
        else:
            self.effectue = ""
        if "interrogation" in data:
            self.interrogation = data["interrogation"]
        else:
            self.interrogation = ""
        if "rendreEnLigne" in data:
            self.rendre_en_ligne = data["rendreEnLigne"]
        else:
            self.rendre_en_ligne = ""
        if "nbJourMaxRenduDevoir" in data:
            self.nb_jour_max_rendu_devoir = data["nbJourMaxRenduDevoir"]
        else:
            self.nb_jour_max_rendu_devoir = ""
        if "contenu" in data:
            self.contenu = data["contenu"]
        else:
            self.contenu = ""


class EDGrade:
    """Grade information"""

    def __init__(self, data):
        if "id" in data:
            self.id = data["id"]
        else:
            self.id = ""
        if "devoir" in data:
            self.devoir = data["devoir"]
        else:
            self.devoir = ""
        if "codePeriode" in data:
            self.code_periode = data["codePeriode"]
        else:
            self.code_periode = ""
        if "codeMatiere" in data:
            self.code_matiere = data["codeMatiere"]
        else:
            self.code_matiere = ""
        if "libelleMatiere" in data:
            self.libelle_matiere = data["libelleMatiere"]
        else:
            self.libelle_matiere = ""
        if "codeSousMatiere" in data:
            self.code_sous_matiere = data["codeSousMatiere"]
        else:
            self.code_sous_matiere = ""
        if "typeDevoir" in data:
            self.type_devoir = data["typeDevoir"]
        else:
            self.type_devoir = ""
        if "enLettre" in data:
            self.en_lettre = data["enLettre"]
        else:
            self.en_lettre = ""
        if "commentaire" in data:
            self.commentaire = data["commentaire"]
        else:
            self.commentaire = ""
        if "uncSujet" in data:
            self.unc_sujet = data["uncSujet"]
        else:
            self.unc_sujet = ""
        if "uncCorrige" in data:
            self.unc_corrige = data["uncCorrige"]
        else:
            self.unc_corrige = ""
        if "coef" in data:
            self.coef = data["coef"]
        else:
            self.coef = ""
        if "noteSur" in data:
            self.note_sur = data["noteSur"]
        else:
            self.note_sur = ""
        if "valeur" in data:
            self.valeur = data["valeur"]
        else:
            self.valeur = ""
        if "nonSignificatif" in data:
            self.non_significatif = data["nonSignificatif"]
        else:
            self.non_significatif = ""
        if "date" in data:
            self.date = data["date"]
        else:
            self.date = ""
        if "dateSaisie" in data:
            self.date_saisie = data["dateSaisie"]
        else:
            self.date_saisie = ""
        if "valeurisee" in data:
            self.valeurisee = data["valeurisee"]
        else:
            self.valeurisee = ""
        if "moyenneClasse" in data:
            self.moyenne_classe = data["moyenneClasse"]
        else:
            self.moyenne_classe = ""
        if "minClasse" in data:
            self.min_classe = data["minClasse"]
        else:
            self.min_classe = ""
        if "maxClasse" in data:
            self.max_classe = data["maxClasse"]
        else:
            self.max_classe = ""
        if "elementsProgramme" in data:
            self.elements_programme = data["elementsProgramme"]
        else:
            self.elements_programme = ""


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


def get_homeworks_by_date(token, eleve, date, config_path):
    """get homeworks by date"""
    json_resp = get_response(
        token,
        f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp?verbe=get&v={APIVERSION}",
        None,
        config_path + INTEGRATION_PATH + "get_homeworks_by_date.json",
    )
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_homeworks_by_date: [%s]", json_resp)
    return None
    # Opening JSON file
    # f = open("config_path + INTEGRATION_PATH + "test_homeworks2.json")

    # # returns JSON object as
    # # a dictionary
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
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_homeworks: [%s]", json_resp)
    return None

    # # Opening JSON file
    # f = open(config_path + INTEGRATION_PATH + "test_homeworks.json")

    # # returns JSON object as
    # # a dictionary
    # data = json.load(f)
    # return data["data"]


def get_grades(token, eleve, annee_scolaire, config_path):
    """get grades"""
    json_resp = get_response(
        token,
        f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp?verbe=get&v={APIVERSION}",
        f"data={{'anneeScolaire': '{annee_scolaire}'}}",
        config_path + INTEGRATION_PATH + "get_grades.json",
    )
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_grades: [%s]", json_resp)
    return None
    # f = open(config_path + INTEGRATION_PATH + "test_grades.json")

    # # returns JSON object as
    # # a dictionary
    # data = json.load(f)
    # return data["data"]


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
