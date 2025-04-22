import pandas as pd
import numpy as np
import os
import tarfile
import urllib.request
import gzip
import shutil
import re
from sklearn.preprocessing import StandardScaler
from utils.py import *

BASE_URL = "https://s3.opensky-network.org/data-samples/states/.2019-07-15"
HOURS = [f"{h:02d}" for h in range(24)]
MASTER_DF = []

for h in tqdm(HOURS, desc = 'Processing OpenSky data'): 
    # define download URL
    filename = f"states_2019-07-15-{h}.csv.tar"
    url = f"{BASE_URL}/{h}/{filename}"
    local_tar = f"./temp/{filename}"
    
    # download tarball from OpenSky
    os.makedirs("./temp", exist_ok=True)
    urllib.request.urlretrieve(url, local_tar)

    # extract .csv.gz
    with tarfile.open(local_tar, "r") as tar:
        tar.extractall("./temp")
        
    for name in os.listdir("./temp"):
        if name.endswith(".csv.gz") and name.startswith("states_2019-07-15"):
            gz_path = f"./temp/{name}"
            csv_path = gz_path[:-3]
    
            # decompress .gz
            with gzip.open(gz_path, 'rb') as f_in:
                with open(csv_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
    
            # load to pandas and filter
            df = pd.read_csv(csv_path)
            df.dropna(subset=["time", "callsign", "lat", "lon", "velocity", "heading", "baroaltitude"], inplace=True)
            MASTER_DF.append(df)
            os.remove(gz_path)
            os.remove(csv_path)

    os.remove(local_tar)

master_df = pd.concat(MASTER_DF, ignore_index=True)

master_df["callsign"] = master_df["callsign"].str.strip()
    
# transform heading to sin/cos 
heading_rad = np.deg2rad(master_df["heading"].values)
sin_heading = np.sin(heading_rad)
cos_heading = np.cos(heading_rad)
master_df["sin_heading"] = sin_heading
master_df["cos_heading"] = cos_heading
    
# remove invalid callsigns
print("Filtering callsigns...")
valid_mask = master_df['callsign'].apply(is_valid_callsign)
cleaned_data = master_df[valid_mask].copy()

# scale altitude and velocity globally
print("Scaling features...")
scaler = StandardScaler()
scaler.fit(cleaned_data[["velocity", "baroaltitude"]].values)
velocity = cleaned_data["velocity"].values.reshape(-1, 1)
altitude = cleaned_data["baroaltitude"].values.reshape(-1, 1)
scaled = scaler.transform(np.hstack([velocity, altitude]))
velocity_z = scaled[:, 0]
altitude_z = scaled[:, 1]
cleaned_data.loc[:, "velocity"] = velocity_z
cleaned_data.loc[:, "altitude"] = altitude_z

cleaned_filtered_data = cleaned_data[["time", "callsign", "lat", "lon", "velocity", "sin_heading", "cos_heading", "altitude"]]

# save locally as parquet (~11M rows, ~450MB)
cleaned_filtered_data.to_parquet("data/opensky_2019-07-15.parquet")
print("All hourly files processed and combined.")