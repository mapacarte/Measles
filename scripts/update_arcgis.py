import os
import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from datetime import datetime

# Connect to ArcGIS Online
print("Connecting to ArcGIS Online...")
def create_gis(): 
    client_id = os.getenv("ARCGIS_CLIENT_ID") 
    client_secret = os.getenv("ARCGIS_CLIENT_SECRET") 
    
gis = create_gis()

# Feature layer item IDs
COUNTY_LAYER_ID = os.environ.get("ARCGIS_RAW_MEASLES")
STATE_MONTH_LAYER_ID = os.environ.get("ARCGIS_STATE_MONTH")

# Load processed data
print("Loading processed data...")
df = pd.read_csv("docs/data/USMeaslesCases.csv")
print(f"Loaded {len(df)} county records")

# Update Daily County Cases Layer
print("\nUpdating county cases layer...")

# Get the feature layer
county_item = gis.content.get(COUNTY_LAYER_ID)
county_layer = county_item.layers[0]

# Prepare data for ArcGIS (add ObjectID if updating, or prepare for overwrite)
county_features = df.to_dict('records')

# Truncate and append (replace all data on update)
print("Truncating existing features...")
county_layer.manager.truncate()

print(f"Adding {len(county_features)} features...")
# Add features in batches (ArcGIS has limits, typically 2000 per request)
batch_size = 2000
for i in range(0, len(county_features), batch_size):
    batch = county_features[i:i+batch_size]
    # Convert to feature format
    features = [{"attributes": record} for record in batch]
    result = county_layer.edit_features(adds=features)
    print(f"  Added batch {i//batch_size + 1}: {len(batch)} features")

print("County layer updated successfully!")

# Aggregate by State and Month
print("\nAggregating data by state and month...")

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])
df['year_month'] = df['date'].dt.to_period('M').astype(str)

# Aggregate by state and month (sum all outcome types together)
agg_df = (
    df.groupby(['state', 'year_month'])
    .agg({'cases': 'sum'})
    .reset_index()
)

# Add additional useful columns
agg_df['year'] = pd.to_datetime(agg_df['year_month']).dt.year
agg_df['month'] = pd.to_datetime(agg_df['year_month']).dt.month
agg_df['month_name'] = pd.to_datetime(agg_df['year_month']).dt.strftime('%B')
agg_df['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print(f"Aggregated to {len(agg_df)} state-month records")

# Update State-Month Aggregated Layer
print("\nUpdating state-month aggregated layer...")

# Get the feature layer
state_month_item = gis.content.get(STATE_MONTH_LAYER_ID)
state_month_layer = state_month_item.layers[0]

# Prepare aggregated data
agg_features = agg_df.to_dict('records')

# Truncate and append
print("Truncating existing features...")
state_month_layer.manager.truncate()

print(f"Adding {len(agg_features)} aggregated features...")
batch_size = 2000
for i in range(0, len(agg_features), batch_size):
    batch = agg_features[i:i+batch_size]
    features = [{"attributes": record} for record in batch]
    result = state_month_layer.edit_features(adds=features)
    print(f"  Added batch {i//batch_size + 1}: {len(batch)} features")

print("State-month layer updated successfully!")

# Update layer metadata
print("\nUpdating layer metadata...")
state_month_item.update(
    item_properties={
        "snippet": f"Measles cases aggregated by state and month. Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
)

print("\n✅ All ArcGIS layers updated successfully!")
print(f"   - County records: {len(df)}")
print(f"   - State-month records: {len(agg_df)}")

print(f"   - Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

