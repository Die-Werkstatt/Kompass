import sys

import kompass


# The unit tests run without Blender, so the package itself must import
# without it.
def test_package_imports_without_bpy():
    assert "bpy" not in sys.modules
    assert callable(kompass.register)
    assert callable(kompass.unregister)
