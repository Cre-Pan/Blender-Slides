# Contributing

Thanks for your interest in improving Slides Pro.

## Good contributions

- Bug reports with clear reproduction steps.
- Small fixes that keep the add-on simple and reliable.
- UI/UX improvements for the presentation workflow.
- Documentation improvements.
- Compatibility fixes for newer Blender versions.

## Development notes

- Keep the extension title as **Slides Pro**.
- Do not register presentation playback handlers on startup.
- Register playback handlers only from manual presentation operators.
- Remove handlers when playback stops or when the add-on is unregistered.
- Keep Gumroad out of the public bug reporting workflow.
