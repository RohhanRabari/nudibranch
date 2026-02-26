"""Map tile widget for displaying dive spot locations on OSM tiles."""

import asyncio
import math
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image as PILImage, ImageDraw
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.widgets import Static

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_SIZE = 256
CACHE_DIR = Path.home() / ".cache" / "nudibranch" / "tiles"
ZOOM = 13
USER_AGENT = "nudibranch/0.1 (dive-conditions-dashboard)"


def lat_lng_to_tile(lat: float, lng: float, zoom: int) -> tuple[int, int, float, float]:
    """Convert lat/lng to tile coordinates.

    Returns:
        (tile_x, tile_y, frac_x, frac_y) where frac is the position within the tile.
    """
    n = 2 ** zoom
    x_float = (lng + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y_float = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n
    tile_x = int(x_float)
    tile_y = int(y_float)
    frac_x = x_float - tile_x
    frac_y = y_float - tile_y
    return tile_x, tile_y, frac_x, frac_y


async def fetch_tile(z: int, x: int, y: int) -> Optional[PILImage.Image]:
    """Fetch a single tile, using disk cache if available."""
    cache_path = CACHE_DIR / str(z) / str(x) / f"{y}.png"

    if cache_path.exists():
        try:
            return PILImage.open(cache_path).convert("RGB")
        except Exception:
            cache_path.unlink(missing_ok=True)

    try:
        url = TILE_URL.format(z=z, x=x, y=y)
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=10.0)
            resp.raise_for_status()

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(resp.content)
        return PILImage.open(BytesIO(resp.content)).convert("RGB")
    except Exception:
        return None


async def fetch_and_stitch(
    lat: float, lng: float, spot_name: str = "",
) -> Optional[PILImage.Image]:
    """Fetch a 2x2 tile grid and stitch into one image with a spot marker."""
    tile_x, tile_y, frac_x, frac_y = lat_lng_to_tile(lat, lng, ZOOM)

    tiles = await asyncio.gather(
        fetch_tile(ZOOM, tile_x, tile_y),
        fetch_tile(ZOOM, tile_x + 1, tile_y),
        fetch_tile(ZOOM, tile_x, tile_y + 1),
        fetch_tile(ZOOM, tile_x + 1, tile_y + 1),
    )

    if not all(tiles):
        return None

    stitched = PILImage.new("RGB", (TILE_SIZE * 2, TILE_SIZE * 2))
    stitched.paste(tiles[0], (0, 0))
    stitched.paste(tiles[1], (TILE_SIZE, 0))
    stitched.paste(tiles[2], (0, TILE_SIZE))
    stitched.paste(tiles[3], (TILE_SIZE, TILE_SIZE))

    # Draw spot marker
    px = int(frac_x * TILE_SIZE)
    py = int(frac_y * TILE_SIZE)
    draw = ImageDraw.Draw(stitched)

    # Red circle marker with white outline
    radius = 8
    draw.ellipse(
        [px - radius - 2, py - radius - 2, px + radius + 2, py + radius + 2],
        fill=(255, 255, 255),
    )
    draw.ellipse(
        [px - radius, py - radius, px + radius, py + radius],
        fill=(220, 30, 30),
    )
    draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255))

    # Label
    if spot_name:
        draw.text((px + radius + 4, py - 8), spot_name, fill=(255, 255, 255))
        draw.text((px + radius + 3, py - 9), spot_name, fill=(40, 40, 40))

    return stitched


class MapTileWidget(Static):
    """Widget displaying an OSM map tile for a dive spot location."""

    DEFAULT_CSS = """
    MapTileWidget {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._lat: Optional[float] = None
        self._lng: Optional[float] = None
        self._spot_name: Optional[str] = None
        self._image_widget = None

    def compose(self) -> ComposeResult:
        yield Static("", id="map_content")

    def on_mount(self) -> None:
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        content = self.query_one("#map_content", Static)
        placeholder = Text()
        placeholder.append("🗺  Map View\n\n", style="bold cyan")
        placeholder.append("Select a dive spot to see its location\n", style="dim")
        placeholder.append("on an OpenStreetMap tile.", style="dim")
        content.update(placeholder)

    def set_location(self, lat: float, lng: float, spot_name: str = "") -> None:
        """Set the location to display on the map."""
        self._lat = lat
        self._lng = lng
        self._spot_name = spot_name
        self._load_map()

    @work(exclusive=True)
    async def _load_map(self) -> None:
        """Fetch and display the map tile."""
        if self._lat is None or self._lng is None:
            return

        content = self.query_one("#map_content", Static)

        # Show loading state
        loading = Text()
        loading.append("🗺  Loading map...\n", style="bold cyan")
        loading.append(f"  {self._spot_name}\n", style="bold")
        loading.append(f"  {self._lat:.4f}, {self._lng:.4f}", style="dim")
        content.update(loading)

        try:
            image = await fetch_and_stitch(self._lat, self._lng, self._spot_name or "")

            if image is None:
                raise RuntimeError("Failed to fetch map tiles")

            # Try to render with textual-image
            try:
                from textual_image.widget import Image as TextualImage

                tmp_path = CACHE_DIR / "_current_map.png"
                tmp_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(tmp_path)

                # Remove old image widget if present
                if self._image_widget is not None:
                    await self._image_widget.remove()
                    self._image_widget = None

                content.update("")
                img_widget = TextualImage(str(tmp_path))
                self._image_widget = img_widget
                await self.mount(img_widget)
            except ImportError:
                self._show_text_fallback()

        except Exception as e:
            self._show_text_fallback(str(e))

    def _show_text_fallback(self, error: str = "") -> None:
        """Show text fallback when image rendering isn't available."""
        content = self.query_one("#map_content", Static)
        text = Text()
        text.append("🗺  Map View\n\n", style="bold cyan")
        if self._spot_name:
            text.append(f"  📍 {self._spot_name}\n", style="bold")
        if self._lat is not None and self._lng is not None:
            text.append(f"  Lat: {self._lat:.4f}\n", style="dim")
            text.append(f"  Lng: {self._lng:.4f}\n", style="dim")
            text.append(f"  Zoom: {ZOOM}\n\n", style="dim")
            tile_x, tile_y, _, _ = lat_lng_to_tile(self._lat, self._lng, ZOOM)
            text.append(f"  Tile: {tile_x},{tile_y}\n", style="dim")
        if error:
            text.append(f"\n  ⚠ {error}", style="yellow")
        content.update(text)

    def clear(self) -> None:
        """Reset to placeholder state."""
        self._lat = None
        self._lng = None
        self._spot_name = None
        if self._image_widget is not None:
            self._image_widget.remove()
            self._image_widget = None
        self._show_placeholder()
