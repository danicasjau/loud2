
from usdt import Usd, UsdUtils
import os
import sys

def getUsdScene():
    USD_PATH_STAGE = r"P:\VFX_Project_30\2LOUD\Spotlight\03_Production\Assets\ASSETS\SOUNDSTAGE\PROPS\ball\Export\asset\master\ball_asset_master.usda"

    if not os.path.exists(USD_PATH_STAGE):
        print("ERROR: USD Scene file path not found:", USD_PATH_STAGE)
        sys.exit(1)

    with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
        stage = Usd.Stage.Open(USD_PATH_STAGE)
        
    return stage
