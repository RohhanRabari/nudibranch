"""Widgets for managing dive spots (add/remove)."""

from pathlib import Path
from typing import Optional

import yaml
from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class AddSpotScreen(ModalScreen[Optional[dict]]):
    """Modal screen for adding a new dive spot."""

    CSS = """
    AddSpotScreen {
        align: center middle;
    }

    AddSpotScreen > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    AddSpotScreen Label {
        margin: 1 0 0 0;
        color: $text;
    }

    AddSpotScreen Input {
        margin: 0 0 1 0;
    }

    AddSpotScreen Grid {
        grid-size: 2;
        grid-gutter: 1;
        margin-top: 1;
    }

    AddSpotScreen Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the add spot form."""
        with Vertical():
            yield Static("🌊 Add New Dive Spot", classes="bold")
            yield Static("")

            yield Label("Name (required):")
            yield Input(placeholder="e.g., Similan Islands", id="name_input")

            yield Label("Latitude (required):")
            yield Input(placeholder="e.g., 8.6542", id="lat_input")

            yield Label("Longitude (required):")
            yield Input(placeholder="e.g., 97.6417", id="lng_input")

            yield Label("Region (optional):")
            yield Input(placeholder="e.g., Similan National Park", id="region_input")

            yield Label("Depth Range (optional):")
            yield Input(placeholder="e.g., 5-30m", id="depth_input")

            yield Label("Description (optional):")
            yield Input(
                placeholder="e.g., Crystal clear water, abundant marine life",
                id="description_input",
            )

            yield Static("")
            with Grid():
                yield Button("Add Spot", variant="primary", id="add_button")
                yield Button("Cancel", variant="default", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "cancel_button":
            self.dismiss(None)
        elif event.button.id == "add_button":
            # Validate and collect data
            name = self.query_one("#name_input", Input).value.strip()
            lat = self.query_one("#lat_input", Input).value.strip()
            lng = self.query_one("#lng_input", Input).value.strip()

            if not name or not lat or not lng:
                # Show error (for now just dismiss)
                self.dismiss(None)
                return

            try:
                lat_float = float(lat)
                lng_float = float(lng)
            except ValueError:
                # Invalid coordinates
                self.dismiss(None)
                return

            # Collect optional fields
            region = self.query_one("#region_input", Input).value.strip()
            depth = self.query_one("#depth_input", Input).value.strip()
            description = self.query_one("#description_input", Input).value.strip()

            # Build spot dict
            spot = {
                "name": name,
                "lat": lat_float,
                "lng": lng_float,
            }

            if region:
                spot["region"] = region
            if depth:
                spot["depth_range"] = depth
            if description:
                spot["description"] = description

            self.dismiss(spot)


class DeleteConfirmScreen(ModalScreen[bool]):
    """Modal screen for confirming spot deletion."""

    CSS = """
    DeleteConfirmScreen {
        align: center middle;
    }

    DeleteConfirmScreen > Vertical {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $error;
        padding: 1 2;
    }

    DeleteConfirmScreen Grid {
        grid-size: 2;
        grid-gutter: 1;
        margin-top: 1;
    }

    DeleteConfirmScreen Button {
        width: 100%;
    }
    """

    def __init__(self, spot_name: str) -> None:
        """Initialize the confirmation dialog.

        Args:
            spot_name: Name of the spot to delete
        """
        super().__init__()
        self.spot_name = spot_name

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Vertical():
            yield Static("⚠️  Delete Dive Spot", classes="bold")
            yield Static("")
            yield Static(f"Are you sure you want to delete '{self.spot_name}'?")
            yield Static("This action cannot be undone.", classes="dim")
            yield Static("")

            with Grid():
                yield Button("Delete", variant="error", id="delete_button")
                yield Button("Cancel", variant="default", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "cancel_button":
            self.dismiss(False)
        elif event.button.id == "delete_button":
            self.dismiss(True)


class SpotManager:
    """Utility class for managing dive spots in YAML file."""

    def __init__(self, config_path: Path):
        """Initialize the spot manager.

        Args:
            config_path: Path to spots.yaml file
        """
        self.config_path = config_path

    def load_spots(self) -> list[dict]:
        """Load spots from YAML file.

        Returns:
            List of spot dictionaries
        """
        if not self.config_path.exists():
            return []

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        return data.get("spots", [])

    def save_spots(self, spots: list[dict]) -> None:
        """Save spots to YAML file.

        Args:
            spots: List of spot dictionaries to save
        """
        data = {"spots": spots}

        with open(self.config_path, "w") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def add_spot(self, spot: dict) -> None:
        """Add a new spot to the configuration.

        Args:
            spot: Spot dictionary to add
        """
        spots = self.load_spots()
        spots.append(spot)
        self.save_spots(spots)

    def remove_spot(self, spot_name: str) -> bool:
        """Remove a spot from the configuration.

        Args:
            spot_name: Name of the spot to remove

        Returns:
            True if spot was removed, False if not found
        """
        spots = self.load_spots()
        original_count = len(spots)

        # Filter out the spot with matching name
        spots = [s for s in spots if s.get("name") != spot_name]

        if len(spots) < original_count:
            self.save_spots(spots)
            return True

        return False
