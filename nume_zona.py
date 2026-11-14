from pathlib import Path
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent
zona_path = PROJECT_ROOT / "data" / "limita_judet.gpkg"

def nume_zona():
    tabel = gpd.read_file(zona_path)
    nume_tabel = tabel.iloc[0, 2]
    return str(nume_tabel)
