"""Non-baseline contenders.

`python -m` on each module attempts the one Stage 0 stud.
`--stub` writes a null scorecard and does not segment.
"""

from __future__ import annotations

from openwall_stud.contenders.cloudcompare_ransac import CLOUDCOMPARE
from openwall_stud.contenders.open3d_ml_s3dis import OPEN3D_ML
from openwall_stud.contenders.pcl_region_grow import PCL
from openwall_stud.contenders.pointcept_ptv3 import POINTCEPT

STUBS = (PCL, CLOUDCOMPARE, POINTCEPT, OPEN3D_ML)
