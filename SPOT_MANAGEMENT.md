# Spot Management Feature

Dynamic dive spot management has been added to Nudibranch!

## Overview

You can now add and remove dive spots directly from the dashboard without editing configuration files manually. All changes are automatically saved to `config/spots.yaml` and take effect immediately.

## Features

### Add New Spots (Press 'a')

Press **a** to open the add spot dialog with the following fields:

**Required Fields:**
- **Name** - The dive spot name (e.g., "Similan Islands")
- **Latitude** - Decimal degrees (e.g., 8.6542)
- **Longitude** - Decimal degrees (e.g., 97.6417)

**Optional Fields:**
- **Region** - Geographic region (e.g., "Similan National Park")
- **Depth Range** - Diving depths (e.g., "5-30m")
- **Description** - Notes about the spot (e.g., "Crystal clear water, abundant marine life")

### Delete Spots (Press 'd')

Press **d** to delete the currently selected dive spot:

1. Navigate to the spot using ↑/↓ arrow keys
2. Press **d**
3. Confirm deletion in the dialog
4. Spot is removed immediately

### Automatic Persistence

All changes are saved to `config/spots.yaml`:
- New spots are appended to the end of the file
- Deleted spots are removed completely
- YAML formatting is preserved
- No manual editing required

## Implementation Details

### New Files

**`src/nudibranch/tui/widgets/spot_manager.py`** (260 lines)
- `AddSpotScreen` - Modal dialog for adding spots
- `DeleteConfirmScreen` - Confirmation dialog for deletion
- `SpotManager` - Utility class for YAML file operations

**`tests/test_spot_manager.py`** (150 lines)
- 8 comprehensive tests covering:
  - Loading spots from YAML
  - Adding new spots
  - Removing spots
  - Error handling
  - Edge cases

**`examples/test_spot_management.py`** (50 lines)
- Demo script showcasing the feature

### Modified Files

**`src/nudibranch/tui/app.py`**
- Added keybindings for 'a' and 'd'
- Added `action_add_spot()` - Shows add spot screen
- Added `action_delete_spot()` - Shows delete confirmation
- Added `_reload_spots()` - Reloads config after changes
- Integrated `SpotManager` for file operations

**`src/nudibranch/tui/widgets/conditions_table.py`**
- Added `update_spots()` - Rebuilds table with new spot list
- Clears cache when spots change
- Triggers data refresh automatically

**`src/nudibranch/tui/widgets/help_screen.py`**
- Updated keybindings documentation
- Added 'a' and 'd' to help screen

**`README.md`**
- Added spot management documentation
- Updated keybindings section
- Added usage examples

## Example Usage

### Adding Similan Islands

```
1. Launch dashboard: nudibranch
2. Press 'a'
3. Enter details:
   Name: Similan Islands
   Latitude: 8.6542
   Longitude: 97.6417
   Region: Similan National Park
   Depth Range: 5-30m
   Description: Crystal clear water, world-class diving
4. Click "Add Spot"
5. Watch data load automatically
```

### Deleting a Spot

```
1. Use ↑/↓ to navigate to the spot
2. Press 'd'
3. Confirm deletion
4. Spot is removed immediately
```

## Technical Architecture

### Data Flow

**Add Spot:**
```
User presses 'a'
  → AddSpotScreen modal appears
  → User fills form
  → SpotManager.add_spot(spot_dict)
  → YAML file updated
  → Config reloaded
  → ConditionsTableWidget.update_spots()
  → Table rebuilt
  → Data fetched for new spot
```

**Delete Spot:**
```
User selects spot with ↑/↓
  → User presses 'd'
  → DeleteConfirmScreen modal appears
  → User confirms
  → SpotManager.remove_spot(name)
  → YAML file updated
  → Config reloaded
  → ConditionsTableWidget.update_spots()
  → Table rebuilt
  → Data refreshed
```

### File Operations

The `SpotManager` class handles all YAML operations:
- **load_spots()** - Reads `config/spots.yaml`
- **save_spots()** - Writes spots list to YAML
- **add_spot()** - Appends new spot and saves
- **remove_spot()** - Filters out spot and saves

YAML formatting is preserved using `yaml.dump()` with:
- `default_flow_style=False` - Block-style formatting
- `sort_keys=False` - Preserves insertion order
- `allow_unicode=True` - Supports international characters

## Testing

**Test Coverage:** 8 new tests, all passing

```bash
# Run spot manager tests
pytest tests/test_spot_manager.py -v

# Run all tests (75 total)
pytest tests/ -v
```

**Test Suite:**
- `test_load_spots` - Verify loading from YAML
- `test_add_spot` - Add new spot and verify
- `test_remove_spot_success` - Remove existing spot
- `test_remove_spot_not_found` - Handle missing spot
- `test_save_spots` - Save spots list
- `test_load_nonexistent_file` - Handle missing file
- `test_add_spot_minimal_fields` - Required fields only
- `test_spot_manager_preserves_order` - Maintain order

## Future Enhancements

Potential improvements (not implemented):
- [ ] Edit existing spots in-place
- [ ] Import/export spots from CSV
- [ ] Duplicate spot detection
- [ ] Coordinate validation with map
- [ ] Bulk add/remove operations
- [ ] Undo/redo for spot changes
- [ ] Search/filter spots by region

## Conclusion

The spot management feature makes Nudibranch more flexible and user-friendly. You can now customize your dive spot list on the fly without leaving the application or editing configuration files manually.

**Total additions:**
- **Source code:** ~260 lines
- **Tests:** ~150 lines
- **Examples:** ~50 lines
- **Total:** ~460 lines

**Test status:** ✅ 75/75 tests passing
