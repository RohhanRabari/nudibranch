"""Wind visualization widgets: animated arrow grid and wind rose chart."""

import math
import random
from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static
from textual_plotext import PlotextPlot


# Arrow chars indexed by direction step (0=N, 1=NE, 2=E, ... 7=NW)
ARROWS = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _wind_color(speed_kt: float) -> tuple[int, int, int]:
    """Return RGB color tuple for a wind speed."""
    if speed_kt < 5:
        return (0, 200, 80)      # calm green
    elif speed_kt < 15:
        return (0, 180, 220)     # moderate cyan
    elif speed_kt < 25:
        return (255, 165, 0)     # strong orange
    else:
        return (220, 30, 30)     # dangerous red


def _deg_to_step(degrees: float) -> int:
    """Convert degrees (0-360) to arrow step index (0-7)."""
    return round(degrees / 45.0) % 8


def _degrees_to_cardinal(degrees: float) -> str:
    """Convert degrees to cardinal direction."""
    return DIRECTIONS[round(degrees / 45) % 8]


class WindGridWidget(Static):
    """Animated Unicode arrow grid showing wind direction and speed."""

    DEFAULT_CSS = """
    WindGridWidget {
        height: 1fr;
        width: 1fr;
    }
    """

    GRID_COLS = 12
    GRID_ROWS = 6

    def __init__(self) -> None:
        super().__init__()
        self._speed_kt: float = 0.0
        self._direction_deg: float = 0.0
        self._gust_kt: Optional[float] = None
        self._frame: int = 0
        self._active: bool = False

    def compose(self) -> ComposeResult:
        yield Static("", id="wind_content")

    def on_mount(self) -> None:
        self._show_placeholder()
        self.set_interval(0.5, self._animate)

    def _show_placeholder(self) -> None:
        content = self.query_one("#wind_content", Static)
        placeholder = Text()
        placeholder.append("💨 Wind Visualization\n\n", style="bold cyan")
        placeholder.append("Select a dive spot to see wind conditions.", style="dim")
        content.update(placeholder)

    def set_wind(self, speed_kt: float, direction_deg: float, gust_kt: Optional[float] = None) -> None:
        """Set wind data for visualization."""
        self._speed_kt = speed_kt
        self._direction_deg = direction_deg or 0.0
        self._gust_kt = gust_kt
        self._active = True
        self._render_grid()

    def _animate(self) -> None:
        """Animation tick — re-render with slight variation."""
        if not self._active:
            return
        self._frame += 1
        self._render_grid()

    def _render_grid(self) -> None:
        """Render the full arrow grid with header."""
        content = self.query_one("#wind_content", Static)
        text = Text()

        # Header line
        direction_str = _degrees_to_cardinal(self._direction_deg)
        text.append("💨 Wind: ", style="bold")
        r, g, b = _wind_color(self._speed_kt)
        text.append(f"{self._speed_kt:.0f}kt {direction_str}", style=f"bold rgb({r},{g},{b})")
        if self._gust_kt:
            text.append(f" (gusts {self._gust_kt:.0f}kt)", style="dim")
        text.append("\n\n")

        base_step = _deg_to_step(self._direction_deg)

        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                # Slight random variation per cell per frame for motion illusion
                seed = hash((row, col, self._frame)) % 100
                if seed < 15:
                    step_offset = 1
                elif seed < 30:
                    step_offset = -1
                else:
                    step_offset = 0

                step = (base_step + step_offset) % 8
                arrow = ARROWS[step]

                # Speed variation per cell
                speed_var = self._speed_kt * (0.8 + 0.4 * ((hash((row, col, self._frame // 2)) % 100) / 100.0))
                r, g, b = _wind_color(speed_var)

                text.append(f" {arrow} ", style=f"rgb({r},{g},{b})")
            text.append("\n")

        # Speed legend
        text.append("\n")
        text.append(" ■", style="rgb(0,200,80)")
        text.append(" <5kt  ", style="dim")
        text.append("■", style="rgb(0,180,220)")
        text.append(" 5-15  ", style="dim")
        text.append("■", style="rgb(255,165,0)")
        text.append(" 15-25  ", style="dim")
        text.append("■", style="rgb(220,30,30)")
        text.append(" 25+kt", style="dim")

        content.update(text)

    def clear(self) -> None:
        """Reset to placeholder state."""
        self._speed_kt = 0.0
        self._direction_deg = 0.0
        self._gust_kt = None
        self._active = False
        self._show_placeholder()


class WindRoseChart(PlotextPlot):
    """Wind rose bar chart showing speed distribution by direction."""

    DEFAULT_CSS = """
    WindRoseChart {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._speed: float = 0.0
        self._direction: float = 0.0

    def set_wind(self, speed_kt: float, direction_deg: float) -> None:
        """Set wind data and redraw."""
        self._speed = speed_kt
        self._direction = direction_deg or 0.0
        self.replot()

    def replot(self) -> None:
        """Redraw the wind rose chart."""
        plt = self.plt
        plt.clear_figure()
        plt.title("Wind Rose")
        plt.theme("textual-design-dark")

        # Build distribution centered on actual direction
        center_idx = round(self._direction / 45.0) % 8
        values = []
        for i in range(8):
            dist = min(abs(i - center_idx), 8 - abs(i - center_idx))
            # Gaussian-ish falloff from center direction
            weight = math.exp(-0.5 * (dist / 1.5) ** 2)
            values.append(self._speed * weight)

        colors = [_wind_color(v) for v in values]
        plt.bar(DIRECTIONS, values, color=(0, 180, 220))
        plt.ylabel("Speed (kt)")

    def on_mount(self) -> None:
        self.replot()

    def clear(self) -> None:
        """Reset chart."""
        self._speed = 0.0
        self._direction = 0.0
        self.replot()
