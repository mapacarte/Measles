import os
import sys
import pandas as pd
from arcgis.gis import GIS
from datetime import datetime
import traceback

from token_helper import get_access_token

def create_gis():
    """Authenticate to ArcGIS Online using a short-lived access token."""
    access_token = get_access_token()
    print("Using short-lived access token.")
    return GIS("https://asu.maps.arcgis.com", token=access_token)

def get_layer_or_table(item):
    # Prefer layers, then tables
    if hasattr(item, "layers") and len(item.layers) > 0:
        print("Using feature layer (item.layers[0])")
        return item.layers[0], "layer"
    if hasattr(item, "tables") and len(item.tables) > 0:
        print("Using hosted table (item.tables[0])")
        return item.tables[0], "table"
    raise RuntimeError("Item has no layers or tables")

def truncate_or_delete(obj):
    # Try truncate; if unavailable, try delete_features(where="1=1")
    try:
        print("Trying manager.truncate()...")
        obj.manager.truncate()
    except Exception as e:
        print(f"truncate() failed: {e}. Trying delete_features(where='1=1')...")
        try:
            obj.delete_features(where="1=1")
        except Exception as e2:
            raise RuntimeError(f"Both truncate() and delete_features() failed: {e2}")

def record_cleaner(rec):
    # Return a dict of Python-native values (None for NaN, ISO string for Timestamp)
    cleaned = {}
    for k, v in rec.items():
        try:
            if pd.isna(v):
                cleaned[k] = None
                continue
        except Exception:
            # pd.isna may fail for some types; continue
            pass

        if isinstance(v, pd.Timestamp):
            cleaned[k] = v.strftime("%Y-%m-%dT%H:%M:%SZ")
            continue

        # convert numpy scalars to native
        try:
            if hasattr(v, "item"):
                v = v.item()
        except Exception:
            pass

        # leave as-is for strings, ints, floats, booleans
        cleaned[k] = v
    return cleaned

def upload_records(obj, kind, records, batch_size=2000):
    # ArcGIS edit_features expects list of {"attributes": {...}}
    features = [{"attributes": record_cleaner(rec)} for rec in records]
    print(f"Adding {len(features)} features to {kind}...")
    for i in range(0, len(features), batch_size):
        batch = features[i:i+batch_size]
        result = obj.edit_features(adds=batch)
        print(f"  Added batch {i//batch_size + 1}: {len(batch)} features, result: {result}")

def main():
    print("Connecting to ArcGIS Online...")
    gis = create_gis()

    COUNTY_LAYER_ID = os.environ.get("ARCGIS_RAW_MEASLES")
    STATE_MONTH_LAYER_ID = os.environ.get("ARCGIS_STATE_MONTH")
    if not COUNTY_LAYER_ID or not STATE_MONTH_LAYER_ID:
        raise RuntimeError("Missing ARCGIS_RAW_MEASLES or ARCGIS_STATE_MONTH environment variables.")

    print("Loading processed data...")
    df = pd.read_csv("docs/data/USMeaslesCases.csv", dtype={"location_id": str})
    print(f"Loaded {len(df)} county records")

    # Keep a copy for aggregations; we'll convert date for upload separately
    upload_df = df.copy()

    print("\nUpdating county cases layer...")
    county_item = gis.content.get(COUNTY_LAYER_ID)
    if county_item is None:
        raise RuntimeError(f"Could not find item with id {COUNTY_LAYER_ID}")
    county_obj, county_kind = get_layer_or_table(county_item)

    # Prepare upload DataFrame
    # Convert pandas NaT -> None and Timestamps to ISO; we'll do this in record_cleaner per-record
    # Optionally convert date column to pd.Timestamp to ensure consistent formatting
    if "date" in upload_df.columns:
        upload_df["date"] = pd.to_datetime(upload_df["date"], errors="coerce")

    county_records = upload_df.to_dict("records")

    print("Truncating existing features/rows...")
    truncate_or_delete(county_obj)

    upload_records(county_obj, county_kind, county_records)

    print("County layer/table updated successfully!")

    # Aggregate by State and Month
    print("\nAggregating data by state and month...")
    # Use the original df (not the upload_df which had date converted) but ensure parsing
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    agg_df = (
        df.groupby(["state", "year_month"])
        .agg({"cases": "sum"})
        .reset_index()
    )

    agg_df["year"] = pd.to_datetime(agg_df["year_month"]).dt.year
    agg_df["month"] = pd.to_datetime(agg_df["year_month"]).dt.month
    agg_df["month_name"] = pd.to_datetime(agg_df["year_month"]).dt.strftime("%B")
    agg_df["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Aggregated to {len(agg_df)} state-month records")

    print("\nUpdating state-month aggregated layer...")
    state_item = gis.content.get(STATE_MONTH_LAYER_ID)
    if state_item is None:
        raise RuntimeError(f"Could not find item with id {STATE_MONTH_LAYER_ID}")
    state_obj, state_kind = get_layer_or_table(state_item)
    
    #keep_cols = ["state", "year_month", "cases"]
    #agg_df = agg_df[keep_cols].copy()

    agg_records = agg_df.to_dict("records")

    print("Truncating existing aggregated features/rows...")
    truncate_or_delete(state_obj)

    upload_records(state_obj, state_kind, agg_records)

    print("State-month layer/table updated successfully!")

    state_item.update(
        item_properties={
            "snippet": f"Measles cases aggregated by state and month. Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    )

    print("\n All ArcGIS layers/tables updated successfully!")
    print(f"   - County records: {len(df)}")
    print(f"   - State-month records: {len(agg_df)}")
    print(f"   - Updated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

