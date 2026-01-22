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
    result = r.json()
    if "access_token" not in result:
        raise RuntimeError(f"Failed to get access token: {result}")
    return result["access_token"]
if __name__ == "__main__":
    token = get_access_token()
    print(token)
