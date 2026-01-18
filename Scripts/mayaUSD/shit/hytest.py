import hou
import os

# ------------------------------------------------
# Paths
# ------------------------------------------------
input_fbx = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\mayaUSD\input\test.fbx"
output_fbx = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\mayaUSD\output\tost.fbx"

os.makedirs(os.path.dirname(output_fbx), exist_ok=True)

print("UI available:", hou.isUIAvailable())

# ------------------------------------------------
# Geometry network
# ------------------------------------------------
obj = hou.node("/obj")
geo = obj.createNode("geo", "fbx_geo")

# Remove default nodes
for n in geo.children():
    n.destroy()

# FBX import
file_sop = geo.createNode("file")
file_sop.parm("file").set(input_fbx)

# Subdivision
subd = geo.createNode("subdivide")
subd.setInput(0, file_sop)
subd.parm("iterations").set(2)

subd.setDisplayFlag(True)
subd.setRenderFlag(True)

geo.layoutChildren()

# ------------------------------------------------
# Cook geometry and export FBX directly
# ------------------------------------------------
print("Cooking geometry...")
subd.cook(force=True)

geo_node = subd.geometry()

print("Saving FBX...")
geo_node.saveToFile(output_fbx)

print("FBX export complete.")

hou.exit()
