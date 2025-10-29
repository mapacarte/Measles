import os, requests
PORTAL_BASE = "https://asu.maps.arcgis.com"

def get_access_token():
    data = {
        "client_id": os.environ["ARCGIS_CLIENT_ID"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["ARCGIS_REFRESH_TOKEN"],
        "f": "json",
    }
    if os.environ.get("ARCGIS_CLIENT_SECRET"):
        data["client_secret"] = os.environ["ARCGIS_CLIENT_SECRET"]

    r = requests.post(f"{PORTAL_BASE}/sharing/rest/oauth2/token", data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]
