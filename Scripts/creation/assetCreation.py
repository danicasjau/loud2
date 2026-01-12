import os

CUSTOM_ASSET_BASIC_USD = """


"""


class createAsset():
    def __init__(self):
        self.id = None
        self.createUsd = True
        self.assetType = "static"
        self.usdProductsReferencePath = r""
        self.assetProductPath = ""

        self.metadata = None

        self.primFuncts = prismFuncts()

    def setMetadata(self):
        if self.assetType == "static":
            self.metadata = {

                
            }

    def set(self, assetType="static", createUsd_=True, id=None, description=None, preview=None, metadata=None):
        self.id = id
        self.createUsd = createUsd_
        self.assetType = assetType


    def create(self):
        if self.assetType == "static":
            self.primFuncts.createAssetEnti("asset")
        elif self.assetType == "dynamic":
            pass
        elif self.assetType == "character":
            pass
        elif self.assetType == "enviorment":
            pass


    def setPaths(self, productPath):
        self.assetProductPath = productPath

    def createUsdProducts(self):
        pass
        

class prismFuncts():
    def __init__(self):
        self.core = None

    def createAssetEnti(self, entityType, description, preview, ):

            entityName = assetPath
            path = self.core.assetPath
            data = {
                "type": "assetFolder" if entityType == "folder" else entityType,
                "asset_path": entityName,
                "asset": os.path.basename(entityName)
            }
            description = None
            preview = None
            metaData = None
            if entityType == "asset":
                descr = self.newItem.getDescription()
                if descr:
                    description = descr

                thumb = self.newItem.getThumbnail()
                if thumb:
                    preview = thumb

                metaData = self.newItem.w_meta.getMetaData()

            result = self.createAsset(data, description=description, preview=preview, metaData=metaData, dialog=self.newItem)

            assetPath = os.path.join(path, entityName)

            if entityType == "asset":
                if self.newItem.chb_taskPreset.isChecked():
                    self.core.entities.createTasksFromPreset(data, self.newItem.cb_taskPreset.currentData())

            data["paths"].append(assetPath)
            self.entityCreated.emit(data)

    def createAssetFolder(self, entity, dialog=None):
        fullAssetPath = os.path.join(self.core.assetPath, entity["asset_path"])

        existed = os.path.exists(fullAssetPath)
        if not os.path.exists(fullAssetPath):
            os.makedirs(fullAssetPath)

        if not existed:
            self.core.callback(
                name="onAssetFolderCreated",
                args=[self, entity, dialog],
            )

        result = {
            "entity": entity,
            "existed": existed,
        }

        return result

    def createAsset(self, entity, description=None, preview=None, metaData=None, dialog=None):
        fullAssetPath = os.path.join(self.core.assetPath, entity["asset_path"])

        assetName = self.getAssetNameFromPath(fullAssetPath)
        if not self.isValidAssetName(assetName):
            return {"error": "Invalid assetname."}

        existed = os.path.exists(fullAssetPath)
        if existed and self.getTypeFromAssetPath(fullAssetPath) == "folder":
            return {"error": "A folder with this name exists already."}

        for f in self.entityFolders["asset"]:
            aFolder = os.path.join(fullAssetPath, f)
            if not os.path.exists(aFolder):
                os.makedirs(aFolder)

        assetDep = self.core.projects.getResolvedProjectStructurePath(
            "departments", context=entity
        )
        assetProducts = self.core.projects.getResolvedProjectStructurePath(
            "products", context=entity
        )
        asset3dRenders = self.core.projects.getResolvedProjectStructurePath(
            "3drenders", context=entity
        )
        asset2dRenders = self.core.projects.getResolvedProjectStructurePath(
            "2drenders", context=entity
        )
        assetPlayblasts = self.core.projects.getResolvedProjectStructurePath(
            "playblasts", context=entity
        )
        assetFolders = [
            os.path.dirname(assetDep),
            os.path.dirname(assetProducts),
            os.path.dirname(asset3dRenders),
            os.path.dirname(asset2dRenders),
            os.path.dirname(assetPlayblasts),
        ]

        for assetFolder in assetFolders:
            if not os.path.exists(assetFolder):
                try:
                    os.makedirs(assetFolder)
                except Exception as e:
                    return {"error": "Failed to create folder:\n\n%s\n\nError: %s" % (assetFolder, str(e))}

        if description:
            self.core.entities.setAssetDescription(assetName, description)

        if preview:
            self.core.entities.setEntityPreview(entity, preview)

        if metaData:
            self.core.entities.setMetaData(entity, metaData)

        if not existed:
            self.core.callback(
                name="onAssetCreated",
                args=[self, entity, dialog],
            )

        result = {
            "entity": entity,
            "existed": existed,
        }

        return result