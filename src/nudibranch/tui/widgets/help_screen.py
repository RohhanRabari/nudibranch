"""Help screen widget for keybindings and usage information."""

from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen):
    """Modal help screen showing keybindings and usage."""

    BINDINGS = [
        ("q", "dismiss", "Close"),
        ("escape", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        yield Static(id="help_content")

    def on_mount(self) -> None:
        """Set up the help screen when mounted."""
        content_widget = self.query_one("#help_content", Static)
        content_widget.update(self._render_help())

    def _render_help(self) -> Panel:
        """Render the help content."""
        content = Text()

        # Header
        content.append("🌊 NUDIBRANCH HELP\n", style="bold cyan")
        content.append("=" * 60 + "\n\n", style="cyan")

        # Overview
        content.append("OVERVIEW\n", style="bold")
        content.append("  Nudibranch is a terminal dashboard for monitoring dive\n")
        content.append("  conditions worldwide at your favorite dive sites.\n\n")

        # Keybindings
        content.append("KEYBINDINGS\n", style="bold")
        content.append("  ↑/↓         Navigate dive spots in table\n", style="green")
        content.append("  a           Add new dive spot\n", style="green")
        content.append("  d           Delete selected dive spot\n", style="green")
        content.append("  r           Refresh all conditions data\n", style="green")
        content.append("  ?           Show this help screen\n", style="green")
        content.append("  q           Quit application\n", style="green")
        content.append("\n")

        # Features
        content.append("FEATURES\n", style="bold")
        content.append("  • Live marine conditions (waves, wind, swell)\n")
        content.append("  • Tide predictions (high/low times, direction)\n")
        content.append("  • Safety assessment (SAFE/CAUTION/UNSAFE)\n")
        content.append("  • Visibility estimation (GOOD/MIXED/POOR)\n")
        content.append("  • Auto-refresh every 5 minutes\n")
        content.append("\n")

        # Data Sources
        content.append("DATA SOURCES\n", style="bold")
        content.append("  • Open-Meteo Marine API (free)\n", style="dim")
        content.append("  • Stormglass.io tide API w/ harmonic fallback\n", style="dim")
        content.append("  • Safety & visibility calculated locally\n", style="dim")
        content.append("\n")

        # Color Guide
        content.append("COLOR GUIDE\n", style="bold")
        content.append("  Safety Status:\n")
        content.append("    ✓ SAFE    ", style="green bold")
        content.append("  All conditions within safe limits\n")
        content.append("    ⚠ CAUTION ", style="yellow bold")
        content.append("  Some conditions approaching limits\n")
        content.append("    ✗ UNSAFE  ", style="red bold")
        content.append("  One or more unsafe conditions\n")
        content.append("\n")
        content.append("  Visibility:\n")
        content.append("    🟢 GOOD   ", style="green bold")
        content.append("  >20m visibility expected\n")
        content.append("    🟡 MIXED  ", style="yellow bold")
        content.append("  10-20m visibility expected\n")
        content.append("    🔴 POOR   ", style="red bold")
        content.append("  <10m visibility expected\n")
        content.append("\n")

        # Footer
        content.append("=" * 60 + "\n", style="cyan")
        content.append("Press 'q' or ESC to close this help screen", style="dim italic")

        return Panel(content, border_style="cyan", padding=(1, 2))

    def action_dismiss(self) -> None:
        """Close the help screen."""
        self.dismiss()
