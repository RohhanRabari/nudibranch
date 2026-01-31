"""Tide panel widget for displaying detailed tide information."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static

from nudibranch.models import FullConditions, TideExtreme


class TidePanelWidget(Static):
    """Widget displaying detailed tide information for a selected spot."""

    def __init__(self) -> None:
        """Initialize the tide panel."""
        super().__init__()
        self.spot_name: Optional[str] = None
        self.conditions: Optional[FullConditions] = None

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield Static(id="tide_content")

    def on_mount(self) -> None:
        """Set up the panel when mounted."""
        self.update_panel()

    def update_panel(self) -> None:
        """Update the panel display."""
        content_widget = self.query_one("#tide_content", Static)

        if not self.conditions or not self.conditions.tides:
            # Show placeholder
            content_widget.update(self._render_placeholder())
        else:
            # Render actual tide data
            content_widget.update(self._render_tide_info())

    def set_conditions(self, spot_name: str, conditions: FullConditions) -> None:
        """Set the conditions to display.

        Args:
            spot_name: Name of the dive spot
            conditions: Full conditions data including tides
        """
        self.spot_name = spot_name
        self.conditions = conditions
        self.update_panel()

    def _render_placeholder(self) -> Panel:
        """Render placeholder when no spot selected."""
        content = Text()
        content.append("🌙 Tide Information\n\n", style="bold cyan")
        content.append("Select a dive spot from the table\n", style="dim")
        content.append("to see detailed tide predictions.\n\n", style="dim")
        content.append("Use arrow keys to navigate the table.", style="italic")

        return Panel(content, border_style="cyan", padding=(1, 2))

    def _render_tide_info(self) -> Panel:
        """Render detailed tide information."""
        if not self.conditions or not self.conditions.tides:
            return self._render_placeholder()

        tides = self.conditions.tides
        now = datetime.now(timezone.utc)

        content = Text()

        # Header
        content.append(f"🌙 {self.spot_name}\n", style="bold cyan")
        content.append("=" * 30 + "\n\n", style="cyan")

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
            time_until = f"in {hours}h {minutes:02d}m"

            content.append("  ↑ High: ", style="green")
            content.append(f"{time_str} ({height}) ", style="bold")
            content.append(f"{time_until}\n", style="dim")

        if tides.next_low:
            time_str = tides.next_low.time.strftime("%I:%M %p")
            height = f"{tides.next_low.height_m:.2f}m"
            time_diff = tides.next_low.time - now
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)
            time_until = f"in {hours}h {minutes:02d}m"

            content.append("  ↓ Low:  ", style="red")
            content.append(f"{time_str} ({height}) ", style="bold")
            content.append(f"{time_until}\n", style="dim")

        content.append("\n")

        # Tide chart (simplified ASCII)
        content.append("TIDE CURVE (24H)\n", style="bold")
        chart = self._create_tide_chart(tides.extremes[:8])  # Next 4 high/low cycles
        content.append(chart)

        # Upcoming extremes
        content.append("\nUPCOMING TIDES\n", style="bold")
        upcoming = [e for e in tides.extremes[:6] if e.time > now]
        for extreme in upcoming:
            time_str = extreme.time.strftime("%a %I:%M %p")
            height_str = f"{extreme.height_m:.2f}m"

            if extreme.type == "High":
                icon = "↑"
                style = "green"
            else:
                icon = "↓"
                style = "red"

            content.append(f"  {icon} ", style=style)
            content.append(f"{time_str} ", style="dim")
            content.append(f"{extreme.type:4s} ", style=style)
            content.append(f"{height_str}\n")

        # Weather section
        if self.conditions.marine:
            content.append("\n")
            content.append("WEATHER\n", style="bold")
            marine = self.conditions.marine

            # Temperature
            if marine.temperature_c is not None:
                temp_c = marine.temperature_c
                temp_f = (temp_c * 9/5) + 32
                content.append(f"  🌡️  Temperature: ", style="dim")
                content.append(f"{temp_c:.1f}°C ({temp_f:.1f}°F)\n")

            # Cloud cover
            if marine.cloud_cover_pct is not None:
                cloud = marine.cloud_cover_pct
                if cloud < 20:
                    cloud_icon = "☀️"
                    cloud_desc = "Clear"
                elif cloud < 50:
                    cloud_icon = "🌤️"
                    cloud_desc = "Partly Cloudy"
                elif cloud < 80:
                    cloud_icon = "⛅"
                    cloud_desc = "Cloudy"
                else:
                    cloud_icon = "☁️"
                    cloud_desc = "Overcast"

                content.append(f"  {cloud_icon}  Cloud Cover: ", style="dim")
                content.append(f"{cloud}% ({cloud_desc})\n")

            # Precipitation
            if marine.precipitation_mm is not None:
                precip = marine.precipitation_mm
                if precip > 0:
                    content.append(f"  🌧️  Precipitation: ", style="dim")
                    content.append(f"{precip:.1f}mm\n")
                else:
                    content.append(f"  ☀️  Precipitation: ", style="dim")
                    content.append(f"None\n")

            # Wind (for context)
            wind_kt = marine.wind_speed_kt
            wind_dir = marine.wind_direction_deg or 0
            direction = self._degrees_to_cardinal(wind_dir)
            content.append(f"  💨 Wind: ", style="dim")
            content.append(f"{wind_kt:.0f}kt {direction}")
            if marine.wind_gust_kt:
                content.append(f" (gusts {marine.wind_gust_kt:.0f}kt)")
            content.append("\n")

        return Panel(content, border_style="cyan", padding=(1, 2))

    def _create_tide_chart(self, extremes: list[TideExtreme]) -> str:
        """Create a professional ASCII tide chart with axes and grid.

        Args:
            extremes: List of tide extremes to chart

        Returns:
            ASCII chart as string with axes, grid, and smooth curve
        """
        if not extremes:
            return "  (No tide data available)\n"

        import math

        # Find min/max heights for scaling
        heights = [e.height_m for e in extremes]
        min_h = min(heights)
        max_h = max(heights)
        range_h = max_h - min_h

        if range_h == 0:
            return "  (Flat tides)\n"

        # Chart dimensions
        chart_height = 10
        chart_width = 36

        # Initialize chart with spaces
        chart = [[" " for _ in range(chart_width)] for _ in range(chart_height)]

        # Draw grid (dotted lines)
        for row in range(chart_height):
            for col in range(chart_width):
                # Horizontal grid lines every 2 rows
                if row % 2 == 0 and col % 6 == 0:
                    chart[row][col] = "·"

        # Filter future extremes
        now = datetime.now(timezone.utc)
        future_extremes = [e for e in extremes if e.time <= now + timedelta(hours=24)]

        if not future_extremes:
            return "  (No upcoming tides)\n"

        # Interpolate smooth curve
        curve_points = []

        for i in range(len(future_extremes) - 1):
            e1 = future_extremes[i]
            e2 = future_extremes[i + 1]

            time_diff = (e2.time - e1.time).total_seconds() / 3600  # hours
            num_points = max(10, int(time_diff * 3))

            for j in range(num_points):
                t = j / num_points
                # Cosine interpolation
                t_smooth = (1 - math.cos(t * math.pi)) / 2

                interp_time = e1.time + timedelta(hours=time_diff * t)
                interp_height = e1.height_m + (e2.height_m - e1.height_m) * t_smooth

                time_offset = (interp_time - now).total_seconds() / 3600
                if 0 <= time_offset <= 24:
                    curve_points.append((time_offset, interp_height))

        # Plot the curve
        for i, (time_offset, height) in enumerate(curve_points):
            x = int((time_offset / 24) * (chart_width - 1))
            if 0 <= x < chart_width:
                normalized_h = (height - min_h) / range_h
                y = chart_height - 1 - int(normalized_h * (chart_height - 1))

                if 0 <= y < chart_height:
                    # Use + for all curve points
                    chart[y][x] = "+"

        # Mark extremes
        for extreme in future_extremes:
            time_offset = (extreme.time - now).total_seconds() / 3600
            if 0 <= time_offset <= 24:
                x = int((time_offset / 24) * (chart_width - 1))
                if 0 <= x < chart_width:
                    normalized_h = (extreme.height_m - min_h) / range_h
                    y = chart_height - 1 - int(normalized_h * (chart_height - 1))

                    if 0 <= y < chart_height:
                        if extreme.type == "High":
                            chart[y][x] = "▲"
                        elif extreme.type == "Low":
                            chart[y][x] = "▼"

        # Build output with Y-axis labels
        result = ""

        for row in range(chart_height):
            # Y-axis label (tide height)
            height_at_row = max_h - (row / (chart_height - 1)) * range_h
            y_label = f"{height_at_row:.1f}m"
            result += f"{y_label:>5} |"

            # Chart row
            result += "".join(chart[row])
            result += "|\n"

        # X-axis
        result += "      +" + "-" * chart_width + "+\n"
        result += "       0h      6h      12h     18h     24h\n"

        return result


    def _degrees_to_cardinal(self, degrees: float) -> str:
        """Convert degrees to cardinal direction.

        Args:
            degrees: Wind direction in degrees (0-360)

        Returns:
            Cardinal direction (N, NE, E, SE, S, SW, W, NW)
        """
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]

    def clear(self) -> None:
        """Clear the panel to placeholder state."""
        self.spot_name = None
        self.conditions = None
        self.update_panel()
