import os
import sys
import pandas as pd
from arcgis.gis import GIS
from datetime import datetime

def create_gis():
    client_id = os.getenv("ARCGIS_CLIENT_ID")
    client_secret = os.getenv("ARCGIS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Missing ARCGIS_CLIENT_ID or ARCGIS_CLIENT_SECRET environment variables.")
    # ASU ArcGIS Online, NOT arcgis.com
    return GIS("https://asu.maps.arcgis.com", client_id=client_id, client_secret=client_secret)

def main():
    print("Connecting to ArcGIS Online...")
    gis = create_gis()

    # Feature layer item IDs (validate)
    COUNTY_LAYER_ID = os.environ.get("ARCGIS_RAW_MEASLES")
    STATE_MONTH_LAYER_ID = os.environ.get("ARCGIS_STATE_MONTH")
    if not COUNTY_LAYER_ID or not STATE_MONTH_LAYER_ID:
        raise RuntimeError("Missing ARCGIS_RAW_MEASLES or ARCGIS_STATE_MONTH environment variables.")

    # Load processed data
    print("Loading processed data...")
    df = pd.read_csv("docs/data/USMeaslesCases.csv")
    print(f"Loaded {len(df)} county records")

    # Update Daily County Cases Layer
    print("\nUpdating county cases layer...")

    # Get the feature layer item
    county_item = gis.content.get(COUNTY_LAYER_ID)
    if county_item is None:
        raise RuntimeError(f"Could not find item with id {COUNTY_LAYER_ID}")
    county_layer = county_item.layers[0]

    # Prepare data for ArcGIS - ensure types are basic Python types
    # Convert pandas NaNs to None and datetimes to ISO strings (or epoch ms if required by the layer)
    df = df.fillna(value=None)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    county_features = []
    for rec in df.to_dict('records'):
        # ArcGIS expects native Python types, not numpy types
        rec_clean = {k: (None if pd.isna(v) else (int(v) if isinstance(v, (float,)) and pd.notna(v) and str(v).isdigit() else v)) for k, v in rec.items()}
        county_features.append({"attributes": rec_clean})

    # Truncate & append
    print("Truncating existing features...")
    county_layer.manager.truncate()

    print(f"Adding {len(county_features)} features...")
    batch_size = 2000
    for i in range(0, len(county_features), batch_size):
        batch = county_features[i:i+batch_size]
        result = county_layer.edit_features(adds=batch)
        print(f"  Added batch {i//batch_size + 1}: {len(batch)} features, result: {result}")

    print("County layer updated successfully!")

    # Aggregate by State and Month
    print("\nAggregating data by state and month...")
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M').astype(str)

    agg_df = (
        df.groupby(['state', 'year_month'])
        .agg({'cases': 'sum'})
        .reset_index()
    )

    agg_df['year'] = pd.to_datetime(agg_df['year_month']).dt.year
    agg_df['month'] = pd.to_datetime(agg_df['year_month']).dt.month
    agg_df['month_name'] = pd.to_datetime(agg_df['year_month']).dt.strftime('%B')
    agg_df['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    print(f"Aggregated to {len(agg_df)} state-month records")

    # Update State-Month Aggregated Layer
    print("\nUpdating state-month aggregated layer...")
    state_month_item = gis.content.get(STATE_MONTH_LAYER_ID)
    if state_month_item is None:
        raise RuntimeError(f"Could not find item with id {STATE_MONTH_LAYER_ID}")
    state_month_layer = state_month_item.layers[0]

    agg_features = []
    for rec in agg_df.to_dict('records'):
        agg_features.append({"attributes": {k: (None if pd.isna(v) else v) for k, v in rec.items()}})

    print("Truncating existing features...")
    state_month_layer.manager.truncate()

    print(f"Adding {len(agg_features)} aggregated features...")
    for i in range(0, len(agg_features), batch_size):
        batch = agg_features[i:i+batch_size]
        result = state_month_layer.edit_features(adds=batch)
        print(f"  Added batch {i//batch_size + 1}: {len(batch)} features, result: {result}")

    print("State-month layer updated successfully!")

    # Update item metadata
    state_month_item.update(
        item_properties={
            "snippet": f"Measles cases aggregated by state and month. Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    )

    print("\n✅ All ArcGIS layers updated successfully!")
    print(f"   - County records: {len(df)}")
    print(f"   - State-month records: {len(agg_df)}")
    print(f"   - Updated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Print full exception and exit non-zero so GitHub Actions reports failure with a clear message
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
