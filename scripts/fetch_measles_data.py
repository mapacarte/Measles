# raw JHU data pipeline
import os
import requests

URL = (
    "https://raw.githubusercontent.com/"
    "CSSEGISandData/measles_data/main/"
    "measles_county_all_updates.csv"
)

resp = requests.get(URL)
resp.raise_for_status()

os.makedirs("docs/data", exist_ok=True)
with open("docs/data/USMeaslesCases.csv", "wb") as f:
    f.write(resp.content)
