from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_FEED = "https://www.infobae.com/arc/outboundfeeds/rss/"
HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto de aprendizaje de charly.notes@gmail.com)"}
ARCHIVO = Path(__file__).resolve().parent.parent / "data" / "noticias_infobae.csv"


def descargar_feed():
    r = requests.get(URL_FEED, headers=HEADERS, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "xml")

    filas = []
    for it in soup.find_all("item"):
        cuerpo = it.find("content:encoded")
        texto = (BeautifulSoup(cuerpo.text, "lxml").get_text(" ", strip=True)
                 if cuerpo else "")
        filas.append({
            "titulo": it.find("title").text.strip(),
            "resumen": it.find("description").text.strip() if it.find("description") else "",
            "texto": texto,
            "fecha": it.find("pubDate").text,
            "url": it.find("link").text.strip(),
        })
    return pd.DataFrame(filas)


def actualizar_corpus(archivo=ARCHIVO):
    archivo.parent.mkdir(parents=True, exist_ok=True)
    nuevo = descargar_feed()
    if archivo.exists():
        viejo = pd.read_csv(archivo)
    else:
        viejo = pd.DataFrame(columns=nuevo.columns)
    total = pd.concat([viejo, nuevo]).drop_duplicates(subset="url")
    total.to_csv(archivo, index=False)
    print(f"Nuevas: {len(total) - len(viejo)} | Total: {len(total)}")


if __name__ == "__main__":
    actualizar_corpus()