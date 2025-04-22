import numpy as np

# Selected major airlines to include in search results
airline_icao_codes = [
    # Star Alliance
    'AEE', 'ACA', 'CCA', 'AIC', 'ANZ', 'ANA', 'AAR', 'AUA', 'AVA', 'BEL', 'CMP', 'CTN', 
    'MSR', 'ETH', 'EVA', 'LOT', 'DLH', 'CSZ', 'SIA', 'SAA', 'SWR', 'TAP', 'THA', 'THY',

    # Oneworld
    'BAW', 'CPA', 'FJI', 'FIN', 'IBE', 'JAL', 'MAS', 'QFA', 'QTR', 'RAM', 'RJA', 'ALK',

    # SkyTeam
    'ARG', 'AMX', 'AEA', 'AFR', 'CAL', 'CES', 'GIA', 'KQA', 'KLM', 'KAL', 'MEA', 'SVA',
    'SAS', 'ROT', 'HVN', 'VIR', 'CXA', 'AFL', 

    # Other flag carriers
    'BBC', 'TAM', 'EIN', 'ELY', 'BWA', 'PIA', 'ETD', 'UAE', 'TUA', 'UZB', 'VCV', 'PAL', 
    'MGL', 'KZR', 'GFA', 'AUI', 'TAR', 'DAH',

    # Low cost carriers
    'RYR', 'IGO', 'EZY', 'AXM', 'GLO', 'NOZ', 'VLG', 'WZZ', 'JST',

    # U.S. carriers
    'UAL', 'AAL', 'DAL', 'ENY'
]

# Specific flight numbers for trunk routes that flew on July 15, 2019.
# Aggregated to form a single vectors for each trunk route.
sfo_lax = ['UAL2757', 'DAL409', 'UAL1200', 'UAL257', 'DAL2861', 'UAL613', 'DAL664', 'UAL256', 'DAL2600', 'AAL1851']
den_ord = ['UAL1938', 'UAL781', 'UAL301', 'AAL2771', 'UAL532', 'UAL682', 'AAL2780', 'UAL336', 'AAL2470', 'AAL773']
dfw_atl = ['DAL2010', 'AAL2749', 'DAL1890', 'DAL1966', 'AAL1309', 'DAL2310', 'DAL2269', 'AAL333', 'DAL1513', 'AAL2403']
dca_bos = ['AAL2150', 'AAL2148', 'AAL2160', 'AAL2169', 'AAL2139', 'AAL2170', 'AAL2119', 'AAL2149', 'AAL2120', 'AAL2134']
ord_lga = ['UAL1823', 'UAL1606', 'AAL129', 'AAL398', 'AAL527', 'DAL379', 'DAL585', 'UAL509', 'DAL2775', 'UAL639'] 
lax_jfk = ['AAL10', 'DAL1908', 'DAL1436', 'AAL118', 'DAL1258', 'AAL2', 'DAL2164', 'AAL238', 'AAL4', 'DAL816']
iah_ord = ['UAL2131', 'UAL1854', 'UAL2246', 'ENY3331', 'UAL1835', 'ENY3621', 'UAL1403', 'UAL1160', 'AAL869', 'UAL1899']
sfo_sea = ['UAL800', 'DAL2787', 'UAL2161', 'DAL0856', 'UAL1074', 'UAL351', 'UAL618', 'DAL2490', 'DAL2429', 'DAL1470']
atl_mco = ['DAL1418', 'DAL863', 'DAL804', 'DAL1883', 'DAL1905', 'DAL2428', 'DAL897', 'DAL768', 'DAL1118', 'DAL186']
lax_atl = ['DAL1901', 'AAL1071', 'DAL2213', 'DAL2270', 'DAL954', 'DAL1592', 'DAL2714', 'DAL1954', 'DAL1140', 'DAL516']
routes = [sfo_lax, den_ord, dfw_atl, dca_bos, ord_lga, lax_jfk, iah_ord, sfo_sea, atl_mco, lax_atl]

MAX_FLIGHT_DURATION = 8 * 3600  # 8 hours in seconds
RESAMPLE_INTERVAL = 60  # seconds
TARGET_LENGTH = 200 # target vector dimension for similarity

def is_valid_callsign(callsign):
    '''
    Returns true if input is of expected ICAO callsign format. 
    '''
    if not isinstance(callsign, str):
        return False

    callsign = callsign.strip().upper()

    # must be at least 4 chrs (eg 'UAL1') and at most 8
    if not (4 <= len(callsign) <= 8):
        return False

    prefix = callsign[:3]
    suffix = callsign[3:]

    # prefix must be a major intl airline
    if prefix not in airline_icao_codes:
        return False   

    # suffix: 1–4 digits, possibly ending in 1 letter
    if not re.fullmatch(r'\d{1,4}[A-Z]?', suffix):
        return False

    return True

def is_non_us_callsign(callsign):
    prefix = callsign[:3]
    if prefix in ['UAL', 'DAL', 'AAL', 'ENY']:
        return False
    return True

def preprocess_flight(df_flight):
    df_flight = df_flight.sort_values("time")
    duration = df_flight["time"].iloc[-1] - df_flight["time"].iloc[0]
    
    if duration > MAX_FLIGHT_DURATION:
        return None
    
    start_time = df_flight["time"].iloc[0]
    df_flight["elapsed"] = df_flight["time"] - start_time
    # resample to 200 steps
    idxs = np.linspace(0, len(df_flight) - 1, TARGET_LENGTH).astype(int)
    df_flight = df_flight.iloc[idxs]
    
    origin_lat = df_flight.iloc[0]["lat"]
    origin_lon = df_flight.iloc[0]["lon"]
    df = df_flight.copy()
    df["delta_lat"] = df["lat"] - origin_lat
    df["delta_lon"] = df["lon"] - origin_lon

    return df[["delta_lat", "delta_lon", "velocity", "sin_heading", "cos_heading", "altitude"]]

def extract_flight(data, callsign):
    return data[data["callsign"] == callsign]

def aggregate_route(data, callsigns):
    '''
    Computes aggregate telemetry vectors for each trunk route. 
    '''
    matrices = []
    for call in callsigns:
        df_flight = extract_flight(data, call)
        traj = preprocess_flight(df_flight)
        if traj is None:
            continue
        matrices.append(traj)

    if len(matrices) == 0:
        return None

    # shape: (num_flights, 200, 6)
    stacked = np.stack(matrices, axis=0)
    aggregate = stacked.mean(axis=0) 

    return aggregate