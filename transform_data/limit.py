from pathlib import Path
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def limit(nume_j: str, buffer_m: float = 10000):
    """Extrage limita judetului in EPSG:3844, zona tampon de 10 km si UAT-urile judetului."""
    path = PROJECT_ROOT / "raw_data" / "Judete.gpkg"
    uat_path = PROJECT_ROOT / "raw_data" / "UAT.gpkg"
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    judete_gdf = gpd.read_file(path)
    judet = judete_gdf.loc[judete_gdf["name"] == nume_j].to_crs("EPSG:3844")

    if judet.empty:
        raise ValueError(f"Judetul '{nume_j}' nu a fost gasit in {path}.")

    judet.to_file(data_dir / "limita_judet.gpkg", driver="GPKG")

    judet_buffer = judet.copy()
    judet_buffer["geometry"] = judet.geometry.buffer(buffer_m)
    judet_buffer.to_file(data_dir / "limita_judet_buffer.gpkg", driver="GPKG")

    if uat_path.exists():
        uat_gdf = gpd.read_file(uat_path)
        uat_judet = uat_gdf.loc[uat_gdf["county"].str.casefold() == nume_j.casefold()].to_crs("EPSG:3844")
        if not uat_judet.empty:
            uat_judet.to_file(data_dir / "uat.gpkg", driver="GPKG")

    return judet
