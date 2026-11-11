# Kompass

A Blender add-on for building your own pie menus, each on its own shortcut.
In development: pies open from their shortcuts, and there is no editor yet.

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
