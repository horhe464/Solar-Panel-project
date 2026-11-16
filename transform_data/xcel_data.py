import re
import subprocess
import unicodedata
import urllib.request
from pathlib import Path

import geopandas as gpd
import pandas as pd
from nume_zona import nume_zona

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RSCRIPT_PATH = Path(r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe")


def normalize_uat_name(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    s = s.upper().replace("-", " ").strip()
    s = re.sub(r"^(MUNICIPIUL|ORASUL|ORAS|COMUNA)\s+", "", s)
    return re.sub(r"\s+", " ", s)


def descarca_venituri(an: int = 2025) -> pd.DataFrame:
    venituri_path = PROJECT_ROOT / "raw_data" / "venituri_per_uat.xlsx"
    if not venituri_path.exists():
        url = f"http://www.dpfbl.mdrap.ro/venituri_si_cheltuieli_uat/Anexa24_{an}.xlsx"
        urllib.request.urlretrieve(url, venituri_path)

    venituri = pd.read_excel(venituri_path, sheet_name="Sheet2", usecols=[0, 1])
    nume_judet = normalize_uat_name(nume_zona())

    venituri = venituri.iloc[5:, :2]
    venituri.columns = ["Cod fiscal - UAT", "Venituri totale"]
    venituri = venituri.dropna(subset=["Cod fiscal - UAT"]).reset_index(drop=True)

    judet_index = venituri.index[venituri["Cod fiscal - UAT"].apply(normalize_uat_name).str.contains(nume_judet)][0]
    rest_venituri = venituri.iloc[judet_index + 1:]
    next_judet = rest_venituri.index[rest_venituri["Cod fiscal - UAT"].str.contains("Judetul:")]
    end_index = next_judet[0] if len(next_judet) > 0 else len(venituri)

    venituri_judet = venituri.iloc[judet_index + 8:end_index].reset_index(drop=True)
    venituri_judet = venituri_judet.loc[venituri_judet["Cod fiscal - UAT"].str.contains("-")].copy()
    venituri_judet["UAT"] = venituri_judet["Cod fiscal - UAT"].str.split("-", n=1).str[1].apply(normalize_uat_name)
    venituri_judet["Venituri totale"] = venituri_judet["Venituri totale"].astype(float).round(2)
    return venituri_judet.reset_index(drop=True)


def tempo_pop(an: int = 2025) -> pd.DataFrame:
    pop_path = PROJECT_ROOT / "raw_data" / "populatie_per_uat.xlsx"
    if not pop_path.exists():
        script_r = PROJECT_ROOT / "transform_data" / "tempo_pop.r"
        subprocess.run([str(RSCRIPT_PATH), str(script_r), str(an)], cwd=PROJECT_ROOT, check=True)

    pop = pd.read_excel(pop_path)
    nume_judet = normalize_uat_name(nume_zona())

    pop = pop[pop["Judet"].apply(normalize_uat_name) == nume_judet].copy()
    pop = pop.rename(columns={"SIRUTA_UAT": "SIRUTA UAT"}).reset_index(drop=True)
    pop["Populatie"] = pop["Populatie"].astype(float)
    pop["SIRUTA"] = pop["SIRUTA"].astype(str)
    pop["UAT"] = pop["UAT"].apply(normalize_uat_name)
    return pop[["SIRUTA UAT", "Populatie", "SIRUTA", "UAT"]]


def uat_economic(an: int = 2025) -> gpd.GeoDataFrame:
    venituri_judet = descarca_venituri(an)
    pop = tempo_pop(an)

    venit_pop = venituri_judet.merge(pop, on="UAT", how="right")
    venit_pop = venit_pop[["UAT", "SIRUTA", "Venituri totale", "Populatie"]]
    venit_pop["Venit per capita"] = (venit_pop["Venituri totale"] / venit_pop["Populatie"]).round(2)
    venit_pop["Economie Punctaj"] = venit_pop["Venit per capita"].rank(pct=True) * 100

    uat_path = PROJECT_ROOT / "data" / "uat.gpkg"
    uat = gpd.read_file(uat_path)
    uat = uat.loc[:, ["natCode", "geometry"]].rename(columns={"natCode": "SIRUTA"})
    uat["SIRUTA"] = uat["SIRUTA"].astype(str)

    gdf_uat_economic = uat.merge(venit_pop, on="SIRUTA", how="right")
    out_gpkg = PROJECT_ROOT / "data" / "uat_economic.gpkg"
    gdf_uat_economic.to_file(out_gpkg, driver="GPKG")

    return gdf_uat_economic
