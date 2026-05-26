# Slides Pro

Slides Pro is a lightweight add-on for Blender that turns image folders and animation frames into layered planes in the 3D viewport. It is designed for artists, animators, storyboarders, and mixed-media workflows where 2D image sequences need to be organized, previewed, aligned, and presented directly in a scene.

## Main features

- Import folders of images as ordered animated planes.
- Preserve folder structure as layers or collections.
- Skip helper folders such as folders starting with `_`.
- Sort numbered frames naturally, so `frame 2` comes before `frame 10`.
- Align generated planes to the active camera.
- Manage imported layers from a compact viewport panel.
- Play image-based presentations without keeping playback handlers active when they are not needed.
- Render presentations in the background and stop background renders when needed.

## Installation

### From Blender Extensions

1. Open Blender.
2. Go to **Edit > Preferences > Get Extensions**.
3. Search for **Slides Pro**.
4. Install and enable the extension.

### Manual installation

1. Download the latest `.zip` release from the Releases page.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Click **Install from Disk**.
4. Select the downloaded `.zip` file.
5. Enable **Slides Pro**.

## Basic workflow

1. Prepare one folder per shot, layer, character, or animation pass.
2. Put the frames inside each folder using readable numbered names.
3. In Blender, open the Slides Pro panel.
4. Choose the parent folder.
5. Review the import list.
6. Generate the planes.
7. Adjust layer visibility, camera alignment, and playback as needed.

## Recommended folder structure

```text
Project/
├── 01 - Background/
│   ├── bg_0001.png
│   ├── bg_0002.png
│   └── bg_0003.png
├── 02 - Character/
│   ├── character_0001.png
│   ├── character_0002.png
│   └── character_0003.png
└── _Reference/
    └── notes.png
```

Folders starting with `_` are intended to be skipped during import.

## Reporting bugs

Please report bugs on GitHub Issues. Include:

- Your Blender version.
- Your operating system.
- The Slides Pro version.
- Steps to reproduce the problem.
- Screenshots or a small test folder when possible.
- The full error message from the Blender console, if available.

## Support and discussion

- Bug reports: GitHub Issues
- Feature requests: GitHub Issues
- Public discussion: Blender Artists thread

Gumroad is used only as an optional download or release page, not as the main bug tracker.

## License

Slides Pro is distributed under the GNU General Public License v3.0 or later.
