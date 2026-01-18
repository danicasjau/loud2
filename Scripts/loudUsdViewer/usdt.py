import sys

sys.path.append(r"P:\VFX_Project_30\2LOUD\Spotlight\00_Pipeline\Plugins\Custom\laud2\Scripts\loudUsdViewer")
sys.path.append("C:\Program Files\Prism2\PythonLibs\Python3\PySide")
sys.path.append(r"C:\Program Files\Side Effects Software\Houdini 21.0.440\bin")

import os 


USD_ROOT = r"D:\2loudAddons\USD\USD_install"

# Ensure Python bindings are found
usd_python = os.path.join(USD_ROOT, "lib", "python")
if usd_python not in sys.path:
    sys.path.insert(0, usd_python)

# Ensure DLLs and plugins are found
usd_bin = os.path.join(USD_ROOT, "bin")
usd_lib = os.path.join(USD_ROOT, "lib")
os.environ["PATH"] = usd_bin + ";" + usd_lib + ";" + os.environ.get("PATH", "")

os.environ["PXR_PLUGINPATH_NAME"] = os.path.join(USD_ROOT, "plugin")

from pxr import Usd, UsdSkel, Sdf, Gf, Vt, UsdGeom, UsdUtils, UsdImagingGL, Ar, UsdAppUtils, UsdLux, UsdShade
from pxr.Usd import TimeCode
from pxr.Usdviewq.stageView import StageView
from pxr.Usdviewq import appController, rootDataModel




print("USD version:", Usd.GetVersion())