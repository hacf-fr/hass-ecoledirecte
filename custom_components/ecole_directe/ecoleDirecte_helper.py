import re
import requests
import base64
import logging

_LOGGER = logging.getLogger(__name__)

APIURL="https://api.ecoledirecte.com/v3"
APIVERSION="4.53.0"

def encodeString(string):
    return string.replace("%", "%25").replace("&", "%26").replace("+", "%2B").replace("+", "%2B").replace("\\", "\\\\\\").replace("\\\\", "\\\\\\\\")

def encodeBody(dictionnary, isRecursive = False):
    body = ""
    for key in dictionnary:
        if isRecursive:
            body += "\"" + key + "\":"
        else:
            body += key + "="

        if type(dictionnary[key]) is dict:
            body += "{" + encodeBody(dictionnary[key], True) + "}"
        else:
            body += "\"" + str(dictionnary[key]) + "\""
        body += ","

    return body[:-1]

def decodeB64(string):
    return base64.b64decode(string)

def getResponse(session, url, data):
    if not isLogin(session):
        return None

    response = requests.post(url, data=data, headers=getHeaders(session.token))
    if 'application/json' in response.headers.get('Content-Type', ''):
        return response.json()

    _LOGGER.warning(f"Error with URL:[{url}] - response:[{response.content}]")
    return None

class ED_Session:
    def __init__(self, data):
        self.token = data["token"]
        self.id = data["data"]["accounts"][0]["id"]
        self.identifiant = data["data"]["accounts"][0]["identifiant"]
        self.idLogin = data["data"]["accounts"][0]["idLogin"]
        self.typeCompte = data["data"]["accounts"][0]["typeCompte"]
        self.eleves = []
        if data["data"]["accounts"][0]["profile"]["eleves"] is not None:
            for eleve in data["data"]["accounts"][0]["profile"]["eleves"]:
                self.eleves.append(ED_Eleve(eleve))

class ED_Eleve:
    def __init__(self, data):
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

def get_ecoledirecte_session(data) -> ED_Session | None:
    try:
        session = login(data['username'], data['password'])
        _LOGGER.info(f"Connection OK - identifiant: [{session.identifiant}]")
    except Exception as err:
        _LOGGER.critical(err)
        return None

    return session

def getMessages(session, eleve, year):
    if(eleve == None):
        return getResponse(session,
                       f"{APIURL}/familles/{session.id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
                       encodeBody({"data": {"anneeMessages": year}}))
    return getResponse(session,
                    f"{APIURL}/eleves/{eleve.eleve_id}/messages.awp?force=false&typeRecuperation=received&idClasseur=0&orderBy=date&order=desc&query=&onlyRead=&page=0&itemsPerPage=100&getAll=0&verbe=get&v={APIVERSION}",
                    encodeBody({"data": {"anneeMessages": year}}))

def getHomework(session, eleve, date):
    return getResponse(session,
                       f"{APIURL}/eleves/{eleve.eleve_id}/cahierdetexte/{date}.awp?verbe=get&v={APIVERSION}",
                       "data={}")

def getHomework(session, eleve):
    return getResponse(session,
                       f"{APIURL}/eleves/{eleve.eleve_id}/cahierdetexte.awp?verbe=get&v={APIVERSION}",
                       "data={}")

def getNotes(session, eleve):
    return getResponse(session,
                       f"{APIURL}/eleves/{eleve.eleve_id}/notes.awp?verbe=get&v={APIVERSION}",
                       "data='data={\"anneeScolaire\": \"\"}'")

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
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
    }
    if token != None:
        headers["X-Token"] = token

    return headers

def login(username, password) ->  ED_Session | None:
    _LOGGER.debug(f"Coordinator uses connection for username: {username} and password: {password}")
    try:
        login = requests.post(f"{APIURL}/login.awp?v={APIVERSION}", data=encodeBody({
            "data": {
                "identifiant": username,
                "motdepasse": password
            }
        }), headers=getHeaders(None)).json()
    except Exception as err:
        _LOGGER.critical(err)
        return None

    _LOGGER.debug(f"login: {login}")
    return ED_Session(login);

def isLogin(session):
    if session.token != None and session.id != None:
        return True

    return False

