"""Module to help communication with Ecole Directe API"""

import re
import logging
import urllib
import requests

_LOGGER = logging.getLogger(__name__)

APIURL = "https://api.ecoledirecte.com/v3"
APIVERSION = "4.53.0"


def encode_body(dictionnary, is_recursive=False):
    """encode payload to send to API"""
    body = ""
    for key in dictionnary:
        if is_recursive:
            body += '"' + key + '":'
        else:
            body += key + "="

        if isinstance(dictionnary[key], dict):
            body += "{" + encode_body(dictionnary[key], True) + "}"
        else:
            body += '"' + urllib.parse.quote(str(dictionnary[key]), safe="") + '"'
        body += ","

    return body[:-1]


def get_response(session, url, payload):
    """send a request to API and return a json if possible or raise an error"""
    if session is not None and is_login(session):
        token = session.token
    else:
        token = None

    if payload is None:
        payload = "data={}"

    _LOGGER.debug("URL: [%s] - Payload: [%s]", url, payload)
    response = requests.post(url, data=payload, headers=get_headers(token), timeout=120)

    try:
        resp_json = response.json()
    except Exception as ex:
        raise RequestError(f"Error with URL:[{url}]: {response.content}") from ex
    if "code" not in resp_json:
        raise RequestError(f"Error with URL:[{url}]: json:[{resp_json}]")
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


def get_ecoledirecte_session(data) -> EDSession | None:
    """Function connecting to Ecole Directe"""
    try:
        _LOGGER.debug(
            "Try connection for username: {%s} and password: {%s}",
            data["username"],
            data["password"],
        )

        login = get_response(
            None,
            f"{APIURL}/login.awp?v={APIVERSION}",
            encode_body(
                {
                    "data": {
                        "identifiant": data["username"],
                        "motdepasse": data["password"],
                    }
                }
            ),
        )

        _LOGGER.info(
            "Connection OK - identifiant: [{%s}]",
            login["data"]["accounts"][0]["identifiant"],
        )
        return EDSession(login)
    except Exception as err:
        _LOGGER.critical(err)
        return None


# def get_messages(session, eleve, annee_scolaire):
#     """Get messages from Ecole Directe"""
#     if eleve is None:
#         return get_response(
#             session,
#             f"{APIURL}/familles/{session.id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
#             encode_body({"data": {"anneeMessages": annee_scolaire}}),
#         )
#     return get_response(
#         session,
#         f"{APIURL}/eleves/{eleve.eleve_id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
#         encode_body({"data": {"anneeMessages": annee_scolaire}}),
#     )


def get_homeworks_by_date(session, eleve, date):
    """get homeworks by date"""
    json_resp = get_response(
        session,
        f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp?verbe=get&v={APIVERSION}",
        None,
    )
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_homeworks_by_date: [%s]", json_resp)
    return None
    # Opening JSON file
    # f = open("config/custom_components/ecole_directe/test_homeworks2.json")

    # # returns JSON object as
    # # a dictionary
    # data = json.load(f)
    # return data["data"]


def get_homeworks(session, eleve):
    """get homeworks"""
    json_resp = get_response(
        session,
        f"{APIURL}/Eleves/{eleve.eleve_id}/cahierdetexte.awp?verbe=get&v={APIVERSION}",
        None,
    )
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_homeworks: [%s]", json_resp)
    return None

    # Opening JSON file
    # f = open("config/custom_components/ecole_directe/test_homeworks.json")

    # # returns JSON object as
    # # a dictionary
    # data = json.load(f)
    # return data["data"]


def get_grades(session, eleve, annee_scolaire):
    """get grades"""
    json_resp = get_response(
        session,
        f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp?verbe=get&v={APIVERSION}",
        encode_body({"data": {"anneeScolaire": annee_scolaire}}),
    )
    if "data" in json_resp:
        return json_resp["data"]
    _LOGGER.warning("get_grades: [%s]", json_resp)
    return None
    # f = open("config/custom_components/ecole_directe/test_grades.json")

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
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    }
    if token is not None:
        headers["X-Token"] = token

    return headers


def is_login(session):
    """Ckeck valid login"""
    if session.token is not None and session.id is not None:
        return True
    return False
