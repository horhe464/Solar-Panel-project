from pathlib import Path
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def arii_protejate():
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"

    limita = gpd.read_file(buffer_path).to_crs("EPSG:3844")
    arii_path = PROJECT_ROOT / "raw_data" / "Limite_arii_naturale_protejate" / "ARII_PROTEJATE_EPSG_3844.shp"

    arii_gdf = gpd.read_file(arii_path).to_crs("EPSG:3844")
    arii_clip = gpd.clip(arii_gdf, limita)

    if not arii_clip.empty:
        arii_diss = arii_clip.dissolve()
        arii_diss.to_file(data_dir / "arii_protejate.gpkg", driver="GPKG")
        return arii_diss

    arii_clip.to_file(data_dir / "arii_protejate.gpkg", driver="GPKG")
    return arii_clip
