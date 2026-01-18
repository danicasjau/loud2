# ///////////////////////////////////////////////////////////////////////////////////////
# USD Loader - by 2LOUD - dev. Roger Armengol Martí
# ///////////////////////////////////////////////////////////////////////////////////////



import sys
import os
import re
import hou
import json
import shutil
from pathlib import Path


try:
    from PySide2 import QtWidgets, QtCore, QtGui
except:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
    except:
        print("no pyside found")



# ========================================================================================================================
# Tool Internal Funcioning Variables
# ========================================================================================================================

toolVersion = "1.0.8"

autoColorSpace = 0 # Manual variable to ensure no colorSpace is applied

assetjsonID = "Feature In Process" # Hard Code define as this feature is not done yet





# ========================================================================================================================
# Load Config
# ========================================================================================================================

# Load the configs from json
def load_config(config_path):

    try:
        if not os.path.exists(config_path): # Check if path exists
            hou.ui.displayMessage(f"Config file not found:\n{config_path}", severity=hou.severityType.Error) # Display hou error

        with open(config_path, "r") as f:
            return json.load(f)
        
    except Exception as e:
        hou.ui.displayMessage(f"Failed to load config:\n{str(e)}", severity=hou.severityType.Error)
        return {}



SCRIPT_DIR = r"P:/VFX_Project_30/2LOUD/Spotlight/00_Pipeline/Plugins/StudioPrograms/Programs/HOUDINI/scripts/usdLoader" # Base script dir

CONFIG_PATH = os.path.join(SCRIPT_DIR, "usdLoader_configs.json") # Get the config path

CONFIG = load_config(CONFIG_PATH) # Create config variable to acces info

# ========================================================================================================================
# Automation Functions
# ========================================================================================================================

# =========================
# Get Single Geo File
# =========================

def get_single_geometry_file(directory): # Get whatever geo file is inside the dir
    try:
        if not os.path.exists(directory): # If path doesnt exist display a hou error
            hou.ui.displayMessage(f"Directory does not exist: {directory}", severity=hou.severityType.Error)
        
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and not f.lower().endswith(".json")] # Get files

        if len(files) == 0: # IF no files, error
            hou.ui.displayMessage(f"No geometry file found in directory: {directory}", severity=hou.severityType.Error)
        
        elif len(files) > 1: # Multiple files, error
            hou.ui.displayMessage(f"Multiple geometry files found in directory: {directory}\nFiles: {files}", severity=hou.severityType.Error)
    
        return files[0]
    
    except Exception as e:
        hou.ui.displayMessage(f"Error reading geometry directory:\n{str(e)}", severity=hou.severityType.Error)
        return None


# =========================
# Get Master Dir
# =========================

def getMasterDir(productDir): # Get master directory of any product
    masterDir = os.path.join(productDir, "master")

    try: # Get master dir
        if not os.path.exists(masterDir):
            os.makedirs(masterDir)
    except Exception as e: # Error if not found
        hou.ui.displayMessage(
            f"Could not create master directory:\n{masterDir}\n\n{e}",
            severity=hou.severityType.Error
        )

    return masterDir





# =========================
# Get Latest Version
# =========================

def getLatestVersion (productDir): # Get latest version from product Dir
    try:
        return sorted(
            entry for entry in os.listdir(productDir)
            if os.path.isdir(os.path.join(productDir, entry))
        )
    except FileNotFoundError:
        hou.ui.displayMessage(f"Path does not exist: {productDir}", severity=hou.severityType.Error)
    except NotADirectoryError:
        hou.ui.displayMessage(f"Not a directory: {productDir}", severity=hou.severityType.Error)


# =========================
# Get Next Version
# =========================

def getNextVersion(productDir):
    try:
        # Create base directory if it doesn't exist
        if not os.path.exists(productDir):
            os.makedirs(productDir)

        # Find existing versions
        versions = []
        pattern = re.compile(r"^v(\d+)$")

        for entry in os.listdir(productDir):
            fullPath = os.path.join(productDir, entry)
            if os.path.isdir(fullPath):
                match = pattern.match(entry)
                if match:
                    versions.append(int(match.group(1)))

        # Determine next version
        nextVersion = max(versions, default=0) + 1
        nextFolder = f"v{nextVersion:04d}"
        nextPath = os.path.join(productDir, nextFolder)

        # Create the next version folder
        if not os.path.exists(nextPath):
            os.mkdir(nextPath)
        return nextPath, nextFolder

    except Exception as e:
        hou.ui.displayMessage(
            f"Could not process path:\n{productDir}\n\n{e}",
            severity=hou.severityType.Error
        )


# =========================
# Create Single Material
# =========================

def createSingleMaterial(libraryNode, mtlName):

    shaderNode = libraryNode.createNode("subnet", f"{mtlName}_MTL") # Create Material Network
    shaderNode.setMaterialFlag(True) # Make Subnet Material

    # Turn Sub Net Into Material Network
    shaderNode.addSpareParmTuple(hou.StringParmTemplate("shader_rendercontextname", "Render Context Name", 1, default_value=("mtlx",)))

    # Add MtlX Menus
    shaderNode.addSpareParmTuple(
        hou.StringParmTemplate("tabmenumask", "Tab Menu Mask", 1, default_value=(
                                                                                    "MaterialX parameter constant collect null "
                                                                                    "genericshader subnet subnetconnector "
                                                                                    "suboutput subinput"
            ,)
        )
    )

    # Translate Children
    shaderNode.addSpareParmTuple(
        hou.ToggleParmTemplate("shader_forcechildren", "Force Translation of Children", default_value=True)
    )

    mtlxStandardSurface = shaderNode.createNode("mtlxstandard_surface", f"{mtlName}_SHD") # Create Shader

    # Surface
    surfaceOutput = shaderNode.createNode("subnetconnector","surface_output") # Create Surface Output
    surfaceOutput.parm("connectorkind").set(1) # Set Kind, OUTPUT
    surfaceOutput.parm("parmname").set("surface") # Set name
    surfaceOutput.parm("parmlabel").set("Surface") # Set label
    surfaceOutput.parm("parmtype").set(24) # Set type, SURFACE
    surfaceOutput.setColor(hou.Color(0.1, 0.78, 0.4)) # Set Color

    # Displacement
    displacementOutput = shaderNode.createNode("subnetconnector","displacement_output") # Create Displacement Output
    displacementOutput.parm("connectorkind").set(1) # Set Kind, OUTPUT
    displacementOutput.parm("parmname").set("displacement") # Set name
    displacementOutput.parm("parmlabel").set("Displacement") # Set label
    displacementOutput.parm("parmtype").set(25) # Set type, DISPLACEMENT
    displacementOutput.setColor(hou.Color(0.55, 0.7, 0.91)) # Set Color


    textureFolder = os.path.join(getMasterDir(product_texturesDir),mtlName)


    try:
        for file in os.listdir(textureFolder):

            textureChanel = "" # Create Empty Texture Channel

            try:
                fileNameSplit = file.split("_")
                textureChanel = fileNameSplit[-2]
                
            except:
                hou.ui.displayMessage("Naming convention was not followed \n Manual Material Creation Required :(")


            fileDir = (os.path.join(textureFolder, file))

            searchUDIM = re.search((r'_(\d{4})\.'),(os.path.join(textureFolder, file)))

            if searchUDIM:
                fileDir = re.sub((r'_(\d{4})\.'), (r'_<UDIM>.'), fileDir)




            imageNode = shaderNode.createNode("mtlximage", textureChanel)
            
            if textureChanel == (CONFIG["textures"]["albedo"]) or (CONFIG["textures"]["normal"]):
                imageNode.parm("signature").set("color3")
                if autoColorSpace == 1:
                    imageNode.parm("filecolorspace").set(CONFIG["ColorSpace"]["Acescg"])
            else:
                imageNode.parm("signature").set("default")
                if autoColorSpace == 1:
                    imageNode.parm("filecolorspace").set(CONFIG["ColorSpace"]["raw"])
            
            imageNode.parm("file").set(fileDir)



            # Connect Albedo
            if textureChanel == CONFIG["textures"]["albedo"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["base_color"]), imageNode, 0)
            
            #Connect Metal
            if textureChanel == CONFIG["textures"]["metalness"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["metalness"]), imageNode, 0)

            # Connect Roughness
            if textureChanel == CONFIG["textures"]["specRoughness"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["specular_roughness"]), imageNode, 0)
            
            # Connect normal
            if textureChanel == CONFIG["textures"]["normal"]:
                normalNode = shaderNode.createNode("mtlxnormalmap")
                normalNode.setInput(0, imageNode)
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["normal"]), normalNode, 0)
            
            # Connect emission
            if textureChanel == CONFIG["textures"]["emission"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["emission"]), imageNode, 0)

            # Connect coat
            if textureChanel == CONFIG["textures"]["coat"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["coat"]), imageNode, 0)

            # Connect SSS
            if textureChanel == CONFIG["textures"]["subsurface"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["subsurface"]), imageNode, 0)

            # Connect sheen
            if textureChanel == CONFIG["textures"]["sheen"]:
                mtlxStandardSurface.setInput((CONFIG["mtlxShaderInputs"]["sheen"]), imageNode, 0)
        
            # Connect Disp
            if textureChanel == CONFIG["textures"]["displacement"]:
                displacementNode = shaderNode.createNode("mtlxdisplacement")
                displacementNode.setInput(0, imageNode)
                displacementOutput.setInput(0, displacementNode)
    except:
        hou.ui.displayMessage(f"No Texture Files Found in {mtlName}")
            
    # Connect Shader
    surfaceOutput.setInput(0, mtlxStandardSurface)


    shaderNode.layoutChildren()

