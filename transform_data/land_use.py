from pathlib import Path
import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Clasificarea codurilor Corine Land Cover 2018 conform metodologiei RENewLand (Tabelul 1, pag. 4, 6, 8)
CLC_WATER_CODES = ["511", "512", "521", "522", "523"]          # Corpuri de apa -> Excludere 0-500 m
CLC_WETLAND_CODES = ["411", "412", "421", "422", "423"]        # Zone umede -> Excludere 0-500 m
CLC_VEGETATION_CODES = [                                       # Vegetatie valoroasa (paduri & pajisti HNV) -> Excludere 0-250 m + Scorare 250-450+ m
    "311", "312", "313",                                       # Paduri (foioase, conifere, mixte)
    "321", "322", "323", "324",                                # Pajisti naturale si tufarisuri de tranzitie
]
CLC_SETTLEMENT_CODES = ["111", "112"]                          # Zone locuite -> Excludere pe suprafata proprie (X) la Solar
CLC_BUILT_UP_CODES = [                                         # Alte zone construite (inclusiv aeroporturi 124) -> Excludere pe suprafata proprie (X) la Solar
    "121", "122", "123", "124",
    "131", "132", "133",
    "141", "142",
]

# Coduri cu adecvare pozitiva la Energie Solara Fotovoltaica (Tabelul 1 & pag. 4, 11, 17):
CLC_ARABLE_AND_BARE_CODES = [                                  # Scor 10: Terenuri arabile (X = 10 in Tabelul 1) si terenuri degradate/fara vegetatie
    "211", "212", "213",
    "331", "332", "333", "334",
]
CLC_PASTURE_AND_MIXED_AGRI_CODES = [                           # Scor 7: Pasuni si terenuri predominant agricole (a 2-a categorie adecvata in raport, pag. 11 & 17)
    "231", "241", "242", "243", "244",
]
CLC_VINEYARDS_ORCHARDS_CODES = ["221", "222", "223"]           # Scor 1: Podgorii si livezi (X = 1 in Tabelul 1 la Energie solara fotovoltaica)


def _assign_solar_lu_score(code: str) -> int:
    """Atribuie scorul de utilizare a terenului (0-10) pentru Energie Solara conform Tabelului 1."""
    code_str = str(code).strip()
    if code_str in CLC_ARABLE_AND_BARE_CODES:
        return 10
    if code_str in CLC_PASTURE_AND_MIXED_AGRI_CODES:
        return 7
    if code_str in CLC_VINEYARDS_ORCHARDS_CODES:
        return 1
    return 0


def land_use():
    """Decupeaza Corine Land Cover 2018, ataseaza legenda si scorurile de adecvare din Tabelul 1,
    si extrage cele 5 straturi tematice de restrictie/distanta:
    - data/land_use.gpkg (stratul complet cu coloanele 'solar_lu_score', 'is_excluded_solar', 'LABEL3', 'RGB')
    - data/water_bodies.gpkg (Corpuri de apa: coduri 511-523, pt. buffer 0-500 m)
    - data/wetlands.gpkg (Zone umede: coduri 411-423, pt. buffer 0-500 m)
    - data/valuable_vegetation.gpkg (Vegetatie valoroasa: paduri 311-313 si pajisti HNV 321-324, pt. buffer 0-250 m si scorare pana la >450 m)
    - data/settlements_clc.gpkg (Zone locuite: coduri 111-112, pt. excludere X si harti Fig. 3/7)
    - data/built_up_clc.gpkg (Alte zone construite + aeroporturi: coduri 121-142, pt. excludere X)
    """
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"

    limita = gpd.read_file(buffer_path).to_crs("EPSG:3844")
    clc_dir = PROJECT_ROOT / "raw_data" / "clc_2018(land use Romania)"
    clc_path = clc_dir / "Romania_18_st.shp"
    legend_path = clc_dir / "Legend" / "CLC_legend.csv"

    clc_gdf = gpd.read_file(clc_path).to_crs("EPSG:3844")
    clc_clip = gpd.clip(clc_gdf, limita).copy()

    clc_clip["code_18"] = clc_clip["code_18"].astype(str).str.strip()

    # Atasare legenda oficiala CLC (LABEL3 si culoarea RGB pentru Fig. 4 / Fig. 8)
    if legend_path.exists():
        legend_df = pd.read_csv(legend_path, sep=";")
        legend_df["CLC_CODE"] = legend_df["CLC_CODE"].astype(str).str.strip()
        clc_clip = clc_clip.merge(
            legend_df[["CLC_CODE", "LABEL3", "RGB"]],
            left_on="code_18",
            right_on="CLC_CODE",
            how="left",
        )

    # Calcul scor utilizare teren (Tabelul 1) si indicator de excludere pe suprafata proprie
    clc_clip["solar_lu_score"] = clc_clip["code_18"].apply(_assign_solar_lu_score)
    clc_clip["is_excluded_solar"] = clc_clip["solar_lu_score"] == 0

    # Salvare strat complet
    clc_clip.to_file(data_dir / "land_use.gpkg", driver="GPKG")

    # Extragere sub-straturi tematice pentru calculul zonelor tampon (Tabelul 1)
    sublayers = {
        "water_bodies.gpkg": CLC_WATER_CODES,
        "wetlands.gpkg": CLC_WETLAND_CODES,
        "valuable_vegetation.gpkg": CLC_VEGETATION_CODES,
        "settlements_clc.gpkg": CLC_SETTLEMENT_CODES,
        "built_up_clc.gpkg": CLC_BUILT_UP_CODES,
    }

    for filename, codes in sublayers.items():
        sub_gdf = clc_clip[clc_clip["code_18"].isin(codes)]
        if not sub_gdf.empty:
            sub_gdf.to_file(data_dir / filename, driver="GPKG")

    return clc_clip
