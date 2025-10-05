import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="darkgrid")
import urllib.parse as urlp
import io
import warnings
warnings.filterwarnings("ignore")

def get_time_series(start_date,end_date,latitude,longitude,variable):
    base_url = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"
    query_parameters = {
        "variable": variable,
        "type": "asc2",
        "location": f"GEOM:POINT({longitude}, {latitude})",
        "startDate": start_date,
        "endDate": end_date,
    }
    full_url = base_url+"?"+ \
         "&".join(["{}={}".format(key,urlp.quote(query_parameters[key])) for key in query_parameters])
    print(full_url)
    iteration = 0
    done = False
    while not done and iteration < 5:
        r=requests.get(full_url)
        if r.status_code == 200:
            done = True
        else:
            iteration +=1
    
    if not done:
        raise Exception(f"Error code {r.status_code} from url {full_url} : {r.text}")
    
    return r.text

def parse_time_series(ts_str):
    """
    Parses the response from data rods.
    """
    lines = ts_str.split("\n")
    parameters = {}
    for line in lines[2:11]:
        key,value = line.split("=")
        parameters[key] = value
    
    
    df = pd.read_table(io.StringIO(ts_str),sep="\t",
                       names=["time","data"],
                       header=10,parse_dates=["time"])
    return parameters, df


def Temp(T):
    return (T - 32) * 5.0/9.0

latitude = 38.89
longitude = -88.93

df_precip = parse_time_series(
            get_time_series(
                start_date="2017-01-01T00", 
                end_date="2023-12-01T23",
                latitude=latitude,
                longitude=longitude,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Rainf"
            )
        )

df_RadWave = parse_time_series(
            get_time_series(
                start_date="2017-01-01T00", 
                end_date="2023-12-01T23",
                latitude=latitude,
                longitude=longitude,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:SWdown"
            )
        )

df_soil = parse_time_series(
            get_time_series(
                start_date="2017-01-01T00", 
                end_date="2023-12-01T23",
                latitude=latitude,
                longitude=longitude,
                variable="NLDAS2:NLDAS_NOAH0125_H_v2.0:SoilM_0_100cm"
          )
        )

df_evap = parse_time_series(
            get_time_series(
                start_date="2017-07-01T00", 
                end_date="2023-07-01T00",
                latitude=38.89,
                longitude=-88.18,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:PotEvap"
                )
            )

df_temp = parse_time_series(
            get_time_series(
                start_date="2017-01-01T00", 
                end_date="2023-12-01T23",
                latitude=latitude,
                longitude=longitude,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Tair"
          )
        )

month = int(input("Ingrese el mes (1-12): "))
day = int(input("Ingrese el día (1-31): "))
hour = int(input("Ingrese la hora (0-23): "))

df_soil[1]['data']
d = {'time': pd.to_datetime(df_precip[1]['time'], unit='s'), 
    'Rainf': df_precip[1]['data'], 
    'SoilM_0_100cm': df_soil[1]['data'],
    'SWdown': df_RadWave[1]['data'],
    'Tair': df_temp[1]['data'],
    'PotEvap': df_evap[1]['data']}
    
df = pd.DataFrame(data=d)
df.head()
df.to_csv('extracr.csv', index=False)
time.sleep(5)
ids_comunes = [f"{year}-{month:02d}-{day:02d} {hour:02d}:00:00" for year in range(2018, 2024)]
filtrado = df[df['time'].isin(ids_comunes)]
print(filtrado)
columna_filtrado = filtrado['Rainf']
promRainf = columna_filtrado.mean()
columna_filtrado2 = filtrado['SoilM_0_100cm']
promSoilM = columna_filtrado2.mean()
columna_filtrado3 = filtrado['SWdown']
promSWdown = columna_filtrado3.mean()
columna_filtrado4 = filtrado['Tair']
promTemp = columna_filtrado4.mean()
columna_filtrado5 = filtrado['PotEvap']
promEvap = columna_filtrado5.mean()
print("El promedio de evaporacion potencial es:", promEvap)
print("El promedio de temperatura es:", promTemp)
print("El promedio de radiacion solar de onda corta es:", promSWdown)
print("El promedio de precipitacion es:", promRainf)
print("El promedio de humedad es:", promSoilM)

# =============================================
# BLOQUE PARA ESTIMAR PORCENTAJE DE LLUVIA
# =============================================
rain_occurrences = (filtrado['Rainf'] > 0).sum()  
total_years = len(filtrado)
rain_probability = (rain_occurrences / total_years) * 100 if total_years > 0 else 0
print(f"Probabilidad histórica de lluvia en {month:02d}-{day:02d} (a las {hour:02d}:00): {rain_probability:.1f}%")