# =========================
# Write Json
# =========================

def writeJson(path, version, assetDir, user, userName, comment):

    from datetime import datetime

    # Current Date
    currentDateTime = datetime.now().strftime("%d.%m.%y %H:%M:%S")
    
    # JSON structure
    data = {
        "asset": currentAsset,
        "asset_path": assetDir,
        "paths": [
            assetDir
        ] * 5,  # repeats the path 5 times
        "type": "asset",
        "project_path": projectDir,
        "product": departmentTag,
        "user": user,
        "version": version,
        "comment": comment,
        "username": userName,
        "date": currentDateTime,
        "dependencies": [],
        "externalFiles": []
    }

    jsonFilePath = os.path.join(path, "versioninfo.json")

    # Write to JSON file
    with open(jsonFilePath, "w") as json_file:
        json.dump(data, json_file, indent=4)

# ========================================================================================================================
# Directories / Variables / Options
# ========================================================================================================================


# Load Base Configs
defaultProjectDir = CONFIG["project"]["projectDirectory"]

projectDir = defaultProjectDir
houdiniStudioProgramsDir = CONFIG["project"]["houiniCustomBuild"]

assetsClassList = CONFIG["project"]["assetClassList"]
assetClass = assetsClassList[0] # THIS IS HARD CODED, MUST BE CHANGED TO UI INTERACTION TO GET FULL EXPANDABILITY BETWEEN ASSETS - X - X - X -

assetInfoDir = os.path.join(projectDir, "00_Pipeline", "Assetinfo")

department_map = CONFIG["departments"]



# Get Directory Pieces from file
currentDir = os.path.dirname(hou.hipFile.path())
splitCurrentDir = currentDir.split("/")



# Project Name
proejctName = projectDir.split("\\")[-1]



# Asset Info Json
ASSETINFO_PATH = os.path.join(projectDir, "00_Pipeline", "Assetinfo", "assetInfo.json") # Get the config path
ASSETINFO = load_config(ASSETINFO_PATH) # Create config variable to acces info




# Department
currentDepartment = splitCurrentDir[-2]
departmentTag = department_map.get(currentDepartment, "Unknown") 



# Asset Dir / Name
assetDir = (currentDir.split("Scenefiles"))[0]
currentAsset = (assetDir.split("/"))[-2]



# Directories
products = os.path.join(assetDir, "Export")
sceneFiles = os.path.join(assetDir, "SceneFiles")


# Products
product_assetDir = os.path.join(products, CONFIG["products"]["asset"])
product_geometryDir = os.path.join(products, CONFIG["products"]["geometry"])
product_meshDir = os.path.join(products, CONFIG["products"]["mesh"])
product_texturesDir = os.path.join(products, CONFIG["products"]["textures"])
product_materialDir = os.path.join(products, CONFIG["products"]["materials"])
product_bindingDir = os.path.join(products, CONFIG["products"]["binding"])


# User
pcUsername = os.environ.get("USERNAME").lower()
pcUsernameSplit = pcUsername.split(".")
userName = pcUsernameSplit[0]
user = userName[:3]  


# Variables

masterTextureFolder = os.path.join(product_texturesDir, getMasterDir(product_texturesDir))

# List of folder names
mtlVariantsName_folders = [
    name for name in os.listdir(masterTextureFolder)
    if os.path.isdir(os.path.join(masterTextureFolder, name))
]

# Number of folders
detectedMtlVariants_folders = len(mtlVariantsName_folders)

# USD Write
usdWrite_version = 7.2


# ========================================================================================================================
# Functions
# ========================================================================================================================

# =========================
# Check Asset File
# =========================

def checkAssetInfo():

    cleanedPath = assetDir.split(projectDir.replace("\\","/"))[-1] # Replace the slash by the other format
    cleanedPath = (cleanedPath[1:-1]).replace("/", "\\") # Get rid of the first and last slashes

    # Check if the asset exists
    ASSETINFO.setdefault("assets", {})
    ASSETINFO["assets"].setdefault(currentAsset, {})
    ASSETINFO["assets"][currentAsset].setdefault("metadata", {})

    ASSETINFO["assets"][currentAsset]["metadata"]["path"] = {
        "value": cleanedPath,
        "show": False
    }

    with open(ASSETINFO_PATH, "w") as file: # Wrtie json file
        json.dump(ASSETINFO, file, indent=4)


# =========================
# Check Asset File
# =========================

def checkAssetFile():
    file_path = os.path.join(getMasterDir(product_assetDir), f"{currentAsset}_asset_master{CONFIG['fileExtension']['usdAst']}")

    if not os.path.isfile(file_path):

        # Create Window Alert --> I create it using pyside as i want it to be centered and use the sound the warning makes :)
        main_window = hou.ui.mainQtWindow()

        msg = QtWidgets.QMessageBox(main_window)
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setWindowTitle("Warning")
        msg.setText("USD Asset file is missing. A new one will be created")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

        # Center on screen (or Houdini window)
        msg.setWindowModality(QtCore.Qt.ApplicationModal)
        msg.adjustSize()

        # Center relative to Houdini main window
        geo = main_window.geometry()
        msg.move(
            geo.center().x() - msg.width() // 2,
            geo.center().y() - msg.height() // 2
        )

        msg.exec_()

        # =======================
        # Create Asset File
        # =======================

        # Template
        templateAssetFile = os.path.join(houdiniStudioProgramsDir, "scripts", "usdLoader", "assetTempalte_asset_master.usda")

        # Master
        destinationFile_master = os.path.join(getMasterDir(product_assetDir), f"{currentAsset}_asset_master{CONFIG['fileExtension']['usdAst']}")
        destinationPath_master = Path(destinationFile_master)

        # Version
        versionDir = os.path.join(product_assetDir, "v0001")
        os.makedirs(versionDir)
        destinationFile_version = os.path.join(versionDir, f"{currentAsset}_asset_v0001{CONFIG['fileExtension']['usdAst']}")
        destinationPath_version = Path(destinationFile_version)

        # Copy USDAs
        shutil.copy(templateAssetFile, destinationFile_master)
        shutil.copy(templateAssetFile, destinationFile_version) 

        # Get USDAs Texts
        text_master = Path(destinationFile_master).read_text(encoding="utf-8")
        text_version = Path(destinationFile_version).read_text(encoding="utf-8")

        # Change USDAs
        if "assetTemplate" in text_master:
            text_master = text_master.replace("assetTemplate", currentAsset)
        
        if "assetTemplate" in text_version:
            text_version = text_version.replace("assetTemplate", currentAsset)

        # Write New USDAs
        destinationPath_master.write_text(text_master, encoding="utf-8")
        destinationPath_version.write_text(text_version, encoding="utf-8")

        # Write Jsons
        writeJson((os.path.join(getMasterDir(product_assetDir))), "v0001", assetDir, user, userName, "")
        writeJson((os.path.join(versionDir)), "0001", assetDir, user, userName, "")

