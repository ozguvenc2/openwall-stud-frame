"""Non-baseline contenders.

Only the Open3D baseline runs in this environment. These modules record a
stub scorecard and document how to install the real stack later.
"""

from __future__ import annotations

from openwall_stud.contenders.cloudcompare_ransac import CLOUDCOMPARE
from openwall_stud.contenders.open3d_ml_s3dis import OPEN3D_ML
from openwall_stud.contenders.pcl_region_grow import PCL
from openwall_stud.contenders.pointcept_ptv3 import POINTCEPT

STUBS = (PCL, CLOUDCOMPARE, POINTCEPT, OPEN3D_ML)
