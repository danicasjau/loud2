import hou
import os
import sys

class usdVariants():
    def __init__(self):
        self.input_format = "fbx"

        self.scale = 0.01

        self.asset_name = "nom"
        self.asset_mesh_path = r""
        self.identifierUnique = "0000"

        self.deafult_name = "asset"
        self.department = "geometry" # (0  Asset, 1 Geo. 2 Mtl & Bind)
        
        self.SOPs = None
        self.LOPs = None
        self.geoNode = None
        self.configureLayerNode = None


        self.outputExportPath = r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\temp"


    def _set(self, asset_name=None, asset_mesh_path=None, version=None):
        self.asset_name = asset_name if asset_name else self.deafult_name
        self.asset_mesh_path = asset_mesh_path if asset_mesh_path else r""
        self.identifierUnique = version if version else "v0001"


    def initialize(self):
        self.SOPs = hou.node("/obj")
        self.LOPs = hou.node("/stage")

        sopSubChildren = self.SOPs.allSubChildren()
        for node in sopSubChildren:
            if node.name() == self.asset_name:
                node.destroy()
                
        self.geoNode = self.SOPs.createNode("geo", self.asset_name)

        lopSubChildren = self.LOPs.allSubChildren()

        destroy = False
        for node in lopSubChildren:
            if node.name() == f"{self.asset_name}_basePrim_PRIMITIVE":
                destroy = True
        if destroy:
            for node in lopSubChildren:
                node.destroy()

    
    # Load Into SOPs
    def loadIntoSop(self):
        # crea geo, importa fbx, blast per name, null per cada blast

        # Import node
        self.fileReadNode = self.geoNode.createNode("file", f"{self.asset_name}_IMPORT")
        self.fileReadNode.parm("file").set(self.asset_mesh_path) #sets import fbx path

        # Transform node
        self.transformNode = self.geoNode.createNode("xform", f"{self.asset_name}_TRANSFORM")
        self.transformNode.setInput(0, self.fileReadNode)
        self.transformNode.parm("scale").set(self.scale)

        # Separate meshes
        self.fileReadNode.cook(force=True)  # -----------------------------------------------------------!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.mesh = self.fileReadNode.geometry()

        if not self.mesh.findPrimAttrib("name"):
            raise NameError
        
        name_attrib = self.mesh.findPrimAttrib("name") # Will return the attribute itself (hou.Attrib)
        self.uniqueNames = sorted({prim.attribValue(name_attrib) for prim in self.mesh.prims()}) # For every face what name it has

        # Create one Blast per mesh (branched)
        for name in self.uniqueNames:
            blastNode = self.geoNode.createNode("blast", f"{name}_BLAST")
            blastNode.setInput(0, self.transformNode) # connect to last node

            blastNode.parm("group").set(f'@name="{name}"')
            blastNode.parm("negate").set(True)  # keep only selected

            nullNode = self.geoNode.createNode("null", f"OUT_{name}")
            nullNode.setInput(0, blastNode) # connect to blast
            nullNode.setDisplayFlag(True)

    # Send To LOPs
    def sendToLop(self):
        # geo node dins. Busca nulls, si out _ guarda variable i passa funcio
        subNodesOfGeo = self.geoNode.children() # allSubChildren()

        self.OUT_nulls = []

        for subNode in subNodesOfGeo:
            subNode_type = subNode.type().name()
            subNode_name = subNode.name()
            subNode_nameParts = subNode_name.split("_")

            if subNode_type == "null" and subNode_nameParts[0] == "OUT": # Add it to the list
                self.OUT_nulls.append(subNode)


    def solarisLoadGeo(self):
        self.primBaseNode = self.LOPs.createNode("primitive", f"{self.asset_name}_basePrim_PRIMITIVE")
        self.primBaseNode.parm("primpath").set(f"/{self.asset_name}") # Configure Path
        self.primBaseNode.parm("primkind").set("component") # Set Kind to Component

        self.primGeoNode = self.LOPs.createNode("primitive", f"{self.asset_name}_geoPrim_PRIMITIVE")
        self.primGeoNode.setInput(0, self.primBaseNode)
        self.primGeoNode.parm("primpath").set(f"/{self.asset_name}/geo") # Configure Path - no need to configure the other parm, default is fine

        self.configureLayerNode = self.LOPs.createNode("configurelayer", f"{self.asset_name}_GEOMETRY_LYR") # Create Node
        self.configureLayerNode.parm("flattenop").set("layer") # Set Flatten Input Layer to Layer

        # Create Start Variants
        self.variantBeginNode = self.LOPs.createNode("begincontextoptionsblock", f"{self.asset_name}_beginGeoVariant")
        self.variantBeginNode.setColor(hou.Color((0.62, 0.42, 0.76)))
        self.variantBeginNode.parm("layerbreak").set(True)
        self.variantBeginNode.setInput(0, self.primGeoNode)

        # Create End Variants
        self.variantEndNode = self.LOPs.createNode("addvariant", f"{self.asset_name}_endGeoVariant")
        self.variantEndNode.parm("primpath").set(f"/{self.asset_name}")
        self.variantEndNode.parm("createoptionsblock").set(1)
        self.variantEndNode.parm("variantset").set("model")
        self.variantEndNode.parm("variantprimpath").set(f"/{self.asset_name}")
        self.variantEndNode.setInput(0, self.primGeoNode)

        self.variantList = []

        for variant in self.OUT_nulls:
            try:
                name = variant.name().split("_")[2] # Get Variant Name -----------------------------------------------------------------!
            except:
                name = f"{self.asset_name}_MSH" # ---------------------------------------------------------------------!
            
            sopImportNode = self.LOPs.createNode("sopimport", f"{self.asset_name}_{name}") # Create SopImport Node and set name

            sopImportNode.parm("soppath").set((variant).path()) # Change USD Path 

            sopImportNode.parm("copycontents").set(1) # Set to Merge SOP Layer Into Existing Active Layer
            sopImportNode.parm("pathprefix").set(f"/{self.asset_name}/geo") # Set Import Path Prefix
            sopImportNode.parm("enable_defineonlyleafprims").set(True) # Enable Set Leaf
            sopImportNode.parm("defineonlyleafprims").set(True) # Set Leaf

            sopImportNode.setInput(0, self.variantBeginNode) # Connect to Begin Variant Block
            self.variantEndNode.setNextInput(sopImportNode) # Connect sopImports to Variant End Node

            self.variantList.append(sopImportNode)


        self.configureLayerNode.setInput(0, self.variantEndNode) # Connect ConfigLayer to the variant end block


    def saveToDisk(self):
        exportsToCreate = []
        extension = "usdc"
        if self.department == "asset":
            exportsToCreate.extend(["geo", "bind", "mtl"])
        elif self.department == "material":
            exportsToCreate.extend(["bind", "mtl"])
        elif self.department == "geometry":
            exportsToCreate.append("geo")

        writeNodes = []

        for export in exportsToCreate:
            if export == "geo": extension = "usdc" 
            elif export == "bind": extension = "usda"
            elif export == "mtl": extension = "usdc"

            outputNodeVersion = self.LOPs.createNode("usd_rop", f"out_{export}_temp")
            exportPathV = self.outputExportPath + f"/out_{self.identifierUnique}_temp.{extension}"
            print(f"Exported to {exportPathV}")
            outputNodeVersion.parm("lopoutput").set(exportPathV)
            outputNodeVersion.setInput(0, self.configureLayerNode)
            writeNodes.append(outputNodeVersion)

        for node in writeNodes:
            node.parm("execute").pressButton()
        
        print(f"Assets exported sucessfully at {self.outputExportPath}")
        #hou.hipFile.save(asset_mesh_path + "\scene.hip")


    def createVariants(self):
        self.initialize()
        self.loadIntoSop()
        self.sendToLop()
        self.solarisLoadGeo()
        self.saveToDisk()


def main(asset_name, asset_mesh_path, version):
    export = usdVariants()
    export._set(
        asset_name = asset_name,
        asset_mesh_path = asset_mesh_path,
        version = version
    )
    export.createVariants()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python variants.py <asset_name> <asset_mesh_path> <version>")
        sys.exit(1)

    asset_name = sys.argv[1]
    asset_mesh_path = sys.argv[2]
    version = sys.argv[3]

    asset_mesh_path = os.path.abspath(asset_mesh_path)
    main(asset_name, asset_mesh_path, version)