# =========================
# Solairs Load GEO
# =========================

def SolarisLoad_geo(outNulls):
    # Get LOPs Context
    LOPs = hou.node("/stage")

    # Check For Existing nodes
    existingNodes = LOPs.allSubChildren()
    for node in existingNodes:
        nodeName = node.name()
        if nodeName == f"{currentAsset}_basePrim_PRIMITIVE":
            return hou.ui.displayMessage(f"{currentAsset} Already Exists. Reload Instead Of Create", severity=hou.severityType.Error) # if it exists stop execution



    # Create Prim Base Node
    primBaseNode = LOPs.createNode("primitive", f"{currentAsset}_basePrim_PRIMITIVE") # Create Node
    primBaseNode.parm("primpath").set(f"/{currentAsset}") # Configure Path
    primBaseNode.parm("primkind").set("component") # Set Kind to Component

    # Create Prim Geo Node
    primGeoNode = LOPs.createNode("primitive", f"{currentAsset}_geoPrim_PRIMITIVE")
    primGeoNode.setInput(0, primBaseNode)
    primGeoNode.parm("primpath").set(f"/{currentAsset}/geo") # Configure Path - no need to configure the other parm, default is fine

    # Create ConfigLayer Node
    configureLayerNode = LOPs.createNode("configurelayer", f"{currentAsset}_GEOMETRY_LYR") # Create Node
    configureLayerNode.parm("flattenop").set("layer") # Set Flatten Input Layer to Layer



    # Create Start Variants
    variantBeginNode = LOPs.createNode("begincontextoptionsblock", f"{currentAsset}_beginGeoVariant")
    variantBeginNode.setColor(hou.Color((0.62, 0.42, 0.76)))
    variantBeginNode.parm("layerbreak").set(True)
    variantBeginNode.setInput(0, primGeoNode)

    # Create End Variants
    variantEndNode = LOPs.createNode("addvariant", f"{currentAsset}_endGeoVariant")
    variantEndNode.parm("primpath").set(f"/{currentAsset}")
    variantEndNode.parm("createoptionsblock").set(1)
    variantEndNode.parm("variantset").set("model")
    variantEndNode.parm("variantprimpath").set(f"/{currentAsset}")
    variantEndNode.setInput(0, primGeoNode)

    variantNodeList = [] # Empty list to put all variant nodes

    # Create Variants
    for variant in outNulls:
        try:
            name = variant.name().split("_")[2] # Get Variant Name
        except:
            name = f"{currentAsset}_MSH"
        
        sopImportNode = LOPs.createNode("sopimport", f"{currentAsset}_{name}") # Create SopImport Node and set name

        sopImportNode.parm("soppath").set((variant).path()) # Change USD Path
        sopImportNode.parm("copycontents").set(1) # Set to Merge SOP Layer Into Existing Active Layer
        sopImportNode.parm("pathprefix").set(f"/{currentAsset}/geo") # Set Import Path Prefix
        sopImportNode.parm("enable_defineonlyleafprims").set(True) # Enable Set Leaf
        sopImportNode.parm("defineonlyleafprims").set(True) # Set Leaf

        sopImportNode.setInput(0, variantBeginNode) # Connect to Begin Variant Block
        variantEndNode.setNextInput(sopImportNode) # Connect sopImports to Variant End Node

        variantNodeList.append(sopImportNode) # Add The nodes into a list, just in case
    
    configureLayerNode.setInput(0,variantEndNode) # Connect ConfigLayer to the variant end block


    
    # Write Geometry USD Node
    try: # This node will not appear / give error, if it's not the custom 2LOUD Houdini
        writeGeoUSDNode = LOPs.createNode(f"tLOUD::usd_write::{usdWrite_version}", f"{currentAsset}_geo_USDWRITE")
        writeGeoUSDNode.setInput(0, configureLayerNode)
        writeGeoUSDNode.parm("depMenu").set(1) # Set Department
        writeGeoUSDNode.parm("autoPath").pressButton() # Set Auto Paths
        writeGeoUSDNode.setDisplayFlag(True) # Set render Flag
        writeGeoUSDNode.parm("hideMtlPath").set(1) # Hide Mtl Path
        writeGeoUSDNode.parm("hideBindPath").set(1) # Hide Bind Path
        writeGeoUSDNode.setSelected(True, clear_all_selected = True) # Select Node
    except:
        hou.ui.displayMessage("2LOUD USD WRITE Node not found \nPlease Check Prism has been correctly set. \n Check the otls folder in the custom Houdini Instalation")

    

    # Layout
    LOPs.layoutChildren(vertical_spacing=1.0)









# =========================
# Load Into SOPs
# =========================

def loadIntoSops(scaleDiff_value):

    # ----- MAIN ASSET NODE ----

    # Get SOPs Context
    SOPs = hou.node("/obj")

    # Check For Existing nodes
    existingNodes = SOPs.allSubChildren()
    for node in existingNodes:
        nodeName = node.name()
        if nodeName == f"{currentAsset}":
            return hou.ui.displayMessage(f"{currentAsset} Already Exists.", severity=hou.severityType.Error) # if it exists stop execution


    # Create main geo node
    mainGeoNode = SOPs.createNode("geo", currentAsset)
    mainGeoNode.moveToGoodPosition() # center the node on the main scene graph



    # ----- ASSET SUB NETWORK -----

    # Create File Node
    fileReadNode = mainGeoNode.createNode("file", f"{currentAsset}_IMPORT")

    product_meshFileDir = os.path.join(getMasterDir(product_meshDir), get_single_geometry_file(getMasterDir(product_meshDir))) # Get file
    fileReadNode.parm("file").set(product_meshFileDir) #change parameter

    # Create Transform
    transformNode = mainGeoNode.createNode("xform", f"{currentAsset}_TRANSFORM")
    transformNode.setInput(0, fileReadNode)


    # Set Scale if check enabeled
    if scaleDiff_value == 1:
        transformNode.parm("scale").set(0.01)



    # Prepare to separate meshes
    fileReadNode.cook(force=True) # Force evaluation of it's content to get all the geo information -> like the name att
    mesh = fileReadNode.geometry() # We create mesh to acces the information the fileReadNode gets from reading the file, all the info is inside here
    
    # Check for name att
    if not mesh.findPrimAttrib("name"):
        hou.ui.displayMessage("No 'name' primitive attribute found in geometry.", severity=hou.severityType.Error)

    # Get names by faces
    name_attrib = mesh.findPrimAttrib("name") # Will return the attribute itself (hou.Attrib)
    unique_names = sorted({prim.attribValue(name_attrib) for prim in mesh.prims()}) # For every face what name it has

    # Create one Blast per mesh (branched)
    for name in unique_names:

        blastNode = mainGeoNode.createNode("blast", f"{name}_BLAST")

        blastNode.setInput(0, transformNode) # connect to file node

        blastNode.parm("group").set(f'@name="{name}"')
        blastNode.parm("negate").set(True)  # keep only selected

        nullNode = mainGeoNode.createNode("null", f"OUT_{name}")
        nullNode.setInput(0, blastNode) # connect to blast

        nullNode.setDisplayFlag(True)

    # Auto-layout nodes
    mainGeoNode.layoutChildren(horizontal_spacing=2.0, vertical_spacing=3.0)
    

    mainGeoNode.setSelected(True, clear_all_selected = True) # Select main geo Node









# =========================
# Send To LOPs
# =========================

