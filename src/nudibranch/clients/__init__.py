"""API clients for marine data sources."""

from nudibranch.clients.copernicus import CopernicusClient
from nudibranch.clients.open_meteo import OpenMeteoClient
from nudibranch.clients.tides import TideClient

__all__ = ["OpenMeteoClient", "TideClient", "CopernicusClient"]
