# Kompass

A Blender add-on for building your own pie menus, each on its own shortcut.
In development: pies open from their shortcuts, as Blender's pie menu or as
the pie Kompass draws. The editor shows a pie and
adds, renames, duplicates and deletes pies, sets their shortcuts, and fills,
swaps and clears their slots.

## Install from source

Needs Blender 5.2 or newer.

```sh
git clone https://github.com/Die-Werkstatt/Kompass.git
cd Kompass
./build.sh install   # Windows: build.bat install
```

The script finds Blender, writes `kompass-0.1.0.zip` and
`kompass_native-0.1.0.zip` into the folder and installs Kompass. Close
Blender first. Without `install` it only builds the two `.zip` files. Where
it finds no Blender, set `BLENDER` to the path of the Blender program first.

## Editions

Kompass opens pies as the pie Kompass draws, with up to 12 slots. Kompass
Pie in its preferences switches pies of 4 and 8 slots to Blender's pie menu.
Kompass Native ships without the drawn pie: every pie opens as Blender's pie
menu, with 4 or 8 slots.

Only one edition can be on at a time. The two keep their pies apart: to move
them, Export All in one and Import in the other.

To install a `.zip` by hand, drag it into Blender, or use Preferences >
Get Extensions > the arrow menu at the top right > Install from Disk.

Kompass starts with no pies. Preferences > Add-ons > Kompass > Add Starter
Pies, then hold Shift+Alt+Q in the 3D Viewport: Object in Object Mode,
Modeling in Edit Mode.

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
