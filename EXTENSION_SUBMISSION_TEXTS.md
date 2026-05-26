# Blender Extensions submission texts

## Extension title

Slides Pro

## Tagline

Create PowerPoint-style presentations inside the 3D View

## Description

Slides Pro is a PowerPoint-style presentation manager for Blender scenes.

It lets artists, teachers, students, and presenters build a live slide deck directly in Blender. Each slide can have its own frame range, camera, notes, checkpoints, and transition timing, so a scene can be presented as a structured deck without exporting it to a separate presentation app.

Main features:

- Create and manage slides from the 3D View sidebar
- Set frame ranges for each slide
- Assign a camera to each slide
- Add presenter notes as a viewport overlay
- Add checkpoints to pause playback at specific frames
- Navigate with smart next/previous controls
- Use hard-skip controls to jump without transitions
- Open a clean projection window for presenting
- Use keyboard shortcuts during playback
- Start playback handlers only when the presentation is launched manually

## Version history

1.5.1

Changed:
- Renamed the extension to Slides Pro to comply with Blender Extensions naming rules.
- Updated the description to explain the presentation workflow clearly.
- Moved public support and bug reports to GitHub Issues.

Fixed:
- Removed startup registration of the notes draw handler.
- Presentation handlers are now enabled only when the user starts presentation playback manually.
- Presentation handlers are removed when playback stops or when the add-on is disabled.
