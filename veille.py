import feedparser
import requests
import time                                                         
from bs4 import BeautifulSoup
import csv
import html

# RÉGLAGES 

SOURCES = {
    "CNIL": "https://www.cnil.fr/fr/rss.xml",
    "ZATAZ": "https://www.zataz.com/feed/",
    "ANSSI": "https://cyber.gouv.fr/actualites/rss/",
}

URL_AFNOR = "https://www.afnor.org/actualites/"

ENTETES = {
    "User-Agent": "VeilleGRC/1.0 (projet etudiant)",
    "Accept": "text/html",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

MOTS_CLES = [
    "iso 27001", "iso 27002", "iso 27005",
    "iso 9001", "iso 14001", "iso 22000",
    "nis 2", "nis2", "dora", "cyber resilience act",
    "rgpd", "ebios", "smsi",
    "conformité", "certification", "homologation",
    "analyse de risques", "référentiel", "réglementation",
    "nouvelle version",
]


# LE FILTRE GRC 

def est_pertinent(texte):
    """Renvoie True si le texte contient un mot-clé GRC, sinon False."""
    texte = texte.lower()
    for mot in MOTS_CLES:
        if mot in texte:
            return True
    return False


articles_retenus = []
total = 0

# LES FLUX RSS 

for nom, url in SOURCES.items():
    flux = feedparser.parse(url)
    total = total + len(flux.entries)

    for article in flux.entries:
        texte = article.title + " " + article.summary

        if est_pertinent(texte):
            articles_retenus.append({
                "source": nom,
                "titre": article.title,
                "date": article.published,
                "lien": article.link,
                "resume": article.summary,
            })

#  L'AFNOR

reponse = requests.get(URL_AFNOR, headers=ENTETES)
soupe = BeautifulSoup(reponse.text, "html.parser")
articles_afnor = soupe.find_all("article", itemtype="https://schema.org/Article")
total = total + len(articles_afnor)

for article_afnor in articles_afnor:
    lien = article_afnor.find("a")
    if not lien:
        continue

    titre = lien.get("aria-label", "Sans titre")
    adresse = "https://www.afnor.org" + lien.get("href")

    balise_date = article_afnor.find("time")
    if balise_date:
        date = balise_date.get_text(strip=True)
    else:
        date = "Date inconnue"

    # Lire le résumé sur la page de l'article                        
    time.sleep(1)                                                    
    page_article = requests.get(adresse, headers=ENTETES)            
    soupe_article = BeautifulSoup(page_article.text, "html.parser") 
    balise_resume = soupe_article.find("meta", attrs={"name": "description"})  
    if balise_resume:                                                
        resume = balise_resume.get("content", "")                    
    else:                                                            
        resume = ""                                                  

    if est_pertinent(titre + " " + resume):                          
        articles_retenus.append({
            "source": "AFNOR",
            "titre": titre,
            "date": date,
            "lien": adresse,
            "resume": resume,                                        
        })

#  AFFICHAGE 

for article in articles_retenus:
    print("[" + article["source"] + "]", article["titre"])
    print("Date :", article["date"])
    print("Lien :", article["lien"])
    print("Résumé :", article["resume"])                            
    print("=" * 50)

print()
print("Total d'articles récupérés :", total)
print("Articles GRC retenus :", len(articles_retenus))

# FICHIER CSV 

with open("veille.csv", "w", newline="", encoding="utf-8-sig") as fichier:
    colonnes = ["source", "titre", "date", "lien", "resume"]
    ecrivain = csv.DictWriter(fichier, fieldnames=colonnes, delimiter=";")
    ecrivain.writeheader()
    ecrivain.writerows(articles_retenus)

print("Fichier veille.csv créé !")



#  PAGE HTML 

STYLE = """
body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 30px; color: #222; }
h1 { margin: 0 0 5px 0; }
.bilan { color: #666; margin-bottom: 25px; }
.grille { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
.carte { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
.source { background: #1f4e79; color: white; padding: 3px 10px; border-radius: 20px; font-size: 13px; }
.carte h2 { font-size: 18px; margin: 12px 0 5px 0; }
.date { color: #888; font-size: 14px; margin: 0 0 10px 0; }
.carte a { display: inline-block; margin-top: 10px; color: #1f4e79; font-weight: bold; }
"""

cartes = ""

for article in articles_retenus:
    source = html.escape(article["source"])
    titre = html.escape(article["titre"])
    date = html.escape(article["date"])
    resume = html.escape(article["resume"])
    lien = html.escape(article["lien"])

    cartes = cartes + f"""
    <div class="carte">
        <span class="source">{source}</span>
        <h2>{titre}</h2>
        <p class="date">{date}</p>
        <p>{resume}</p>
        <a href="{lien}" target="_blank">Lire l'article →</a>
    </div>
    """

page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Veille GRC</title>
    <style>{STYLE}</style>
</head>
<body>
    <h1>Veille GRC</h1>
    <p class="bilan">{len(articles_retenus)} articles retenus sur {total} récupérés</p>
    <div class="grille">
        {cartes}
    </div>
</body>
</html>
"""

with open("veille.html", "w", encoding="utf-8") as fichier:
    fichier.write(page)

print("Page veille.html crée !")