def sendToLops():

    # Get LOPs Context
    SOPs = hou.node("/obj")


    # ----- Get All OUT Null Nodes -----

    # Get Selection
    currentSel = hou.selectedNodes()

    # Error if more than one node is selected
    if len(currentSel) != 1:
        hou.ui.displayMessage("Please select one geo node", severity=hou.severityType.Error)
        return
    

    currentSel = currentSel[0] # Get first input  
    subNodes_inSel = currentSel.allSubChildren() # Load all nodes inside subnetwork
    outNulls = [] # Create empty list to add nodes latrer
    nullsOutOfScope = [] # Create empty list to add null nodes that don't match OUT

    # Check node type and name
    for subNode in subNodes_inSel:

        subNode_type = subNode.type().name()
        subNode_name = subNode.name()
        subNode_nameParts = subNode_name.split("_")

        if subNode_type == "null" and subNode_nameParts[0] == "OUT": # Add it to the list
            outNulls.append(subNode)

        elif subNode_type == "null": # Add it to a seperate list to tell the user
            nullsOutOfScope.append(subNode)
    
    noNullsError = 0
        
    # If there are no nulls out of scope start Lops Creation
    if not nullsOutOfScope:
        SolarisLoad_geo(outNulls)

    else: # Allow the user to decide wheather to continue or not
        userChoice = hou.ui.displayCustomConfirmation(
                                        f"Nulls without OUT_ were detected: {nullsOutOfScope}",
                                        severity=hou.severityType.ImportantMessage,
                                        buttons=("Continue", "Cancel"),
                                        default_choice=0, close_choice=1)  

        if userChoice == 0:
            if not outNulls:
                hou.ui.displayMessage(f"No nulls found inside {currentSel.name()}", severity=hou.severityType.Error)
                return
            SolarisLoad_geo(outNulls)

        if userChoice == 1:
            hou.ui.displayMessage(f"Operation Cancelled, check out nodes: {nullsOutOfScope} and try again")
    

    # Error Handeling
    if not outNulls:
        hou.ui.displayMessage(f"No nulls found inside {currentSel.name()}", severity=hou.severityType.Error)
        return












# =========================
# Reload LOPs
# =========================

def reloadLops():
    # Get SOPs Context
    LOPs = hou.node("/stage")


    # Display Warning
    choice = hou.ui.displayMessage(
                                    f"{currentAsset} will be recreated, all LOPs / SOLARIS modifications will get deleted",
                                    buttons=("Continue", "Cancel"),
                                    severity=hou.severityType.Warning,
                                    title="Warning - LOPs")

    # If Continue delete the node and restart the operation
    if choice == 0:
        for node in LOPs.children():
            if node.name().split("_")[0] == f"{currentAsset}":
                node.destroy()
        sendToLops()
        
    # Display message of cancelation
    else:
        hou.ui.displayMessage("Operation Cancelled", severity=hou.severityType.Message)










# =========================
# Reload SOPs
# =========================

def reloadSops(scaleDiff_value, LOPsReladCheckValue):
    # Get SOPs Context
    SOPs = hou.node("/obj")

    # Display Warning
    choice = hou.ui.displayMessage(
                                    f"{currentAsset} will be recreated, all SOPs modifications inside the current node will get deleted",
                                    buttons=("Continue", "Cancel"),
                                    severity=hou.severityType.Warning,
                                    title="Warning - SOPs")

    # If Continue delete the node and restart the operation
    if choice == 0:
        for node in SOPs.children():
            if node.name() == f"{currentAsset}":
                node.destroy()
        loadIntoSops(scaleDiff_value)
        if LOPsReladCheckValue == True:
            reloadLops()
        
    # Display message of cancelation
    else:
        hou.ui.displayMessage("Operation Cancelled", severity=hou.severityType.Message)









# =========================
# Create Materials
# =========================

def createMaterials (mtlVariants_UI):
    
    # Get LOPs Context
    LOPs = hou.node("/stage")



    # Check For Existing nodes
    existingNodes = LOPs.allSubChildren()
    for node in existingNodes:
        nodeName = node.name()
        if nodeName == f"{currentAsset}_basePrim_PRIMITIVE":
            return hou.ui.displayMessage(f"{currentAsset} Already Exists. Reload Instead Of Create", severity=hou.severityType.Error) # if it exists stop execution





    # Create Prim Base Node
    primBaseNode = LOPs.createNode("primitive", f"{currentAsset}_basePrim_PRIMITIVE") # Create Node
    primBaseNode.parm("primpath").set(f"/{currentAsset}") # Configure Path
    primBaseNode.parm("primkind").set("component") # Set Kind to Component

    # Create Prim Geo Node
    primGeoNode = LOPs.createNode("primitive", f"{currentAsset}_geoPrim_PRIMITIVE")
    primGeoNode.setInput(0, primBaseNode)
    primGeoNode.parm("primpath").set(f"/{currentAsset}/geo") # Configure Path - no need to configure the other parm, default is fine

    # Create Prim Mtl Node
    primMtlNode = LOPs.createNode("primitive", f"{currentAsset}_mtlPrim_PRIMITIVE")
    primMtlNode.setInput(0, primGeoNode)
    primMtlNode.parm("primtype").set("UsdGeomScope") # Set Prim Type to Scope
    primMtlNode.parm("primpath").set(f"/{currentAsset}/mtl") # Configure Path - no need to configure the other parm, default is fine

    # Create Sublayer
    sublayerNode = LOPs.createNode("sublayer", f"{currentAsset}_loadGeo_SUBLAYER")
    try:
        sublayerNode.parm("filepath1").set(f"{getMasterDir(product_geometryDir)}/{currentAsset}_geometry_master{(CONFIG['fileExtension']['usdGeo'])}")
    except:
        hou.ui.displayMessage("Could not set sublayer path", severity=hou.severityType.Error)
    
    # Craete Reference Node RefGeo
    geoReferenceNode = LOPs.createNode("reference::2.0", f"{currentAsset}_geometry_REFERENCE") # Create Reference Node
    geoReferenceNode.parm("primpath").set(f"/{currentAsset}") # Set USD Path
    geoReferenceNode.parm("num_files").set(0) # Eliminate default number of references
    geoReferenceNode.setInput(0, primMtlNode) # Connect to primMtlNode
    geoReferenceNode.setInput(1, sublayerNode)
    geoReferenceNode.bypass(True)

    # Create Reference Node RefMtl
    mtlReferenceNode = LOPs.createNode("reference::2.0", f"{currentAsset}_material_REFERENCE") # Create Reference Node
    mtlReferenceNode.parm("primpath").set(f"/{currentAsset}/mtl") # Set USD Path
    mtlReferenceNode.parm("num_files").set(0) # Eliminate default number of references
    mtlReferenceNode.setInput(0, geoReferenceNode) # Connect to primMtlNode









    # Create Material Library
    materialLibraryNode = LOPs.createNode("materiallibrary", f"{currentAsset}_MTLLIBRARY") # Create Material Library

    # Create Material / Materials

    materialList = mtlVariantsName_folders
    
    materialDifference = mtlVariants_UI-detectedMtlVariants_folders
    
    if materialDifference == 0:
        pass
    else:
        newMaterials = list(range(materialDifference))
        userSelection = hou.ui.displayMessage(
            f"{detectedMtlVariants_folders} Materials were detected.\nUser asked for {mtlVariants_UI}.\nMissing {materialDifference}.\n Please clarify new materials names",
            buttons=("Clarify Names", "Cancel"), severity=hou.severityType.Warning, title="Clarify Materials")
        
        if userSelection == 0:
            for new in newMaterials:
                userInputName = (hou.ui.readInput("Enter Material Name:"))[1]
                userInputName = userInputName.replace(" ","_")
                newName = f"{currentAsset}_{userInputName}"
                materialList.append(newName)
        else:
            hou.ui.displayMessage("LOPs Will Be Cleaned, The Process will start again")
            reloadMaterials()

    materialIndex = 1


    for material in materialList:

        mtlName = material

        if materialIndex > detectedMtlVariants_folders:
            mtlType = 1

        materialIndex += 1
        
        createSingleMaterial(materialLibraryNode, mtlName)
    


    materialLibraryNode.layoutChildren()
    materialLibraryNode.parm("fillmaterials").pressButton()



    # Create ConfigLayer Node
    configureLayerNode = LOPs.createNode("configurelayer", f"{currentAsset}_MATERIAL_LYR") # Create Node
    configureLayerNode.parm("flattenop").set("layer") # Set Flatten Input Layer to Layer
    configureLayerNode.parm("startnewlayer").set(1) 
    configureLayerNode.parm("setsavepath").set(1) 
    configureLayerNode.parm("savepath").set(f"{getMasterDir(product_materialDir)}/{currentAsset}_materials_master{(CONFIG['fileExtension']['usdMtl'])}")
    configureLayerNode.setInput(0, materialLibraryNode)


    mtlReferenceNode.setInput(1, configureLayerNode)



    # Check for Variants


    # Create Variants or just one node
    if mtlVariants_UI == 1:
        assignMtlNode = LOPs.createNode("assignmaterial", f"{materialList[0]}") # Create SopImport Node and set name

        assignMtlNode.parm("primpattern1").set(f"/{currentAsset}/geo") # Set USD geo to bind
        assignMtlNode.parm("matspecpath1").set(f"/{currentAsset}/mtl/{materialList[0]}_MTL") # Material to bind

        assignMtlNode.setInput(0,mtlReferenceNode) # Connect to reference Node
        #configureLayerNode.setInput(0,assignMtlNode) # Connect ConfigLayer to Import Node
    
    elif mtlVariants_UI < 1:
        hou.ui.displayMessage("Material index = 0 \n Error loading materials", severity=hou.severityType.Error) # Display error
        raise hou.Error("No materials Created Operation Cancelled")

    else:
        # Create Start Variants
        variantBeginNode = LOPs.createNode("begincontextoptionsblock", f"{currentAsset}_beginMtlVariant")
        variantBeginNode.setColor(hou.Color((0.62, 0.42, 0.76)))
        variantBeginNode.parm("layerbreak").set(True)
        variantBeginNode.setInput(0, mtlReferenceNode)

        # Create End Variants
        variantEndNode = LOPs.createNode("addvariant", f"{currentAsset}_endMtlVariant")
        variantEndNode.parm("primpath").set(f"/{currentAsset}")
        variantEndNode.parm("createoptionsblock").set(1)
        variantEndNode.parm("variantset").set("mtl")
        variantEndNode.parm("variantprimpath").set(f"/{currentAsset}")
        variantEndNode.setInput(0, mtlReferenceNode)

        variantNodeList = [] # Empty list to put all variant nodes

        # Create Variants
        for variant in materialList:
            name = variant # Get Variant Name
            assignMtlNode = LOPs.createNode("assignmaterial", f"{name}") # Create SopImport Node and set name

            assignMtlNode.parm("primpattern1").set(f"/{currentAsset}/geo") # Set USD geo to bind
            assignMtlNode.parm("matspecpath1").set(f"/{currentAsset}/mtl/{name}_MTL") # Material to bind

            assignMtlNode.setInput(0, variantBeginNode) # Connect to Begin Variant Block
            variantEndNode.setNextInput(assignMtlNode) # Connect sopImports to Variant End Node

            variantNodeList.append(assignMtlNode) # Add The nodes into a list, just in case
        
    # Create ConfigLayer Node
    configureLayerBindNode = LOPs.createNode("configurelayer", f"{currentAsset}_BIND_LYR") # Create Node
    configureLayerBindNode.parm("flattenop").set("layer") # Set Flatten Input Layer to Layer

    try:
        configureLayerBindNode.setInput(0, variantEndNode) # Connect
    except:
        configureLayerBindNode.setInput(0, assignMtlNode) # Connect
    
    configureLayerBindNode.setDisplayFlag(True) # Set render Flag

    # Write Geometry USD Node
    try: # This node will not appear / give error, if it's not the custom 2LOUD Houdini
        writeMtlBindUSDNode = LOPs.createNode(f"tLOUD::usd_write::{usdWrite_version}", f"{currentAsset}_geo_USDWRITE") 
        writeMtlBindUSDNode.setInput(0, configureLayerBindNode)
        writeMtlBindUSDNode.parm("depMenu").set(2) # Set Department
        writeMtlBindUSDNode.parm("autoPath").pressButton() # Set Auto Paths
        writeMtlBindUSDNode.setDisplayFlag(True) # Set render Flag
        writeMtlBindUSDNode.parm("hideGeoPath").set(1) # Hide Mtl Path
        writeMtlBindUSDNode.setSelected(True, clear_all_selected = True) # Select Node

    except:
        hou.ui.displayMessage("2LOUD USD WRITE Node not found \nPlease Check Prism has been correctly set. \n Check the otls folder in the custom Houdini Instalation")



    LOPs.layoutChildren()



    






