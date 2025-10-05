import requests
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="darkgrid")
import urllib.parse as urlp
import io
import warnings
warnings.filterwarnings("ignore")
import os

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
    lines = ts_str.split("\n")
    parameters = {}
    for line in lines[2:11]:
        key,value = line.split("=")
        parameters[key] = value
    
    
    df = pd.read_table(io.StringIO(ts_str),sep="\t",
                       names=["time","data"],
                       header=10,parse_dates=["time"])
    return parameters, df

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
def print_full():
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

    df_temp = parse_time_series(
                get_time_series(
                    start_date="2017-01-01T00", 
                    end_date="2023-12-01T23",
                    latitude=latitude,
                    longitude=longitude,
                    variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Tair"
            )
        )
    return df_RadWave, df_soil, df_temp
month = int(input("Ingrese el mes (1-12): "))
day = int(input("Ingrese el día (1-31): "))
d = {'time': pd.to_datetime(df_precip[1]['time'], unit='s'), 
    'Rainf': df_precip[1]['data']}
    
df = pd.DataFrame(data=d)
df.head()
df.to_csv('extracr.csv', index=False)
time.sleep(5)

per_hour = np.array([])

for i in range(0, 24):
    ids_comunes = [f"{year}-{month:02d}-{day:02d} {i:02d}:00:00" for year in range(2018, 2024)]
    filtrado = df[df['time'].isin(ids_comunes)]
    columna_filtrado = filtrado['Rainf']
    promRainf = columna_filtrado.mean()
    print("El promedio de precipitacion es:", promRainf, "A la hora:", i, ":00:00")
    per_hour = np.append(per_hour, promRainf)

print(per_hour.mean())

print("\nLo quieres imprimir? (s/n)")
if input().lower() == 's':
    df_RadWave, df_soil, df_temp = print_full()
    d = {'time': pd.to_datetime(df_precip[1]['time'], unit='s'), 
    'Rainf': df_precip[1]['data'],
    'SoilM_0_100cm': df_soil[1]['data'],
    'SWdown': df_RadWave[1]['data'],
    'Tair': df_temp[1]['data']}
    df2 = pd.DataFrame(data=d)
    df2.head()
    df2.to_csv('extracr2.csv', index=False)
    time.sleep(5)
    ids_comunes = [f"{year}-{month:02d}-{day:02d} 00:00:00" for year in range(2018, 2024)]
    filtrado2 = df2[df2['time'].isin(ids_comunes)]
    print(filtrado2)
    columna_filtrado = filtrado2['Rainf']
    promRain = columna_filtrado.mean()
    columna_filtrado2 = filtrado2['SoilM_0_100cm']
    promSoilM = columna_filtrado2.mean()
    columna_filtrado3 = filtrado2['SWdown']
    promSWdown = columna_filtrado3.mean()
    columna_filtrado4 = filtrado2['Tair']
    promTemp = columna_filtrado4.mean()
    print("El promedio de humedad es:", promSoilM)
    print("El promedio de radiacion solar es:", promSWdown)
    print("El promedio de temperatura es:", promTemp)
    rain_probability = (per_hour.mean()) * 100 if len(per_hour) > 0 else 0
    f = open(f"resultados_{month:02d}_{day:02d}.txt", "w")
    f.write(f"Datos climáticos para {month:02d}-{day:02d} (años 2018-2023)\n\n")
    f.write(f"Promedio de temperatura (Tair): {promTemp}\n")
    f.write(f"Promedio de radiación solar de onda corta (SWdown): {promSWdown}\n")
    f.write(f"Promedio de precipitación (Rainf): {per_hour.mean()}\n")
    f.write(f"Promedio de humedad del suelo (SoilM_0_100cm): {promSoilM}\n\n")
    f.write(f"Probabilidad histórica de lluvia: {rain_probability:.1f}%\n\n")
    f.close()
    print("Datos guardados en resultados_{:02d}_{:02d}.txt".format(month, day))
# =============================================
#  BLOQUE PARA ESTIMAR PORCENTAJE DE LLUVIA
# =============================================

rain_probability = (per_hour.mean()) * 100 if len(per_hour) > 0 else 0
print(f"Probabilidad histórica de lluvia en {month:02d}-{day:02d}: {rain_probability:.1f}%")

ruta1 = 'extracr.csv'
if os.path.exists(ruta1):
    os.remove(ruta1)

ruta2 = 'extracr2.csv'
if os.path.exists(ruta2):
    os.remove(ruta2)