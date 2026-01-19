
from usdt import Usd, UsdUtils
import os
import sys

def getUsdScene(path=None):
    if not path:
        path = r"P:\VFX_Project_30\2LOUD\Spotlight\03_Production\Assets\ASSETS\EXT\BUILDINGASSETS\fenceBuilding\Export\asset\master\fenceBuilding_asset_master.usda"

    if not os.path.exists(path):
        print("ERROR: USD Scene file path not found:", path)
        sys.exit(1)

    with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
        stage = Usd.Stage.Open(path)
        
    return stage