# =========================
# Reload Materials
# =========================

def reloadMaterials(mtlVariants_UI):

    # Get LOPs Context
    LOPs = hou.node("/stage")

    # Get Existing Nodes
    existingNodes = LOPs.allSubChildren()

    # DisplayWarning
    userChoice = hou.ui.displayMessage(f"{currentAsset} will be recreated, all Material modifications will get deleted",
                                         severity=hou.severityType.Warning,
                                         buttons=("Continue", "Cancel"),
                                         default_choice=1) 
    
    if userChoice == 0:
        for node in existingNodes:
            try:
                node.destroy()
            except:
                pass
        
        createMaterials(mtlVariants_UI)
        hou.ui.displayMessage("Operation Succesful")
    
    else:
        hou.ui.displayMessage("Operation Cancelled")









# =========================
# Add Material
# =========================

def addMaterial ():
    
    # Get LOPs Context
    LOPs = hou.node("/stage")

    userInputName = (hou.ui.readInput("Enter Material Name:"))[1]
    newName = f"{currentAsset}_{userInputName}"


    # Declare Nodes
    materialLibraryNode = ""
    variantBeginNode = ""
    variantEndNode = ""
    referenceMtlNode = ""
    configLayerNode = ""


    existingNodes = LOPs.allSubChildren()

    bindNodes = [] # Empty List For All Bind Nodes

    for node in existingNodes:
        if node.name() == f"{currentAsset}_MTLLIBRARY":
            materialLibraryNode = node

        if node.name() == f"{currentAsset}_beginMtlVariant":
            variantBeginNode = node

        if node.name() == f"{currentAsset}_endMtlVariant":
            variantEndNode = node

        if node.name() == f"{currentAsset}_material_REFERENCE":
            referenceMtlNode = node
        
        if node.type().name() == "assignmaterial":
            bindNodes.append(node)
        
        if node.name() == f"{currentAsset}_BIND_LYR":
            configLayerNode = node


    if not variantBeginNode:
        # Create Start Variants
        variantBeginNode = LOPs.createNode("begincontextoptionsblock", f"{currentAsset}_beginMtlVariant")
        variantBeginNode.setColor(hou.Color((0.62, 0.42, 0.76)))
        variantBeginNode.parm("layerbreak").set(True)
        variantBeginNode.setInput(0, referenceMtlNode)

    if not variantEndNode:
        # Create End Variants
        variantEndNode = LOPs.createNode("addvariant", f"{currentAsset}_endMtlVariant")
        variantEndNode.parm("primpath").set(f"/{currentAsset}")
        variantEndNode.parm("createoptionsblock").set(1)
        variantEndNode.parm("variantset").set("mtl")
        variantEndNode.parm("variantprimpath").set(f"/{currentAsset}")
        variantEndNode.setInput(0, referenceMtlNode)
    


    if len(bindNodes) == 1:
        (bindNodes[0]).setInput(0, variantBeginNode) # Connect to Begin Variant Block
        variantEndNode.setInput(1, (bindNodes[0])) # Connect sopImports to Variant End Node

    # Add New Material To The List
    bindNodes.append(newName)
    

    createSingleMaterial(materialLibraryNode, newName)

    materialLibraryNode.layoutChildren()
    materialLibraryNode.parm("fillmaterials").pressButton()

    # Create Variants
    
    name = bindNodes[-1] # Get Variant Name
    assignMtlNode = LOPs.createNode("assignmaterial", f"{name}") # Create SopImport Node and set name

    assignMtlNode.parm("primpattern1").set(f"/{currentAsset}/geo") # Set USD geo to bind
    assignMtlNode.parm("matspecpath1").set(f"/{currentAsset}/mtl/{name}_MTL") # Material to bind

    
    assignMtlNode.setInput(0, variantBeginNode) # Connect to Begin Variant Block
    variantEndNode.setNextInput(assignMtlNode) # Connect sopImports to Variant End Node

    configLayerNode.setInput(0, variantEndNode)

    LOPs.layoutChildren()









# =========================
# Load HDRIs
# =========================

