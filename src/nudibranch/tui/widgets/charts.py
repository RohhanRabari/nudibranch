"""Plotext-based chart widgets and info panel for the nudibranch dashboard."""

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static
from textual_plotext import PlotextPlot

from nudibranch.models import FullConditions, TideExtreme


class TideChart(PlotextPlot):
    """24-hour tide curve with braille markers."""

    DEFAULT_CSS = """
    TideChart {
        height: 1fr;
        width: 1fr;
        min-height: 12;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._hours: list[float] = []
        self._heights: list[float] = []
        self._current_hour: float = 0.0

    def set_tide_data(self, extremes: list[TideExtreme], current_hour: float) -> None:
        """Set tide data from extremes and interpolate a smooth curve.

        Args:
            extremes: List of TideExtreme objects
            current_hour: Current hour offset (0-24) for the 'now' marker
        """
        self._current_hour = current_hour

        if not extremes:
            self._hours = []
            self._heights = []
            self.replot()
            return

        now = datetime.now(timezone.utc)
        hours: list[float] = []
        heights: list[float] = []

        # Filter to next 24h window
        window_extremes = [e for e in extremes if e.time <= now + timedelta(hours=26)]
        if len(window_extremes) < 2:
            self._hours = []
            self._heights = []
            self.replot()
            return

        # Cosine interpolation between consecutive extremes
        for i in range(len(window_extremes) - 1):
            e1 = window_extremes[i]
            e2 = window_extremes[i + 1]
            time_span_h = (e2.time - e1.time).total_seconds() / 3600.0
            num_points = max(10, int(time_span_h * 4))

            for j in range(num_points):
                t = j / num_points
                t_smooth = (1.0 - math.cos(t * math.pi)) / 2.0

                interp_time = e1.time + timedelta(hours=time_span_h * t)
                offset_h = (interp_time - now).total_seconds() / 3600.0

                if 0 <= offset_h <= 24:
                    hours.append(round(offset_h, 2))
                    heights.append(e1.height_m + (e2.height_m - e1.height_m) * t_smooth)

        self._hours = hours
        self._heights = heights
        self.replot()

    def replot(self) -> None:
        """Redraw the tide chart."""
        plt = self.plt
        plt.clear_figure()
        plt.title("Tide — 24h")
        plt.theme("textual-design-dark")

        if self._hours and self._heights:
            plt.plot(
                self._hours, self._heights,
                color=(0, 206, 209), marker="braille", label="Tide (m)",
            )
            plt.vline(self._current_hour, color=(255, 165, 0))
        plt.grid(True)
        plt.xlabel("Hour")
        plt.ylabel("m")

    def on_mount(self) -> None:
        self.replot()

    def clear(self) -> None:
        """Clear the chart."""
        self._hours = []
        self._heights = []
        self._current_hour = 0.0
        self.replot()


class WaveWindChart(PlotextPlot):
    """Wave height and wind speed overlay chart."""

    DEFAULT_CSS = """
    WaveWindChart {
        height: 1fr;
        width: 1fr;
        min-height: 12;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._hours: list[float] = []
        self._wave_heights: list[float] = []
        self._wind_speeds: list[float] = []

    def set_data(self, wave_height_m: float, wind_speed_kt: float) -> None:
        """Generate a simulated 24h forecast from current conditions.

        Uses diurnal variation: wind peaks mid-afternoon, waves lag slightly.
        """
        current_h = datetime.now().hour + datetime.now().minute / 60.0
        hours = [h * 0.5 for h in range(49)]  # 0..24 in 0.5h steps

        wind_speeds: list[float] = []
        wave_heights: list[float] = []

        for h in hours:
            t = (current_h + h) % 24
            # Wind: diurnal pattern peaking around 14:00
            wind_diurnal = 0.7 + 0.3 * math.sin(math.pi * max(0, t - 6) / 12)
            wind_speeds.append(wind_speed_kt * wind_diurnal)

            # Waves: similar but lagged ~2h and dampened
            wave_diurnal = 0.8 + 0.2 * math.sin(math.pi * max(0, t - 8) / 12)
            wave_heights.append(wave_height_m * wave_diurnal)

        self._hours = hours
        self._wave_heights = wave_heights
        self._wind_speeds = wind_speeds
        self.replot()

    def replot(self) -> None:
        """Redraw the chart."""
        plt = self.plt
        plt.clear_figure()
        plt.title("Wave & Wind — 24h")
        plt.theme("textual-design-dark")

        if self._hours:
            plt.plot(
                self._hours, self._wave_heights,
                color=(0, 120, 255), marker="braille", label="Wave (m)",
            )
            plt.plot(
                self._hours, self._wind_speeds,
                color=(255, 120, 0), marker="braille", label="Wind (kt)",
            )
        plt.grid(True)
        plt.xlabel("Hour")

    def on_mount(self) -> None:
        self.replot()

    def clear(self) -> None:
        """Clear the chart."""
        self._hours = []
        self._wave_heights = []
        self._wind_speeds = []
        self.replot()


def _degrees_to_cardinal(degrees: float) -> str:
    """Convert degrees to cardinal direction."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(degrees / 45) % 8]


class InfoPanel(Static):
    """Information panel showing tide details and weather data (for Info tab)."""

    DEFAULT_CSS = """
    InfoPanel {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.spot_name: Optional[str] = None
        self.conditions: Optional[FullConditions] = None

    def compose(self) -> ComposeResult:
        yield Static("", id="info_content")

    def on_mount(self) -> None:
        self._update_display()

    def set_conditions(self, spot_name: str, conditions: FullConditions) -> None:
        """Update with new conditions data."""
        self.spot_name = spot_name
        self.conditions = conditions
        self._update_display()

    def _update_display(self) -> None:
        """Render tide info and weather as Rich Text."""
        content_widget = self.query_one("#info_content", Static)

        if not self.conditions or not self.conditions.tides:
            placeholder = Text()
            placeholder.append("ℹ️  Spot Information\n\n", style="bold cyan")
            placeholder.append("Select a dive spot to see details.", style="dim")
            content_widget.update(placeholder)
            return

        tides = self.conditions.tides
        now = datetime.now(timezone.utc)
        content = Text()

        # Header
        content.append(f"ℹ️  {self.spot_name}\n", style="bold cyan")
        content.append("═" * 30 + "\n\n", style="cyan")

        # Current tide
        content.append("CURRENT TIDE\n", style="bold")
        if tides.current_height_m is not None:
            height_str = f"{tides.current_height_m:.2f}m"
            if tides.is_rising is not None:
                if tides.is_rising:
                    direction = Text("↑ RISING", style="green bold")
                else:
                    direction = Text("↓ FALLING", style="red bold")
                content.append(f"  {height_str} ")
                content.append(direction)
                content.append("\n\n")
            else:
                content.append(f"  {height_str}\n\n")
        else:
            content.append("  Unknown\n\n", style="dim")

        # Next events
        content.append("NEXT EVENTS\n", style="bold")
        if tides.next_high:
            time_str = tides.next_high.time.strftime("%I:%M %p")
            height = f"{tides.next_high.height_m:.2f}m"
            time_diff = tides.next_high.time - now
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)
            content.append("  ↑ High: ", style="green")
            content.append(f"{time_str} ({height}) ", style="bold")
            content.append(f"in {hours}h {minutes:02d}m\n", style="dim")

        if tides.next_low:
            time_str = tides.next_low.time.strftime("%I:%M %p")
            height = f"{tides.next_low.height_m:.2f}m"
            time_diff = tides.next_low.time - now
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)
            content.append("  ↓ Low:  ", style="red")
            content.append(f"{time_str} ({height}) ", style="bold")
            content.append(f"in {hours}h {minutes:02d}m\n", style="dim")

        content.append("\n")

        # Upcoming tides
        content.append("UPCOMING TIDES\n", style="bold")
        upcoming = [e for e in tides.extremes[:6] if e.time > now]
        for extreme in upcoming:
            time_str = extreme.time.strftime("%a %I:%M %p")
            height_str = f"{extreme.height_m:.2f}m"
            if extreme.type == "High":
                icon, style = "↑", "green"
            else:
                icon, style = "↓", "red"
            content.append(f"  {icon} ", style=style)
            content.append(f"{time_str} ", style="dim")
            content.append(f"{extreme.type:4s} ", style=style)
            content.append(f"{height_str}\n")

        # Weather section
        if self.conditions.marine:
            content.append("\n")
            content.append("WEATHER\n", style="bold")
            marine = self.conditions.marine

            if marine.temperature_c is not None:
                temp_c = marine.temperature_c
                temp_f = (temp_c * 9 / 5) + 32
                content.append("  🌡️  Temperature: ", style="dim")
                content.append(f"{temp_c:.1f}°C ({temp_f:.1f}°F)\n")

            if marine.cloud_cover_pct is not None:
                cloud = marine.cloud_cover_pct
                if cloud < 20:
                    cloud_icon, cloud_desc = "☀️", "Clear"
                elif cloud < 50:
                    cloud_icon, cloud_desc = "🌤️", "Partly Cloudy"
                elif cloud < 80:
                    cloud_icon, cloud_desc = "⛅", "Cloudy"
                else:
                    cloud_icon, cloud_desc = "☁️", "Overcast"
                content.append(f"  {cloud_icon}  Cloud Cover: ", style="dim")
                content.append(f"{cloud}% ({cloud_desc})\n")

            if marine.precipitation_mm is not None:
                precip = marine.precipitation_mm
                if precip > 0:
                    content.append("  🌧️  Precipitation: ", style="dim")
                    content.append(f"{precip:.1f}mm\n")
                else:
                    content.append("  ☀️  Precipitation: ", style="dim")
                    content.append("None\n")

            wind_kt = marine.wind_speed_kt
            wind_dir = marine.wind_direction_deg or 0
            direction = _degrees_to_cardinal(wind_dir)
            content.append("  💨 Wind: ", style="dim")
            content.append(f"{wind_kt:.0f}kt {direction}")
            if marine.wind_gust_kt:
                content.append(f" (gusts {marine.wind_gust_kt:.0f}kt)")
            content.append("\n")

        content_widget.update(Panel(content, border_style="cyan", padding=(1, 2)))

    def clear(self) -> None:
        """Clear to placeholder state."""
        self.spot_name = None
        self.conditions = None
        self._update_display()
