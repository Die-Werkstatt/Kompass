# Kompass

A Blender add-on for building your own pie menus, each on its own shortcut.
In development: pies open from their shortcuts, and there is no editor yet.

## Install from source

Needs Blender 5.2 or newer. Where `blender` is not on your `PATH`, as on
Windows, write the full path instead, for example
`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`.

```sh
git clone https://github.com/Die-Werkstatt/Kompass.git
cd Kompass
blender --command extension build --source-dir kompass
blender --command extension install-file -r user_default --enable kompass-0.1.0.zip
```

Or install the `.zip` from inside Blender: Preferences > Get Extensions >
the arrow menu at the top right > Install from Disk.

Kompass starts with no pies. Preferences > Add-ons > Kompass > Import and
pick `tests/data/example.json`, then hold Shift+Alt+Q in the 3D Viewport.

## Keep your pies

Uninstalling Kompass deletes your pies. Blender removes the add-on's own
folder, with the pie file in it. Updating or disabling Kompass keeps them.

Export them first: Preferences > Add-ons > Kompass > Export All writes every
pie to one `.json` file. The button on a pie's row exports that pie with its
sub-pies. Import adds the pies of such a file to yours. A pie you already
have is kept beside the imported one unless you tick Replace My Pies in the
file browser. An imported pie loses its shortcut when one of your pies
already has it.

## Development

See [`agent_docs/CLAUDE.md`](agent_docs/CLAUDE.md) for structure, commands and
conventions, and [`CONTRIBUTING.md`](CONTRIBUTING.md) for how changes land.

<!-- Created from https://github.com/sandrogekeler/AllesSandro. -->
