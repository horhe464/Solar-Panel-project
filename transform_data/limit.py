from pathlib import Path
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def limit(nume_j: str, buffer_m: float = 1000):
    """Extrage limita judetului in EPSG:3844 si creeaza si zona tampon de 1 km (conform metodologiei RENewLand)."""
    path = PROJECT_ROOT / "raw_data" / "Judete.gpkg"
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    judete_gdf = gpd.read_file(path)
    judet = judete_gdf.loc[judete_gdf["name"] == nume_j].to_crs("EPSG:3844")

    if judet.empty:
        raise ValueError(f"Judetul '{nume_j}' nu a fost gasit in {path}.")

    # Salvam limita exacta a judetului (pentru decuparea finala si calculul suprafetelor)
    judet.to_file(data_dir / "limita_judet.gpkg", driver="GPKG")

    # Salvam limita cu buffer de 1km
    judet_buffer = judet.copy()
    judet_buffer["geometry"] = judet.geometry.buffer(buffer_m)
    judet_buffer.to_file(data_dir / "limita_judet_buffer.gpkg", driver="GPKG")

    return judet
