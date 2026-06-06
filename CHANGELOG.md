# Changelog

## 1.6.2

### Fixed

- Fixed Blender 5.1 registration/UI crash caused by the removed `SpaceView3D.annotation_data` API.
- Updated the Clear Annotations operator to use `scene.grease_pencil` on newer Blender versions, with safe legacy fallbacks.


## 1.6.1

Initial Blender Extensions release update.

### Added

- Optional **Autoplay When Selected Slide** setting.
- Initial release log for Blender Extensions.

### Improved

- Selecting a slide from the list now updates the timeline cursor and the scene In/Out frame range.
- Selected slide Color Tag control is now icon-only.
- Metadata updated to version 1.6.1.

### Fixed

- Registration remains clean for Blender Extensions: no `bpy.data.scenes` access in `register()`.
- Registration remains clean for Blender Extensions: no `bpy.context` access in `register()`.

## 1.6.0

Improved UI and Blender Extensions preparation update.

### Added

- Cleaner slide list layout
- Compact slide rows with active slide indicator
- Visual color tags for slides
- Selected slide details panel
- Add/Delete slide controls above the slide list
- Automatic jump to the selected slide frame when choosing a slide from the list
- Clean View overlay toggle for presentation mode
- Rendered/Solid View toggle in the controller
- Safer note handling for empty and multiple notes

### Improved

- Better UI for slide management
- Better alignment for Title and Note fields
- Cleaner notes layout with add/remove note buttons
- More compact slide rows for projects with many slides
- Simpler checkpoint display
- More readable controller layout
- Better presentation workflow inside the 3D View

### Fixed

- Notes no longer disappear when empty
- Removing a note now deletes the correct note row
- Slide selection from the list now updates the timeline position
- Overlay toggle now keeps notes visible while hiding unnecessary viewport overlays
- Registration process cleaned up for Blender Extensions
- Extension package now includes only the files required to run the add-on
- Manifest now uses only the 3D View tag
