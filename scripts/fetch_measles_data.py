# fetch_measles_data.py
import os
import requests
import pandas as pd

# fetch raw JHU csv
URL = (
    "https://raw.githubusercontent.com/"
    "CSSEGISandData/measles_data/main/"
    "measles_county_all_updates.csv"
)
resp = requests.get(URL)
resp.raise_for_status()

os.makedirs("docs/data", exist_ok=True)
raw_path = "docs/data/measles_raw.csv"
with open(raw_path, "wb") as f:
    f.write(resp.content)

# load
df = pd.read_csv(raw_path, dtype={"location_id": str})

# split out county & state
df[["county", "state"]] = df.location_name.str.split(", ", expand=True)

# upper-case & trim
df["county"] = df["county"].str.upper().str.strip()
df["state"]  = df["state"].str.upper().str.strip()
df["state"] = df["state"].str.title()
df['state'] = df['state'].str.replace('District Of Columbia', 'District of Columbia')

# 5) rename & select columns
df = (
    df
    .rename(columns={"value": "cases"})
    [["county", "state", "location_id", "date", "outcome_type", "cases"]]
)

# write to csv
out_path = "docs/data/USMeaslesCases.csv"
df.to_csv(out_path, index=False)
print(f"Wrote {len(df)} rows to {out_path}")
