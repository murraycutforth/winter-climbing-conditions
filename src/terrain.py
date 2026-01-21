"""Terrain analysis module for DEM processing, aspect, and slope calculation."""

import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import rasterio
from scipy import ndimage

import config


class TerrainAnalyzer:
    """Handles DEM data loading and terrain analysis."""

    def __init__(self, dem_path: Optional[str] = None):
        """
        Initialize terrain analyzer.

        Args:
            dem_path: Path to existing DEM file. If None, will attempt to download.
        """
        self.dem_path = dem_path
        self.dem_data: Optional[np.ndarray] = None
        self.transform = None
        self.crs = None
        self._bounds = None

    def load_dem(self, bounds: Optional[dict] = None) -> bool:
        """
        Load or download DEM data for the specified bounds.

        Args:
            bounds: Dict with north, south, east, west keys. Defaults to Scotland bounds.

        Returns:
            True if DEM loaded successfully, False otherwise.
        """
        if bounds is None:
            bounds = config.SCOTLAND_BOUNDS

        self._bounds = bounds

        if self.dem_path and os.path.exists(self.dem_path):
            return self._load_from_file(self.dem_path)

        # Try to download DEM
        cache_dir = Path(config.DEM_CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        dem_file = cache_dir / "scotland_dem.tif"

        if dem_file.exists():
            return self._load_from_file(str(dem_file))

        return self._download_dem(bounds, str(dem_file))

    def _load_from_file(self, path: str) -> bool:
        """Load DEM from existing file."""
        try:
            with rasterio.open(path) as src:
                self.dem_data = src.read(1)
                self.transform = src.transform
                self.crs = src.crs
                self._bounds = {
                    "west": src.bounds.left,
                    "east": src.bounds.right,
                    "south": src.bounds.bottom,
                    "north": src.bounds.top,
                }
            print(f"Loaded DEM from {path}")
            return True
        except Exception as e:
            print(f"Failed to load DEM: {e}")
            return False

    def _download_dem(self, bounds: dict, output_path: str) -> bool:
        """Download SRTM DEM data using elevation library."""
        try:
            import elevation

            # elevation library uses (west, south, east, north) order
            elevation.clip(
                bounds=(bounds["west"], bounds["south"], bounds["east"], bounds["north"]),
                output=output_path,
                product="SRTM3",  # 90m resolution
            )
            return self._load_from_file(output_path)

        except ImportError:
            print("elevation library not installed. Run: pip install elevation")
            return False
        except Exception as e:
            print(f"Failed to download DEM: {e}")
            print("You may need to install GDAL: brew install gdal")
            return False

    def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """Get elevation at a specific coordinate."""
        if self.dem_data is None or self.transform is None:
            return None

        try:
            row, col = rasterio.transform.rowcol(self.transform, lon, lat)
            if 0 <= row < self.dem_data.shape[0] and 0 <= col < self.dem_data.shape[1]:
                return float(self.dem_data[row, col])
        except Exception:
            pass
        return None

    def get_aspect(self, lat: float, lon: float) -> Optional[float]:
        """
        Get terrain aspect (compass direction the slope faces) at coordinate.

        Returns:
            Aspect in degrees (0=N, 90=E, 180=S, 270=W), or None if unavailable.
        """
        if self.dem_data is None:
            return None

        aspect_grid = self._calculate_aspect_grid()
        return self._sample_at_coord(aspect_grid, lat, lon)

    def get_slope(self, lat: float, lon: float) -> Optional[float]:
        """
        Get terrain slope angle at coordinate.

        Returns:
            Slope angle in degrees, or None if unavailable.
        """
        if self.dem_data is None:
            return None

        slope_grid = self._calculate_slope_grid()
        return self._sample_at_coord(slope_grid, lat, lon)

    def get_terrain_info(self, lat: float, lon: float) -> dict:
        """Get all terrain information at a coordinate."""
        return {
            "elevation": self.get_elevation(lat, lon),
            "aspect": self.get_aspect(lat, lon),
            "slope": self.get_slope(lat, lon),
        }

    def _calculate_aspect_grid(self) -> np.ndarray:
        """Calculate aspect grid from DEM using gradient."""
        if self.dem_data is None:
            return np.array([])

        # Calculate gradients
        dy, dx = np.gradient(self.dem_data.astype(float))

        # Calculate aspect in degrees
        # atan2(dx, dy) gives angle from north, clockwise
        aspect = np.degrees(np.arctan2(-dx, dy))

        # Convert to 0-360 range
        aspect = np.where(aspect < 0, aspect + 360, aspect)

        return aspect

    def _calculate_slope_grid(self) -> np.ndarray:
        """Calculate slope grid from DEM."""
        if self.dem_data is None:
            return np.array([])

        # Get cell size in meters (approximate for geographic coordinates)
        if self.transform:
            cell_size = abs(self.transform[0]) * 111320  # degrees to meters at equator
        else:
            cell_size = 90  # Default SRTM resolution

        # Calculate gradients
        dy, dx = np.gradient(self.dem_data.astype(float), cell_size)

        # Calculate slope magnitude and convert to degrees
        slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

        return slope

    def _sample_at_coord(self, grid: np.ndarray, lat: float, lon: float) -> Optional[float]:
        """Sample a grid at a specific coordinate."""
        if grid.size == 0 or self.transform is None:
            return None

        try:
            row, col = rasterio.transform.rowcol(self.transform, lon, lat)
            if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
                return float(grid[row, col])
        except Exception:
            pass
        return None

    def generate_grid_points(
        self, interval_km: float = 1.0
    ) -> list[Tuple[float, float]]:
        """
        Generate a grid of sample points within the bounds.

        Args:
            interval_km: Spacing between grid points in kilometers.

        Returns:
            List of (lat, lon) tuples.
        """
        if self._bounds is None:
            self._bounds = config.SCOTLAND_BOUNDS

        # Convert km to approximate degrees
        lat_step = interval_km / 111.0  # ~111 km per degree latitude
        lon_step = interval_km / (111.0 * np.cos(np.radians(57)))  # Adjust for latitude

        points = []
        lat = self._bounds["south"]
        while lat <= self._bounds["north"]:
            lon = self._bounds["west"]
            while lon <= self._bounds["east"]:
                points.append((lat, lon))
                lon += lon_step
            lat += lat_step

        return points
