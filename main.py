from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS (kad frontend galėtų kalbėti su backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globalūs set'ai
legal_domains = set()
illegal_domains = set()


def load_domains():
    global legal_domains, illegal_domains

    def load_file(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return set(
                    line.strip().lower()
                    for line in f
                    if line.strip() and not line.startswith("#")
                )
        except FileNotFoundError:
            return set()

    legal_domains = load_file("legal_domains.txt")
    illegal_domains = load_file("illegal_domains.txt")

    print(f"✔ Loaded legal: {len(legal_domains)}")
    print(f"✔ Loaded illegal: {len(illegal_domains)}")


# Užkraunam startuojant
load_domains()


def normalize(domain: str):
    domain = domain.lower().strip()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    domain = domain.split("/")[0]
    return domain


def match(domain, domain_set):
    if domain in domain_set:
        return True

    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        candidate = ".".join(parts[i:])
        if candidate in domain_set:
            return True

    return False


class DomainRequest(BaseModel):
    domain: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "legal_count": len(legal_domains),
        "illegal_count": len(illegal_domains),
    }


@app.post("/check-domain")
def check_domain(data: DomainRequest):
    domain = normalize(data.domain)

    if match(domain, legal_domains):
        return {
            "domain": domain,
            "status": "legal",
            "title": "Svetainė yra legali",
            "text": "Ši svetainė rasta licencijuotų domenų sąraše.",
            "basis": "Atitikmuo rastas legalių domenų sąraše."
        }

    if match(domain, illegal_domains):
        return {
            "domain": domain,
            "status": "illegal",
            "title": "Svetainė yra nelegali",
            "text": "Ši svetainė rasta nelegalių ar blokuojamų domenų sąraše.",
            "basis": "Atitikmuo rastas nelegalių domenų sąraše."
        }

    return {
        "domain": domain,
        "status": "unknown",
        "title": "Svetainės statusas neaiškus",
        "text": "Pagal turimus duomenis svetainė nerasta sąrašuose.",
        "basis": "Atitikmuo nerastas."
    }


@app.post("/reload")
def reload_domains():
    load_domains()
    return {"status": "reloaded"}