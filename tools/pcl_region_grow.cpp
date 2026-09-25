// Call pcl::RegionGrowing on one XYZ cloud and write a cluster id per point.
//
// This is a small BSD-library driver. It does not merge clusters into a stud
// and it does not force the axis to Z. Cuboid assembly stays in Python.
//
// Usage:
//   pcl_region_grow in.xyz out.labels smoothness_deg curvature k min_cluster

#include <pcl/features/normal_3d.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/search/kdtree.h>
#include <pcl/segmentation/region_growing.h>

#include <cmath>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

bool load_xyz(const std::string& path, pcl::PointCloud<pcl::PointXYZ>::Ptr cloud) {
  std::ifstream in(path);
  if (!in) {
    return false;
  }
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty() || line[0] == '#') {
      continue;
    }
    std::istringstream row(line);
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    if (!(row >> x >> y >> z)) {
      continue;
    }
    cloud->push_back(pcl::PointXYZ(static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)));
  }
  cloud->width = static_cast<std::uint32_t>(cloud->size());
  cloud->height = 1;
  cloud->is_dense = true;
  return !cloud->empty();
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 7) {
    std::cerr << "usage: pcl_region_grow in.xyz out.labels smoothness_deg curvature k min_cluster\n";
    return 2;
  }
  const std::string in_path = argv[1];
  const std::string out_path = argv[2];
  const float smoothness_deg = std::stof(argv[3]);
  const float curvature = std::stof(argv[4]);
  const int k = std::stoi(argv[5]);
  const int min_cluster = std::stoi(argv[6]);
  if (k < 2 || min_cluster < 1) {
    std::cerr << "k and min_cluster must be positive\n";
    return 2;
  }

  pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
  if (!load_xyz(in_path, cloud)) {
    std::cerr << "failed to read xyz: " << in_path << "\n";
    return 1;
  }

  pcl::search::KdTree<pcl::PointXYZ>::Ptr tree(new pcl::search::KdTree<pcl::PointXYZ>);
  tree->setInputCloud(cloud);

  pcl::NormalEstimation<pcl::PointXYZ, pcl::Normal> normals_est;
  pcl::PointCloud<pcl::Normal>::Ptr normals(new pcl::PointCloud<pcl::Normal>);
  normals_est.setInputCloud(cloud);
  normals_est.setSearchMethod(tree);
  normals_est.setKSearch(k);
  // The synthetic stud is centered on the origin, which is inside the section.
  // Pointing normals at the origin keeps each face consistently oriented.
  normals_est.setViewPoint(0.0f, 0.0f, 0.0f);
  normals_est.compute(*normals);

  pcl::RegionGrowing<pcl::PointXYZ, pcl::Normal> grow;
  grow.setMinClusterSize(static_cast<pcl::uindex_t>(min_cluster));
  grow.setMaxClusterSize(static_cast<pcl::uindex_t>(cloud->size()));
  grow.setSearchMethod(tree);
  grow.setNumberOfNeighbours(static_cast<unsigned int>(k));
  grow.setInputCloud(cloud);
  grow.setInputNormals(normals);
  grow.setSmoothnessThreshold(smoothness_deg * static_cast<float>(M_PI / 180.0));
  grow.setCurvatureThreshold(curvature);
  grow.setSmoothModeFlag(true);
  grow.setCurvatureTestFlag(true);
  grow.setResidualTestFlag(false);

  std::vector<pcl::PointIndices> clusters;
  grow.extract(clusters);

  std::vector<int> labels(cloud->size(), -1);
  for (std::size_t cluster_id = 0; cluster_id < clusters.size(); ++cluster_id) {
    for (int index : clusters[cluster_id].indices) {
      if (index >= 0 && static_cast<std::size_t>(index) < labels.size()) {
        labels[static_cast<std::size_t>(index)] = static_cast<int>(cluster_id);
      }
    }
  }

  std::ofstream out(out_path);
  if (!out) {
    std::cerr << "failed to write labels: " << out_path << "\n";
    return 1;
  }
  for (int label : labels) {
    out << label << '\n';
  }

  std::cerr << "pcl_region_growing"
            << " points=" << cloud->size()
            << " clusters=" << clusters.size()
            << " smoothness_deg=" << smoothness_deg
            << " curvature=" << curvature
            << " k=" << k
            << " min_cluster=" << min_cluster
            << "\n";
  return 0;
}
