from pathlib import Path
from pyrosm import OSM
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MAIN_ROADS = [
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
]


def osm_data():
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"

    limita = gpd.read_file(buffer_path).to_crs("EPSG:3844")

    limit_wgs84 = limita.to_crs("EPSG:4326")
    bbox_geom = limit_wgs84.geometry.iloc[0]

    osm_path = PROJECT_ROOT / "raw_data" / "romania.osm.pbf"
    osm = OSM(str(osm_path), bounding_box=bbox_geom)

    drumuri = osm.get_data_by_custom_criteria(
        custom_filter={"highway": MAIN_ROADS},
        filter_type="keep",
        keep_nodes=False,
        keep_ways=True,
        keep_relations=False,
    )

    cai_ferate = osm.get_data_by_custom_criteria(
        custom_filter={"railway": ["rail"]},
        filter_type="keep",
        keep_nodes=False,
        keep_ways=True,
        keep_relations=False,
    )

    linii_electrice = osm.get_data_by_custom_criteria(
        custom_filter={"power": ["line"]},
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
        custom_filter={
            "place": ["city", "town", "village", "hamlet"],
            "landuse": ["residential"],
        },
        filter_type="keep",
        keep_nodes=False,
        keep_ways=True,
        keep_relations=True,
    )

    if drumuri is not None and not drumuri.empty:
        drumuri_3844 = gpd.clip(drumuri.to_crs("EPSG:3844"), limita)
        drumuri_3844.to_file(data_dir / "drumuri.gpkg", driver="GPKG")

    if cai_ferate is not None and not cai_ferate.empty:
        cai_ferate_3844 = gpd.clip(cai_ferate.to_crs("EPSG:3844"), limita)
        cai_ferate_3844.to_file(data_dir / "cai_ferate.gpkg", driver="GPKG")

    if linii_electrice is not None and not linii_electrice.empty:
        linii_3844 = gpd.clip(linii_electrice.to_crs("EPSG:3844"), limita)
        linii_3844.to_file(data_dir / "linii_electrice.gpkg", driver="GPKG")

    if statii is not None and not statii.empty:
        statii_3844 = gpd.clip(statii.to_crs("EPSG:3844"), limita)
        statii_3844.to_file(data_dir / "statii.gpkg", driver="GPKG")

    if localitati is not None and not localitati.empty:
        loc_3844 = localitati.to_crs("EPSG:3844")
        loc_poly = loc_3844[loc_3844.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
        if not loc_poly.empty:
            loc_clip = gpd.clip(loc_poly, limita)
            loc_clip.to_file(data_dir / "localitati.gpkg", driver="GPKG")
        else:
            gpd.clip(loc_3844, limita).to_file(data_dir / "localitati.gpkg", driver="GPKG")
