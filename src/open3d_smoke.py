"""Import Open3D and print the installed version.

Does not download or open a point cloud.
"""

import open3d as o3d


def main() -> None:
    print(f"open3d {o3d.__version__}")


if __name__ == "__main__":
    main()
