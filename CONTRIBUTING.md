# Contributing

Contributions, bug reports, and feature suggestions are welcome.

Before opening a pull request:

1. Test the add-on in a supported Blender version.
2. Keep the extension package minimal.
3. Avoid adding unnecessary files to the Blender Extensions build.
4. Keep the manifest tag list limited to `3D View`.
5. Do not register playback handlers on startup.

For Blender Extensions builds, the final zip should contain only:

```text
__init__.py
blender_manifest.toml
```
