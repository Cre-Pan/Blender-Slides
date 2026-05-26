# Slides Pro

Slides Pro is a PowerPoint-style presentation add-on for Blender.

It lets you turn a Blender scene into a live slide deck: each slide can have its own frame range, camera, notes, checkpoints, and transition timing. The goal is to present animation, layout, previz, storyboards, lectures, breakdowns, or 3D projects directly from the 3D View, without exporting everything to a separate presentation app.

## What it does

- Create a list of slides inside the 3D View sidebar.
- Assign each slide a start frame, end frame, title, notes, and optional camera.
- Play slides as looping frame ranges.
- Move to the next or previous slide with smart transitions.
- Add checkpoints inside a slide to pause playback at specific frames.
- Open a clean projection window for presenting to an audience or a second monitor.
- Display presenter notes as an overlay in the viewport.
- Navigate with UI buttons or keyboard shortcuts.
- Start playback handlers only when the presentation is launched manually.

## Typical use cases

- Presenting a 3D project directly inside Blender.
- Building a lecture, demo, or class presentation from a Blender scene.
- Showing an animated storyboard or previz sequence.
- Creating a portfolio presentation with multiple cameras and animated transitions.
- Using Blender as a visual presentation tool instead of a traditional slide editor.

## Installation

### From Blender Extensions

1. Download the extension ZIP.
2. Open Blender.
3. Go to `Edit > Preferences > Extensions`.
4. Install the ZIP file.
5. Enable **Slides Pro**.

### Manual installation

1. Download or clone this repository.
2. Put the add-on folder in your Blender add-ons directory, or install the ZIP from Blender preferences.
3. Enable **Slides Pro** from the Extensions/Add-ons preferences.

## Location

Open the 3D View, press `N`, then open the **Slides Pro** tab.

## Basic workflow

1. Create or animate your scene.
2. Add a slide from the Slides Pro panel.
3. Set the slide frame range.
4. Optionally assign a camera, title, notes, and checkpoints.
5. Repeat for all slides.
6. Press **Start** to begin the presentation.
7. Use the navigation buttons or shortcuts to move through the deck.
8. Use **Projection Window** for a clean presentation viewport.

## Shortcuts

- `Alt + Right Arrow`: next slide / continue from checkpoint
- `Alt + Left Arrow`: previous slide
- `Shift + Alt + Right Arrow`: hard skip forward, without transition
- `Shift + Alt + Left Arrow`: hard skip backward, without transition

## Notes and checkpoints

Slides can include notes that appear as a viewport overlay. Checkpoints pause playback at chosen frames, which is useful for explaining animation steps, before/after states, or different phases of a scene.

## Handler behavior

Slides Pro does not register presentation playback handlers on Blender startup. Handlers are enabled only when the user starts a presentation and are removed when the presentation is stopped or the add-on is disabled.

## Support

Use GitHub Issues for bug reports and feature requests.

When reporting a bug, please include:

- Blender version
- Operating system
- Slides Pro version
- Steps to reproduce the issue
- A screenshot or screen recording, when useful
- The console error, if available

## License

Slides Pro is released under the GNU General Public License v3.0 or later.
