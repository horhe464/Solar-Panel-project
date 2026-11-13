from pathlib import Path
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def land_use():
    """Decupeaza Corine Land Cover 2018 pe zona tampon de 1 km a judetului si il salveaza in data/land_use.gpkg."""
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"

    limita = gpd.read_file(buffer_path).to_crs("EPSG:3844")
    clc_path = PROJECT_ROOT/ "raw_data"/ "clc_2018(land use Romania)"/ "Romania_18_st.shp"

    clc_gdf = gpd.read_file(clc_path).to_crs("EPSG:3844")
    clc_clip = gpd.clip(clc_gdf, limita)
    clc_clip.to_file(data_dir / "land_use.gpkg", driver="GPKG")
    return clc_clip
