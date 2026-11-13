from pathlib import Path
from pyrosm import OSM
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def osm_data():
    """Extrage drumurile, caile ferate, liniile electrice, statiile si localitatile din OSM pe zona judetului (+1 km buffer)."""
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"

    # Atentie: EPSG:4326 (WGS84) este necesar pentru pyrosm bounding_box
    limit_wgs84 = gpd.read_file(buffer_path).to_crs("EPSG:4326")
    bbox_geom = limit_wgs84.geometry.iloc[0]

    osm_path = PROJECT_ROOT / "raw_data" / "romania.osm.pbf"
    osm = OSM(str(osm_path), bounding_box=bbox_geom)

    drumuri = osm.get_network(network_type="driving")

    cai_ferate = osm.get_data_by_custom_criteria(
        custom_filter={"railway": ["rail"]},
        filter_type="keep",
        keep_nodes=False,
        keep_ways=True,
        keep_relations=False,
    )

    linii_electrice = osm.get_data_by_custom_criteria(
        custom_filter={"power": ["line", "minor_line"]},
        filter_type="keep",
        keep_nodes=False,
        keep_ways=True,
        keep_relations=False,
    )

    statii = osm.get_data_by_custom_criteria(
        custom_filter={"power": ["substation"]},
        filter_type="keep",
        keep_nodes=True,
        keep_ways=True,
        keep_relations=True,
    )

    localitati = osm.get_data_by_custom_criteria(
        custom_filter={"place": ["city", "town", "village", "hamlet"]},
        filter_type="keep",
        keep_nodes=True,
        keep_ways=True,
        keep_relations=True,
    )

    if drumuri is not None and not drumuri.empty:
        drumuri.to_crs("EPSG:3844").to_file(data_dir / "roads.gpkg", driver="GPKG")
    if cai_ferate is not None and not cai_ferate.empty:
        cai_ferate.to_crs("EPSG:3844").to_file(data_dir / "railways.gpkg", driver="GPKG")
    if linii_electrice is not None and not linii_electrice.empty:
        linii_electrice.to_crs("EPSG:3844").to_file(data_dir / "lines.gpkg", driver="GPKG")
    if statii is not None and not statii.empty:
        statii.to_crs("EPSG:3844").to_file(data_dir / "substations.gpkg", driver="GPKG")
    if localitati is not None and not localitati.empty:
        localitati.to_crs("EPSG:3844").to_file(data_dir / "places.gpkg", driver="GPKG")
