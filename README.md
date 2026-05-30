# Slides PRO

Slides PRO is a slide-based presentation add-on for Blender's 3D View.

It lets you create, organize, and play presentations directly inside a 3D scene using cameras, timeline ranges, speaker notes, checkpoints, viewport controls, and scene objects.

## Features

- Create and manage slide-based presentations inside the 3D View
- Use timeline ranges as slide sections
- Use cameras as slide viewpoints
- Select a slide from the list and jump directly to its start frame
- Add speaker notes and display them as a viewport overlay
- Add checkpoints to pause during a slide
- Navigate with presentation controls or keyboard shortcuts
- Use visual color tags to organize slides
- Toggle a clean presentation view while keeping notes visible
- Toggle Rendered/Solid viewport mode from the controller
- Open a dedicated projection window

## What's new in 1.6.0

- Better UI for slide management
- Cleaner and more compact slide list
- Active slide indicator
- Visual color tags for slides
- Add/Delete slide controls moved above the slide list
- Selected slide details panel improved
- Better alignment for Title and Note fields
- Safer handling of empty and multiple notes
- Fixed note deletion so the correct note row is removed
- Selecting a slide now jumps to its frame in the timeline
- Clean View overlay toggle improved for presentation mode
- Extension package cleaned for Blender Extensions submission
- Manifest uses only the 3D View tag

## Installation

### From Blender Extensions

Install the add-on from the Blender Extensions platform when it becomes available.

### Manual install

1. Download the extension zip.
2. Open Blender.
3. Go to `Edit > Preferences > Add-ons`.
4. Use `Install from Disk` and select the zip file.
5. Enable **Slides PRO**.
6. Open the 3D View sidebar and find the **Slides PRO** tab.

## Basic workflow

1. Create a slide.
2. Set its frame range with `In` and `Out`.
3. Assign a camera if needed.
4. Add notes and checkpoints.
5. Select slides from the list to jump through the timeline.
6. Use the Controller panel to start, stop, navigate, and present.

## Keyboard shortcuts

- Previous / Next Slide: `Alt + Left Arrow` / `Alt + Right Arrow`
- Skip Transition: `Shift + Alt + Left Arrow` / `Shift + Alt + Right Arrow`

## Blender Extensions notes

The extension package should only include the files required to run the add-on:

```text
__init__.py
blender_manifest.toml
```

The manifest should use only the `3D View` tag.

## Support

Please report bugs and feature requests through GitHub Issues.

When reporting a bug, include:

- Blender version
- Operating system
- Slides PRO version
- Steps to reproduce the issue
- Console error, if available
- Example `.blend` file, if useful

## License

GPL-3.0-or-later.