def loadHDRIs():
    # Get LOPs Context
    LOPs = hou.node("/stage")

    # Try to get resources path from config
    ressourcesPath = CONFIG["project"].get("resources")
    if not ressourcesPath:
        hou.ui.displayMessage(
            "Project 'resources' path is not defined in the config.",
            severity=hou.severityType.Error
        )
        return

    # Construct HDRI path
    hdriPath = os.path.join(ressourcesPath, "HDRIs", "Studio_01.exr")

    # Check if HDRI file exists
    if not os.path.exists(hdriPath):
        hou.ui.displayMessage(
            f"HDRI file not found:\n{hdriPath}",
            severity=hou.severityType.Error
        )
        return

    # Create Environment Light in LOPs
    try:
        hdriNode = LOPs.createNode("domelight::2.0", "general_HDRI_LGT")
        hdriNode.parm("xn__inputstexturefile_r3ah").set(hdriPath)
        hdriNode.setDisplayFlag(True)
        LOPs.layoutChildren() # Organize
        hou.ui.displayMessage(f"HDRI loaded successfully:\n{hdriPath}")
    except Exception as e:
        hou.ui.displayMessage(
            f"Failed to create HDRI light node:\n{str(e)}",
            severity=hou.severityType.Error
        )
    
    







# =========================
# Check Asset
# =========================

def checkAsset():

    # Get LOPs Context
    LOPs = hou.node("/stage")


    # Create Prim Base Node
    primBaseNode = LOPs.createNode("primitive", f"{currentAsset}_basePrim_PRIMITIVE") # Create Node
    primBaseNode.parm("primpath").set(f"/{currentAsset}") # Configure Path
    primBaseNode.parm("primkind").set("component") # Set Kind to Component
    primBaseNode.parm("parentprimtype").set("UsdGeomScope") # Set Parent Prim Type to Scope
    primBaseNode.parm("primtype").set("UsdGeomScope") # Set PrimType to Scope

    # Create Prim Geo Node
    primGeoNode = LOPs.createNode("primitive", f"{currentAsset}_geoPrim_PRIMITIVE")
    primGeoNode.setInput(0, primBaseNode)
    primGeoNode.parm("primpath").set(f"/{currentAsset}/geo") # Configure Path - no need to configure the other parm, default is fine

    # Create Prim Mtl Node
    primMtlNode = LOPs.createNode("primitive", f"{currentAsset}_mtlPrim_PRIMITIVE")
    primMtlNode.setInput(0, primGeoNode)
    primMtlNode.parm("primpath").set(f"/{currentAsset}/mtl") # Configure Path - no need to configure the other parm, default is fine

    # Craete Reference Node RefGeo
    geoReferenceNode = LOPs.createNode("reference::2.0", f"{currentAsset}_geometry_REFERENCE") # Create Reference Node
    geoReferenceNode.parm("primpath").set(f"/{currentAsset}") # Set USD Path
    geoReferenceNode.parm("num_files").set(0) # Eliminate default number of references
    geoReferenceNode.setInput(0, primMtlNode) # Connect

    # Create Reference Node RefMtl
    mtlReferenceNode = LOPs.createNode("reference::2.0", f"{currentAsset}_material_REFERENCE") # Create Reference Node
    mtlReferenceNode.parm("primpath").set(f"/{currentAsset}/mtl") # Set USD Path
    mtlReferenceNode.parm("num_files").set(0) # Eliminate default number of references
    mtlReferenceNode.setInput(0, geoReferenceNode) # Connect

    # Create Reference Node Bind
    bindReferenceNode = LOPs.createNode("reference::2.0", f"{currentAsset}_binding_REFERENCE") # Create Reference Node
    bindReferenceNode.parm("primpath").set(f"/{currentAsset}") # Set USD Path
    bindReferenceNode.parm("num_files").set(0) # Eliminate default number of references
    bindReferenceNode.setInput(0, mtlReferenceNode) # Connect

    # Create Set Variant
    setVariantNode = LOPs.createNode("setvariant", f"{currentAsset}_SETVARIANT") # Create Variant Node
    setVariantNode.parm("num_variants").set(2) # Set Num Variants
    setVariantNode.parm("primpattern1").set(f"/{currentAsset}") # Set Prim Pattern
    setVariantNode.parm("primpattern2").set(f"/{currentAsset}") # Set Prim Pattern
    setVariantNode.parm("variantset1").set("model") # Set Variant Type
    setVariantNode.parm("variantset2").set("mtl") # Set Variant Type
    setVariantNode.setInput(0, bindReferenceNode) # Connect to reference

    # Create Null
    endNull = LOPs.createNode("null", f"{currentAsset}_check_NULL") # Create Null
    endNull.setInput(0, setVariantNode) # Connect to bind

    # Create geoSublayer
    geoSublayerNode = LOPs.createNode("sublayer", f"{currentAsset}_GEOMETRY_SUBLAYER") #
    geoSublayerNode.parm("filepath1").set(f"{getMasterDir(product_geometryDir)}\\{currentAsset}_geometry_master{(CONFIG['fileExtension']['usdGeo'])}")
    geoReferenceNode.setNextInput(geoSublayerNode)

    # Create geoSublayer
    mtlSublayerNode = LOPs.createNode("sublayer", f"{currentAsset}_MATERIALS_SUBLAYER") #
    mtlSublayerNode.parm("filepath1").set(f"{getMasterDir(product_materialDir)}\\{currentAsset}_materials_master{(CONFIG['fileExtension']['usdMtl'])}")
    mtlReferenceNode.setNextInput(mtlSublayerNode)

    # Create geoSublayer
    bindSublayerNode = LOPs.createNode("sublayer", f"{currentAsset}_BINDING_SUBLAYER") #
    bindSublayerNode.parm("filepath1").set(f"{getMasterDir(product_bindingDir)}\\{currentAsset}_binding_master{(CONFIG['fileExtension']['usdBind'])}")
    bindReferenceNode.setNextInput(bindSublayerNode)

    LOPs.layoutChildren() # Organize


    





# =========================
# Load Asset
# =========================


