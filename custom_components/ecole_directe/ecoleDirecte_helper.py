import re
import requests
import logging
import urllib

_LOGGER = logging.getLogger(__name__)

APIURL = "https://api.ecoledirecte.com/v3"
APIVERSION = "4.53.0"


def encodeBody(dictionnary, isRecursive=False):
    body = ""
    for key in dictionnary:
        if isRecursive:
            body += '"' + key + '":'
        else:
            body += key + "="

        if isinstance(dictionnary[key], dict):
            body += "{" + encodeBody(dictionnary[key], True) + "}"
        else:
            body += '"' + urllib.parse.quote(str(dictionnary[key]), safe="") + '"'
        body += ","

    return body[:-1]


def getResponse(session, url, payload):
    if session is not None and isLogin(session):
        token = session.token
    else:
        token = None

    if payload is None:
        payload = "data={}"

    _LOGGER.debug("URL: [%s] - Payload: [%s]", url, payload)
    response = requests.post(url, data=payload, headers=getHeaders(token), timeout=60)

    if "application/json" in response.headers.get("Content-Type", ""):
        respJson = response.json()
        if respJson["code"] != 200:
            raise RequestError(
                "Error with URL:[{}] - Code {}: {}".format(
                    url, respJson["code"], respJson["message"]
                )
            )
        _LOGGER.debug("%s", respJson)
        return respJson

    raise RequestError("Error with URL:[{}]: {}".format(url, response.content))


class RequestError(Exception):
    def __init__(self, message):
        super(RequestError, self).__init__(message)


