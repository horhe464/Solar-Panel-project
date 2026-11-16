from pathlib import Path
import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLC_WATER_CODES = ["511", "512", "521", "522", "523"]
CLC_WETLAND_CODES = ["411", "412", "421", "422", "423"]
CLC_VEGETATION_CODES = ["311", "312", "313", "321", "322", "323", "324"]
CLC_SETTLEMENT_CODES = ["111", "112"]
CLC_BUILT_UP_CODES = ["121", "122", "123", "124", "131", "132", "133", "141", "142"]

CLC_ARABLE_AND_BARE_CODES = ["211", "212", "213", "331", "332", "333", "334"]
CLC_PASTURE_AND_MIXED_AGRI_CODES = ["231", "241", "242", "243", "244"]
CLC_VINEYARDS_ORCHARDS_CODES = ["221", "222", "223"]


def _assign_solar_lu_score(code: str) -> int:
    code_str = str(code).strip()
    if code_str in CLC_ARABLE_AND_BARE_CODES:
        return 10
    if code_str in CLC_PASTURE_AND_MIXED_AGRI_CODES:
        return 7
    if code_str in CLC_VINEYARDS_ORCHARDS_CODES:
        return 1
    return 0


def land_use():
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"

    limita = gpd.read_file(buffer_path).to_crs("EPSG:3844")
    clc_dir = PROJECT_ROOT / "raw_data" / "clc_2018(land use Romania)"
    clc_path = clc_dir / "Romania_18_st.shp"
    legend_path = clc_dir / "Legend" / "CLC_legend.csv"

    clc_gdf = gpd.read_file(clc_path).to_crs("EPSG:3844")
    clc_clip = gpd.clip(clc_gdf, limita).copy()

    clc_clip["code_18"] = clc_clip["code_18"].astype(str).str.strip()

    if legend_path.exists():
        legend_df = pd.read_csv(legend_path, sep=";")
        legend_df["CLC_CODE"] = legend_df["CLC_CODE"].astype(str).str.strip()
        clc_clip = clc_clip.merge(
            legend_df[["CLC_CODE", "LABEL3", "RGB"]],
            left_on="code_18",
            right_on="CLC_CODE",
            how="left",
        )

    clc_clip["solar_lu_score"] = clc_clip["code_18"].apply(_assign_solar_lu_score)
    clc_clip["is_excluded_solar"] = clc_clip["solar_lu_score"] == 0

    clc_clip.to_file(data_dir / "land_use.gpkg", driver="GPKG")

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
