from pathlib import Path
import geopandas as gpd
import xarray as xr
import rioxarray
import xrspatial
from rasterio.enums import Resampling

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def process_rasters(resolution: float = 30.0):
    data_dir = PROJECT_ROOT / "data"
    buffer_path = data_dir / "limita_judet_buffer.gpkg"
    if not buffer_path.exists():
        buffer_path = data_dir / "limita_judet.gpkg"

    limita = gpd.read_file(buffer_path).to_crs("EPSG:3844")

    dem_path = PROJECT_ROOT / "raw_data" / "dem.tif"
    dem_ds = xr.open_dataset(dem_path, engine="rasterio")
    dem_ds = dem_ds.rio.reproject(
        "EPSG:3844", resolution=resolution, resampling=Resampling.bilinear
    )
    dem_ds = dem_ds.rio.clip(geometries=limita.geometry)
    dem_ds = dem_ds.squeeze("band", drop=True).rename({"band_data": "elevation"})

    slope_da = xrspatial.slope(dem_ds["elevation"])
    slope_da.rio.write_crs("EPSG:3844", inplace=True)
    slope_da.rio.to_raster(data_dir / "slope.tif")

    ghi_path = PROJECT_ROOT / "raw_data" / "GHI.tif"
    ghi_ds = xr.open_dataset(ghi_path, engine="rasterio")
    ghi_ds = ghi_ds.squeeze("band", drop=True).rename({"band_data": "ghi"})
    ghi_matched = ghi_ds["ghi"].rio.reproject_match(
        slope_da, resampling=Resampling.bilinear
    )
    ghi_matched = ghi_matched.rio.clip(geometries=limita.geometry)
    ghi_matched.rio.to_raster(data_dir / "ghi.tif")

    return slope_da, ghi_matched