class ED_Session:
    def __init__(self, data):
        self.token = data["token"]
        self.id = data["data"]["accounts"][0]["id"]
        self.identifiant = data["data"]["accounts"][0]["identifiant"]
        self.idLogin = data["data"]["accounts"][0]["idLogin"]
        self.typeCompte = data["data"]["accounts"][0]["typeCompte"]
        self.modules = []
        for module in data["data"]["accounts"][0]["modules"]:
            if module["enable"]:
                self.modules.append(module["code"])
        self.eleves = []
        if self.typeCompte == "E":
            self.eleves.append(
                ED_Eleve(
                    None,
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
                    self.eleves.append(ED_Eleve(eleve))


class ED_Eleve:
    def __init__(
        self,
        data=None,
        id=None,
        firstName=None,
        lastName=None,
        classe_id=None,
        classe_name=None,
        modules=None,
    ):
        if data is None:
            self.classe_id = classe_id
            self.classe_name = classe_name
            self.eleve_id = id
            self.eleve_lastname = lastName
            self.eleve_firstname = firstName
            self.modules = modules
        else:
            if "classe" in data:
                self.classe_id = data["classe"]["id"]
                self.classe_name = data["classe"]["libelle"]
            self.eleve_id = data["id"]
            self.eleve_lastname = data["nom"]
            self.eleve_firstname = data["prenom"]
            self.modules = []
            for module in data["modules"]:
                if module["enable"]:
                    self.modules.append(module["code"])

    def get_fullnameLower(self) -> str | None:
        return f"{re.sub("[^A-Za-z]", "_", self.eleve_firstname.lower())}_{re.sub("[^A-Za-z]", "_", self.eleve_lastname.lower())}"

    def get_fullname(self) -> str | None:
        return f"{self.eleve_firstname} {self.eleve_lastname}"


class ED_Devoir:
    def __init__(self, data, pourLe):
        try:
            if "matiere" in data:
                self.matiere = data["matiere"]
            else:
                self.matiere = ""
            if "codeMatiere" in data:
                self.codeMatiere = data["codeMatiere"]
            else:
                self.codeMatiere = ""
            if "aFaire" in data:
                self.aFaire = data["aFaire"]
            else:
                self.aFaire = ""
            if "idDevoir" in data:
                self.idDevoir = data["idDevoir"]
            else:
                self.idDevoir = ""
            if "documentsAFaire" in data:
                self.documentsAFaire = data["documentsAFaire"]
            else:
                self.documentsAFaire = ""
            if "donneLe" in data:
                self.donneLe = data["donneLe"]
            else:
                self.donneLe = ""
            self.pourLe = pourLe
            if "effectue" in data:
                self.effectue = data["effectue"]
            else:
                self.effectue = ""
            if "interrogation" in data:
                self.interrogation = data["interrogation"]
            else:
                self.interrogation = ""
            if "rendreEnLigne" in data:
                self.rendreEnLigne = data["rendreEnLigne"]
            else:
                self.rendreEnLigne = ""
        except Exception as err:
            _LOGGER.warning("ED_Devoir Error: [%s] - Data[%s]", err, data)

    def format(self):
        try:
            return {
                "matiere": self.matiere,
                "codeMatiere": self.codeMatiere,
                "aFaire": self.aFaire,
                "idDevoir": self.idDevoir,
                "documentsAFaire": self.documentsAFaire,
                "donneLe": self.donneLe,
                "pourLe": self.pourLe,
                "effectue": self.effectue,
                "interrogation": self.interrogation,
                "rendreEnLigne": self.rendreEnLigne,
            }
        except Exception:
            return {}


class ED_Note:
    def __init__(self, data):
        try:
            if "id" in data:
                self.id = data["id"]
            else:
                self.id = ""
            if "devoir" in data:
                self.devoir = data["devoir"]
            else:
                self.devoir = ""
            if "codePeriode" in data:
                self.codePeriode = data["codePeriode"]
            else:
                self.codePeriode = ""
            if "codeMatiere" in data:
                self.codeMatiere = data["codeMatiere"]
            else:
                self.codeMatiere = ""
            if "libelleMatiere" in data:
                self.libelleMatiere = data["libelleMatiere"]
            else:
                self.libelleMatiere = ""
            if "codeSousMatiere" in data:
                self.codeSousMatiere = data["codeSousMatiere"]
            else:
                self.codeSousMatiere = ""
            if "typeDevoir" in data:
                self.typeDevoir = data["typeDevoir"]
            else:
                self.typeDevoir = ""
            if "enLettre" in data:
                self.enLettre = data["enLettre"]
            else:
                self.enLettre = ""
            if "commentaire" in data:
                self.commentaire = data["commentaire"]
            else:
                self.commentaire = ""
            if "uncSujet" in data:
                self.uncSujet = data["uncSujet"]
            else:
                self.uncSujet = ""
            if "uncCorrige" in data:
                self.uncCorrige = data["uncCorrige"]
            else:
                self.uncCorrige = ""
            if "coef" in data:
                self.coef = data["coef"]
            else:
                self.coef = ""
            if "noteSur" in data:
                self.noteSur = data["noteSur"]
            else:
                self.noteSur = ""
            if "valeur" in data:
                self.valeur = data["valeur"]
            else:
                self.valeur = ""
            if "nonSignificatif" in data:
                self.nonSignificatif = data["nonSignificatif"]
            else:
                self.nonSignificatif = ""
            if "date" in data:
                self.date = data["date"]
            else:
                self.date = ""
            if "dateSaisie" in data:
                self.dateSaisie = data["dateSaisie"]
            else:
                self.dateSaisie = ""
            if "valeurisee" in data:
                self.valeurisee = data["valeurisee"]
            else:
                self.valeurisee = ""
            if "moyenneClasse" in data:
                self.moyenneClasse = data["moyenneClasse"]
            else:
                self.moyenneClasse = ""
            if "minClasse" in data:
                self.minClasse = data["minClasse"]
            else:
                self.minClasse = ""
            if "maxClasse" in data:
                self.maxClasse = data["maxClasse"]
            else:
                self.maxClasse = ""
            if "elementsProgramme" in data:
                self.elementsProgramme = data["elementsProgramme"]
            else:
                self.elementsProgramme = ""
        except Exception as err:
            _LOGGER.warning("ED_Note error: [%s] - Data[%s]", err, data)

    def format(self):
        try:
            return {
                "id": self.id,
                "devoir": self.devoir,
                "codePeriode": self.codePeriode,
                "codeMatiere": self.codeMatiere,
                "libelleMatiere": self.libelleMatiere,
                "codeSousMatiere": self.codeSousMatiere,
                "typeDevoir": self.typeDevoir,
                "enLettre": self.enLettre,
                "commentaire": self.commentaire,
                "uncSujet": self.uncSujet,
                "uncCorrige": self.uncCorrige,
                "coef": self.coef,
                "noteSur": self.noteSur,
                "valeur": self.valeur,
                "nonSignificatif": self.nonSignificatif,
                "date": self.date,
                "dateSaisie": self.dateSaisie,
                "valeurisee": self.valeurisee,
                "moyenneClasse": self.moyenneClasse,
                "minClasse": self.minClasse,
                "maxClasse": self.maxClasse,
                "elementsProgramme": self.elementsProgramme,
            }
        except Exception:
            return {}


def get_ecoledirecte_session(data) -> ED_Session | None:
    """Function connecting to Ecole Directe"""
    try:
        _LOGGER.debug(
            "Try connection for username: {%s} and password: {%s}",
            data["username"],
            data["password"],
        )

        login = getResponse(
            None,
            f"{APIURL}/login.awp?v={APIVERSION}",
            encodeBody(
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
        return ED_Session(login)
    except Exception as err:
        _LOGGER.critical(err)
        return None


def getMessages(session, eleve, anneeScolaire):
    if eleve is None:
        return getResponse(
            session,
            f"{APIURL}/familles/{session.id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
            encodeBody({"data": {"anneeMessages": anneeScolaire}}),
        )
    return getResponse(
        session,
        f"{APIURL}/eleves/{eleve.eleve_id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
        encodeBody({"data": {"anneeMessages": anneeScolaire}}),
    )


def getDevoirsByDate(session, eleve, date):
    return getResponse(
        session,
        f"{APIURL}/eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp?verbe=get&v={APIVERSION}",
        None,
    )


def getDevoirs(session, eleve):
    return getResponse(
        session,
        f"{APIURL}/eleves/{eleve.eleve_id}/cahierdetexte.awp?verbe=get&v={APIVERSION}",
        None,
    )


def getNotes(session, eleve, anneeScolaire):
    return getResponse(
        session,
        f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp?verbe=get&v={APIVERSION}",
        encodeBody({"data": {"anneeScolaire": anneeScolaire}}),
    )


def getHeaders(token):
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


def isLogin(session):
    if session.token is not None and session.id is not None:
        return True

    return False
