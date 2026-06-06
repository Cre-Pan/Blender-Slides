# Blender Extensions submission texts

## Name

Blender Slides

## Tagline

Create and play slide-based presentations in the 3D View

## Website

https://github.com/Cre-Pan/Blender-Slides

## Report Issues

https://github.com/Cre-Pan/Blender-Slides/issues

## Description

Blender Slides is a presentation workflow add-on for the 3D View.

It allows users to build and play slide-based presentations directly inside a scene. Users can use cameras, timeline ranges, text, objects, lights, images, annotations, notes, and scene elements as part of a visual presentation.

Main features:

- Create and manage slide-based presentations
- Use camera views as slide framing
- Navigate between slides
- Start and stop presentation playback manually
- Add and show speaker notes
- Add checkpoints to pause during a slide
- Select a slide and jump to its frame in the timeline
- Use visual tags to organize slides
- Toggle a clean presentation view
- Toggle Rendered/Solid View from the controller
- Open a dedicated projection window

Blender Slides is useful for portfolio presentations, project pitches, visual lessons, art and design reviews, storyboard presentations, concept presentations, creative talks, and scene-based demonstrations.

## Version history

1.6.1

Improved UI and Blender Extensions preparation update.

Added:
- Cleaner slide list layout
- Compact slide rows with active slide indicator
- Visual color tags for slides
- Selected slide details panel
- Add/Delete slide controls above the slide list
- Automatic jump to the selected slide frame when choosing a slide from the list
- Clean View overlay toggle for presentation mode
- Rendered/Solid View toggle in the controller
- Safer note handling for empty and multiple notes

Improved:
- Better UI for slide management
- Better alignment for Title and Note fields
- Cleaner notes layout with add/remove note buttons
- More compact slide rows for projects with many slides
- Simpler checkpoint display
- More readable controller layout
- Better presentation workflow inside the 3D View

Fixed:
- Notes no longer disappear when empty
- Removing a note now deletes the correct note row
- Slide selection from the list now updates the timeline position
- Overlay toggle now keeps notes visible while hiding unnecessary viewport overlays
- Registration process cleaned up for Blender Extensions
- Extension package now includes only the files required to run the add-on
- Manifest now uses only the 3D View tag