class AssetImageWidget(QtWidgets.QWidget): # Create Buttons with images and extra data



    def __init__(self, image_path, size=96): # Image path and predifinded size
        super().__init__() # initialize


        # Layout
        layout = QtWidgets.QVBoxLayout(self) # Create Layout for buttona nd text
        layout.setContentsMargins(0,0,0,0) # Set no margins
        layout.setSpacing(2) # set gap between iamge and text



        # Button Creation
        self.image_path = image_path # store full image path inside the button
        self.image_name = os.path.splitext(os.path.basename(image_path))[0] # strip image name

        self.button = QtWidgets.QPushButton()
        self.button.setCheckable(True) # clikable
        self.button.setFixedSize(size, size) # Use the size created before

        pixmap = QtGui.QPixmap(image_path) # Image Data
        icon = QtGui.QIcon(pixmap) # Turn image data into icon
        self.button.setIcon(icon) # Set the icon
        self.button.setIconSize(QtCore.QSize(size - 8, size - 8)) # Set icon size and make smaller so it doesnt overlapp

        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #333;
                background-color: #222;
            }
            QPushButton:checked {
                border: 2px solid #42f5b6;
                background-color: #333;
            }
        """) # Create style guide. for the selection color: 2LOUD color was used



        # Text Creation
        fileName = image_path.split("\\")[-1] # Strip image file name
        name = fileName.split("_preview.jpg")[0] # strip image name
        self.label = QtWidgets.QLabel(f"{name}") # Set Label
        self.label.setFixedHeight(20)
        self.label.setAlignment(QtCore.Qt.AlignCenter) # Align
        self.label.setStyleSheet("color: #ccc; font-size: 10pt;") # Set text style



        # Layout
        layout.addWidget(self.button, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)

        # Store
        self.button.image_name = name # Store the name on the button




class AssetPickerWindow(QtWidgets.QDialog):


    def __init__(self, image_dir, parent=None):
        super().__init__(parent) # Initialize

        self.setWindowTitle("Select Asset") # Title
        self.resize(600, 450) # Window size --> This one is resizable

        self.selected_asset = None # Empty variable to store results
        self.buttons = [] # Empty list of buttons

        main_layout = QtWidgets.QVBoxLayout(self) # Main layout Vertixal    

        # Title Layout
        title_layout = QtWidgets.QHBoxLayout()

        # Title
        title = QtWidgets.QLabel("Select Asset")
        title.setStyleSheet("font-size: 25px; font-weight: bold;")

        # Put All Together
        title_layout.addWidget(title)

        # Add Title Layout To 
        main_layout.addLayout(title_layout)

        # Scroll area
        scroll = QtWidgets.QScrollArea() # Create Scrolalble widget
        scroll.setWidgetResizable(True) # Riziseable as window
        main_layout.addWidget(scroll) # And parent

        content = QtWidgets.QWidget() # Content to scroll
        scroll.setWidget(content) # Add the content to scroll

        grid = QtWidgets.QGridLayout(content) # Create grid
        grid.setSpacing(6) # spacing between iamges

        images = [] # Empty list of every image in the dir

        for image in os.listdir(image_dir): # Loop every file in the image_dir
            if image.lower().endswith(".jpg"): # Only .jpg as that's how prism saves the images
                images.append(os.path.join(image_dir, image)) # Append the iamge to the dir

        if not images: # If there are no images
            QtWidgets.QLabel("No asset images found.")

        columns = 5 # number of columns

        for i, img in enumerate(images):
            widget = AssetImageWidget(img) # Create the widget using
            btn = widget.button # button
            btn.clicked.connect(self._make_callback(btn)) # run function
            self.buttons.append(btn) # append button to buttons list 

            grid.addWidget(widget, i // columns, i % columns) # put onto grid 

            fileName = img.split("\\")[-1] # Strip image file name
            name = fileName.split("_preview.jpg")[0] # strip image name

            try:
                assetInfo_Id = ASSETINFO["assets"][name]["metadata"]["id"]["value"]
            except:
                assetInfo_Id = ""

            try:
                assetInfo_geoVariants = ASSETINFO["assets"][name]["metadata"]["geoVariants"]["value"]
            except:
                assetInfo_geoVariants = ""

            try:
                assetInfo_mtlVariants = ASSETINFO["assets"][name]["metadata"]["mtlVariants"]["value"]
            except:
                assetInfo_mtlVariants = ""



            # Set Tool Tip
            btn.setToolTip(
                            f"{name}<br>"
                            "<br>"
                            f"Asset ID:       {assetInfo_Id}<br>"
                            "<br>"
                            f"Geo Varaints:   {assetInfo_geoVariants}<br>"
                            f"Mtl Varaints:   {assetInfo_mtlVariants}<br>")

        # Buttons - basic button, layout and connect stuff
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()

        accept_btn = QtWidgets.QPushButton("Accept")
        cancel_btn = QtWidgets.QPushButton("Cancel")

        accept_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(accept_btn)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)



    # Set selected
    def _make_callback(self, button):
        def callback():

            for b in self.buttons: # unselect all buttons
                b.setChecked(False)

            button.setChecked(True) # select only that button

            self.selected_asset = button.image_name # store result

        return callback



    # User Accept
    def _accept(self):
        if not self.selected_asset: # Don't let anything happen until asset is selected
            return
        self.accept()



def pick_asset_from_images(image_dir):
    dialog = AssetPickerWindow(image_dir, parent=hou.ui.mainQtWindow()) # Create Pikker Window

    if dialog.exec_(): # Freezes code execution until user closes it or accepts
        return dialog.selected_asset

    return None



def laodAst():

    # Path missing
    if not os.path.exists(assetInfoDir):
        hou.ui.displayMessage(
            f"Assetinfo directory not found:\n{assetInfoDir}",
            severity=hou.severityType.Error
        )
        return

    # Geet Selected Asset
    selected_asset = pick_asset_from_images(assetInfoDir)

    # Safe Chekc
    if not selected_asset:
        return



    # Action
    LOPs = hou.node("/stage") # Load LOPs Stage

    referenceAssetNode = LOPs.createNode("reference::2.0", f"{selected_asset}_IMPORT") # Create Node

    assetPath = ASSETINFO["assets"][selected_asset]["metadata"]["path"]["value"] # Get Node Path froma ssetInfo
    selectedAssetPath = os.path.join(projectDir, assetPath, "Export", "asset", "master", f"{selected_asset}_asset_master{(CONFIG['fileExtension']['usdAst'])}") # Finish path
    selectedAssetPath = selectedAssetPath.replace("\\", "/") # Replace so no houdini Errors
    referenceAssetNode.parm("filepath1").set(selectedAssetPath) # Set paramater
    referenceAssetNode.parm("primpath1").set(f"/{selected_asset}")
    referenceAssetNode.moveToGoodPosition() # Move
    referenceAssetNode.setSelected(True, clear_all_selected = True)
    referenceAssetNode.setDisplayFlag(True)

    hou.ui.displayMessage(f"Imported {selected_asset}") # Siplay message



    



    





# ========================================================================================================================
# UI
# ========================================================================================================================


class USDLoader(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(USDLoader, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)


        # Set Window
        self.setWindowTitle("USD Loader")
        self.setFixedSize(450, 500)





        # Main Layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)





        # =========================
        # Main Title
        # =========================        

        # Title Layout
        title_layout = QtWidgets.QHBoxLayout()

        # Title
        title = QtWidgets.QLabel("USD LOADER")
        title.setStyleSheet("font-size: 50px; font-weight: bold;")

        # Version
        version = QtWidgets.QLabel(f"v {toolVersion}")
        version.setStyleSheet("font-size: 15px; color: gray;")

        # Put All Together
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(version)

        # Add Title Layout To 
        main_layout.addLayout(title_layout)





        # =========================
        # SEPARATOR
        # =========================
        main_layout.addWidget(self._separator())





        # =========================
        # PATH ROW
        # =========================

        # Layout
        path_layout = QtWidgets.QHBoxLayout()

        # Text
        path_label = QtWidgets.QLabel("Prj Root")

        # Text Field
        self.path_field = QtWidgets.QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setStyleSheet("QLineEdit { color: grey;}")
        self.path_field.setText(f"{projectDir}")

        # Add Widgets
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_field)

        # Add to main layout
        main_layout.addLayout(path_layout)





        # =========================
        # SEPARATOR
        # =========================
        main_layout.addWidget(self._separator())

        



        # =========================
        # INFO ROW
        # =========================

        # info Layout
        info_layout = QtWidgets.QVBoxLayout()

        # Project Layout
        project_layout = QtWidgets.QHBoxLayout()

        # Asset Layout
        asset_layout = QtWidgets.QHBoxLayout()



        # Project Text
        projectText = QtWidgets.QLabel("Current Project:")

        # Project
        self.project_name = QtWidgets.QLineEdit()
        self.project_name.setReadOnly(True)
        self.project_name.setStyleSheet("QLineEdit { color: white; font-weight: bold; }")
        self.project_name.setText(proejctName)

        # Department Text
        departmentText = QtWidgets.QLabel("Current Department:")

        # Department
        self.department_name = QtWidgets.QLineEdit()
        self.department_name.setReadOnly(True)
        self.department_name.setStyleSheet("QLineEdit { color: white; font-weight: bold; }")
        self.department_name.setText(f"{departmentTag}")



        # Asset Text
        assetText = QtWidgets.QLabel("Current Asset:")

        # Asset Name
        self.asset_name = QtWidgets.QLineEdit()
        self.asset_name.setReadOnly(True)
        self.asset_name.setStyleSheet("QLineEdit { color: white; font-weight: bold; }")
        self.asset_name.setText(f"{currentAsset}")

        # Asset ID
        assetIDText = QtWidgets.QLabel("Asset ID:")

        # Asset ID
        self.asset_id = QtWidgets.QLineEdit()
        self.asset_id.setReadOnly(True)
        self.asset_id.setStyleSheet("QLineEdit { color: white; font-weight: bold; }")
        self.asset_id.setText(f"{assetjsonID}")


        project_layout.addWidget(projectText)
        project_layout.addWidget(self.project_name)
        project_layout.addWidget(departmentText)
        project_layout.addWidget(self.department_name)

        asset_layout.addWidget(assetText)
        asset_layout.addWidget(self.asset_name)
        asset_layout.addWidget(assetIDText)
        asset_layout.addWidget(self.asset_id)

        info_layout.addLayout(project_layout)
        info_layout.addLayout(asset_layout)

        #asset_layout.addStretch()

        main_layout.addLayout(info_layout)

        # =========================
        # SEPARATOR
        # =========================
        main_layout.addWidget(self._separator())

        # =========================
        # MODELING SECTION
        # =========================

        # Modeling Title
        modeling_label = QtWidgets.QLabel("Modeling")
        modeling_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(modeling_label)

        # Create 1rst Row
        modeling_row = QtWidgets.QHBoxLayout()

        # SOPs Button
        self.load_sops_btn = QtWidgets.QPushButton("SOPs Load")

        # Reload SOPs Button
        self.reloadSOPs_btn = QtWidgets.QPushButton()
        reloadIconDir = os.path.join(houdiniStudioProgramsDir, "icons", "reload.svg")
        reloadIcon = QtGui.QIcon(reloadIconDir)
        self.reloadSOPs_btn.setIcon(reloadIcon)

        # Reload LOPs Checkbox
        self.reloadLOPs_check = QtWidgets.QCheckBox("Auto Relad LOPs")
        self.reloadLOPs_check.setChecked(True)

        # Scale Differnece Checkbox
        self.scaleDif_check =  QtWidgets.QCheckBox("Apply Scale Difference")
        self.scaleDif_check.setChecked(True)

        # Add Widgets to 1rst Row
        modeling_row.addWidget(self.load_sops_btn)
        modeling_row.addWidget(self.reloadSOPs_btn)
        modeling_row.addWidget(self.reloadLOPs_check)
        modeling_row.addWidget(self.scaleDif_check)
        modeling_row.addStretch()

        # Attach TO Main Layout
        main_layout.addLayout(modeling_row)

        # Create 2rst Row
        modeling_2ndrow = QtWidgets.QHBoxLayout()

        # Solaris Button
        self.send_lops_btn = QtWidgets.QPushButton("LOPs Send")

        # Reload LOPs Button
        self.reloadLOPs_btn = QtWidgets.QPushButton()
        reloadIconDir = os.path.join(houdiniStudioProgramsDir, "icons", "reload.svg")
        reloadIcon = QtGui.QIcon(reloadIconDir)
        self.reloadLOPs_btn.setIcon(reloadIcon)

        # Add Widgets to 2nd Row
        modeling_2ndrow.addWidget(self.send_lops_btn)
        modeling_2ndrow.addWidget(self.reloadLOPs_btn)
        modeling_2ndrow.addStretch()

        # Add Layout to main
        main_layout.addLayout(modeling_2ndrow)
    

        # =========================
        # SEPARATOR
        # =========================
        main_layout.addWidget(self._separator())

        # =========================
        # LOOKDEV SECTION
        # =========================

        lookdev_label = QtWidgets.QLabel("LookDev")
        lookdev_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(lookdev_label)

        # Variants Layout
        variants_layout = QtWidgets.QHBoxLayout()

        # Variants Text
        variants_label = QtWidgets.QLabel("Material Variants")

        # Variant Spin Box
        self.variant_spin = QtWidgets.QSpinBox()
        self.variant_spin.setRange(detectedMtlVariants_folders, 15)
        self.variant_spin.setValue(detectedMtlVariants_folders)

        # Reload Button
        self.reloadMtls_btn = QtWidgets.QPushButton()
        self.reloadMtls_btn.setIcon(reloadIcon)

        # Add Material Button
        self.addMaterial_btn = QtWidgets.QPushButton()
        plusIconDir = os.path.join(houdiniStudioProgramsDir, "icons", "plus.svg")
        plusIcon = QtGui.QIcon(plusIconDir)
        self.addMaterial_btn.setIcon(plusIcon)

        # Add Widgets To Variants Layout
        variants_layout.addWidget(variants_label)
        variants_layout.addWidget(self.variant_spin)
        variants_layout.addWidget(self.reloadMtls_btn)
        variants_layout.addWidget(self.addMaterial_btn)
        variants_layout.addStretch()

        # Add To Main Layout
        main_layout.addLayout(variants_layout)

        # Create Button
        self.create_btn = QtWidgets.QPushButton("Create")

        # Add Button To Main Layout
        main_layout.addWidget(self.create_btn)

        # =========================
        # SEPARATOR
        # =========================
        main_layout.addWidget(self._separator())

        # =========================
        # GENERAL SECTION
        # =========================

        # General Title
        general_label = QtWidgets.QLabel("General")
        general_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(general_label)

        # General Layout
        general_layout = QtWidgets.QHBoxLayout()

        # Check Asset Button
        self.checkAsset_btn = QtWidgets.QPushButton("  Check Asset")
        assetIconDir = os.path.join(houdiniStudioProgramsDir, "icons", "view_graph")
        assetIcon = QtGui.QIcon(assetIconDir)
        self.checkAsset_btn.setIcon(assetIcon)

        # Load Asset Button
        self.loadAsset_btn = QtWidgets.QPushButton("  Load Asset")
        assetIconDir = os.path.join(houdiniStudioProgramsDir, "icons", "assetreference")
        assetIcon = QtGui.QIcon(assetIconDir)
        self.loadAsset_btn.setIcon(assetIcon)
    
        # HDRI Button
        self.hdri_btn = QtWidgets.QPushButton("  Load HDRIs")
        hdriIconDir = os.path.join(houdiniStudioProgramsDir, "icons", "light_environment")
        hdriIconDir = QtGui.QIcon(hdriIconDir)
        self.hdri_btn.setIcon(hdriIconDir)

    
        # Attach To Main Layout
        general_layout.addWidget(self.checkAsset_btn)
        general_layout.addWidget(self.loadAsset_btn)
        general_layout.addWidget(self.hdri_btn)

        main_layout.addLayout(general_layout)
        main_layout.addStretch()


        # =========================
        # SIGNALS
        # =========================
        self.load_sops_btn.clicked.connect(self.loadIntoSops_trigger)
        self.send_lops_btn.clicked.connect(self.sendToLops_trigger)
        self.reloadSOPs_btn.clicked.connect(self.reloadSOPs_trigger)
        self.reloadLOPs_btn.clicked.connect(self.reloadLOPs_trigger)
        self.create_btn.clicked.connect(self.createMaterials_trigger)
        self.reloadMtls_btn.clicked.connect(self.reloadMaterials_trigger)
        self.addMaterial_btn.clicked.connect(self.addMaterial_trigger)
        self.checkAsset_btn.clicked.connect(self.checkAst_trigger)
        self.loadAsset_btn.clicked.connect(self.loadAst_trigger)
        self.hdri_btn.clicked.connect(self.loadHDRIs_trigger)

        
    # =========================
    # HELPERS
    # =========================
    def _separator(self):
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        return sep



    # =========================
    # TRIGGERS
    # =========================

    def loadIntoSops_trigger(self):
        scaleDiff_value = self.scaleDif_check.isChecked()
        loadIntoSops(scaleDiff_value)

    def sendToLops_trigger(self):
        sendToLops()
    
    def reloadSOPs_trigger(self):
        scaleDiff_value = self.scaleDif_check.isChecked()
        checkedLOPsValue = self.reloadLOPs_check.isChecked()
        reloadSops(scaleDiff_value, checkedLOPsValue)

    def reloadLOPs_trigger(self):
        reloadLops()

    def createMaterials_trigger(self):
        numberOfMaterials = self.variant_spin.value()
        createMaterials(numberOfMaterials)

    def reloadMaterials_trigger(self):
        numberOfMaterials = self.variant_spin.value()
        reloadMaterials(numberOfMaterials)
    
    def addMaterial_trigger(self):
        addMaterial()

    def checkAst_trigger(self):
        checkAsset()

    def loadAst_trigger(self):
        laodAst()

    def loadHDRIs_trigger(self):
        loadHDRIs()

def show_UI():
    if hasattr(hou.session, "usd_loader_ui"):
        try:
            if hou.session.usd_loader_ui.isVisible():
                hou.session.usd_loader_ui.raise_()
                hou.session.usd_loader_ui.activateWindow()
                return
            else:
                hou.session.usd_loader_ui.deleteLater()
        except:
            pass

    hou.session.usd_loader_ui = USDLoader(parent=hou.ui.mainQtWindow())
    hou.session.usd_loader_ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    hou.session.usd_loader_ui.show()

show_UI()
checkAssetFile()
checkAssetInfo()

