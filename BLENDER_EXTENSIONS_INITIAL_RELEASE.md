# Blender Slides — Initial Release

> **Version:** 1.6.1  
> **Category:** 3D View  
> **Type:** Add-on

## Overview

Blender Slides is a presentation workflow add-on for Blender's 3D View.

It lets you create, organize, and play slide-based presentations directly inside a Blender scene using cameras, timeline ranges, viewport objects, speaker notes, checkpoints, and presentation controls.

## Main Features

### Slide Management

- Create and delete slides from the 3D View sidebar.
- Organize slides in a compact UI list.
- Use slide titles for clear presentation structure.
- Select a slide from the list to jump to its timeline range.
- Automatically update the scene **In** and **Out** range when a slide is selected.
- Optional **Autoplay When Selected Slide** setting.

### Timeline-Based Presentation Workflow

- Each slide has its own **In** and **Out** frame range.
- Use the current timeline frame to quickly set slide start and end frames.
- Use transition frame values between slides.
- Loop the active slide during playback.
- Navigate to the next or previous slide during a presentation.
- Hard-skip to the next or previous slide without transition playback.

### Camera Support

- Assign a camera to each slide.
- Automatically switch the active scene camera when selecting or playing a slide.
- Use Blender scenes as presentation spaces, combining cameras, objects, lights, images, annotations, and animation.

### Speaker Notes Overlay

- Add one or more speaker notes to each slide.
- Display notes directly in the 3D View as an overlay.
- Show the slide title with the notes overlay.
- Choose the notes position:
  - Bottom Left
  - Top Left
  - Bottom Right
  - Top Right
- Adjust title font size.
- Adjust notes font size.
- Notes use a shadowed overlay style for readability during presentation.

### Checkpoints

- Add checkpoints inside a slide.
- Pause playback automatically at checkpoint frames.
- Continue playback from a paused checkpoint.
- Use checkpoint tags for visual organization.

### Visual Tags

- Assign visual color tags to slides.
- Tags are shown as icons in the slide list.
- The selected slide settings now use an icon-only tag selector for a cleaner interface.

### Presentation Controller

- Start presentation playback from the selected slide.
- Stop presentation playback.
- Move to previous or next slide.
- Skip transitions manually.
- Continue from checkpoints.
- View the current active slide number and title.

### Viewport Presentation Tools

- Toggle a cleaner viewport presentation mode.
- Hide unnecessary viewport overlays while keeping the notes overlay available.
- Toggle between Rendered View and Solid View from the add-on controller.
- Open a dedicated projection window for presenting.

## Blender Extensions Preparation

- The extension package includes only the files required to run the add-on:

```text
__init__.py
blender_manifest.toml
```

- The manifest uses only the required tag:

```toml
tags = ["3D View"]
```

- Registration was cleaned to avoid accessing file data or context during add-on registration.
- The add-on no longer iterates through `bpy.data.scenes` during `register()`.
- The add-on does not call `bpy.context` inside `register()`.

## Initial Release Notes

> This is the first public Blender Extensions release of Blender Slides.

This release focuses on a stable, scene-based presentation workflow for artists, students, teachers, designers, and creators who want to present directly inside Blender instead of exporting to external slide software.

## Typical Uses

- Portfolio presentations
- Project pitches
- Storyboard presentations
- Concept art reviews
- Art direction breakdowns
- Lessons and visual explanations
- Scene-based demos
- Animation and film project presentations
