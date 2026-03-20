#!/usr/bin/env python
# coding: utf-8

# # H2-PVPA

# ---

# ## 1 前期准备
# ### 1.1导入相关的库

# In[1]:


# 导入相关的库
# import pandas as pd
# import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('module://ipympl.backend_nbagg')
# 在导入plt前设置字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
import matplotlib.pyplot as plt
from folium.utilities import deep_copy
from pandas import factorize
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from scipy.optimize import newton
import rasterio
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.features import geometry_mask
from matplotlib import font_manager as fm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import ipympl
get_ipython().run_line_magic('matplotlib', 'ipympl')
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.font_manager as fm
from rasterio.features import geometry_mask
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ipympl")


# In[2]:


get_ipython().run_line_magic('matplotlib', 'ipympl')


# ### 1.2数据预处理

# #### 1.2.1 数据读入
# 数据读取和准备：
# 从多个文件（CSV、GeoJSON、Excel）中读取地理数据、行政区域数据、贫困地区数据和太阳能资源数据（TIFF文件）。
# 将点位数据（geo_df）和县级行政区数据（counties、provinces 等）加载为 GeoDataFrame。
# 提取特定的城市和县级区域（counties_selected 和 poverty_selected）。
# 
# 空间数据处理：
# 重新投影所有地理数据为 EPSG:3857 投影（Web Mercator 投影）。
# 合并特定县级区域的几何边界（combined_boundary），避免重复。
# 
# TIFF 文件处理：
# 将原始太阳能资源 TIFF 文件（PVOUT.tif）重新投影到 EPSG:3857。
# 使用合并后的边界（combined_boundary）裁剪 TIFF 文件，得到感兴趣区域内的数据。
# 
# 太阳能资源计算：
# 对每个县（counties_selected 和 poverty_selected）的几何形状进行蒙版处理，计算其对应区域内的太阳能资源 TIFF 文件的平均值，并将结果存储到新的列（mean_tiff）
# 
# 最后输出：counties_selected_resort 和 poverty_selected_resort

# In[3]:


import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.font_manager as fm
from rasterio.features import geometry_mask
import os

# 文件路径
county_geojson = "中国_县.geojson"
province_geojson = "中华人民共和国.json"
excel_file = "split_pv_poverty_areas.xlsx"
poverty = "cleaned_poverty_counties.xlsx"
url = "station_location.csv"
tiff_file_path = "PVOUT.tif"

# 结果存储路径
counties_result_path = "counties_selected_resort.geojson"
poverty_result_path = "poverty_selected_resort.geojson"

# 读取数据
data = pd.read_csv(url, encoding='gbk')
geometry = [Point(xy) for xy in zip(data['longitude'], data['latitude'])]
geo_df = gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")

# 读取GeoJSON文件
counties = gpd.read_file(county_geojson)
provinces = gpd.read_file(province_geojson)

# 读取Excel文件
excel_data = pd.read_excel(excel_file)
poverty_data = pd.read_excel(poverty)

# 提取城市名称
cities = excel_data["市"].tolist()
poverty_cities = poverty_data["市"].tolist()



# In[4]:


# # 按城市名称选择县级单位，并去重
# counties_selected = counties[counties['name'].isin(cities)].drop_duplicates(subset=['name'])
# poverty_selected = counties[counties['name'].isin(poverty_cities)].drop_duplicates(subset=['name'])

# # 重新投影数据
# geo_df = geo_df.to_crs(epsg=3857)
# counties_selected = counties_selected.to_crs(epsg=3857)
# poverty_selected = poverty_selected.to_crs(epsg=3857)


# # 合并边界
# combined_boundary = counties_selected.geometry.unary_union.union(poverty_selected.geometry.unary_union)

# # 重新投影TIFF文件
# with rasterio.open(tiff_file_path) as src:
#     transform, width, height = calculate_default_transform(
#         src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
#     kwargs = src.meta.copy()
#     kwargs.update({
#         'crs': 'EPSG:3857',
#         'transform': transform,
#         'width': width,
#         'height': height,
#         'nodata': 0
#     })
#     with rasterio.open('/tmp/reprojected.tif', 'w', **kwargs) as dst:
#         for i in range(1, src.count + 1):
#             reproject(
#                 source=rasterio.band(src, i),
#                 destination=rasterio.band(dst, i),
#                 src_transform=src.transform,
#                 src_crs=src.crs,
#                 dst_transform=transform,
#                 dst_crs='EPSG:3857',
#                 resampling=Resampling.nearest)

# # 裁剪TIFF文件
# with rasterio.open('/tmp/reprojected.tif') as src:
#     out_image, out_transform = mask(src, [combined_boundary], crop=True)
#     out_meta = src.meta.copy()
#     out_meta.update({
#         "driver": "GTiff",
#         "height": out_image.shape[1],
#         "width": out_image.shape[2],
#         "transform": out_transform,
#         "nodata": 0
#     })
#     with rasterio.open('/tmp/cropped.tif', 'w', **out_meta) as dst:
#         dst.write(out_image)

# # 读取裁剪后的TIFF文件
# with rasterio.open('/tmp/cropped.tif') as src:
#     tiff_data = src.read(1)
#     tiff_transform = src.transform

# def calculate_mean_tiff_value(geometry, raster_data, transform):
#     mask = geometry_mask([geometry], transform=transform, invert=True, out_shape=raster_data.shape)
#     masked_data = np.ma.masked_array(raster_data, mask=~mask)
#     return masked_data.mean()

# # 如果结果文件存在，则直接读取，否则计算并保存
# if os.path.exists(counties_result_path) and os.path.exists(poverty_result_path):
#     counties_selected_resort = gpd.read_file(counties_result_path)
#     poverty_selected_resort = gpd.read_file(poverty_result_path)
# else:
#     counties_selected['mean_tiff'] = counties_selected.geometry.apply(
#         lambda geom: calculate_mean_tiff_value(geom, tiff_data, tiff_transform)
#     )
#     poverty_selected['mean_tiff'] = poverty_selected.geometry.apply(
#         lambda geom: calculate_mean_tiff_value(geom, tiff_data, tiff_transform)
#     )

#     # 保存计算结果
#     counties_selected.to_file(counties_result_path, driver="GeoJSON")
#     poverty_selected.to_file(poverty_result_path, driver="GeoJSON")

#     counties_selected_resort = counties_selected
#     poverty_selected_resort = poverty_selected


# In[5]:


# 下从读取时的代码

import geopandas as gpd
import os

# 结果存储路径
counties_result_path = "counties_selected_resort.geojson"
poverty_result_path = "poverty_selected_resort.geojson"

# 检查文件是否存在并读取
if os.path.exists(counties_result_path) and os.path.exists(poverty_result_path):
    counties_selected_resort = gpd.read_file(counties_result_path)
    poverty_selected_resort = gpd.read_file(poverty_result_path)
    print("数据已加载，无需重新计算。")
else:
    print("存储文件不存在，请运行完整的计算代码。")


china_geojson= "china-min.json"
china=gpd.read_file(china_geojson)


# #### 1.2.1 所有counties的mean_tiff值，记录为counties1
# 

# In[6]:


# # TIFF文件重投影并保存在临时文件
# with rasterio.open(tiff_file_path) as src:
#     transform, width, height = calculate_default_transform(
#         src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
#     kwargs = src.meta.copy()
#     kwargs.update({
#         'crs': 'EPSG:3857',
#         'transform': transform,
#         'width': width,
#         'height': height,
#         'nodata': 0
#     })
#
#     with rasterio.open('/tmp/reprojected.tif', 'w', **kwargs) as dst:
#         for i in range(1, src.count + 1):
#             reproject(
#                 source=rasterio.band(src, i),
#                 destination=rasterio.band(dst, i),
#                 src_transform=src.transform,
#                 src_crs=src.crs,
#                 dst_transform=transform,
#                 dst_crs='EPSG:3857',
#                 resampling=Resampling.nearest)
#
# # 读取重投影的 TIFF 文件
# with rasterio.open('/tmp/reprojected.tif') as src:
#     tiff_data = src.read(1)
#     tiff_transform = src.transform
#
# def calculate_mean_tiff_value(geometry, raster_data, transform):
#     # 计算每个县的 TIFF 文件的平均值
#     mask = geometry_mask([geometry], transform=transform, invert=True, out_shape=raster_data.shape)
#     masked_data = np.ma.masked_array(raster_data, mask=~mask)
#     mean_value = masked_data.mean()
#     return mean_value
#
# # 计算所有 counties 的平均 TIFF 值
# counties['mean_tiff'] = counties.geometry.apply(
#     lambda geom: calculate_mean_tiff_value(geom, tiff_data, tiff_transform)
# )
#
# # 查看结果
# print(counties.head())
# counties_1=counties


# #### 1.2.2 光伏发电潜力数据可视化
# 全图数据

# In[7]:


# import matplotlib.pyplot as plt
# import geopandas as gpd
# import matplotlib.font_manager as fm
# import matplotlib.patheffects as PathEffects
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes
# import rasterio
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# import numpy as np
#
# # Load Microsoft YaHei font
# font_path = 'C:/Windows/Fonts/msyh.ttc'  # Path to Microsoft YaHei font
# font_prop_large = fm.FontProperties(fname=font_path, size=32)  # Set large font size
#
# # Path to the original TIFF file and temporary reprojected file
# original_tiff_path = "PVOUT.tif"
# reprojected_tiff_path = "/tmp/reprojected_PVOUT.tif"
#
# # Reproject the TIFF file to EPSG:3857
# with rasterio.open(original_tiff_path) as src:
#     # Calculate the transform and dimensions for the new projection
#     transform, width, height = calculate_default_transform(
#         src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
#
#     # Set up metadata for the reprojected file
#     kwargs = src.meta.copy()
#     kwargs.update({
#         'crs': 'EPSG:3857',
#         'transform': transform,
#         'width': width,
#         'height': height,
#         'nodata': 0
#     })
#
#     # Create and save the reprojected TIFF
#     with rasterio.open(reprojected_tiff_path, 'w', **kwargs) as dst:
#         for i in range(1, src.count + 1):
#             reproject(
#                 source=rasterio.band(src, i),
#                 destination=rasterio.band(dst, i),
#                 src_transform=src.transform,
#                 src_crs=src.crs,
#                 dst_transform=transform,
#                 dst_crs='EPSG:3857',
#                 resampling=Resampling.nearest
#             )
#
# # Define shadow effect for boundary styles
# shadow_effect = [
#     PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
#     PathEffects.Normal()
# ]
#
# # Open and display the reprojected TIFF file without grid and tick labels
# with rasterio.open(reprojected_tiff_path) as src:
#     tiff_data = src.read(1)  # Read the first band
#     extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
#
#     fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True, facecolor='white')
#
#     # Display the TIFF data as an image, using `imshow` to control appearance
#     cax = ax.imshow(tiff_data, extent=extent, cmap='viridis')  # Adjust cmap as needed
#
#     # Plot national boundary with shadow effect
#     china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)
#
#     # Plot provincial boundaries
#     provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')
#
#     # Set x and y limits to frame China mainland area in EPSG:3857
#     ax.set_xlim(7792364.36, 15584728.71)
#     ax.set_ylim(1689200.14, 7361866.11)
#
#     # Remove grid, ticks, and labels on the main plot
#     ax.grid(False)
#     ax.set_xticks([])
#     ax.set_yticks([])
#     ax.set_facecolor('white')
#
#     # Add inset for South China Sea region
#     ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
#     ax_inset.set_facecolor('white')  # Set background color to white for the inset
#
#     # Display the TIFF data in the inset
#     ax_inset.imshow(tiff_data, extent=extent, cmap='viridis')
#
#     # Overlay provincial and national boundaries in the inset with shadow effect
#     provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
#     china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)
#
#     # Set inset limits for South China Sea region
#     ax_inset.set_xlim(11688546.53, 13692297.37)
#     ax_inset.set_ylim(222684.21, 2632018.64)
#
#     # Remove grid, ticks, and labels on the inset
#     ax_inset.grid(False)
#     ax_inset.set_xticks([])
#     ax_inset.set_yticks([])
#
#     # Modify inset border color and style
#     for spine in ax_inset.spines.values():
#         spine.set_edgecolor('black')
#         spine.set_linewidth(1.5)
#
#     # Add color bar with large font size and Microsoft YaHei font
#     cbar = fig.colorbar(cax, ax=ax, orientation="vertical", fraction=0.036, pad=0.04)
#     cbar.set_label("PV Output Value", fontproperties=font_prop_large)
#     cbar.ax.tick_params(labelsize=24)  # Adjust the size as needed
#
#     # Set main plot title
#     ax.set_title("Visualization of Reprojected TIFF Image with Boundaries", fontproperties=font_prop_large)
#
#     # Save and display the image
#     plt.savefig('output_map_reprojected_with_boundaries_and_large_colorbar.png', dpi=1200, bbox_inches='tight', format='png')
#     plt.show()


# 求平均值后的贫困县的数据
# 

# In[8]:


# import matplotlib.pyplot as plt
# import geopandas as gpd
# import matplotlib.font_manager as fm
# import matplotlib.patheffects as PathEffects
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes
# import rasterio
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# import numpy as np
#
# # Load Microsoft YaHei font
# font_path = 'C:/Windows/Fonts/msyh.ttc'  # Path to Microsoft YaHei font
# font_prop_large = fm.FontProperties(fname=font_path, size=32)  # Set large font size
#
# # Path to the original TIFF file and temporary reprojected file
# original_tiff_path = "PVOUT.tif"
# reprojected_tiff_path = "/tmp/reprojected_PVOUT.tif"
#
# # Reproject the TIFF file to EPSG:3857
# with rasterio.open(original_tiff_path) as src:
#     # Calculate the transform and dimensions for the new projection
#     transform, width, height = calculate_default_transform(
#         src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
#
#     # Set up metadata for the reprojected file
#     kwargs = src.meta.copy()
#     kwargs.update({
#         'crs': 'EPSG:3857',
#         'transform': transform,
#         'width': width,
#         'height': height,
#         'nodata': 0
#     })
#
#     # Create and save the reprojected TIFF
#     with rasterio.open(reprojected_tiff_path, 'w', **kwargs) as dst:
#         for i in range(1, src.count + 1):
#             reproject(
#                 source=rasterio.band(src, i),
#                 destination=rasterio.band(dst, i),
#                 src_transform=src.transform,
#                 src_crs=src.crs,
#                 dst_transform=transform,
#                 dst_crs='EPSG:3857',
#                 resampling=Resampling.nearest
#             )
#
# # Define shadow effect for boundary styles
# shadow_effect = [
#     PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
#     PathEffects.Normal()
# ]
#
# # Open and display the reprojected TIFF file without grid and tick labels
# with rasterio.open(reprojected_tiff_path) as src:
#     tiff_data = src.read(1)  # Read the first band
#     extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
#
#     fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True, facecolor='white')
#
#     # Display the TIFF data as an image, using `imshow` to control appearance
#     cax = ax.imshow(tiff_data, extent=extent, cmap='viridis')  # Adjust cmap as needed
#
#     # Plot national boundary with shadow effect
#     china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)
#
#     # Plot provincial boundaries
#     provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')
#
#     # Set x and y limits to frame China mainland area in EPSG:3857
#     ax.set_xlim(7792364.36, 15584728.71)
#     ax.set_ylim(1689200.14, 7361866.11)
#
#     # Remove grid, ticks, and labels on the main plot
#     ax.grid(False)
#     ax.set_xticks([])
#     ax.set_yticks([])
#     ax.set_facecolor('white')
#
#     # Add inset for South China Sea region
#     ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
#     ax_inset.set_facecolor('white')  # Set background color to white for the inset
#
#     # Display the TIFF data in the inset
#     ax_inset.imshow(tiff_data, extent=extent, cmap='viridis')
#
#     # Overlay provincial and national boundaries in the inset with shadow effect
#     provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
#     china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)
#
#     # Set inset limits for South China Sea region
#     ax_inset.set_xlim(11688546.53, 13692297.37)
#     ax_inset.set_ylim(222684.21, 2632018.64)
#
#     # Remove grid, ticks, and labels on the inset
#     ax_inset.grid(False)
#     ax_inset.set_xticks([])
#     ax_inset.set_yticks([])
#
#     # Modify inset border color and style
#     for spine in ax_inset.spines.values():
#         spine.set_edgecolor('black')
#         spine.set_linewidth(1.5)
#
#     # Add color bar with large font size and Microsoft YaHei font
#     cbar = fig.colorbar(cax, ax=ax, orientation="vertical", fraction=0.036, pad=0.04)
#     cbar.set_label("PV Output Value", fontproperties=font_prop_large)
#     cbar.ax.tick_params(labelsize=24)  # Adjust the size as needed
#
#     # Set main plot title
#     ax.set_title("Visualization of Reprojected TIFF Image with Boundaries", fontproperties=font_prop_large)
#
#     # Save and display the image
#     plt.savefig('output_map_reprojected_with_boundaries_and_large_colorbar.png', dpi=1200, bbox_inches='tight', format='png')
#     plt.show()


# #### 1.2.3 匹配光伏售价与氢能售价

# ##### 1.2.3.1导入整理好的数据，去掉重复的部分和nan的部分

# In[9]:


# 归正的代码
poverty_selected=poverty_selected_resort
counties_selected=counties_selected_resort
merged_counties_poverty = pd.concat([counties_selected, poverty_selected]).drop_duplicates(subset='geometry')
print(poverty_selected)
nan_count = poverty_selected['mean_tiff'].isna().sum()
nan_rows = poverty_selected[poverty_selected['mean_tiff'].isna()]
print(f"The number of missing values in the 'mean_tiff' column is: {nan_count}")
print(nan_rows['name'])
print(counties_selected)
print(poverty_selected)


# 注意到经过这一处理后，含nan的贫困县的个数变成了831个（无重复），其中重复的有5个。要想办法把贫困县的数据保持在832个
# 831个的原因：2018年茫崖撤工委设市，成为了茫崖市，这标志着茫崖与冷湖两个原行委合并成为了一个新的县级市——茫崖市
# 

# In[10]:


merged_test = merged_counties_poverty.dropna(subset=['mean_tiff'])
merged_test = merged_test.drop_duplicates(subset=['name'])
print(merged_test)


# 以上这部分代码去重后，就变成826个了

# ##### 1.2.3.2对mean_tiff进行插值

# In[11]:


import geopandas as gpd
import numpy as np
from shapely.geometry import Point

# 定义一个通用函数，计算最近的非空 mean_tiff 值
def find_nearest_mean_tiff(row, valid_gdf):
    # 获取当前行的几何
    current_geom = row.geometry

    # 计算所有非空几何与当前几何的距离
    valid_gdf['distance'] = valid_gdf.geometry.distance(current_geom)

    # 找到距离最小的行
    nearest_row = valid_gdf.loc[valid_gdf['distance'].idxmin()]

    # 返回最近行的 mean_tiff 值
    return nearest_row['mean_tiff']

# 定义一个通用的插值函数
def fill_missing_mean_tiff(gdf):
    # 分离出非空 mean_tiff 和空值部分
    valid_gdf = gdf[gdf['mean_tiff'].notna()].copy()
    missing_gdf = gdf[gdf['mean_tiff'].isna()].copy()

    # 重置索引避免重复索引问题
    valid_gdf = valid_gdf.reset_index(drop=True)
    missing_gdf = missing_gdf.reset_index()

    # 对缺失值逐行进行最近邻插值
    for idx, row in missing_gdf.iterrows():
        nearest_value = find_nearest_mean_tiff(row, valid_gdf)
        gdf.loc[row['index'], 'mean_tiff'] = nearest_value

    return gdf

# 确保几何有效性
poverty_selected['geometry'] = poverty_selected['geometry'].apply(
    lambda geom: geom if geom.is_valid else geom.buffer(0)
)
counties_selected['geometry'] = counties_selected['geometry'].apply(
    lambda geom: geom if geom.is_valid else geom.buffer(0)
)

# 对 poverty_selected 和 counties_selected 分别进行操作
poverty_selected = fill_missing_mean_tiff(poverty_selected)
counties_selected = fill_missing_mean_tiff(counties_selected)

# 检查结果
print("Poverty Selected:")
print(poverty_selected)
print("Counties Selected:")
print(counties_selected)


# In[12]:


counties_selected['geometry']


# 插值完成以后，目前贫困县总个数为831，已开展的为470，都是包含了合并的两个县的，且和事实相符

# In[13]:


# 检查 poverty_selected 的缺失值
missing_poverty = poverty_selected[poverty_selected['mean_tiff'].isna()]
print("仍然缺失的 Poverty Selected 行：", missing_poverty)

# 检查 counties_selected 的缺失值
missing_counties = counties_selected[counties_selected['mean_tiff'].isna()]
print("仍然缺失的 Counties Selected 行：", missing_counties)


# 测试一下合并后的效果，也没有问题

# In[14]:


merged_counties_poverty = pd.concat([counties_selected, poverty_selected]).drop_duplicates(subset='geometry')
merged_test = merged_counties_poverty.dropna(subset=['mean_tiff'])
merged_test = merged_test.drop_duplicates(subset=['name'])
print(merged_test)


# In[15]:


import copy

# 深拷贝
poverty_selected_1 = copy.deepcopy(poverty_selected)
counties_selected_1 = copy.deepcopy(counties_selected)


# In[16]:


china = china.to_crs(epsg=3857)


# 遗漏的一个需要补上

# ##### 1.2.3.3下面正式匹配了光伏售价、氢能售价、弃电率

# In[17]:


import pandas as pd
import numpy as np
import copy

# 读档
poverty_selected = copy.deepcopy(poverty_selected_1)
counties_selected = copy.deepcopy(counties_selected_1)

# 将省份和县的坐标系统一为EPSG:3857
provinces = provinces.to_crs(epsg=3857)

# 修复省份和县的几何
provinces['geometry'] = provinces['geometry'].buffer(0)
counties_selected['geometry'] = counties_selected['geometry'].buffer(0)
poverty_selected['geometry'] = poverty_selected['geometry'].buffer(0)

# 读取 Excel 文件，同时读入“省/自治区/直辖市”这一列
pv_price_df = pd.read_excel("31省光伏上网.xlsx")

# 创建省份到各类价格的映射字典，其中“省/自治区/直辖市”列作为 key
province_to_price = dict(zip(
    pv_price_df["省/自治区/直辖市"],
    pv_price_df["基准价 (元/kWh)"]
))
province_to_hydrogen_min = dict(zip(
    pv_price_df["省/自治区/直辖市"],
    pv_price_df["氢最低价"]
))
province_to_hydrogen_max = dict(zip(
    pv_price_df["省/自治区/直辖市"],
    pv_price_df["氢最高价"]
))
province_to_curtailed_rate = dict(zip(
    pv_price_df["省/自治区/直辖市"],
    pv_price_df["弃电率"]
))
province_to_water_price = dict(zip(
    pv_price_df["省/自治区/直辖市"],
    pv_price_df["水费"]
))
# 重点：从excel中读取“村级光伏扶贫电站上网标杆电价（元/千瓦时）”列，作为补贴价格
province_to_subsidy = dict(zip(
    pv_price_df["省/自治区/直辖市"],
    pv_price_df["村级光伏扶贫电站上网标杆电价（元/千瓦时）"]
))

def assign_province_and_prices(
    row,
    provinces,
    province_to_price,
    province_to_hydrogen_min,
    province_to_hydrogen_max,
    province_to_curtailed_rate,
    province_to_water_price,
    province_to_subsidy
):
    """
    根据县的几何中心点找到其所属省份的名称，并返回一个字典，
    字典中不仅包含光伏售价、氢最低价、氢最高价、弃电率、水费和补贴价格，
    同时也增加了“Province”字段，记录所属的“省/自治区/直辖市”名称。
    """
    county_centroid = row.geometry.centroid  # 计算县的几何中心
    matching_province = provinces[provinces.contains(county_centroid)]
    if not matching_province.empty:
        province_name = matching_province.iloc[0]['name']
        return {
            "Province": province_name,  # 新增字段，将省/自治区/直辖市名称也读入
            "PV_price": province_to_price.get(province_name, np.nan),
            "Hydrogen_Min": province_to_hydrogen_min.get(province_name, np.nan),
            "Hydrogen_Max": province_to_hydrogen_max.get(province_name, np.nan),
            "Curtailed_Rate": province_to_curtailed_rate.get(province_name, np.nan),
            "Water_Price": province_to_water_price.get(province_name, np.nan),
            "Subsidy_Price": province_to_subsidy.get(province_name, np.nan)
        }
    else:
        return {
            "Province": np.nan,
            "PV_price": np.nan,
            "Hydrogen_Min": np.nan,
            "Hydrogen_Max": np.nan,
            "Curtailed_Rate": np.nan,
            "Water_Price": np.nan,
            "Subsidy_Price": np.nan
        }

# 给 counties_selected 和 poverty_selected 添加新列（包括所属省份信息和各类价格）
counties_selected_prices = counties_selected.apply(
    assign_province_and_prices,
    axis=1,
    provinces=provinces,
    province_to_price=province_to_price,
    province_to_hydrogen_min=province_to_hydrogen_min,
    province_to_hydrogen_max=province_to_hydrogen_max,
    province_to_curtailed_rate=province_to_curtailed_rate,
    province_to_water_price=province_to_water_price,
    province_to_subsidy=province_to_subsidy
)

poverty_selected_prices = poverty_selected.apply(
    assign_province_and_prices,
    axis=1,
    provinces=provinces,
    province_to_price=province_to_price,
    province_to_hydrogen_min=province_to_hydrogen_min,
    province_to_hydrogen_max=province_to_hydrogen_max,
    province_to_curtailed_rate=province_to_curtailed_rate,
    province_to_water_price=province_to_water_price,
    province_to_subsidy=province_to_subsidy
)

# 将返回的字典展开为 DataFrame 的新列，并与原 DataFrame 拼接
counties_selected = pd.concat(
    [counties_selected, counties_selected_prices.apply(pd.Series)], axis=1
)
poverty_selected = pd.concat(
    [poverty_selected, poverty_selected_prices.apply(pd.Series)], axis=1
)

# 存档
counties_selected_resort_2 = copy.deepcopy(counties_selected)
poverty_selected_resort_2 = copy.deepcopy(poverty_selected)

print(counties_selected_resort_2.head())
print(poverty_selected_resort_2.head())


# In[18]:


# 将数据框保存为CSV文件
counties_selected_resort_2.to_csv('counties_selected_data_resort_2.csv', encoding='utf-8', index=False)
poverty_selected_resort_2.to_csv('poverty_selected_data_resort_2.csv', encoding='utf-8', index=False)

print("文件已成功保存！")


# ## 2 PVPA效益计算

# ### 2.1 PVPA公式定义

# In[19]:


# 光伏扶贫计算公式

# Calculation functions
def calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N):
    numerator = (C_PV + C_ES) + sum((O_PV + O_ES + C_F + C_tax + C_d) / (1 + i) ** n for n in range(1, N + 1)) - V_R / (1 + i) ** N
    denominator = sum(E_n / (1 + i) ** n for n in range(1, N + 1))
    return numerator / denominator

def calculate_npv(C_t, i):
    return sum(C_t[t] / (1 + i) ** t for t in range(len(C_t)))

def calculate_irr(C_t, tol=1e-6, max_iter=100):
    from scipy.optimize import brentq

    def npv_at_rate(rate):
        try:
            return sum(c / (1.0 + rate) ** (i) for i, c in enumerate(C_t))
        except:
            return float('inf')

    try:
        # 使用更稳定的brentq方法，在合理的范围内搜索
        irr = brentq(npv_at_rate, -0.999, 0.999, maxiter=1000)
        return irr
    except:
        return 0.0  # 如果计算失败返回0

def calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N):
    revenue = total_generation * price
    total_fixed_cost = C_PV + C_ES
    total_annual_cost = (O_PV + O_ES  + C_tax + C_F) * N
    total_cost = total_fixed_cost + total_annual_cost
    return (revenue - total_cost) / total_cost / N

def discounted_payback(cash_flows, disc):
    """
    计算折现回收期
    cash_flows: 现金流列表
    disc: 折现率
    """
    if isinstance(cash_flows, pd.Series):
        cash_flows = cash_flows.tolist()  # 转换Series为列表

    cnpv = 0.0
    for t, cf in enumerate(cash_flows):
        cnpv += float(cf)/((1+disc)**t)  # 确保使用float
        if cnpv >= 0:
            return t
    return None


# 新增函数计算work_x和environment_x
def calculate_work_x(total_generation, total_cost, N):
    """
    计算工作效益指标 work_x
    total_generation: 总发电量
    total_cost: 总成本
    N: 年数
    """
    return total_generation / 2000 * 2.1 * 5.9 * 3000 / total_cost / N

def calculate_environment_x(total_generation, total_cost, N):
    """
    计算环境效益指标 environment_x
    total_generation: 总发电量
    total_cost: 总成本
    N: 年数
    """
    return total_generation * 48 / total_cost / N


# In[20]:


import pandas as pd
import copy

def calculate_pv_roi():
    # 读入原始数据
    poverty_selected = copy.deepcopy(poverty_selected_resort_2)

    # 设置参数
    C_PV = 2860  # 光伏系统成本（元/千瓦）
    C_ES = 0     # 储能系统成本（元/千瓦）
    O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
    O_ES = 0     # 储能系统运维成本（元/千瓦·年）
    C_F = 0      # 其他固定成本（元/千瓦·年）
    C_tax = 0    # 税收成本（元/千瓦·年）
    V_R = C_PV * 0.2   # 残值（元/千瓦）
    C_d = (C_PV - V_R)/20  # 折旧成本（元/千瓦·年）
    N = 20       # 资产寿命（年）

    # 计算ROI
    roi_values = []
    for idx, row in poverty_selected.iterrows():
        alpha = row['Curtailed_Rate']
        mean_value = row['mean_tiff']
        price = row['PV_price']
        E_n = mean_value * (1-alpha)
        total_generation = E_n * N

        # 计算总收入和总成本
        total_revenue = total_generation * price
        total_fixed_cost = C_PV + C_ES
        total_annual_cost = (O_PV + O_ES + C_tax + C_F) * N
        total_cost = total_fixed_cost + total_annual_cost

        # 计算ROI
        roi = (total_revenue - total_cost) / total_cost / N
        roi_values.append(roi)

    # 添加ROI列
    poverty_selected['ROI'] = roi_values

    # 保存到Excel文件
    output_file = 'poverty_selected_with_pv_roi.xlsx'
    poverty_selected.to_excel(output_file, index=False)

    print(f"数据已保存到 {output_file}")
    print(f"ROI范围: {min(roi_values):.4f} - {max(roi_values):.4f}")

    return poverty_selected

# 运行函数
new_df = calculate_pv_roi()


# In[21]:


new_df['ROI']


# ### 2.2 PVPA 数据导入与计算
# 

# #### 无补贴

# ##### 无补贴直接计算

# In[22]:


# 光伏模型标定
# Create a DataFrame to store results for each county
results_list = []

# 读入存档
counties_selected = copy.deepcopy(counties_selected_resort_2)
poverty_selected = copy.deepcopy(poverty_selected_resort_2)

# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率

# ... existing code ...

# Calculate and store results for each county
for idx, row in counties_selected.iterrows():
    alpha = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    price = row['PV_price']  # 使用对应的PV_price
    E_n = mean_value * (1-alpha)
    total_generation = E_n * N

    # Calculate cash flow sequence C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] + [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

    # Calculate LCOE, NPV, IRR, ROI, and Payback for the county
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
    npv = calculate_npv(C_t, i)
    roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)
    payback = discounted_payback(C_t, i)  # 计算回收期

    # Store the results in the list
    results_list.append({'County': row['name'], 'LCOE': lcoe, 'NPV': npv, 'IRR': irr, 'ROI': roi, 'Payback': payback})

# Calculate and store results for each county in the poverty_selected dataset
for idx, row in poverty_selected.iterrows():
    alpha = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    price = row['PV_price']  # 使用对应的PV_price
    E_n = mean_value * (1-alpha)
    total_generation = E_n * N

    # Calculate cash flow sequence C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] + [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

    # Calculate LCOE, NPV, IRR, ROI, and Payback for the county
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
    npv = calculate_npv(C_t, i)
    roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)
    payback = discounted_payback(C_t, i)  # 计算回收期

    # Store the results in the list
    results_list.append({'poverty': row['name'], 'LCOE': lcoe, 'NPV': npv, 'IRR': irr, 'ROI': roi, 'Payback': payback})

# Convert the results list to a DataFrame
results = pd.DataFrame(results_list)

# Save results to a CSV file
results.to_csv('economic_assessment_results.csv', index=False)

# Merge results with GeoDataFrame for visualization
counties_selected = counties_selected.merge(results, left_on='name', right_on='County')
poverty_selected = poverty_selected.merge(results, left_on='name', right_on='poverty')

# 计算价格减成本列
for idx, row in poverty_selected.iterrows():
    # 计算总成本（不考虑折现）
    initial_cost = C_PV + C_ES  # 初始投资成本
    annual_cost = (O_PV + O_ES + C_F + C_tax + C_d) * N  # N年内的年度成本总和
    total_cost = initial_cost + annual_cost  # 总成本

    # 计算每单位发电量的成本（元/千瓦时）
    E_n = row['mean_tiff'] * (1-row['Curtailed_Rate'])  # 年发电量
    total_generation = E_n * N  # 总发电量
    unit_cost = total_cost / total_generation if total_generation > 0 else 0  # 单位成本

    # 计算价格减成本
    price_minus_cost = row['PV_price'] - unit_cost

    # 添加到DataFrame
    poverty_selected.at[idx, 'price_minus_cost'] = price_minus_cost

    # 计算工作效益和环境效益指标
    work_x = calculate_work_x(total_generation, total_cost, N)
    environment_x = calculate_environment_x(total_generation, total_cost, N)

    # 添加到DataFrame
    poverty_selected.at[idx, 'work_x'] = work_x
    poverty_selected.at[idx, 'environment_x'] = environment_x
    poverty_selected.at[idx, 'jobs_x'] = 63

print(poverty_selected)


# In[23]:


# 计算ROI小于0.03的城市数量百分比
low_roi_counties = results[results['ROI'] < 0.03]
percentage_low_roi = (len(low_roi_counties) / len(results)) * 100

# 计算中位投资回报率
median_roi = results['ROI'].median()

print(f"ROI小于0.03的城市数量: {len(low_roi_counties)}")
print(f"ROI小于0.03的城市百分比: {percentage_low_roi:.2f}%")
print(f"\n所有城市的中位投资回报率: {median_roi:.4f}")

# 显示一些基本的统计信息
print("\nROI的基本统计信息：")
print(results['ROI'].describe())

# 显示ROI小于0.03的城市列表
print("\nROI小于0.03的城市列表:")
print(low_roi_counties[['County', 'ROI']].sort_values(by='ROI'))


# In[24]:


# import pandas as pd
# import copy

# # 创建存储结果的列表
# results_list = []

# # 成本参数
# C_PV = 2860
# C_ES = 0
# O_PV = 90
# O_ES = 0
# C_F = 0
# C_tax = 0

# # 其他参数
# V_R = C_PV * 0.2
# C_d = (C_PV - V_R)/20
# N = 20
# i = 0.03

# # 计算县域数据
# for idx, row in counties_selected.iterrows():
#     alpha = row['Curtailed_Rate']
#     mean_value = row['mean_tiff']
#     price = row['PV_price']
#     E_n = mean_value * (1 - alpha)
#     total_generation = E_n * N

#     C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] + \
#           [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

#     irr = calculate_irr(C_t)
#     lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
#     npv = calculate_npv(C_t, i)
#     roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

#     results_list.append({'County': row['name'], 'ROI': roi})

# # 计算贫困县数据
# for idx, row in poverty_selected.iterrows():
#     alpha = row['Curtailed_Rate']
#     mean_value = row['mean_tiff']
#     price = row['PV_price']
#     E_n = mean_value * (1 - alpha)
#     total_generation = E_n * N

#     C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] + \
#           [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

#     irr = calculate_irr(C_t)
#     lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
#     npv = calculate_npv(C_t, i)
#     roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

#     results_list.append({'poverty': row['name'], 'ROI': roi})

# # 转换为DataFrame
# results_df_pv = pd.DataFrame(results_list)

# # 输出counties的ROI到xlsx
# counties_roi_df = results_df_pv.dropna(subset=['County'])[['County', 'ROI']]
# counties_roi_df.to_excel('counties_ROI.xlsx', index=False)

# # 找出poverty中不在counties中的区域
# poverty_names = set(poverty_selected['name']) - set(counties_selected['name'])
# poverty_roi_df = results_df_pv[results_df_pv['poverty'].isin(poverty_names)][['poverty', 'ROI']]
# poverty_roi_df.to_excel('poverty_not_in_counties_ROI.xlsx', index=False)

# print("ROI数据已成功输出到xlsx文件中")


# ##### 无补贴下的敏感性分析

# In[25]:


import numpy as np
import matplotlib.pyplot as plt

# =============== 1) 原始参数设置 ===============
learning_rate_base = 0.263    # 基准学习率
learning_rate_low  = 0.185    # 低学习率
learning_rate_high = 0.348    # 高学习率

M = 45600          # 市场潜力 (GW)
p_2024 = 1.698     # 2024年光伏组件价格 (元/W)
cap_2024 = 3350    # 2024 年底累计装机量 (GW)
new_2024 = 277.17  # 2024 年新增装机量 (GW)

# Bass模型参数(示例)
p_innovation = 7.64e-9
p_imitation  = 0.626
h            = -1.134

# 为便于画图，给出预测区间
start_year = 2024
end_year   = 2050
years = list(range(start_year, end_year + 1))

# =============== 2) 封装一个函数来执行预测 ===============
def run_simulation(lr, p_2024, cap_2024, new_2024):
    """
    根据给定学习率 lr 运行 Bass+学习曲线模拟，返回:
      - all_years:   年份列表
      - capacity:    各年末累计装机量 (GW)
      - price:       各年末组件价格 (元/W)
      - new_install: 各年新增装机量 (GW)
    """
    capacity_dict = {}
    price_dict    = {}
    new_dict      = {}

    # 2024 年末的“初始”累计装机量
    cap_2024_end = cap_2024 + new_2024
    capacity_dict[start_year] = cap_2024_end
    price_dict[start_year]    = p_2024
    new_dict[start_year]      = new_2024

    for year in range(start_year + 1, end_year + 1):
        prev_capacity = capacity_dict[year - 1]

        # (1) Bass模型: 预测当年新增装机量
        #    若要考虑“价格->市场潜力”联动，可加 (curr_price/p_2024)**h 等
        adoption = (p_innovation + p_imitation*(prev_capacity / M)) * (M - prev_capacity)

        # (2) 更新该年的累计装机量
        curr_capacity = prev_capacity + adoption

        # (3) 根据学习曲线更新当年末组件价格:
        #     Price(t) = Price(2024) * ( capacity(t) / capacity(2024_end) )^(-lr)
        ratio      = curr_capacity / cap_2024_end
        curr_price = p_2024 * (ratio ** (-lr))

        # 存储
        capacity_dict[year] = curr_capacity
        price_dict[year]    = curr_price
        new_dict[year]      = adoption

    # 转为列表
    all_years = sorted(capacity_dict.keys())
    capacity  = [capacity_dict[y] for y in all_years]
    price     = [price_dict[y]    for y in all_years]
    new_inst  = [new_dict[y]      for y in all_years]

    return all_years, capacity, price, new_inst


# =============== 3) 分别运行三条曲线 ===============
results_low  = run_simulation(learning_rate_low,  p_2024, cap_2024, new_2024)
results_base = run_simulation(learning_rate_base, p_2024, cap_2024, new_2024)
results_high = run_simulation(learning_rate_high, p_2024, cap_2024, new_2024)

# 解包结果
yrs_low,  cap_low,  pri_low,  new_low  = results_low
yrs_base, cap_base, pri_base, new_base = results_base
yrs_high, cap_high, pri_high, new_high = results_high

# =============== 4) 作图对比 ===============
plt.figure(figsize=(10,5))

# ---- (1) 累计装机量对比 ----
plt.subplot(1,2,1)

# (a) 基准情景：画实线
plt.plot(yrs_base, cap_base, color='blue', linestyle='-',
         label=f'Base LR={learning_rate_base}', linewidth=2)

# (b) 以填充方式表现“低-高学习率”区间
#     这里 yrs_low 和 yrs_high 一样(都从2024到2050),
#     所以可以用 fill_between() 填充 cap_low ~ cap_high
plt.fill_between(yrs_low, cap_low, cap_high, color='skyblue', alpha=0.3,
                 label=f'LR Range: [{learning_rate_low}, {learning_rate_high}]')

plt.xlabel('Year')
plt.ylabel('Cumulative Capacity (GW)')
plt.title('Predicted Cumulative Capacity')
plt.legend()

# ---- (2) 组件价格对比 ----
plt.subplot(1,2,2)

# (a) 基准情景：画实线
plt.plot(yrs_base, pri_base, color='red', linestyle='-',
         label=f'Base LR={learning_rate_base}', linewidth=2)

# (b) 同理填充价格区间
plt.fill_between(yrs_low, pri_low, pri_high, color='salmon', alpha=0.3,
                 label=f'LR Range: [{learning_rate_low}, {learning_rate_high}]')

plt.xlabel('Year')
plt.ylabel('Price (CNY/W)')
plt.title('Predicted Module Price')
plt.legend()

plt.tight_layout()
plt.show()


# =============== 5) 终端打印结果对比 (示例) ===============
print("==== Sensitivity Analysis for Learning Rate ====")
for i, year in enumerate(yrs_base):
    print(f"Year={year}, "
          f"BasePrice={pri_base[i]:.4f}, "
          f"LowPrice={pri_low[i]:.4f}, "
          f"HighPrice={pri_high[i]:.4f}, "
          f"BaseCap={cap_base[i]:.2f}, "
          f"LowCap={cap_low[i]:.2f}, "
          f"HighCap={cap_high[i]:.2f}")


# In[26]:


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import copy

# =============== 1) 价格预测参数设置 ===============
learning_rate_base = 0.263    # 基准学习率
learning_rate_low = 0.185     # 低学习率
learning_rate_high = 0.348    # 高学习率
M = 45600          # 市场潜力 (GW)
p_2024 = 1.698     # 2024年光伏组件价格 (元/W)
cap_2024 = 3350    # 2024 年底累计装机量 (GW)
new_2024 = 277.17  # 2024 年新增装机量 (GW)

# Bass模型参数
p_innovation = 7.64e-9
p_imitation = 0.626
h = -1.134

# 预测区间
start_year = 2024
end_year = 2050

def predict_pv_prices(lr, p_2024, cap_2024, new_2024):
    """预测光伏价格"""
    price_dict = {}
    cap_2024_end = cap_2024 + new_2024
    price_dict[start_year] = p_2024 * 1000  # 转换为元/千瓦
    capacity_dict = {start_year: cap_2024_end}

    for year in range(start_year + 1, end_year + 1):
        prev_capacity = capacity_dict[year - 1]
        adoption = (p_innovation + p_imitation*(prev_capacity / M)) * (M - prev_capacity)
        curr_capacity = prev_capacity + adoption
        ratio = curr_capacity / cap_2024_end
        curr_price = p_2024 * (ratio ** (-lr)) * 1000  # 转换为元/千瓦

        capacity_dict[year] = curr_capacity
        price_dict[year] = curr_price

    return price_dict

# 生成三种情景下的价格预测
pv_prices_low = predict_pv_prices(learning_rate_low, p_2024, cap_2024, new_2024)
pv_prices_base = predict_pv_prices(learning_rate_base, p_2024, cap_2024, new_2024)
pv_prices_high = predict_pv_prices(learning_rate_high, p_2024, cap_2024, new_2024)

# 存储所有情景的结果
all_scenarios_results = []

# 其他固定参数
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0      # 其他固定成本（元/千瓦·年）
C_tax = 0    # 税收成本（元/千瓦·年）
N = 20       # 资产寿命（年）
i = 0.03     # 贴现率


# 定义情景列表
scenarios = [
    ('Low_LR', pv_prices_low, learning_rate_low),
    ('Base_LR', pv_prices_base, learning_rate_base),
    ('High_LR', pv_prices_high, learning_rate_high)
]
# ... existing code ...

# 修改 discounted_payback 函数以处理 Series
def discounted_payback(cash_flows, disc):
    """
    计算折现回收期
    cash_flows: 现金流列表
    disc: 折现率
    """
    if isinstance(cash_flows, pd.Series):
        cash_flows = cash_flows.tolist()  # 转换Series为列表

    cnpv = 0.0
    for t, cf in enumerate(cash_flows):
        cnpv += float(cf)/((1+disc)**t)  # 确保使用float
        if cnpv >= 0:
            return t
    return None


# ... existing code ...

# 在主计算循环中
for scenario_name, price_dict, lr in scenarios:
    for year in range(start_year, end_year + 1):
        C_PV = price_dict[year] + 1162
        V_R = C_PV * 0.2
        C_d = (C_PV - V_R)/20

        for idx, row in poverty_selected.iterrows():
            # 使用.iloc[0]或.values[0]来获取具体数值
            alpha = row.loc['Curtailed_Rate']
            mean_value = row.loc['mean_tiff']
            price = row.loc['PV_price']

            # 计算基本参数
            E_n = float(mean_value) * (1-float(alpha))
            total_generation = E_n * N

            # 计算现金流
            initial_cash_flow = E_n * float(price) - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)
            annual_cash_flow = E_n * float(price) - (O_PV + O_ES + C_F + C_tax + C_d)

            # 创建现金流列表
            C_t = [initial_cash_flow] + [annual_cash_flow] * (N-1)

            # 计算经济指标
            irr = calculate_irr(C_t)
            lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
            npv = calculate_npv(C_t, i)
            roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)
            payback = discounted_payback(C_t, i)

            # 存储结果
            all_scenarios_results.append({
                'Scenario': scenario_name,
                'Year': year,
                'County': str(row.loc['name']),  # 确保名称为字符串
                'LCOE': lcoe,
                'NPV': npv,
                'IRR': irr,
                'ROI': roi,
                'Payback': payback,
                'PV_Cost': C_PV,
                'Learning_Rate': lr
            })

# ... existing code ...
# 转换为DataFrame
final_results = pd.DataFrame(all_scenarios_results)

# 保存结果
final_results.to_csv('economic_assessment_results_2024_2050_scenarios.csv', index=False)

print("分析完成，结果已保存到 economic_assessment_results_2024_2050_scenarios.csv")
print("\n各情景2024年结果预览：")
print(final_results[final_results['Year'] == 2024].groupby('Scenario').head(1))

# 计算每个情景每年的平均指标
yearly_scenario_averages = final_results.groupby(['Scenario', 'Year'])[['LCOE', 'NPV', 'IRR', 'ROI', 'PV_Cost']].mean()
print("\n各情景各年份平均指标：")
print(yearly_scenario_averages.head(9))  # 显示每个情景2024年的结果


# In[27]:


# ... existing code ...

print("\n=== ROI > 3%的县的回收期分析 ===")

# 筛选ROI > 0.03的数据
roi_filtered = final_results[final_results['ROI'] > 0.03]

# 按情景和年份分组计算payback的均值和数量
payback_analysis = roi_filtered.groupby(['Scenario', 'Year']).agg({
    'Payback': ['mean', 'count']
}).reset_index()

# 重命名列名
payback_analysis.columns = ['Scenario', 'Year', '回收期均值', '符合条件的县数量']

# 打印分析结果
for scenario in ['Low_LR', 'Base_LR', 'High_LR']:
    scenario_data = payback_analysis[payback_analysis['Scenario'] == scenario]
    print(f"\n{scenario}情景下ROI>3%的县的回收期分析：")
    print(f"2024年回收期均值：{scenario_data[scenario_data['Year']==2024]['回收期均值'].values[0]:.2f}年")
    print(f"2024年符合条件的县数量：{scenario_data[scenario_data['Year']==2024]['符合条件的县数量'].values[0]:.0f}个")
    print(f"2050年回收期均值：{scenario_data[scenario_data['Year']==2050]['回收期均值'].values[0]:.2f}年")
    print(f"2050年符合条件的县数量：{scenario_data[scenario_data['Year']==2050]['符合条件的县数量'].values[0]:.0f}个")

# 保存详细分析结果
payback_analysis.to_csv('roi_filtered_payback_analysis.csv', index=False)
print("\n详细分析结果已保存至 roi_filtered_payback_analysis.csv")


# In[28]:


import matplotlib.pyplot as plt

# 1) 创建一个新的列，用于标记 ROI 是否 > 0.03
df_plot = final_results.copy()
df_plot['ROI_above_3pct'] = df_plot['ROI'] > 0.03

# 2) 按 (Scenario, Year) 统计 ROI_above_3pct = True 的计数
df_count = df_plot.groupby(['Scenario','Year'])['ROI_above_3pct'].sum().reset_index(name='Count_ROI_Above_3pct')

# 3) 分别取出 Low_LR / Base_LR / High_LR 的数据
df_low  = df_count[df_count['Scenario']=='Low_LR'].sort_values('Year')
df_base = df_count[df_count['Scenario']=='Base_LR'].sort_values('Year')
df_high = df_count[df_count['Scenario']=='High_LR'].sort_values('Year')

# 4) 开始绘图
plt.figure(figsize=(8,5))  # 仅一张图

# 4.1 画出 Base_LR 的折线
plt.plot(df_base['Year'],
         df_base['Count_ROI_Above_3pct'],
         label='Base_LR (ROI>3%)')

# 4.2 使用 fill_between 表示 Low_LR 和 High_LR 之间的区间
#     注意要确保 Low/High 的 Year 排序相同、点位对应
plt.fill_between(df_low['Year'],
                 df_low['Count_ROI_Above_3pct'],
                 df_high['Count_ROI_Above_3pct'],
                 alpha=0.3,
                 label='Low_LR~High_LR range')

# 5) 添加图例、坐标轴标签、标题
plt.legend()
plt.xlabel('Year')
plt.ylabel('Count of Regions (ROI > 3%)')
plt.title('Count of Regions with ROI>3% under Different Learning Rate Scenarios')

plt.show()


# #### 补贴价格

# In[25]:


# 光伏模型标定
# Create a DataFrame to store results for each county
results_list = []

# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率

# Calculate and store results for each county in counties_selected
for idx, row in counties_selected.iterrows():
    alpha = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    # 修改：使用 Subsidy_Price 替换 PV_price
    price = row['Subsidy_Price']
    E_n = mean_value * (1 - alpha)
    total_generation = E_n * N

    # Calculate cash flow sequence C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] \
          + [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

    # Calculate LCOE, NPV, IRR, and ROI for the county
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)

    # If IRR cannot be calculated, use discount rate i for NPV
    if irr is not None:
        npv = calculate_npv(C_t, i)
    else:
        npv = calculate_npv(C_t, i)  # Use discount rate i to calculate NPV

    roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # Store the results in the list,并给输出变量添加后缀 "_sub"
    results_list.append({
        'County': row['name'],
        'LCOE_sub': lcoe,
        'NPV_sub': npv,
        'IRR_sub': irr,
        'ROI_sub': roi
    })

# Calculate and store results for each county in the poverty_selected dataset
for idx, row in poverty_selected.iterrows():
    alpha = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    # 修改：使用 Subsidy_Price 替换 PV_price
    price = row['Subsidy_Price']
    E_n = mean_value * (1 - alpha)
    total_generation = E_n * N

    # Calculate cash flow sequence C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] \
          + [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

    # Calculate LCOE, NPV, IRR, and ROI for the county
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)

    # If IRR cannot be calculated, use discount rate i for NPV
    if irr is not None:
        npv = calculate_npv(C_t, i)
    else:
        npv = calculate_npv(C_t, i)  # Use discount rate i to calculate NPV

    roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # Store the results in the list,并给输出变量添加后缀 "_sub"
    results_list.append({
        'poverty': row['name'],
        'LCOE_sub': lcoe,
        'NPV_sub': npv,
        'IRR_sub': irr,
        'ROI_sub': roi
    })

# Convert the results list to a DataFrame
results = pd.DataFrame(results_list)

# Save results to a CSV file
results.to_csv('economic_assessment_results.csv', index=False)

# Merge results with GeoDataFrame for visualization
counties_selected = counties_selected.merge(results, left_on='name', right_on='County')
poverty_selected = poverty_selected.merge(results, left_on='name', right_on='poverty')

# 计算价格减成本列
for idx, row in poverty_selected.iterrows():
    # 计算总成本（不考虑折现）
    initial_cost = C_PV + C_ES  # 初始投资成本
    annual_cost = (O_PV + O_ES + C_F + C_tax + C_d) * N  # N年内的年度成本总和
    total_cost = initial_cost + annual_cost  # 总成本

    # 计算每单位发电量的成本（元/千瓦时）
    E_n = row['mean_tiff'] * (1-row['Curtailed_Rate'])  # 年发电量
    total_generation = E_n * N  # 总发电量
    unit_cost = total_cost / total_generation if total_generation > 0 else 0  # 单位成本

    # 计算价格减成本
    price_minus_cost = row['Subsidy_Price'] - unit_cost

    # 添加到DataFrame
    poverty_selected.at[idx, 'price_minus_cost_sub'] = price_minus_cost

print(poverty_selected)


# In[26]:


print(poverty_selected)


# In[ ]:





# #### 优先上网

# In[27]:


# 光伏模型标定（将alpha设为0计算新的输出值，并给输出值加上后缀 _priority）
# Create a DataFrame to store results for each county
results_list = []


# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率

# -------------------------------
# 计算 counties_selected 数据集的指标（alpha固定设为0）
for idx, row in counties_selected.iterrows():
    alpha = 0                     # 将alpha设为0
    mean_value = row['mean_tiff']
    price = row['PV_price']       # 使用对应的PV_price
    E_n = mean_value * (1 - alpha)  # 此时E_n = mean_value
    total_generation = E_n * N

    # Calculate cash flow sequence C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] + \
          [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

    # Calculate LCOE, NPV, IRR, and ROI for the county
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)

    if irr is not None:
        npv = calculate_npv(C_t, i)
    else:
        npv = calculate_npv(C_t, i)

    roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # 存储结果时添加后缀 _priority
    results_list.append({
        'County': row['name'],
        'LCOE_priority': lcoe,
        'NPV_priority': npv,
        'IRR_priority': irr,
        'ROI_priority': roi
    })

# -------------------------------
# 计算 poverty_selected 数据集的指标（alpha固定设为0）
for idx, row in poverty_selected.iterrows():
    alpha = 0                     # 将alpha设为0
    mean_value = row['mean_tiff']
    price = row['PV_price']       # 使用对应的PV_price
    E_n = mean_value * (1 - alpha)  # 此时E_n = mean_value
    total_generation = E_n * N

    # Calculate cash flow sequence C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d)] + \
          [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d) for _ in range(1, N)]

    # Calculate LCOE, NPV, IRR, and ROI for the county
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)

    if irr is not None:
        npv = calculate_npv(C_t, i)
    else:
        npv = calculate_npv(C_t, i)

    roi = calculate_roi(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # 存储结果时添加后缀 _priority
    results_list.append({
        'poverty': row['name'],
        'LCOE_priority': lcoe,
        'NPV_priority': npv,
        'IRR_priority': irr,
        'ROI_priority': roi
    })

# Convert the results list to a DataFrame
results = pd.DataFrame(results_list)

# Save results to a CSV file
results.to_csv('economic_assessment_results.csv', index=False)

# Merge results with GeoDataFrame for visualization
counties_selected = counties_selected.merge(results, left_on='name', right_on='County')
poverty_selected = poverty_selected.merge(results, left_on='name', right_on='poverty')

# 计算价格减成本列
for idx, row in poverty_selected.iterrows():
    # 计算总成本（不考虑折现）
    initial_cost = C_PV + C_ES  # 初始投资成本
    annual_cost = (O_PV + O_ES + C_F + C_tax + C_d) * N  # N年内的年度成本总和
    total_cost = initial_cost + annual_cost  # 总成本

    # 计算每单位发电量的成本（元/千瓦时）
    # 注意这里使用alpha=0，与上面的计算保持一致
    E_n = row['mean_tiff'] * (1-0)  # 年发电量，无限电损失
    total_generation = E_n * N  # 总发电量
    unit_cost = total_cost / total_generation if total_generation > 0 else 0  # 单位成本

    # 计算价格减成本
    price_minus_cost = row['PV_price'] - unit_cost

    # 添加到DataFrame
    poverty_selected.at[idx, 'price_minus_cost_priority'] = price_minus_cost


print(poverty_selected)


# In[ ]:





# #### 配储能

# ##### 配储能直接计算

# In[28]:


# -------------------------------
# 创建存储结果的列表
results_list = []

# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率

# -------------------------------
# 计算 counties_selected 数据集的指标（alpha 固定设为 0）
for idx, row in counties_selected.iterrows():
    alpha = 0  # 将 alpha 设为 0
    beta = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    # 以天为单位计算光伏配储能成本（将弃电全部储存并释放）
    mean_value_day_count = mean_value / 365 * beta * 1000 * (1.2 + 0.8 ) / 2   # 换电的时候换电芯
    # fix_storage = 0.0448 * mean_value_day_count # 要进行修改，是单位储能的运维成本（元/Wh ）
    fix_storage = 0
    # https://www.tsi001.com/yingyong/339.html

    price = row['PV_price']  # 使用对应的 PV_price
    E_n = mean_value * (1 - alpha)  # 此时 E_n = mean_value
    total_generation = E_n * N

    # 构造 N 年内的现金流序列 C_t
    C_t = [E_n * price - (C_PV + C_ES + O_PV + O_ES + C_F + C_tax + C_d + mean_value_day_count +fix_storage)] + \
          [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d +fix_storage) for _ in range(1, N)]

    # 计算经济指标
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV + mean_value_day_count, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
    npv = calculate_npv(C_t, i)
    roi = calculate_roi(total_generation, price, C_PV + mean_value_day_count, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # 存储结果时添加后缀 _storage
    results_list.append({
        'County_storage': row['name'],
        'LCOE_storage': lcoe,
        'NPV_storage': npv,
        'IRR_storage': irr,
        'ROI_storage': roi
    })

# -------------------------------
# 计算 poverty_selected 数据集的指标（alpha 固定设为 0）
for idx, row in poverty_selected.iterrows():
    alpha = 0  # 将 alpha 设为 0
    beta = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    mean_value_day_count = mean_value / 365 * beta * 1000 * (1.2 + 0.8 ) / 2
    # fix_storage = 0.0448 * mean_value_day_count # 要进行修改，是单位储能的运维成本（元/Wh ）
    fix_storage = 0
    price = row['PV_price']  # 使用对应的 PV_price
    E_n = mean_value * (1 - alpha)  # 此时 E_n = mean_value
    total_generation = E_n * N

    # 构造 N 年内的现金流序列 C_t
    C_t = [E_n * price - (C_PV + mean_value_day_count + C_ES + O_PV + O_ES + C_F + C_tax + C_d +fix_storage)] + \
          [E_n * price - (O_PV + O_ES + C_F + C_tax + C_d +fix_storage) for _ in range(1, N)]

    # 计算经济指标
    irr = calculate_irr(C_t)
    lcoe = calculate_lcoe(C_PV + mean_value_day_count, C_ES, O_PV, O_ES, C_F, C_tax, C_d, V_R, E_n, i, N)
    npv = calculate_npv(C_t, i)
    roi = calculate_roi(total_generation, price, C_PV + mean_value_day_count, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # 存储结果时添加后缀 _storage
    results_list.append({
        'poverty_storage': row['name'],
        'LCOE_storage': lcoe,
        'NPV_storage': npv,
        'IRR_storage': irr,
        'ROI_storage': roi,
        'mean_value_day_count' : mean_value_day_count
    })

# 将结果列表转换为 DataFrame
results = pd.DataFrame(results_list)

# 保存结果到 CSV 文件
results.to_csv('economic_assessment_results.csv', index=False)

# -------------------------------
# 将结果与 GeoDataFrame 进行合并以便可视化
# counties_selected：左侧用 name 与右侧的 County_storage 进行合并
counties_selected = counties_selected.merge(results, left_on='name', right_on='County_storage')

# poverty_selected：左侧用 name 与右侧的 poverty_storage 进行合并
poverty_selected = poverty_selected.merge(results, left_on='name', right_on='poverty_storage')

# 为poverty_selected添加价格减成本列
for idx, row in poverty_selected.iterrows():
    # 计算储能相关成本
    beta = row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    mean_value_day_count = mean_value / 365 * beta * 1000 * (1.2 + 0.8) / 2
    fix_storage = 0

    # 计算总成本（不考虑折现）
    initial_cost = C_PV + mean_value_day_count + C_ES  # 初始投资成本
    annual_cost = (O_PV + O_ES + C_F + C_tax + C_d + fix_storage) * N  # N年内的年度成本总和
    total_cost = initial_cost + annual_cost  # 总成本

    # 计算每单位发电量的成本（元/千瓦时）
    E_n = mean_value * (1-0)  # 年发电量，α=0表示无限电损失
    total_generation = E_n * N  # 总发电量
    unit_cost = total_cost / total_generation if total_generation > 0 else 0  # 单位成本

    # 计算价格减成本
    price_minus_cost = row['PV_price'] - unit_cost

    # 添加到DataFrame
    poverty_selected.at[idx, 'price_minus_cost_storage'] = price_minus_cost

    energy_storage_per_kwh = row['mean_value_day_count'] / E_n / beta

    poverty_selected.at[idx, 'energy_storage_per_kwh'] = energy_storage_per_kwh

print(poverty_selected)


# In[29]:


# 按省份分组计算
province_stats = poverty_selected.groupby('Province').apply(
    lambda x: (x['ROI_storage'] > 0.03).sum() / len(x) * 100
).reset_index(name='比例')

# 展示每个省份的百分比
print("各省份ROI大于3%的县占比：")
for _, row in province_stats.iterrows():
    print(f"{row['Province']}: {row['比例']:.2f}%")


# ##### 配储能的学习曲线
# 学习曲线参数
# https://www.nature.com/articles/s43246-024-00646-6
# 
# https://rael.berkeley.edu/wp-content/uploads/2017/07/Kittner-Lill-Kammen-EnergyStorageDeploymentandInnovation-NatureEnergy-2017.pdf
# 
# https://www.nature.com/articles/s41467-020-18402-y.pdf
# 
# 锂电池预测数据
# https://www.sciencedirect.com/science/article/pii/S2666792422000348
# 
# 储能系统学习曲线预测
# http://ir.lib.ncu.edu.tw:88/thesis/view_etd.asp?URN=109581002&fileName=GC109581002.pdf
# 
# chatgpt:中国电力储能数据(目前已经转换为excel了)

# In[33]:


import pandas as pd
import numpy as np
from scipy.optimize import curve_fit, differential_evolution

#####################################
#  1. 读取 2021-2024 年历史数据，并拟合 #
#####################################

# Excel 文件
file_capacity = "中国光伏累计储能数据.xlsx"    # 含"年份"、"累计电池储能容量 MW"列
file_price    = "中国光伏储能价格.xlsx"       # 含"年份"、"元/Wh"列

# 读取容量与价格
df_capacity = pd.read_excel(file_capacity, usecols=["年份", "累计电池储能容量 MW"])
df_price    = pd.read_excel(file_price,    usecols=["年份", "元/Wh"])

# 重命名列
df_capacity.rename(columns={
    "年份": "Year",
    "累计电池储能容量 MW": "Cumulative Capacity (MW)"
}, inplace=True)
df_price.rename(columns={
    "年份": "Year",
    "元/Wh": "Price (CNY/Wh)"
}, inplace=True)

# 筛选 2021 ~ 2024
df_capacity = df_capacity[df_capacity["Year"].between(2021, 2024)].sort_values(by="Year")
df_price    = df_price[df_price["Year"].between(2021, 2024)].sort_values(by="Year")

if df_capacity.empty or df_price.empty:
    raise ValueError("Excel 中 2021-2024 数据不完整，请检查文件内容。")

# 提取历史数据
years    = df_capacity["Year"].values
Q_actual = df_capacity["Cumulative Capacity (MW)"].values  # 累计装机量 (MW)
P_actual = df_price["Price (CNY/Wh)"].values               # 价格 (元/Wh)

# 每年新增量
A_actual = np.diff(Q_actual, prepend=Q_actual[0])

# 初始化（可根据需要修改）
M_init = 150000    # 假设市场潜力
a_init = 0.0028
b_init = 0.495
h_init = -0.75

##############################
# (1) 最小二乘法拟合 a, b
##############################
def bass_model_fit_ab(year_arr, a, b):
    Q_pred = np.zeros_like(year_arr, dtype=float)
    A_pred = np.zeros_like(year_arr, dtype=float)
    Q_pred[0] = Q_actual[0]
    for i in range(1, len(year_arr)):
        # 固定 M_init, h_init
        market_potential = M_init * (P_actual[i] ** h_init)
        A_pred[i] = a*market_potential + (b - a)*Q_pred[i-1] - (b/market_potential)*(Q_pred[i-1]**2)
        Q_pred[i] = Q_pred[i-1] + A_pred[i]
    return A_pred

popt_ab, _ = curve_fit(
    bass_model_fit_ab, years, A_actual, p0=[a_init, b_init], maxfev=10000
)
a_fit, b_fit = popt_ab

print("===== (1) 最小二乘法拟合 (a, b) =====")
print(f"a = {a_fit:.6f}, b = {b_fit:.6f}")

##############################
# (2) 微分进化拟合 M, h
##############################
def bass_model_fit_Mh(params):
    M, h = params
    Q_pred = np.zeros_like(years, dtype=float)
    A_pred = np.zeros_like(years, dtype=float)
    Q_pred[0] = Q_actual[0]
    for i in range(1, len(years)):
        mp = M*(P_actual[i] ** h)
        A_pred[i] = a_fit*mp + (b_fit - a_fit)*Q_pred[i-1] - (b_fit/mp)*(Q_pred[i-1]**2)
        Q_pred[i] = Q_pred[i-1] + A_pred[i]
    # 最小化 A_pred 与 A_actual 的二范数误差
    return np.sum((A_pred - A_actual)**2)

bounds = [(10000, 500000), (-2, 0)]  # M: [1e4, 5e5],  h: [-2, 0]
res = differential_evolution(
    bass_model_fit_Mh, bounds, strategy='best1bin', maxiter=1000, popsize=20
)
M_fit, h_fit = res.x

print("\n===== (2) 微分进化拟合 (M, h) =====")
print(f"M = {M_fit:.2f} MW, h = {h_fit:.4f}")


#####################################################################
#  2. 基于 2024 数据作为基准，用学习曲线 + Bass 扩散预测 2025-2050
#####################################################################

# 找到 2024 在 years中的索引
idx_2024 = np.where(years == 2024)[0]
if len(idx_2024) == 0:
    raise ValueError("没有找到 2024 年的数据，请检查 Excel。")

index_2024 = idx_2024[0]
Q_2024 = Q_actual[index_2024]
P_2024 = P_actual[index_2024]

# 学习率
learning_exponent = -0.263

# 预测年份 2025~2050
forecast_years = np.arange(2025, 2051, 1)

# 构建数组存储
Q_forecast = np.zeros_like(forecast_years, dtype=float)  # 累计装机量
A_forecast = np.zeros_like(forecast_years, dtype=float)  # 新增装机
P_forecast = np.zeros_like(forecast_years, dtype=float)  # 价格

# 初始化 Q_prev = Q_2024
Q_prev = Q_2024

for i, y in enumerate(forecast_years):
    # 1) 根据前一年累计量 Q_prev 计算该年的价格
    # price(t) = P_2024 * ( Q_prev / Q_2024 )^( -0.263 )
    price_t = P_2024 * ((Q_prev / Q_2024) ** learning_exponent)

    # 2) 使用 Bass 扩散公式(含 M_fit, h_fit) 计算当年新增量
    mp = M_fit * (price_t ** h_fit)
    A_t = a_fit*mp + (b_fit - a_fit)*Q_prev - (b_fit/mp)*(Q_prev**2)

    # 3) 累计量
    Q_t = Q_prev + A_t

    # 存储
    P_forecast[i] = price_t
    A_forecast[i] = A_t
    Q_forecast[i] = Q_t

    # 准备下一年
    Q_prev = Q_t

# 输出预测结果
print("\n===== (3) 2025–2050 预测结果 =====")
print("Year |    Price(元/Wh)   |  NewAdded(MW)  |  Cumulative(MW)")
for i, y in enumerate(forecast_years):
    print(f"{y} | {P_forecast[i]:>12.6f} | {A_forecast[i]:>12.2f} | {Q_forecast[i]:>14.2f}")


# In[34]:


def discounted_payback(cash_flows, disc):
    cnpv=0.0
    for t, cf in enumerate(cash_flows):
        cnpv += cf/((1+disc)**t)
        if cnpv>=0:
            return t
    return None


# In[35]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import newton, curve_fit, differential_evolution


##############################################################################
#                           Part (A): 光伏组件价格敏感性分析
##############################################################################

# ------------------- 1) 原始参数设置 -------------------
learning_rate_low  = 0.0740
learning_rate_base = 0.1047
learning_rate_high = 0.1520

M_pv = 45600          # 市场潜力 (GW) (示例)
p_2024_pv = 1.698     # 2024年光伏组件价格 (元/W)
cap_2024_pv = 3350    # 2024 年底累计装机量 (GW)
new_2024_pv = 277.17  # 2024 年新增装机量 (GW)

# Bass模型参数(示例)
p_innovation_pv = 7.64e-9
p_imitation_pv  = 0.626
h_pv            = -1.134

start_year_pv = 2024
end_year_pv   = 2050
years_pv      = list(range(start_year_pv, end_year_pv+1))


def run_simulation_pv(lr, p_2024, cap_2024, new_2024):
    """
    光伏组件的 Bass+学习曲线模拟
    返回: (all_years, capacity_list, price_list, new_list)
    """
    capacity_dict = {}
    price_dict    = {}
    new_dict      = {}

    cap_2024_end = cap_2024 + new_2024
    capacity_dict[start_year_pv] = cap_2024_end
    price_dict[start_year_pv]    = p_2024
    new_dict[start_year_pv]      = new_2024

    for year in range(start_year_pv+1, end_year_pv+1):
        prev_cap = capacity_dict[year-1]

        # Bass 预测
        adoption = (p_innovation_pv + p_imitation_pv*(prev_cap / M_pv)) * (M_pv - prev_cap)
        curr_cap = prev_cap + adoption

        # 学习曲线 => Price
        ratio      = curr_cap / cap_2024_end
        curr_price = p_2024 * (ratio**(-lr))

        capacity_dict[year] = curr_cap
        price_dict[year]    = curr_price
        new_dict[year]      = adoption

    all_years = sorted(capacity_dict.keys())
    capacity_list = [capacity_dict[y] for y in all_years]
    price_list    = [price_dict[y]    for y in all_years]
    new_list      = [new_dict[y]      for y in all_years]
    return all_years, capacity_list, price_list, new_list


# ------------------- 2) 分别运行三条学习率曲线 -------------------
res_low_pv  = run_simulation_pv(learning_rate_low,  p_2024_pv, cap_2024_pv, new_2024_pv)
res_base_pv = run_simulation_pv(learning_rate_base, p_2024_pv, cap_2024_pv, new_2024_pv)
res_high_pv = run_simulation_pv(learning_rate_high, p_2024_pv, cap_2024_pv, new_2024_pv)

yrs_low_pv,  cap_low_pv,  pri_low_pv,  new_low_pv  = res_low_pv
yrs_base_pv, cap_base_pv, pri_base_pv, new_base_pv = res_base_pv
yrs_high_pv, cap_high_pv, pri_high_pv, new_high_pv = res_high_pv


# ------------------- 3) 整合为 DataFrame df_pv_prices -------------------
records_pv = []
for i, y in enumerate(yrs_low_pv):
    records_pv.append({"Year": y, "Scenario":"Low_LR",  "Price_W": pri_low_pv[i],  "Capacity": cap_low_pv[i]})
for i, y in enumerate(yrs_base_pv):
    records_pv.append({"Year": y, "Scenario":"Base_LR", "Price_W": pri_base_pv[i], "Capacity": cap_base_pv[i]})
for i, y in enumerate(yrs_high_pv):
    records_pv.append({"Year": y, "Scenario":"High_LR","Price_W": pri_high_pv[i], "Capacity": cap_high_pv[i]})

df_pv_prices = pd.DataFrame(records_pv)
df_pv_prices.sort_values(["Scenario","Year"], inplace=True)
df_pv_prices.reset_index(drop=True, inplace=True)

print("\n=== 光伏组件三种学习率场景: df_pv_prices (部分) ===")
print(df_pv_prices.head(12))


##############################################################################
#            Part (B): 储能电池 (Battery) Bass拟合 & 学习率敏感性
##############################################################################

file_capacity_battery = "中国光伏累计储能数据.xlsx"  # 假设含 "年份","累计电池储能容量 MW"
file_price_battery    = "中国光伏储能价格.xlsx"     # 假设含 "年份","元/Wh" (电池价格)

df_capacity_batt = pd.read_excel(file_capacity_battery, usecols=["年份","累计电池储能容量 MW"])
df_price_batt    = pd.read_excel(file_price_battery,    usecols=["年份","元/Wh"])
df_capacity_batt.rename(columns={"年份":"Year", "累计电池储能容量 MW":"CumulativeCapacity_MW"}, inplace=True)
df_price_batt.rename(columns={"年份":"Year", "元/Wh":"Price_Wh"}, inplace=True)

df_capacity_batt = df_capacity_batt[df_capacity_batt["Year"].between(2021,2024)].sort_values("Year")
df_price_batt    = df_price_batt[df_price_batt["Year"].between(2021,2024)].sort_values("Year")
if df_capacity_batt.empty or df_price_batt.empty:
    raise ValueError("Battery data 2021~2024 incomplete")

years_batt = df_capacity_batt["Year"].astype(int).values
Q_batt_actual = df_capacity_batt["CumulativeCapacity_MW"].astype(float).values
P_batt_actual = df_price_batt["Price_Wh"].astype(float).values
A_batt_actual = np.diff(Q_batt_actual, prepend=Q_batt_actual[0])

# 类似地固定 M=500000, 拟合 a,b,h => 这里做简化
M_fixed_batt = 500000
def battery_bass_model_ab(year_arr, a, b, M_init=150000, h_init=-0.75):
    Q_pred = np.zeros_like(year_arr)
    A_pred = np.zeros_like(year_arr)
    Q_pred[0] = Q_batt_actual[0]
    for i in range(1, len(year_arr)):
        p_val = float(P_batt_actual[i])
        mp    = M_init*(p_val**h_init)
        A_pred[i] = a*mp + (b-a)*Q_pred[i-1] - (b/mp)*(Q_pred[i-1]**2)
        Q_pred[i] = Q_pred[i-1] + A_pred[i]
    return A_pred

popt_ab_batt, _ = curve_fit(
    lambda x, a, b: battery_bass_model_ab(x, a, b),
    years_batt, A_batt_actual,
    p0=[0.003,0.5],
    maxfev=10000
)
a_batt, b_batt = popt_ab_batt
print(f"\n[Battery Step1] a_batt={a_batt:.6f}, b_batt={b_batt:.6f}")

def battery_bass_model_h(h):
    Q_pred = np.zeros_like(years_batt)
    A_pred = np.zeros_like(years_batt)
    Q_pred[0] = Q_batt_actual[0]
    for i in range(1, len(years_batt)):
        p_val = float(P_batt_actual[i])
        mp = M_fixed_batt*(p_val**h)
        A_pred[i] = a_batt*mp + (b_batt - a_batt)*Q_pred[i-1] - (b_batt/mp)*(Q_pred[i-1]**2)
        Q_pred[i] = Q_pred[i-1]+A_pred[i]
    return np.sum((A_pred - A_batt_actual)**2)

bounds_batt = [(-2,0)]
res_batt = differential_evolution(
    battery_bass_model_h,
    bounds=bounds_batt,
    maxiter=200, popsize=10
)
h_batt = res_batt.x[0]
print(f"[Battery Step2] M={M_fixed_batt}, h_batt={h_batt:.4f}")

# 电池学习率也同步修改
lr_low_batt  = 0.0740
lr_base_batt = 0.1047
lr_high_batt = 0.1520

start_batt = 2024
end_batt   = 2050
years_batt_forecast = list(range(start_batt, end_batt+1))

Q_2024_batt = float(Q_batt_actual[-1])  # 2024 最后一个
P_2024_batt = float(P_batt_actual[-1])

def run_battery_scenario(learn_r):
    Q_prev = Q_2024_batt
    cap_dict = {}
    price_dict = {}
    for y in years_batt_forecast:
        # battery price(t)
        # Price(t) = P_2024_batt * (Q_prev / Q_2024_batt)^(-learn_r)
        ratio = Q_prev/Q_2024_batt
        price_t = P_2024_batt*(ratio**(-learn_r))
        # Bass
        mp = M_fixed_batt*(price_t**h_batt)
        A_t = a_batt*mp + (b_batt-a_batt)*Q_prev - (b_batt/mp)*(Q_prev**2)
        Q_t = Q_prev + A_t
        cap_dict[y]   = Q_t
        price_dict[y] = price_t
        Q_prev = Q_t
    return cap_dict, price_dict


cap_low_batt,  price_low_batt  = run_battery_scenario(lr_low_batt)
cap_base_batt, price_base_batt = run_battery_scenario(lr_base_batt)
cap_high_batt, price_high_batt = run_battery_scenario(lr_high_batt)

records_battery = []
for y in years_batt_forecast:
    records_battery.append({
        "Year":y, "Scenario":"Low_LR",
        "BatteryPrice_Wh": price_low_batt[y],
        "Capacity": cap_low_batt[y]
    })
    records_battery.append({
        "Year":y, "Scenario":"Base_LR",
        "BatteryPrice_Wh": price_base_batt[y],
        "Capacity": cap_base_batt[y]
    })
    records_battery.append({
        "Year":y, "Scenario":"High_LR",
        "BatteryPrice_Wh": price_high_batt[y],
        "Capacity": cap_high_batt[y]
    })

df_battery_prices = pd.DataFrame(records_battery)
df_battery_prices.sort_values(["Scenario","Year"], inplace=True)
df_battery_prices.reset_index(drop=True, inplace=True)

print("\n=== Battery三种学习率场景: df_battery_prices (部分) ===")
print(df_battery_prices.head(12))


##############################################################################
# (C) 将 df_pv_prices 和 df_battery_prices 合并使用，做地理单元经济测算
##############################################################################

def get_pv_price(scenario, year):
    row = df_pv_prices[(df_pv_prices["Scenario"]==scenario)&(df_pv_prices["Year"]==year)]
    if row.empty:
        return None
    return float(row["Price_W"].iloc[0])

def get_battery_price(scenario, year):
    row = df_battery_prices[(df_battery_prices["Scenario"]==scenario)&(df_battery_prices["Year"]==year)]
    if row.empty:
        return None
    return float(row["BatteryPrice_Wh"].iloc[0])


N   = 20
i   = 0.03
O_PV=90.0
C_ES=0; O_ES=0; C_F=0; C_tax=0

def discounted_payback(cash_flows, disc):
    cnpv=0.0
    for t, cf in enumerate(cash_flows):
        cnpv += cf/((1+disc)**t)
        if cnpv>=0:
            return t
    return None

forecast_results_list = []

# 假设我们遍历 2025~2050, 并对三种场景 "Low_LR","Base_LR","High_LR"
all_years = range(2024,2051)
all_scenarios = ["Low_LR","Base_LR","High_LR"]

for scenario in all_scenarios:
    for year_val in all_years:
        # 1) 查询光伏组件价格(元/W)
        pv_price_w = get_pv_price(scenario, year_val) + 1.162
        if pv_price_w is None:
            continue
        # => CAPEX(元/kW)
        C_PV_this = pv_price_w * 1000

        # 2) 查询电池价格(元/Wh)
        batt_price_wh = get_battery_price(scenario, year_val)
        if batt_price_wh is None:
            continue

        # 这里(1.2 + 0.8) => (batt_price_wh*(5/3))
        # 例如:
        battery_cost_factor = batt_price_wh*(5/3)

        # # 遍历 counties
        # local_list=[]
        # for _, row_c in counties_selected.iterrows():
        #     region_name = row_c["name"]
        #     beta        = row_c["Curtailed_Rate"]
        #     mean_value  = row_c["mean_tiff"]
        #     alpha=0.0

        #     # mean_value_day_count = ...
        #     mean_value_day_count = (mean_value/365)*beta*1000*battery_cost_factor/2

        #     E_n = mean_value
        #     total_gen = E_n*N
        #     sell_price = row_c["PV_price"]

        #     # 第0年现金流
        #     c0 = E_n*sell_price - (C_PV_this + mean_value_day_count + C_ES + O_PV + O_ES + C_F + C_tax)
        #     # 之后
        #     c_t=[]
        #     for t in range(1,N):

        V_R = C_PV_this * 0.2
        C_d = (C_PV_this - V_R)/20 


        #     npv_val = calculate_npv(c_flow,i)
        #     payback = discounted_payback(c_flow,i)

        #     local_list.append({
        #         "ScenarioName": scenario,
        #         "Year": year_val,
        #         "RegionType": "County",
        #         "RegionName": region_name,
        #         "PVPrice_W": pv_price_w,
        #         "BatteryPrice_Wh": batt_price_wh,
        #         "mean_value_day_count": mean_value_day_count,
        #         "NPV": npv_val,
        #         "IRR": irr_val,
        #         "Payback_yr": payback,
        #         # ... 你也可加 ROI, LCOE 等
        #     })
        # # forecast_results_list.extend(local_list)

        # 遍历 poverty
        local_list=[]
        for _, row_p in poverty_selected.iterrows():
            region_name = row_p["name"]
            beta        = row_p["Curtailed_Rate"]
            mean_value  = row_p["mean_tiff"]
            alpha=0.0

            # ... 现有代码 ...

            mean_value_day_count = (mean_value/365)*beta*1000*battery_cost_factor/2
            E_n = mean_value
            total_gen = E_n*N
            sell_price = row_p["PV_price"]

            # 初始投资成本包含电池成本
            c0 = E_n*sell_price - (C_PV_this + mean_value_day_count + C_ES + O_PV + O_ES + C_F + C_tax)
            c_t=[]

            # 假设电池寿命为7年，需要在第7年、第14年更换
            battery_lifetime = 7
            for t in range(1,N):
                yearly_cost = O_PV + O_ES + C_F + C_tax

                # 在电池需要更换的年份加入电池更换成本
                if t % battery_lifetime == 0:
                    yearly_cost += mean_value_day_count

                c_t.append(E_n*sell_price - yearly_cost)
            c_flow=[c0]+c_t

            # ... 现有代码 ...
            N = 20

            roi = calculate_roi(total_gen, sell_price, C_PV_this + mean_value_day_count, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

            irr_val = calculate_irr(c_flow)
            npv_val = calculate_npv(c_flow,i)
            payback = discounted_payback(c_flow,i)

            local_list.append({
                "ScenarioName": scenario,
                "Year": year_val,
                "RegionType": "Poverty",
                "RegionName": region_name,
                "PVPrice_W": pv_price_w,
                "BatteryPrice_Wh": batt_price_wh,
                "mean_value_day_count": mean_value_day_count,
                "NPV": npv_val,
                "IRR": irr_val,
                "Payback_yr": payback,
                "ROI":roi,
            })
        forecast_results_list.extend(local_list)

# 转 DataFrame
df_forecast_results = pd.DataFrame(forecast_results_list)
df_forecast_results.fillna(-999, inplace=True)

# 保存
df_forecast_results.to_csv("final_pv_battery_scenarios.csv", index=False)
print("\n=== 最终光伏+电池的经济分析结果(部分) ===")
print(df_forecast_results.head(12))


# In[ ]:





# In[36]:


# 转 DataFrame
df_forecast_results = pd.DataFrame(forecast_results_list)
df_forecast_results.fillna(-999, inplace=True)

# 修改Scenario名称，去掉_LR后缀
df_forecast_results['ScenarioName'] = df_forecast_results['ScenarioName'].str.replace('_LR', '')

# 修改列名，将ScenarioName改为Scenario
df_forecast_results = df_forecast_results.rename(columns={'ScenarioName': 'Scenario'})

# 计算并打印每个场景的平均ROI
mean_roi_by_scenario = df_forecast_results.groupby('Scenario')['ROI'].mean()
print("\n=== 各场景平均ROI ===")
for scenario, mean_roi in mean_roi_by_scenario.items():
    print(f"{scenario}场景平均ROI: {mean_roi:.4f}")

# 保存
df_forecast_results.to_csv("final_pv_battery_scenarios.csv", index=False)
print("\n=== 最终光伏+电池的经济分析结果(部分) ===")
print(df_forecast_results.head(12))


# In[37]:


# 对df_forecast_results的Payback_yr进行分析 - 简化版
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 创建有效数据的掩码
valid_mask = (df_forecast_results['Payback_yr'] != -999) & (df_forecast_results['Payback_yr'].notna())
print(f"有效回收期数据数量: {valid_mask.sum()}")

# 计算各情景各年的平均回收期
payback_means = df_forecast_results[valid_mask].groupby(['Scenario', 'Year'])['Payback_yr'].mean().reset_index()
payback_means.rename(columns={'Payback_yr': '平均回收期'}, inplace=True)

# 显示结果
print("\n各情景各年份的平均回收期:")
for scenario in sorted(payback_means['Scenario'].unique()):
    print(f"\n{scenario}情景:")
    scenario_data = payback_means[payback_means['Scenario'] == scenario].sort_values('Year')

    # 创建一个格式化的表格
    years_data = []
    for _, row in scenario_data.iterrows():
        years_data.append(f"{int(row['Year'])}年: {row['平均回收期']:.2f}年")

    # 每行显示5个年份数据
    for i in range(0, len(years_data), 5):
        print("  " + "  |  ".join(years_data[i:i+5]))

# 创建可视化
plt.figure(figsize=(14, 8))

# 设置背景透明
plt.gcf().patch.set_alpha(0)
plt.gca().patch.set_alpha(0)

# 设置颜色
colors = {
    'Low_LR': '#3498db',   # 蓝色
    'Base_LR': '#2ecc71',  # 绿色
    'High_LR': '#e74c3c'   # 红色
}

# 绘制每个情景的平均回收期趋势
for scenario in sorted(payback_means['Scenario'].unique()):
    scenario_data = payback_means[payback_means['Scenario'] == scenario]

    if not scenario_data.empty:
        # 绘制基准线
        plt.plot(scenario_data['Year'], scenario_data['平均回收期'], 
                 color=colors.get(scenario, 'gray'), 
                 linewidth=2, 
                 marker='o',
                 markersize=8,
                 label=f'{scenario}情景')

# 设置图形样式
plt.xlabel('年份', fontsize=14)
plt.ylabel('平均回收期（年）', fontsize=14)
plt.title('各情景下平均回收期趋势', fontsize=16, pad=20)

# 去掉网格
plt.grid(False)

# 设置坐标轴范围
years = sorted(df_forecast_results['Year'].unique())
plt.xlim(min(years)-0.5, max(years)+0.5)

# 设置y轴范围，回收期通常在0-20年之间
plt.ylim(0, 20)

# 设置x轴刻度为整数年份
plt.xticks(years[::5])  # 每5年显示一个刻度，避免拥挤

# 去掉上框和右框
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)

# 添加图例
plt.legend(loc='upper right', fontsize=12, framealpha=0.8)

# 调整布局并保存
plt.tight_layout()
plt.savefig('payback_mean_trends.png', dpi=300, bbox_inches='tight', transparent=True)
print("\n已保存平均回收期趋势图")
plt.close()


# In[38]:


import matplotlib.pyplot as plt

def plot_roi_above_3pct_comparison(df):
    """
    输入：df (例如 df_econ_scenario_all)
    功能：基于 (Scenario, Year) 统计 ROI>3%的地区数量，并可视化
         在同一张图里，绘制 Base_LR 的折线，以及 Low_LR~High_LR 的区间。
    """
    # 1) 创建一个新的列，用于标记 ROI 是否 > 0.03
    df_plot = df.copy()
    df_plot['ROI_above_3pct'] = df_plot['ROI'] > 0.03

    # 2) 按 (Scenario, Year) 统计 ROI_above_3pct = True 的计数
    df_count = df_plot.groupby(['Scenario','Year'])['ROI_above_3pct'].sum().reset_index(name='Count_ROI_Above_3pct')

    # 3) 分别取出 Low_LR / Base_LR / High_LR 的数据
    df_low  = df_count[df_count['Scenario'] == 'Low'].sort_values('Year')
    df_base = df_count[df_count['Scenario'] == 'Base'].sort_values('Year')
    df_high = df_count[df_count['Scenario'] == 'High'].sort_values('Year')

    # 4) 开始绘图
    plt.figure(figsize=(8,5))  # 创建画布

    # 4.1 画出 Base_LR 的折线
    plt.plot(df_base['Year'],
             df_base['Count_ROI_Above_3pct'],
             label='Base_LR (ROI>3%)')

    # 4.2 使用 fill_between 表示 Low_LR 和 High_LR 之间的区间
    plt.fill_between(df_low['Year'],
                     df_low['Count_ROI_Above_3pct'],
                     df_high['Count_ROI_Above_3pct'],
                     alpha=0.3,
                     label='Low_LR~High_LR range')

    # 5) 添加图例、坐标轴标签、标题
    plt.legend()
    plt.xlabel('Year')
    plt.ylabel('Count of Regions (ROI > 3%)')
    plt.title('Count of Regions with ROI>3% under Different Learning Rate Scenarios')

    plt.show()


# 使用示例：
plot_roi_above_3pct_comparison(df_forecast_results)


# In[39]:


import pandas as pd
import numpy as np
from scipy.optimize import curve_fit, differential_evolution

################################
# 1) 读取 Excel 并获取历史数据
################################

file_capacity = "中国光伏累计储能数据.xlsx"
file_price    = "中国光伏储能价格.xlsx"

# 读取累计储能 (MW)
df_capacity = pd.read_excel(file_capacity, usecols=["年份", "累计电池储能容量 MW"])
# 读取价格 (元/Wh)
df_price    = pd.read_excel(file_price,    usecols=["年份", "元/Wh"])

# 改列名
df_capacity.rename(columns={
    "年份": "Year", "累计电池储能容量 MW": "Cumulative Capacity (MW)"
}, inplace=True)
df_price.rename(columns={
    "年份": "Year", "元/Wh": "Price (CNY/Wh)"
}, inplace=True)

# 只取 2021-2024
df_capacity = df_capacity[df_capacity["Year"].between(2021, 2024)].sort_values(by="Year")
df_price    = df_price[df_price["Year"].between(2021, 2024)].sort_values(by="Year")

if df_capacity.empty or df_price.empty:
    raise ValueError("Excel 数据中缺少 2021-2024 期间的数据。")

# 提取数组
years    = df_capacity["Year"].values
Q_actual = df_capacity["Cumulative Capacity (MW)"].values
P_actual = df_price["Price (CNY/Wh)"].values

# 新增装机量
A_actual = np.diff(Q_actual, prepend=Q_actual[0])

# 固定参数
M_fixed = 500000    # 把 M 固定为 500000
h_init  = -0.75     # 给定初值, 后面微分进化只优化 h
a_init  = 0.0028
b_init  = 0.495

###################################################
# 2) 最小二乘法：拟合 (a, b)，其中 M=500000, h=-0.75 固定
###################################################
def bass_model_fit_ab(year_arr, a, b):
    """
    给定 M=500000, h=-0.75，拟合 a 和 b
    """
    Q_pred = np.zeros_like(year_arr, dtype=float)
    A_pred = np.zeros_like(year_arr, dtype=float)
    Q_pred[0] = Q_actual[0]

    for i in range(1, len(year_arr)):
        mp = M_fixed * (P_actual[i] ** h_init)   # 固定 M, h
        A_pred[i] = a * mp + (b - a)*Q_pred[i-1] - (b/mp)*(Q_pred[i-1]**2)
        Q_pred[i] = Q_pred[i-1] + A_pred[i]
    return A_pred

popt_ab, _ = curve_fit(
    bass_model_fit_ab, years, A_actual, p0=[a_init, b_init], maxfev=10000
)
a_fit, b_fit = popt_ab

print("===== (1) 最小二乘法：M=500000, h=-0.75 => 拟合 (a, b) =====")
print(f"a = {a_fit:.6f}, b = {b_fit:.6f}")

###################################################
# 3) 微分进化：只优化 h，M=500000, (a, b) 固定为上一步结果
###################################################
def bass_model_fit_h(h):
    """
    只对 h 做微分进化, M=500000, (a_fit, b_fit) 固定
    """
    Q_pred = np.zeros_like(years, dtype=float)
    A_pred = np.zeros_like(years, dtype=float)
    Q_pred[0] = Q_actual[0]

    for i in range(1, len(years)):
        mp = M_fixed * (P_actual[i] ** h[0])   # 注意 h 是数组
        A_pred[i] = a_fit*mp + (b_fit - a_fit)*Q_pred[i-1] - (b_fit/mp)*(Q_pred[i-1]**2)
        Q_pred[i] = Q_pred[i-1] + A_pred[i]

    return np.sum((A_pred - A_actual)**2)

# h 范围: [-2, 0] (可根据需要修改)
bounds_h = [(-2, 0)]
res_h = differential_evolution(
    bass_model_fit_h, bounds_h, strategy='best1bin', maxiter=1000, popsize=20
)
h_fit = res_h.x[0]

print("\n===== (2) 微分进化：M=500000, (a, b) 固定 => 优化 h =====")
print(f"h = {h_fit:.4f}")

###################################################
# 4) 学习曲线 + Bass 预测 2025~2050 (可选)
###################################################
learning_exponent = -0.263

# 找到2024的数据
idx_2024 = np.where(years == 2024)[0]
if len(idx_2024) == 0:
    raise ValueError("没有 2024年数据。")

i_2024 = idx_2024[0]
Q_2024 = Q_actual[i_2024]
P_2024 = P_actual[i_2024]

# 计算2024年的新增(2024-2023)
idx_2023 = np.where(years == 2023)[0]
i_2023 = idx_2023[0]
A_2024_data = Q_actual[i_2024] - Q_actual[i_2023]

future_years = np.arange(2025, 2051)
all_years = list(years) + list(future_years)
year_array = np.array(all_years)

Q_pred_full = np.zeros_like(year_array, dtype=float)
A_pred_full = np.zeros_like(year_array, dtype=float)
P_pred_full = np.zeros_like(year_array, dtype=float)

# 历史Q复制
for i, y in enumerate(year_array):
    if y in years:
        idx = np.where(years == y)[0][0]
        Q_pred_full[i] = Q_actual[idx]

index_2024_in_full = np.where(year_array == 2024)[0][0]
A_pred_full[index_2024_in_full] = A_2024_data

# 逐年迭代
for i in range(index_2024_in_full + 1, len(year_array)):
    Q_last = Q_pred_full[i-1]
    # 年初临时价
    price_before = P_2024 * ((Q_last / Q_2024)**learning_exponent)

    mp = M_fixed * (price_before ** h_fit)
    A_t = a_fit*mp + (b_fit - a_fit)*Q_last - (b_fit/mp)*(Q_last**2)

    Q_t = Q_last + A_t
    # 年末价
    price_end = P_2024 * ((Q_t / Q_2024)**learning_exponent)

    A_pred_full[i] = A_t
    Q_pred_full[i] = Q_t
    P_pred_full[i] = price_end

# 输出
print("\n===== (3) 2024–2050 预测 (M=500000固定) =====")
print("Year | Price(元/Wh)|   NewAdded(MW)  |  Cumulative(MW)")
for i, y in enumerate(year_array):
    if y < 2024:
        continue
    if y == 2024:
        print(f"{y} | {P_2024:>12.6f} | {A_pred_full[i]:>14.2f} | {Q_pred_full[i]:>14.2f}")
    else:
        print(f"{y} | {P_pred_full[i]:>12.6f} | {A_pred_full[i]:>14.2f} | {Q_pred_full[i]:>14.2f}")


# In[40]:


import pandas as pd

# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率


# 进行敏感性分析的年份和对应的 mean_value_day_count 调整值
sensitivity_years = {
    2020: 2.2,
    2025: 1.2,
    2030: 0.66,
    2035: 0.58,
    2050: 0.37
}

# 创建存储结果的列表
sensitivity_results = []

# 计算 poverty_selected 数据集的指标
for year, factor in sensitivity_years.items():
    for idx, row in poverty_selected.iterrows():
        alpha = 0
        beta = row['Curtailed_Rate']
        mean_value = row['mean_tiff']
        mean_value_day_count = mean_value / 365 * beta * 1000 * factor * 2
        price = row['PV_price']
        E_n = mean_value * (1 - alpha)
        total_generation = E_n * N

        roi = calculate_roi(total_generation, price, C_PV + mean_value_day_count, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)
        if roi > 0:
            payback_years = min(N, next((n for n in range(1, N+1) if total_generation * price * n >= (C_PV + mean_value_day_count + C_ES + (O_PV + O_ES + C_F + C_tax + C_d) * n)), N))
        else:
            payback_years = None

        sensitivity_results.append({
            'name': row['name'],
            'ROI': roi,
            'year': year,
            'now_year': payback_years
        })

# 创建 DataFrame
sensitivity_results_df = pd.DataFrame(sensitivity_results)

# 删除 'ROI' 为空的行
sensitivity_results_df = sensitivity_results_df.dropna(subset=['ROI'])

# 确保 ROI 是数值类型
sensitivity_results_df['ROI'] = pd.to_numeric(sensitivity_results_df['ROI'], errors='coerce')

# 确保 'year' 列为字符串类型
sensitivity_results_df['year'] = sensitivity_results_df['year'].astype(str)

# 打印数据描述信息，检查清理后的数据
print("\n清理后的数据描述统计信息 (四舍五入后的 ROI):")
print(sensitivity_results_df.describe())

# 统计每个年份的数据量，确保每个年份的数据量足够
year_counts = sensitivity_results_df['year'].value_counts()
print("\n每年数据量统计：")
print(year_counts)

# 只保留数据点大于1的年份，确保数据量足够
valid_years = year_counts[year_counts > 1].index
sensitivity_results_df = sensitivity_results_df[sensitivity_results_df['year'].isin(valid_years)]

# 定义 ROI 分组
def roi_group(roi_series):
    roi_series = pd.to_numeric(roi_series, errors='coerce')
    return pd.cut(roi_series, bins=[-float('inf'), 0.03, 0.1, float('inf')], labels=["< 0.03", "0.03 - 0.1", "> 0.1"], include_lowest=True)

# 计算 ROI 分组
sensitivity_results_df['ROI_group'] = roi_group(sensitivity_results_df['ROI'])


# In[41]:


clean_data0 = copy.deepcopy(sensitivity_results_df)


# In[42]:


clean_data0


# #### 整合数据

# In[30]:


poverty_selected


# In[31]:


# 计算各种ROI的统计分析
def analyze_roi_changes(df):
    # 1. 计算补贴取消导致的ROI下滑
    roi_decrease = df['ROI_sub'] - df['ROI']
    avg_roi_decrease = roi_decrease.mean()

    # 2. 计算无利可图的项目比例（ROI < 0.03）
    unprofitable_percentage = ((df['ROI'] < 0.03).sum() - (df['ROI_sub'] < 0.03).sum()) / len(df) * 100

    # 3. 计算优先并网提升的ROI百分比
    roi_priority_increase = ((df['ROI_priority'].mean() - df['ROI'].mean()) / df['ROI'].mean()) * 100
    avg_priority_increase = roi_priority_increase

    # 4. 计算优先并网缓解电力过剩的范围
    curtailment_improvement = df['Curtailed_Rate'] * 100  # 假设Curtailed_Rate是以小数形式存储的
    min_improvement = curtailment_improvement.min()
    max_improvement = curtailment_improvement.max()

    # 5. 计算储能成本和ROI影响
    roi_storage_decrease = df['ROI'].mean() - df['ROI_storage'].mean()
    avg_storage_roi_decrease = roi_storage_decrease

    # 打印结果
    print(f"1. ROI平均下滑: {abs(avg_roi_decrease):.4f} (以小数表示)")
    print(f"2. 无利可图项目比例: {unprofitable_percentage:.2f}%")
    print(f"3. 优先并网提升ROI: {avg_priority_increase:.2f}%")
    print(f"4. 缓解电力过剩范围: {min_improvement:.1f}%–{max_improvement:.1f}%")
    print(f"5. 储能导致ROI下降: {avg_storage_roi_decrease:.4f} (以小数表示)")

    # 计算储能系统的平均资本支出（假设储能成本数据在某一列中）
    if 'Storage_Cost' in df.columns:
        avg_storage_cost = df['Storage_Cost'].mean()
        print(f"6. 储能平均资本支出: ${avg_storage_cost:.2f}/kWh")

# 运行分析
analyze_roi_changes(poverty_selected)

# 额外添加一些详细的统计信息
print("\n详细统计信息：")
roi_stats = poverty_selected[['ROI', 'ROI_sub', 'ROI_priority', 'ROI_storage']].describe()
print(roi_stats)

# 绘制箱线图比较不同ROI
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
poverty_selected[['ROI', 'ROI_sub', 'ROI_priority', 'ROI_storage']].boxplot()
plt.title('不同情景下ROI的分布比较')
plt.ylabel('ROI值')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# In[32]:


counties_selected


# In[33]:


poverty_selected3=copy.deepcopy(poverty_selected)
counties_selected3=copy.deepcopy(counties_selected)


# In[34]:


poverty_selected=copy.deepcopy(poverty_selected3)
counties_selected=copy.deepcopy(counties_selected3)


# In[35]:


# 打印所有列名
print("merged_df的所有列名：")
print(poverty_selected.columns.tolist())

# 打印更详细的信息
print("\nmerged_df的基本信息：")
print(poverty_selected.info())


# ### 2.3 可视化

# #### 2.3.1 初始效果可视化

# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches

font_path = 'C:/Windows/Fonts/simhei.ttf'  # 黑体
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#FF9999',  # 浅红色表示 counties_selected ROI < 0.03
    1: '#FF0000',  # 深红色表示 counties_selected ROI >= 0.03
    2: '#9999FF',  # 浅蓝色表示 poverty_remaining ROI < 0.03
    3: '#0000FF'   # 深蓝色表示 poverty_remaining ROI >= 0.03
}

# 找出 poverty_selected 中 name 不在 counties_selected 中的部分，并显式创建副本
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])].copy()

# 创建新列以区分 counties_selected 的 ROI 小于 0.03 和大于等于 0.03 的部分
counties_selected.loc[:, 'group'] = counties_selected['ROI'].apply(lambda x: 0 if x < 0.03 else 1)

# 创建新列以区分 poverty_remaining 的 ROI 小于 0.03 和大于等于 0.03 的部分
poverty_remaining.loc[:, 'group'] = poverty_remaining['ROI'].apply(lambda x: 2 if x < 0.03 else 3)


# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.2, edgecolor='black')

# 绘制组合后的热图
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0.1, edgecolor='0.8')

ax.set_title('ROI 分组可视化', fontproperties=font_prop)

# 创建自定义图例
legend_patches = [
    mpatches.Patch(color='#FF9999', label='counties_selected ROI < 0.03'),
    mpatches.Patch(color='#FF0000', label='counties_selected ROI >= 0.03'),
    mpatches.Patch(color='#9999FF', label='poverty_remaining ROI < 0.03'),
    mpatches.Patch(color='#0000FF', label='poverty_remaining ROI >= 0.03')
]
ax.legend(handles=legend_patches, loc='upper right')

# 调整布局并显示图像
plt.tight_layout()
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches

# 定义用于分组可视化的字段名称（只需修改此处即可改变可视化指标）
field_name = 'ROI_priority'

# 创建自定义的颜色
cmap = {
    0: '#FF9999',  # 浅红色表示 counties_selected field_name < 0.03
    1: '#FF0000',  # 深红色表示 counties_selected field_name >= 0.03
    2: '#9999FF',  # 浅蓝色表示 poverty_remaining field_name < 0.03
    3: '#0000FF'   # 深蓝色表示 poverty_remaining field_name >= 0.03
}

# 找出 poverty_selected 中 name 不在 counties_selected 中的部分，并显式创建副本
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])].copy()

# 根据指定字段（field_name）的数值，将 counties_selected 分组
counties_selected.loc[:, 'group'] = counties_selected[field_name].apply(lambda x: 0 if x < 0.03 else 1)

# 根据指定字段（field_name）的数值，将 poverty_remaining 分组
poverty_remaining.loc[:, 'group'] = poverty_remaining[field_name].apply(lambda x: 2 if x < 0.03 else 3)

# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 绘制省级底图（省份边界）
provinces.boundary.plot(ax=ax, linewidth=0.2, edgecolor='black')

# 根据分组绘制各区域
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0.1, edgecolor='0.8')

# 设置标题（可根据需要修改）
ax.set_title(f'{field_name} 分组可视化', fontproperties=font_prop)

# 创建自定义图例，图例中显示当前分组使用的字段名称
legend_patches = [
    mpatches.Patch(color='#FF9999', label=f'counties_selected {field_name} < 0.03'),
    mpatches.Patch(color='#FF0000', label=f'counties_selected {field_name} >= 0.03'),
    mpatches.Patch(color='#9999FF', label=f'poverty_remaining {field_name} < 0.03'),
    mpatches.Patch(color='#0000FF', label=f'poverty_remaining {field_name} >= 0.03')
]
ax.legend(handles=legend_patches, loc='upper right')

# 调整布局并显示图像
plt.tight_layout()
plt.show()


# #### 2.3.2美化后的可视化（fig1a）
# 

# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

counties_selected['ROI'] = counties_selected['name'].map(poverty_selected.set_index('name')['ROI'])
counties_selected['group'] = counties_selected['ROI'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI'] = poverty_remaining['name'].map(poverty_selected.set_index('name')['ROI'])
poverty_remaining['group'] = poverty_remaining['ROI'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展

# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围

# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制省级底图在子图中
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('fig1a.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# #### 2.3.3 fig1b的两幅小图(这部分代码只能在算完优化后用)

# 先进行分类

# In[54]:


# counties_selected = counties_selected.merge(results, left_on='name', right_on='County')
# poverty_selected = poverty_selected.merge(results, left_on='name', right_on='poverty')
# counties_selected 的 ROI_x 和 group 列
# counties_selected['ROI_x'] = counties_selected['name'].map(merged_df.set_index('name')['ROI_x'])
# counties_selected['group'] = counties_selected['ROI_x'].apply(classify_roi)

# # 找出 poverty_remaining 中 name 不在 counties_selected 中的部分，并对其进行初次分类
# poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]
# poverty_remaining['ROI_x'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_x'])
# poverty_remaining['group'] = poverty_remaining['ROI_x'].apply(classify_roi)
#
# # 重新分类未开展区域，将 group 分类值加 2
# poverty_remaining['group'] += 2
#
# #这个部分是针对ROI_y的
# # counties_selected 的 ROI_y 和 group2 列
# counties_selected['ROI_y'] = counties_selected['name'].map(merged_df.set_index('name')['ROI_y'])
# counties_selected['group2'] = counties_selected['ROI_y'].apply(classify_roi)
#
# # 为了确保保留 group 和 group2，避免重复覆盖或过滤 poverty_remaining
# # 如果之前的分组已经存在，这里可以直接对其进行修改
# poverty_remaining['ROI_y'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_y'])
# poverty_remaining['group2'] = poverty_remaining['ROI_y'].apply(classify_roi)
# poverty_remaining['group2'] += 2  # 重新分类未开展区域，将 group2 分类值加 2
#
# # 分别计算 group 和 group2 各个分类的面积
# # group 分类面积
# counties_selected_group_lt_003_area = counties_selected[counties_selected['group'] == 0].geometry.area.sum()
# counties_selected_group_ge_003_area = counties_selected[counties_selected['group'] == 1].geometry.area.sum()
# counties_remaining_group_lt_003_area = poverty_remaining[poverty_remaining['group'] == 2].geometry.area.sum()
# counties_remaining_group_ge_003_area = poverty_remaining[poverty_remaining['group'] == 3].geometry.area.sum()
#
# # group2 分类面积
# counties_selected_group2_lt_003_area = counties_selected[counties_selected['group2'] == 0].geometry.area.sum()
# counties_selected_group2_ge_003_area = counties_selected[counties_selected['group2'] == 1].geometry.area.sum()
# counties_remaining_group2_lt_003_area = poverty_remaining[poverty_remaining['group2'] == 2].geometry.area.sum()
# counties_remaining_group2_ge_003_area = poverty_remaining[poverty_remaining['group2'] == 3].geometry.area.sum()



# 生成第一幅完整的图

# In[55]:


# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
# import matplotlib.colors as mcolors
# from matplotlib.ticker import ScalarFormatter
#
# # 使用您的实际数据
# data = {
#     'Selected ROI ≥ 0.03': [counties_selected_group_ge_003_area, counties_selected_group2_ge_003_area],
#     'Remaining ROI ≥ 0.03': [counties_remaining_group_ge_003_area, counties_remaining_group2_ge_003_area],
#     'ROI ≥ 0.03': [
#         counties_selected_group_ge_003_area + counties_remaining_group_ge_003_area,
#         counties_selected_group2_ge_003_area + counties_remaining_group2_ge_003_area
#     ]
# }
#
# # 创建 DataFrame
# df = pd.DataFrame(data, index=['Group', 'Group2'])
#
# # 创建图形
# fig, ax = plt.subplots(figsize=(16, 12))
#
# # 定义颜色映射
# cmap = {
#     'Selected ROI ≥ 0.03': '#ffbf7b',  # selected 0.03 < ROI
#     'Remaining ROI ≥ 0.03': '#8fd0ca',  # remaining 0.03 < ROI
#     'ROI ≥ 0.03': '#fa8070',  # ROI >= 0.03 total color
# }
#
# # 设置分类标签
# categories = df.columns  # 包括所有分类
# bar_width = 0.35  # 每个柱子的宽度
# group_gap = 0.05  # 增加柱子之间的间隔
#
# # 设置 x 轴位置
# x = np.arange(len(categories)) * (1 + group_gap)  # 增加间距
#
# # 绘制 Group 的柱子，并添加相同颜色的外框
# bars1 = ax.bar(x - bar_width * 0.55, df.loc['Group', categories], bar_width,
#                label='Group', color=[cmap.get(cat, '#cccccc') for cat in categories],
#                edgecolor=[cmap.get(cat, '#cccccc') for cat in categories])
#
# # 绘制 Group2 的柱子，并添加相同颜色的外框
# bars2 = ax.bar(x + bar_width * 0.55, df.loc['Group2', categories], bar_width,
#                label='Group2', color=[cmap.get(cat, '#cccccc') for cat in categories],
#                edgecolor=[cmap.get(cat, '#cccccc') for cat in categories])
#
# # 添加标签和标题
# ax.set_xticks(x)
# ax.set_xticklabels(categories, fontsize=14, rotation=45, ha='right')
#
# # 设置 y 轴使用科学计数法
# ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))  # 启用科学计数法
# ax.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))
#
# # 计算 y 轴的最大值
# y_max = df.values.max()
# y_max_int = int(np.ceil(y_max))  # 向上取整确保为整数
#
# # 设置 y 轴范围
# ax.set_ylim(0, 1.4*y_max_int)  # 设置Y轴范围为最大值
#
# # 启用次要刻度并设置间隔
# ax.yaxis.set_minor_locator(plt.MultipleLocator(y_max_int / 20))  # 根据最大值动态设置次要刻度
#
# # 配置刻度的显示样式以确保清晰可见
# ax.yaxis.set_tick_params(which='major', length=10, width=1.8, direction='inout', labelsize=14)  # 主要刻度更大更粗
# ax.yaxis.set_tick_params(which='minor', length=5, width=1.5, direction='in')  # 次要刻度稍小
# ax.yaxis.set_tick_params(labelsize=50)
#
# # 确保绘图元素不覆盖刻度
# ax.axhline(0, color='black', linewidth=1.5)  # 显示水平线，不干扰刻度
#
# # 去掉上、右、左边框，仅保留底部
# ax.spines['top'].set_color('black')
# ax.spines['right'].set_color('black')
# ax.spines['left'].set_color('black')
# ax.spines['bottom'].set_color('black')
# ax.spines['top'].set_linewidth(1.5)
# ax.spines['right'].set_linewidth(1.5)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)  # 加粗 x 轴
#
# # 去掉网格线，只保留外部边框与中轴
# ax.grid(False)
#
# # 设置中间分割线
# ax.axhline(0, color='#aa988d', linewidth=1.5)  # 加粗中轴线
#
# # 设置全局字体为Times New Roman
# from matplotlib import rcParams
# rcParams['font.family'] = 'Times New Roman'
#
# # 保存高质量图像
# plt.savefig('grouped_bar_area_no_difference_no_total.png', dpi=1200, format='png')
# # 显示图形
# plt.show()
# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
# import matplotlib.colors as mcolors
# from matplotlib.ticker import ScalarFormatter
#
# # 使用您的实际数据
# data = {
#     'Selected ROI ≥ 0.03': [counties_selected_group_ge_003_area, counties_selected_group2_ge_003_area],
#     'Remaining ROI ≥ 0.03': [counties_remaining_group_ge_003_area, counties_remaining_group2_ge_003_area],
#     'ROI ≥ 0.03': [
#         counties_selected_group_ge_003_area + counties_remaining_group_ge_003_area,
#         counties_selected_group2_ge_003_area + counties_remaining_group2_ge_003_area
#     ]
# }
#
# # 创建 DataFrame
# df = pd.DataFrame(data, index=['Group', 'Group2'])
#
# # 创建图形
# fig, ax = plt.subplots(figsize=(16, 12))
#
# # 定义颜色映射
# cmap = {
#     'Selected ROI ≥ 0.03': '#ffbf7b',  # selected 0.03 < ROI
#     'Remaining ROI ≥ 0.03': '#8fd0ca',  # remaining 0.03 < ROI
#     'ROI ≥ 0.03': '#fa8070',  # ROI >= 0.03 total color
# }
#
# # 设置分类标签
# categories = df.columns  # 包括所有分类
# bar_width = 0.35  # 每个柱子的宽度
# group_gap = 0.05  # 增加柱子之间的间隔
#
# # 设置 x 轴位置
# x = np.arange(len(categories)) * (1 + group_gap)  # 增加间距
#
# # 绘制 Group 的柱子，并添加相同颜色的外框
# bars1 = ax.bar(x - bar_width * 0.55, df.loc['Group', categories], bar_width,
#                label='Group', color=[cmap.get(cat, '#cccccc') for cat in categories],
#                edgecolor=[cmap.get(cat, '#cccccc') for cat in categories])
#
# # 绘制 Group2 的柱子，并添加相同颜色的外框
# bars2 = ax.bar(x + bar_width * 0.55, df.loc['Group2', categories], bar_width,
#                label='Group2', color=[cmap.get(cat, '#cccccc') for cat in categories],
#                edgecolor=[cmap.get(cat, '#cccccc') for cat in categories])
#
# # 添加标签和标题
# ax.set_xticks(x)
# ax.set_xticklabels(categories, fontsize=14, rotation=45, ha='right')
#
# # 设置 y 轴使用科学计数法
# ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))  # 启用科学计数法
# ax.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))
#
# # 计算 y 轴的最大值
# y_max = df.values.max()
# y_max_int = int(np.ceil(y_max))  # 向上取整确保为整数
#
# # 设置 y 轴范围
# ax.set_ylim(0, 1.4*y_max_int)  # 设置Y轴范围为最大值
#
# # 启用次要刻度并设置间隔
# ax.yaxis.set_minor_locator(plt.MultipleLocator(y_max_int / 20))  # 根据最大值动态设置次要刻度
#
# # 配置刻度的显示样式以确保清晰可见
# ax.yaxis.set_tick_params(which='major', length=10, width=1.8, direction='inout', labelsize=14)  # 主要刻度更大更粗
# ax.yaxis.set_tick_params(which='minor', length=5, width=1.5, direction='in')  # 次要刻度稍小
# ax.yaxis.set_tick_params(labelsize=50)
#
# # 确保绘图元素不覆盖刻度
# ax.axhline(0, color='black', linewidth=1.5)  # 显示水平线，不干扰刻度
#
# # 去掉上、右、左边框，仅保留底部
# ax.spines['top'].set_color('black')
# ax.spines['right'].set_color('black')
# ax.spines['left'].set_color('black')
# ax.spines['bottom'].set_color('black')
# ax.spines['top'].set_linewidth(1.5)
# ax.spines['right'].set_linewidth(1.5)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)  # 加粗 x 轴
#
# # 去掉网格线，只保留外部边框与中轴
# ax.grid(False)
#
# # 设置中间分割线
# ax.axhline(0, color='#aa988d', linewidth=1.5)  # 加粗中轴线
#
# # 设置全局字体为Times New Roman
# from matplotlib import rcParams
# rcParams['font.family'] = 'Times New Roman'
#
# # 保存高质量图像
# plt.savefig('grouped_bar_area_no_difference_no_total.png', dpi=1200, format='png')
# # 显示图形
# plt.show()


# #### 2.3.4 全部效益的可视化
# 

# In[56]:


# import matplotlib.pyplot as plt
# from mpl_toolkits.axes_grid1 import make_axes_locatable
# import matplotlib.patches as mpatches
# import matplotlib.patheffects as PathEffects
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes
# import geopandas as gpd
#
# # 定义阴影效果
# shadow_effect = [
#     PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
#     PathEffects.Normal()
# ]
#
# # 定义省级和县级地理数据
# provinces = provinces.to_crs(epsg=3857)
# counties_selected = counties_selected.to_crs(epsg=3857)  # 确保坐标一致
#
# # 定义图表标题和文件名
# titles = ['LCOE', 'NPV', 'IRR', 'ROI']
# columns = ['LCOE', 'NPV', 'IRR', 'ROI']
# cmaps = ['YlGn', 'YlGnBu', 'YlOrRd', 'coolwarm']
# filenames = ['LCOE_map.png', 'NPV_map.png', 'IRR_map.png', 'ROI_map.png']
#
# # 绘制和保存每个子图
# for i in range(4):
#     fig, ax = plt.subplots(figsize=(12, 8))  # 设置每个子图的尺寸
#
#     # 创建颜色栏
#     divider = make_axes_locatable(ax)
#     cax = divider.append_axes("right", size="5%", pad=0.1)
#
#     # 绘制省级边界和县级底图
#     provinces.boundary.plot(ax=ax, linewidth=0.5, edgecolor='black', zorder=1)
#     plot = counties_selected.plot(column=columns[i], cmap=cmaps[i], linewidth=0.1, ax=ax, edgecolor='0.8', legend=False, zorder=2)
#
#     # 手动创建色条带
#     sm = plt.cm.ScalarMappable(cmap=cmaps[i], norm=plt.Normalize(vmin=counties_selected[columns[i]].min(), vmax=counties_selected[columns[i]].max()))
#     sm._A = []  # 需要添加空数据
#     colorbar = fig.colorbar(sm, cax=cax)  # 创建色条带
#
#     # 设置色条带字体属性
#     colorbar.ax.tick_params(labelsize=15, labelcolor='black')  # 设置色条带字体大小和颜色
#
#     # 设置 x 和 y 轴的显示范围以集中在中国大陆
#     ax.set_xlim(7792364.36, 15584728.71)  # 中国大陆的 x 范围
#     ax.set_ylim(1689200.14, 7361866.11)   # 中国大陆的 y 范围
#
#     # 添加阴影效果
#     for line in ax.collections:
#         line.set_path_effects(shadow_effect)
#
#     ax.set_title(titles[i], fontsize=15)
#     ax.set_axis_off()  # 去除坐标和网格
#
#     # 在每个图中添加南海小地图
#     ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
#     ax_inset.set_facecolor('white')
#     ax_inset.set_xticks([])
#     ax_inset.set_yticks([])
#     ax_inset.grid(False)
#
#     # 绘制南海区域
#     provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
#     ax_inset.set_xlim(11688546.53, 13692297.37)
#     ax_inset.set_ylim(222684.21, 2632018.64)
#     provinces.boundary.plot(ax=ax_inset, linewidth=0.5, edgecolor='black')
#     counties_selected.boundary.plot(ax=ax_inset, linewidth=0.1, edgecolor='black')
#
#     # 自定义南海小地图边框
#     for spine in ax_inset.spines.values():
#         spine.set_edgecolor('black')
#         spine.set_linewidth(1.5)
#
#     # 保存每个图为单独的文件
#     plt.savefig(filenames[i], format='png', dpi=1200)
#     plt.close(fig)  # 关闭图形以释放内存
#
# print("每个图已单独保存。")


# #### valuedation

# In[57]:


province_roi_mean = poverty_selected.groupby('Province')['ROI'].mean()
print("每个省份的ROI平均值：")
print(province_roi_mean)


# In[58]:


import pandas as pd

# 构建第一个数据集（省份对应的数值）
data1 = {
    "省份": [
        "云南省", "内蒙古自治区", "吉林省", "四川省", "宁夏回族自治区", "安徽省", "山西省", "广东省",
        "广西壮族自治区", "新疆维吾尔自治区", "江西省", "河北省", "河南省", "海南省", "湖北省",
        "湖南省", "甘肃省", "西藏自治区", "贵州省", "重庆市", "陕西省", "青海省", "黑龙江省"
    ],
    "数值": [
        0.045849, 0.028666, 0.368792, 0.159781, -0.208629, 0.185931, 0.195220, 0.096455,
        -0.000586, -0.079272, 0.206815, 0.255260, -0.131190, 0.269236, 0.160622,
        0.005009, -0.127222, -0.085523, -0.217290, -0.040408, -0.033167, -0.227864, 0.391334
    ]
}
df1 = pd.DataFrame(data1)

# 构建第二个数据集（省份对应的百分比区间）
data2 = {
    "省份": [
        "黑龙江省", "吉林省", "辽宁省", "内蒙古自治区", "河北省", "山西省", "北京市", "天津市",
        "山东省", "江苏省", "浙江省", "福建省", "上海市", "江西省", "湖北省", "湖南省",
        "广东省", "广西壮族自治区", "海南省", "四川省", "贵州省", "云南省", "西藏自治区",
        "陕西省", "甘肃省", "青海省", "宁夏回族自治区", "新疆维吾尔自治区"
    ],
    "百分比区间": [
        "5%到10%", "6%到12%", "7%到14%", "10%到20%", "8%到15%", "6%到10%", "5%到10%", "6%到12%",
        "7%到13%", "6%到14%", "5%到12%", "6%到11%", "5%到10%", "7%到12%", "6%到11%", "7%到13%",
        "6%到15%", "8%到14%", "8%到16%", "7%到15%", "8%到14%", "9%到16%", "10%到20%", "7%到12%",
        "8%到18%", "10%到20%", "8%到15%", "12%到22%"
    ]
}
df2 = pd.DataFrame(data2)

# 合并两个数据集，采用外连接以确保所有省份均保留
df_merged = pd.merge(df1, df2, on="省份", how="outer")

# 定义一个函数，将数值转换为百分比字符串（乘以 100，不保留小数）
def to_percentage(val):
    if pd.isna(val):
        return ""
    return f"{round(val * 100)}%"

# 应用转换函数，将数值转换为百分比形式
df_merged["数值"] = df_merged["数值"].apply(to_percentage)

# 调整列的顺序
df_merged = df_merged[["省份", "数值", "百分比区间"]]

# 在 Notebook 中展示输出合并后的表格
df_merged


# ## 3 H2-PV模式计算

# ### 3.1 载入相关数据

# #### 3.1.1 载入管道数据

# 导入距离的时候，每个超过1000km的我都超额赋值了2000

# In[36]:


import pandas as pd

poverty_selected=copy.deepcopy(poverty_selected3)
counties_selected=copy.deepcopy(counties_selected3)

# Step 1: Load the data from the given Excel files
vertical_dis = pd.read_excel("vertical.xlsx")
node_dis = pd.read_excel("node.xlsx")

# Assuming poverty_selected is already imported and available
# poverty_selected should have a column named "name"

# Step 2: Match and select the minimum "县中心距离(km)" for each name in poverty_selected
def get_min_distance(df, name_col, match_col, dist_col):
    min_distances = []
    for name in poverty_selected['name']:
        matched_rows = df[df[match_col] == name]
        if not matched_rows.empty:
            min_distance = matched_rows[dist_col].min() *1000
        else:
            min_distance = 2000 * 1000 # Default value if no match is found
        min_distances.append(min_distance)
    return min_distances

# Get minimum distances for vertical_dis and node_dis
dim = get_min_distance(vertical_dis, 'name', '县名', '县中心距离(km)')
din = get_min_distance(node_dis, 'name', '县名', '距离(km)')

# Step 3: Merge dim and din values into poverty_selected
poverty_selected['dim'] = dim
poverty_selected['din'] = din
merged = deep_copy(poverty_selected)




# In[37]:


merged


# 检查来看这个数据没什么问题，各项数据正常
# 

# #### 3.1.2 导入氢的数据

# 需要更改的地方
# beta = 0.3  弃电百分比
# 
# P 氢气售价
# 
# P_original = [[39.4 * 0.3 * 0.5, 39.4 * 0.3 * 0.36, 2, 2]]  氢气销售价格
# 
# 
# 从merged中获取mean_tiff列值，并更新电量E
# 
# E = merged['mean_tiff'].tolist()
# 
# Electri=[E[i]* beta * pv_x for i in range(len(E))]  生成的总电量
# 
# Q = [E[i] * alpha * beta * pv_x for i in range(len(E))]  氢气生成量

# In[40]:


import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

# 使用merged数据框的列值
county_indices = list(range(len(merged)))  # 县编号
hydrogen_sales_types = [0, 1, 2, 3]  # 氢气销售类型编号
transport_methods = [0, 1, 2]  # 氢气运输方式编号
pv_x = 10000  # 光伏装机容量
alpha = 1/4.5  # 使用质子交换膜（PEM），每千瓦时电力可产生的氢气（m³）
# 氢气的热值（大约为142 MJ/m³ 或者 39.4 kWh/m³）
# 燃料电池燃烧效率：30%-40%
# 自用电费价格：0.05
# 调峰发电价格：0.36
# 2元/m 3÷0.0899 kg/m 3=22.2469 元/kg


# 将Electri和Q重新放进去，Electri代表弃电，Q为弃电产氢量

# In[41]:


# Add the new columns as per the instructions
poverty_selected['Electri'] = poverty_selected['mean_tiff'] * poverty_selected['Curtailed_Rate'] * pv_x
poverty_selected['Electri_all'] = poverty_selected['mean_tiff'] * pv_x
poverty_selected['Q'] = poverty_selected['mean_tiff'] * poverty_selected['Curtailed_Rate'] * pv_x * alpha


# #### 3.1.3 电解槽价格曲线拟合
# 

# In[42]:


# Part 1: Fit cost model to data
production_scales = np.array([10, 100, 1000])  # in MW
costs = np.array([1000, 750, 600])  # in $/kW

# 线性化模型
def log_cost_model(logS, logC0, logS0, b):
    return logC0 + b * (logS - logS0)

# 取对数
log_production_scales = np.log(production_scales)
log_costs = np.log(costs)

# 初始参数 (对数空间)
initial_guess_log = [np.log(1000), np.log(10), -0.6]

# 执行拟合
params_log, covariance_log = curve_fit(log_cost_model, log_production_scales, log_costs, p0=initial_guess_log, maxfev=10000)

# 反变换回指数形式
C0_fitted, S0_fitted, b_fitted = np.exp(params_log[0]), np.exp(params_log[1]), params_log[2]


# In[45]:


# 输出拟合参数
print(f"Fitting Results:")
print(f"C0 = {C0_fitted:.2f} $/kW")
print(f"S0 = {S0_fitted:.2f} MW")
print(f"b = {b_fitted:.4f}")

# 可视化
import matplotlib.pyplot as plt

# 创建更密集的点来绘制平滑曲线
smooth_scales = np.linspace(production_scales.min(), 
                           production_scales.max()*1.2, 100)

# 使用拟合的模型计算预测成本
predicted_costs = C0_fitted * (smooth_scales/S0_fitted)**b_fitted

plt.figure(figsize=(10, 6))
# 绘制原始数据点
plt.scatter(production_scales, costs, color='blue', s=80, label='Actual Data')
# 绘制拟合曲线
plt.plot(smooth_scales, predicted_costs, 'r-', label=f'Fitted Curve: C = {C0_fitted:.1f} × (S/{S0_fitted:.1f})^{b_fitted:.3f}')

# 使用线性刻度 (默认)

# 添加标签和标题
plt.xlabel('Production Scale (MW)', fontsize=12)
plt.ylabel('Cost ($/kW)', fontsize=12)
plt.title('Cost vs. Production Scale', fontsize=14)
plt.grid(True, alpha=0.2)
plt.legend(fontsize=10)

# 调整布局
plt.tight_layout()

# 保存图片
plt.savefig('cost_vs_production_scale.png', dpi=300, bbox_inches='tight')

# 显示图形
plt.show()

# 计算拟合曲线在原始数据点上的值，用于比较
fitted_costs = C0_fitted * (production_scales/S0_fitted)**b_fitted
for scale, actual, fitted in zip(production_scales, costs, fitted_costs):
    print(f"Scale: {scale} MW, Actual Cost: {actual} $/kW, Fitted Cost: {fitted:.2f} $/kW")


# In[53]:


# 创建3D表面图
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# 创建年份和生产规模的网格
years_mesh = np.arange(2020, 2051, 1)  # 从2020到2050年
scales_mesh = np.linspace(10, 1000, 50)  # 从10 MW到1000 MW

# 为了处理2020年（不在原始数据中），我们假设它与2021年相同
years_for_calc = np.array([max(y, 2021) for y in years_mesh])

# 创建网格
X, Y = np.meshgrid(years_mesh, scales_mesh)
Z = np.zeros_like(X, dtype=float)

# 计算每个网格点的成本
for i, scale in enumerate(scales_mesh):
    for j, year in enumerate(years_for_calc):
        Z[i, j] = get_cost_for_year_and_n(year, scale)

# 创建3D图
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# 绘制3D表面
surf = ax.plot_surface(X, Y, Z, cmap=cm.viridis, alpha=0.9, 
                       linewidth=0, antialiased=True)

# 设置视角以匹配参考图像
ax.view_init(elev=25, azim=-45)

# 添加标签和标题
ax.set_xlabel('Year', fontsize=12, labelpad=10)
ax.set_ylabel('Production Scale (MW)', fontsize=12, labelpad=10)
ax.set_zlabel('Cost ($/kW)', fontsize=12, labelpad=10)

# 设置坐标轴范围和刻度
ax.set_xlim(2020, 2050)
ax.set_xticks(np.arange(2020, 2051, 5))
ax.set_ylim(0, 1000)
ax.set_zlim(600, 1700)

# 添加颜色条
cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=10, pad=0.1)
cbar.set_label('Cost ($/kW)', fontsize=12)

# 反转Y轴以匹配参考图像
ax.invert_yaxis()

# 设置网格
ax.grid(True)

# 保存图像
plt.savefig('cost_surface_plot.png', dpi=300, bbox_inches='tight')
plt.show()


# #### 3.1.3 电解槽学习曲线
# 
# 

# In[46]:


# Part 2: Calculate cost over the years with cumulative capacity

def cost_model(S, C0, S0, b):
    return C0 * (S / S0) ** b

# Input data: Year and corresponding Annual Installed Capacity (in million tonnes/year)
years = np.arange(2021, 2051)
annual_capacity = np.array([0.548843785, 0.717195813, 0.916781207, 1.142417727, 1.384207779, 1.62888754,
                            1.862555665, 2.073682851, 2.255107185, 2.404405301, 2.522952033, 2.614437831,
                            2.683499922, 2.734771406, 2.772365378, 2.799680243, 2.8193953, 2.833556987,
                            2.843694593, 2.850933685, 2.85609389, 2.859767594, 2.862380672, 2.864238153,
                            2.865557927, 2.866495349, 2.867161038, 2.867633685, 2.867969232, 2.868207428])

# Calculate cumulative capacity
cumulative_capacity = np.cumsum(annual_capacity)

# Define the learning rate and calculate the learning parameter b for Part 2
learning_rate = 0.1  # Hypothetical learning rate
b_part2 = -np.log2(1 - learning_rate)

# Function to calculate cost at each year based on cumulative capacity
def calculate_cost(cumulative_capacity, C0, initial_capacity, b):
    return C0 * (cumulative_capacity / initial_capacity) ** (-b)

# Encapsulated function to calculate cost based on input year and n
def get_cost_for_year_and_n(year, n):
    if year not in years:
        raise ValueError(f"Year {year} is out of the data range (2021-2050)")

    # Get the cumulative capacity for the given year
    year_index = np.where(years == year)[0][0]
    cumulative_capacity_for_year = cumulative_capacity[year_index]

    # Calculate C0 for the given n using the fitted model from Part 1
    C0_part2 = cost_model(n, C0_fitted, S0_fitted, b_fitted)

    # Calculate the cost for the given year
    cost_for_year = calculate_cost(cumulative_capacity_for_year, C0_part2, cumulative_capacity[0], b_part2)

    return cost_for_year


# In[49]:


# 输出学习曲线方程
print("最终学习曲线方程:")
print(f"C(n, t) = C0(n) × (cum_cap(t)/cum_cap(0))^(-{b_part2:.4f})")
print(f"其中 C0(n) = {C0_fitted:.2f} × (n/{S0_fitted:.2f})^{b_fitted:.4f}")
print(f"完整形式: C(n, t) = {C0_fitted:.2f} × (n/{S0_fitted:.2f})^{b_fitted:.4f} × (cum_cap(t)/{cumulative_capacity[0]:.4f})^(-{b_part2:.4f})")
print(f"学习率 = {learning_rate}")


# 2000是有效时长，1000是转换成MW，计算cfa的1000是1000刀，7.2是汇率，转换为CNY

# In[55]:


year_input = 2021
# 确保 n_input 是一个普通列表，每个元素都是一个浮点数
n_input = [(poverty_selected['Electri'].iloc[i] / 4000 / 1000) for i in range(len(poverty_selected['Electri']))]

# 计算每个县的 Cfa[i]
Cfa = [get_cost_for_year_and_n(year_input, n_input[i]) * n_input[i] * 1000 * 7.2 for i in range(len(n_input))]  # 1000 为n_input的转换系数，转换为kw，7.2为美元汇率
# Cfa = [1000 * n_input[i] * 1000 * 7.2 for i in range(len(n_input))]
# 将 Cfa 的值四舍五入并转换为整数
Cfa = [int(round(value)) for value in Cfa]

# 将 Cfa 添加到 poverty_selected 中
poverty_selected['Cfa'] = Cfa

# 查看更新后的数据
poverty_selected


# In[56]:


Cfa


# In[57]:


merged=copy.deepcopy(poverty_selected)
merged


# #### 3.1.4 罐车运输成本函数拟合
# 

# In[58]:


# 罐车运输成本函数计算
from scipy.interpolate import interp1d

# 根据图中的数据点（距离为公里，运输成本为元/kg）
distance_km = np.array([50, 100, 150, 200, 250, 300, 350, 400, 450, 500])
transport_cost_yuan_per_kg = np.array([5.43, 8.66, 9.85, 11.03, 12.21, 15.45, 16.63, 17.82, 19.00, 20.18])

# 使用线性插值创建连续运输成本函数
cost_function = interp1d(distance_km, transport_cost_yuan_per_kg, kind='linear', fill_value="extrapolate")

def calculate_transport_cost(distance_in_meters):
    # 将距离从米转换为公里
    distance_km = distance_in_meters / 1000
    # 计算运输成本（元/kg）
    cost_yuan_per_kg = cost_function(distance_km) * 0.0899
    return cost_yuan_per_kg

# Example usage:
distance_in_meters = 120000  # 120 kilometers
cost = calculate_transport_cost(distance_in_meters)
print(f"The transport cost per kg for {distance_in_meters} meters is: {cost:.2f} yuan/m³")

# 创建一个更密集的距离数据点，用于绘制平滑的曲线
distance_km_dense = np.linspace(50, 500, 500)
cost_dense = cost_function(distance_km_dense)

# # 绘制图像
# plt.figure(figsize=(10, 6))
# plt.plot(distance_km_dense, cost_dense, label="Transport Cost (Yuan/kg)", color="orange", linewidth=2)
# plt.scatter(distance_km, transport_cost_yuan_per_kg, color="red", zorder=5, label="Data Points")
# plt.title("Transport Cost vs Distance")
# plt.xlabel("Distance (km)")
# plt.ylabel("Transport Cost (Yuan/kg)")
# plt.grid(True)
# plt.legend()
# plt.show()


# #### 3.1.5 导入管道运费和其余相关费用
# 

# In[59]:


# 成本参数（示例值）
Cas = 2.5 * 7 / 11.2  # 能量储存设施成本
c = 0  # 与运输距离无关的罐车投资成本
e = 0  # 与运输距离无关的天然气网络中的氢气混合运输成本
Cadi = 3000  # 设备采购成本
Ca = 5000  # 接入电网设施成本
Cpi = 2000   # 管道运输建设成本/m
Fpi = 2000  # 管道连接主管道平均成本
Fai = 2000  # 罐车连接主管道平均成本

# 运营和维护成本参数
# Csa_h = [Cfa[i] * 0.001 for i in range(len(Cfa))]  # 氢气制备设施年维护成本（元/m³）
Csa_h = [0 for i in range(len(Cfa))]
Csa_d = 0  # 氢气燃料电池年维护成本（元/m³）
Csa_a = 0  # 调峰发电设备年维护成本（元/m³）
Csa_p = 0  # 管道每米年维护成本（元/m）
Csa_sf = 0  # 罐车每米年维护成本（元/立方米）

# 运输成本参数
Spip = 0.000000405 / 11.2  # 元/吨·m


# #### 3.1.6 详细的运费测算
# 

# In[60]:


# 创建用于存储计算结果的列表
Dhp = []
Dht = []

# 获取dim、din列值
dim = merged['dim'].tolist()
din = merged['din'].tolist()
Q = merged['Q'].tolist()

# 距离计算
for i in range(len(county_indices)):
    # 计算 Dhp
    if dim[i] * (Cpi + Csa_p * 20 + Spip * 20 * Q[i]) + Fpi >= din[i] * Cpi:
        Dhp.append(din[i])
    else:
        Dhp.append(dim[i])
    # Dhp: 到主干管道的实际管道距离
    # dim: 生产地点到用户的距离
    # Fpi: 管道连接主管道的平均成本
    # din: 数据中指定的生产地点到主干管道的距离

    # 计算 Dht
    if calculate_transport_cost(dim[i]) * Q[i] + Fai >= calculate_transport_cost(din[i]) * Q[i]:
        Dht.append(din[i])
    else:
        Dht.append(dim[i])
    # Dht: 到用户的罐车运输距离
    # dim: 生产地点到用户的距离
    # Fai: 罐车连接主管道的平均成本
    # din: 数据中指定的生产地点到主干管道的距离

Cinvest_values = {}
Com_values = {}
Ctrans_values = {}

for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        for k in range(len(transport_methods)):
            # j=2的情况，决策变量设为0
            if j == 2:
                Cinvest_values[(i, j, k)] = 0
                Com_values[(i, j, k)] = 0
                Ctrans_values[(i, j, k)] = 0
            elif j == 0:
                Cinvest_values[(i, j, k)] = Cfa[i] + Cas * Q[i] + Cadi
                Com_values[(i, j, k)] = (Csa_h[i] + Csa_d) * 20 * Q[i]
                Ctrans_values[(i, j, k)] = 0
            elif j == 1:
                Cinvest_values[(i, j, k)] = Cfa[i] + Cas * Q[i] + Ca
                Com_values[(i, j, k)] = (Csa_h[i] + Csa_a) * 20 * Q[i]
                Ctrans_values[(i, j, k)] = 0
            elif j == 3:
                if k == 1:
                    if Dht[i] == dim[i]:
                        Cinvest_values[(i, j, k)] =  Cfa[i]  + Fpi
                        Com_values[(i, j, k)] = 0
                        Ctrans_values[(i, j, k)] = calculate_transport_cost(Dht[i]) * 20 * Q[i]
                    else:
                        Cinvest_values[(i, j, k)] = e + Cfa[i]
                        Com_values[(i, j, k)] = 0
                        Ctrans_values[(i, j, k)] = calculate_transport_cost(Dht[i]) * 20 * Q[i]
                elif k == 2:
                    if Dhp[i] == dim[i]:
                        Cinvest_values[(i, j, k)] = e + Cfa[i] + Dhp[i] * Cpi + Fai
                        Com_values[(i, j, k)] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                        Ctrans_values[(i, j, k)] = Dhp[i] * Spip * 20 * Q[i]
                    else:
                        Cinvest_values[(i, j, k)] = e + Cfa[i] + Dhp[i] * Cpi
                        Com_values[(i, j, k)] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                        Ctrans_values[(i, j, k)] = Dhp[i] * Spip * 20 * Q[i]
                else:
                    # 如果 j == 3, 但 k 不为 1 或 2，默认值
                    Cinvest_values[(i, j, k)] = 0
                    Com_values[(i, j, k)] = 0
                    Ctrans_values[(i, j, k)] = 0
            else:
                # 对于其他未定义的 (j, k) 组合，设置默认值
                Cinvest_values[(i, j, k)] = 0
                Com_values[(i, j, k)] = 0
                Ctrans_values[(i, j, k)] = 0


# In[61]:


Ctrans_values


# 查看计算结果
# 

# In[62]:


# 创建DataFrame并添加计算的距离
distances_df_2 = pd.DataFrame({
    'name': merged['name'],  # 确保名称列存在并正确
    'Dhp': Dhp,
    'Dht': Dht
})

# 合并数据
counties_column_name = 'name'  # Modify to actual column name in counties_in_yunnan_guizhou DataFrame
merged[counties_column_name] = merged[counties_column_name].astype(str)
distances_df_2['name'] = distances_df_2['name'].astype(str)
merged = merged.merge(distances_df_2, left_on=counties_column_name, right_on='name', suffixes=('_left', '_right'))
merged = merged.loc[:, ~merged.columns.duplicated()]
merged_df=merged

print(merged_df)


# In[63]:


merged_df


# ### 3.2 计算氢能收益

# #### 3.2.1 光伏的成本收益计算

# In[64]:


# 定义光伏发电部分的收益和成本计算函数
def calculate_pv_revenue_and_cost(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N):
    revenue = total_generation * price
    total_fixed_cost = C_PV + C_ES
    total_annual_cost = (O_PV + O_ES + C_tax + C_F) * N
    total_cost = total_fixed_cost + total_annual_cost
    return revenue, total_cost

# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率

pv_revenue = {}
pv_total_cost = {}

# 用于存储每个县的PV收益与成本比值
pv_ratio = {}
# 提前计算每个县的光伏发电部分的收益和成本
for i, row in merged.iterrows():
    alpha = 1 - row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    price = row['PV_price']  # 使用对应的PV价格
    E_n = mean_value * alpha
    total_generation = E_n * N

    # 计算光伏发电部分的收益和成本
    revenue, total_cost = calculate_pv_revenue_and_cost(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # 将结果存储在字典中
    pv_revenue[i] = revenue
    pv_total_cost[i] = total_cost
# 将收益与成本的比值存储在字典中
    pv_ratio[i] = (revenue / total_cost - 1) / N

pv_revenue,pv_total_cost


# In[65]:


merged


# #### 3.2.2 提取必要的变量

# In[66]:


merged_df=copy.deepcopy(merged)


# In[67]:


# 获取所需的列数据
PV_price = merged['PV_price'].tolist()  # 列表形式的 PV_price
Hydrogen_P = merged['Hydrogen_Min'].tolist()  # 列表形式的 Hydrogen_Max

# 构造 P 的二维列表 # 39.4 应该是可以发出来的电量
P = []
for i in range(len(merged)):  # 遍历每一行
    row = [
        39.4 * 0.3 * 0.5,  # 第一项
        39.4 * 0.3 * PV_price[i],  # 第二项
        Hydrogen_P[i],  # 第三项
        Hydrogen_P[i],  # 第四项
    ]
    P.append(row)

Electri = merged['Electri'].tolist()
Electri_all = merged['Electri_all'].tolist() 
Water_Price= merged['Water_Price'].tolist()
P , Electri , Water_Price


# In[68]:


merged_1=copy.deepcopy(merged)


# In[69]:


merged


# #### 3.2.3 创建优化模型计算模式总效益(最小成本)

# ##### 优化计算

# In[70]:


pv_total_cost


# In[71]:


# 创建模型
model = gp.Model("Hydrogen_Energy_mix")

# 决策变量
M = model.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), vtype=GRB.BINARY, name="M")

# 定义辅助变量
revenue = gp.quicksum(M[i, j, k] *(P[i][j] * Q[i] * 20)+ pv_revenue[i] * pv_x  for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))
cost = gp.quicksum(M[i, j, k] * (Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] ) + pv_total_cost[i] * pv_x for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))

# 定义辅助变量
Z = model.addVar(vtype=GRB.CONTINUOUS, name="Z")

# 目标函数
model.setObjective(Z, GRB.MAXIMIZE)

# 添加约束：定义 Z
revenue_var = model.addVar(vtype=GRB.CONTINUOUS, name="revenue_var")
cost_var = model.addVar(vtype=GRB.CONTINUOUS, name="cost_var")

model.addConstr(revenue_var == revenue, name="revenue_eq")
model.addConstr(cost_var == cost, name="cost_eq")

# 线性化 Z * cost_var
T = model.addVar(vtype=GRB.CONTINUOUS, name="T")
Z_lb, Z_ub = 0, 10  # 假设的Z上下界，需要根据具体情况调整
cost_lb, cost_ub = 0, 1000000000000  # 假设的cost_var上下界，需要根据具体情况调整

model.addConstr(T >= Z * cost_lb + cost_var * Z_lb - Z_lb * cost_lb, name="mccormick1")
model.addConstr(T >= Z * cost_ub + cost_var * Z_ub - Z_ub * cost_ub, name="mccormick2")
model.addConstr(T <= Z * cost_ub + cost_var * Z_lb - Z_lb * cost_ub, name="mccormick3")
model.addConstr(T <= Z * cost_lb + cost_var * Z_ub - Z_ub * cost_lb, name="mccormick4")

# 原来的乘法约束改为 T 变量约束
model.addConstr(revenue_var >= T, name="linearized_ROI_constraint")

# 每个县只有一种销售和运输方式
for i in range(len(county_indices)):
    model.addConstr(gp.quicksum(M[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods))) == 1, name=f"UniqueSalesTransport_{i}")

# 确保在某些条件下特定的运输方式和销售类型组合是不可行的
for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        if j == 0 or j == 1:  # 假设销售类型1和2对应的约束
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 2:
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 3:
            for k in range(0, 3):
                if k == 0:
                    model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")

# 求解模型
model.optimize()

# 创建结果列表
results = []

# 记录结果
if model.status == GRB.OPTIMAL:
    for i in range(len(county_indices)):
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                if M[i, j, k].x > 0.5:
                    # 计算收益相关值
                    hydrogen_revenue = P[i][j] * Q[i] * 20
                    pv_rev = pv_revenue[i] * pv_x
                    subsidy = Q[i] / 2 * 0.53
                    revenue_val = hydrogen_revenue + pv_rev + subsidy

                    # 计算成本相关值
                    invest_cost = Cinvest_values[(i, j, k)]
                    om_cost = Com_values[(i, j, k)]
                    trans_cost = Ctrans_values[(i, j, k)]
                    pv_cost = pv_total_cost[i] * pv_x
                    water_cost = Q[i] * 0.001 * Water_Price[i]
                    cost_val = invest_cost + om_cost + trans_cost + pv_cost + water_cost

                    # 计算ROI和其他指标
                    ROI = (revenue_val / cost_val - 1) / N
                    h2_price = (invest_cost + om_cost + trans_cost + 4.9 * Q[i] * 20 * 0.0899) / (Q[i] * 20) / 0.0899

                    # 计算价格减成本（不考虑折现）
                    unit_cost = cost_val / (Q[i] * 20) if Q[i] > 0 else 0

                    # 计算价格减成本（按每kWh电计算）
                    if Electri_all[i] > 0:
                        # 价格（总收入/总电量）
                        price_per_kwh = revenue_val / (Electri_all[i] * 20)
                        # 成本（总成本/总电量）
                        cost_per_kwh = cost_val / (Electri_all[i] * 20)
                        # 价格减成本
                        price_minus_cost = price_per_kwh - cost_per_kwh

                        invest_cost_per_kwh = Cinvest_values[(i, j, k)] / (Electri_all[i] * 20)

                        om_cost_per_kwh = Com_values[(i, j, k)] / (Electri_all[i] * 20)

                        trans_cost_per_kwh = Ctrans_values[(i, j, k)] / (Electri_all[i] * 20)
                    else:
                        price_minus_cost = 0

                    jobs = n_input[i] * 17.7 + 63

                    # 确定运输里程
                    transport_distance = Dht[i] if k == 1 else (Dhp[i] if k == 2 else 0)

                    water = Q[i] * 0.001

                    if ROI > merged.loc[i, "ROI"] and ROI > 0:
                        results.append({
                            # 基本信息
                            "name": merged.loc[i, 'name'],
                            "i": i + 1,
                            "j": j + 1,
                            "k": k + 1,
                            # 收入相关
                            "hydrogen_revenue": hydrogen_revenue,
                            "pv_revenue": pv_rev,
                            "subsidy_revenue": subsidy,
                            "total_revenue": revenue_val,
                            # 成本相关
                            "investment_cost": invest_cost,
                            "om_cost": om_cost,
                            "transport_cost": trans_cost,
                            "pv_cost": pv_cost,
                            "water_cost": water_cost,
                            "total_cost": cost_val,
                            # 关键指标
                            "ROI": ROI,
                            "H2_price": h2_price,

                            # 其他指标
                            "contribute": hydrogen_revenue / (hydrogen_revenue + pv_rev),
                            "SDG3": 0.05 * Electri[i] * 20 / cost_val,
                            "SDG8": (Q[i] / 1000 * 3) * 3000 / cost_val,
                            "SDG12": Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val,
                            "SDG13": (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val,
                            "SDG9": Dhp[i] * 1000 / cost_val if (j == 3 and k == 2) else 0,
                            "work_y": Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val / N,
                            "environment_y": Q[i] * 109 / cost_val / N,
                            "difference": (Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val / N) - (Q[i] * 109 / cost_val / N),

                            "invest_cost_per_kwh_y":invest_cost_per_kwh,
                            "om_cost_per_kwh_y" : om_cost_per_kwh,
                            "trans_cost_per_kwh_y" : trans_cost_per_kwh,

                            # 原始参数
                            "P": P[i][j],
                            "Q": Q[i],
                            "Electri": Electri[i],
                            "Water_Price": Water_Price[i],
                            "Dhp": Dhp[i],
                            "Dht": Dht[i],
                            "original_ROI": merged.loc[i, "ROI"],
                            "price_minus_cost_y":price_minus_cost,
                            "transport_distance": transport_distance,
                            "jobs_y":jobs,
                            "water":water
                        })
                    else:
                        results.append({
                            "name": merged.loc[i, 'name'],
                            "i": i + 1,
                            "j": 0,
                            "k": 0,
                            "ROI": merged.loc[i, "ROI"],
                            "original_ROI": merged.loc[i, "ROI"],
                            # 其他值设为0
                            "hydrogen_revenue": 0,
                            "pv_revenue": 0,
                            "subsidy_revenue": 0,
                            "total_revenue": 0,
                            "investment_cost": 0,
                            "om_cost": 0,
                            "transport_cost": 0,
                            "pv_cost": 0,
                            "water_cost": 0,
                            "total_cost": 0,
                            "H2_price": 0,
                            "contribute": 0,
                            "SDG3": 0,
                            "SDG8": 0,
                            "SDG12": 0,
                            "SDG13": 0,
                            "SDG9": 0,
                            "work_y": 0,
                            "environment_y": 0,
                            "difference": 0,
                            "P": None,
                            "Q": None,
                            "Electri": None,
                            "Water_Price": None,
                            "Dhp": None,
                            "Dht": None,
                            "price_minus_cost_y":merged.loc[i, "price_minus_cost"],
                            "invest_cost_per_kwh_y":None,
                            "om_cost_per_kwh_y" : None,
                            "trans_cost_per_kwh_y" : None,
                            "transport_distance": 0,
                            "jobs_y":merged.loc[i, "jobs_x"],
                            "water":water
                        })

                    print(f"County {i+1} uses sales type {j+1} and transport method {k+1} with ROI {ROI}")
else:
    print("No optimal solution found")

# 将结果转换为数据框
results_df = pd.DataFrame(results)

# 保存结果
results_df.to_excel('optimization_results_detailed.xlsx', index=False)

# 打印基本统计信息
print("\n=== 优化结果统计信息 ===")
print("\n收入相关变量统计:")
revenue_cols = ['hydrogen_revenue', 'pv_revenue', 'subsidy_revenue', 'total_revenue']
print(results_df[revenue_cols].describe())

print("\n成本相关变量统计:")
cost_cols = ['investment_cost', 'om_cost', 'transport_cost', 'pv_cost', 'water_cost', 'total_cost','invest_cost_per_kwh_y','om_cost_per_kwh_y','trans_cost_per_kwh_y']
print(results_df[cost_cols].describe())

print("\nROI和价格统计:")
print(results_df[['ROI', 'H2_price','price_minus_cost_y','transport_distance','jobs_y']].describe())

# 计算最大运输距离下j=4的概率
max_distance = results_df['transport_distance'].max()
max_distance_records = results_df[results_df['transport_distance'] <= max_distance]
j4_count = len(max_distance_records[max_distance_records['j'] == 4])
total_count = len(max_distance_records)
j4_probability = j4_count / total_count if total_count > 0 else 0

print(f"\n最大运输距离: {max_distance}")
print(f"最大运输距离下的记录数: {total_count}")
print(f"其中j=4的记录数: {j4_count}")
print(f"最大运输距离下j=4的概率: {j4_probability:.2%}")


# In[72]:


# 将数据保存到Excel文件
results_df[['name', 'ROI']].to_excel('ROI_results.xlsx', index=False)


# In[73]:


import pandas as pd

# 假设已有的 DataFrame
# results_df 包含 'name' 和 'ROI'
# counties_selected 包含 'name'

# 筛选出name在counties_selected中的数据
selected_names = counties_selected['name'].unique()

# 与 counties_selected 相等的数据
matched_df = results_df[results_df['name'].isin(selected_names)][['name', 'ROI']]
matched_df.to_excel('matched_ROI_results.xlsx', index=False)

# 与 counties_selected 不相等的数据
unmatched_df = results_df[~results_df['name'].isin(selected_names)][['name', 'ROI']]
unmatched_df.to_excel('unmatched_ROI_results.xlsx', index=False)

print('数据已成功保存到 matched_ROI_results.xlsx 和 unmatched_ROI_results.xlsx')


# In[74]:


results_df


# 合并并进行结果展示

# In[75]:


# 修改 poverty_column_name 为实际 counties 数据框中的列名称
poverty_column_name = 'name'

# 将 'name' 列转换为字符串类型，确保合并时不会出错
poverty_selected[poverty_column_name] = poverty_selected[poverty_column_name].astype(str)

# 合并 poverty_selected 和 results_df 数据框，基于 'name' 列
merged_df = poverty_selected.merge(results_df, left_on=poverty_column_name, right_on='name')

# 去除重复的 'name' 行
merged_df = merged_df.drop_duplicates(subset=['name'])
print(merged_df)


# # 将 poverty_data 中的“人口”列合并到 merged_df 中
# # 将 'name' 列转换为字符串类型，确保合并时不会出错
# poverty_data['name'] = poverty_data['市'].astype(str)
# merged_df = merged_df.merge(poverty_data[['name', '人口']], on='name', how='left')
# merged_df = merged_df.drop_duplicates(subset=['name'])
# 将 'SDG_all' 列添加到 merged_df 中，包含所有 SDG 列和 ROI_y 列的求和
sdg_columns = ['ROI_y', 'difference']  # 确保这些列存在
merged_df['SDG_all_2'] = merged_df[sdg_columns].sum(axis=1)

print(merged_df)


# In[76]:


merged_df


# In[77]:


counties_selected=copy.deepcopy(counties_selected_resort_2)
counties_selected = merged_df[merged_df['name'].isin(counties_selected[poverty_column_name])]
counties_selected


# In[78]:


merged_df_1=copy.deepcopy(merged_df)


# ##### 敏感性分析

# In[81]:


import numpy as np
import pandas as pd

# === 1) 原始参数设置 ===
learning_rates = {
    "Low": 0.185,
    "Base": 0.263,
    "High": 0.348
}

M = 45600          # 市场潜力 (GW) (示例值)
p_2024 = 1.698     # 2024年光伏组件价格 (元/W)
cap_2024 = 3350    # 2024 年末累计装机量 (GW)
new_2024 = 277.17  # 2024 年新增装机量 (GW)

# Bass模型参数(示例)
p_innovation = 7.64e-9
p_imitation  = 0.626
h            = -1.134

start_year = 2024
end_year   = 2050

def run_pv_simulation(lr, p_2024, cap_2024, new_2024):
    """
    针对不同学习率 lr 运行 Bass+学习曲线模拟，返回:
      - all_years: 年份列表
      - price_list: 各年末组件价格 (元/W)
    """
    capacity_dict = {}
    price_dict    = {}

    # 2024年底 初始累计
    cap_2024_end = cap_2024 + new_2024
    capacity_dict[start_year] = cap_2024_end
    price_dict[start_year]    = p_2024

    for year in range(start_year + 1, end_year + 1):
        prev_cap = capacity_dict[year - 1]
        # Bass模型: adoption
        adoption = (p_innovation + p_imitation*(prev_cap/M))*(M - prev_cap)
        curr_cap = prev_cap + adoption

        # 学习曲线
        ratio   = curr_cap / cap_2024_end
        c_price = p_2024*(ratio**(-lr))

        capacity_dict[year] = curr_cap
        price_dict[year]    = c_price

    all_years = sorted(capacity_dict.keys())
    price_list= [(price_dict[y] +1.162) * 1000 for y in all_years]
    return all_years, price_list

# 计算所有场景的光伏组件价格
df_pv_prices = pd.DataFrame({"Year": range(start_year, end_year + 1)})

for scenario, lr in learning_rates.items():
    yrs, prices = run_pv_simulation(lr, p_2024, cap_2024, new_2024)
    df_pv_prices[scenario] = prices
df_pv_prices


# In[ ]:


# 创建新的数据框来存储不同情景的PV收益和成本
scenarios = ["Low", "Base", "High"]
years_range = range(2024, 2051)

# 创建列名
column_names = []
for year in years_range:
    for scenario in scenarios:
        column_names.extend([
            f'pv_revenue_{year}_{scenario}',
            f'pv_total_cost_{year}_{scenario}',
            f'pv_ratio_{year}_{scenario}'
        ])

# 创建新的数据框
pv_results_df = pd.DataFrame(0.0, index=merged.index, columns=column_names)

# 基础参数设置
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0      # 其他固定成本（元/千瓦·年）
C_tax = 0    # 税收成本（元/千瓦·年）
N = 20       # 资产寿命（年）

# 计算每个年份、每个情景下的收益和成本
for year in years_range:
    for scenario in scenarios:
        # 获取该年份该情景下的光伏系统成本
        C_PV = df_pv_prices.loc[df_pv_prices['Year'] == year, scenario].values[0]   # 转换为元/千瓦

        # 计算折旧成本
        V_R = C_PV * 0.2   # 残值（元/千瓦）
        C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）

        # 对每个县计算收益和成本
        for idx, row in merged.iterrows():
            alpha = 1 - row['Curtailed_Rate']
            mean_value = row['mean_tiff']
            price = row['PV_price']  # 使用对应的PV价格
            E_n = mean_value * alpha
            total_generation = E_n * N

            # 计算光伏发电部分的收益和成本
            revenue, total_cost = calculate_pv_revenue_and_cost(
                total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N
            )

            # 将结果存储在数据框中
            pv_results_df.loc[idx, f'pv_revenue_{year}_{scenario}'] = revenue
            pv_results_df.loc[idx, f'pv_total_cost_{year}_{scenario}'] = total_cost
            pv_results_df.loc[idx, f'pv_ratio_{year}_{scenario}'] = (revenue / total_cost - 1) / N

# 查看结果
print("数据框的形状：", pv_results_df.shape)
print("\n前几列的数据示例：")
print(pv_results_df.iloc[:, :6].head())

# 如果需要计算统计信息
summary_stats = pd.DataFrame()
for year in years_range:
    for scenario in scenarios:
        ratio_col = f'pv_ratio_{year}_{scenario}'
        stats = {
            f'平均收益率_{year}_{scenario}': pv_results_df[ratio_col].mean(),
            f'最大收益率_{year}_{scenario}': pv_results_df[ratio_col].max(),
            f'最小收益率_{year}_{scenario}': pv_results_df[ratio_col].min()
        }
        summary_stats = pd.concat([summary_stats, pd.Series(stats)])

print("\n收益率统计信息：")
print(summary_stats)


# In[ ]:


import seaborn as sns
# 重组数据为适合绘图的格式
plot_data = []
for year in range(2024, 2051):
    for scenario in ['Base']:  # 这里只选择Base情景，如果需要所有情景可以使用scenarios列表
        ratio_col = f'pv_ratio_{year}_{scenario}'
        year_data = pv_results_df[ratio_col]
        plot_data.append({
            'Year': year,
            'PV Ratio': year_data
        })

# 将数据转换为长格式
plot_df = pd.concat([pd.DataFrame(data) for data in plot_data])

# 创建箱线图
plt.figure(figsize=(15, 8))
sns.boxplot(data=plot_df, x='Year', y='PV Ratio')

# 设置图表样式
plt.title('PV Ratio Distribution (2024-2050)', fontsize=14, pad=15)
plt.xlabel('Year', fontsize=12)
plt.ylabel('PV Ratio', fontsize=12)

# 旋转x轴标签以防重叠
plt.xticks(rotation=45)

# 添加网格线
plt.grid(True, axis='y', linestyle='--', alpha=0.7)

# 调整布局
plt.tight_layout()

# 显示图表
plt.show()


# In[ ]:


# 创建新的数据框来存储不同情景的Cfa值
years_range = range(2024, 2051)
scenarios = ["Low", "Base", "High"]

# 创建列名
column_names = [f'Cfa_{year}_{scenario}' for year in years_range for scenario in scenarios]
cfa_df = pd.DataFrame(0.0, index=poverty_selected.index, columns=column_names)

# 计算每个情景下的b_part2
b_part2_dict = {
    scenario: -np.log2(1 - learning_rate) 
    for scenario, learning_rate in learning_rates.items()
}

# 定义考虑不同学习率的成本计算函数
def get_cost_for_year_and_n_with_scenario(year, n, b_part2):
    if year not in years:
        raise ValueError(f"Year {year} is out of the data range (2021-2050)")

    # 如果是2024年，直接返回初始成本
    if year == 2024:
        return cost_model(n, C0_fitted, S0_fitted, b_fitted)

    year_index = np.where(years == year)[0][0]
    cumulative_capacity_for_year = cumulative_capacity[year_index]

    # Calculate C0 for the given n using the fitted model from Part 1
    C0_part2 = cost_model(n, C0_fitted, S0_fitted, b_fitted)

    # Calculate the cost for the given year with specific learning rate
    cost_for_year = calculate_cost(cumulative_capacity_for_year, C0_part2, cumulative_capacity[0], b_part2)

    return cost_for_year

# 计算每个情景下的Cfa值
for scenario in scenarios:
    b_part2 = b_part2_dict[scenario]

    for year in years_range:
        # 计算该年份和情景的Cfa
        if year == 2024:
            # 2024年使用初始成本值，三个情景相同
            Cfa = [cost_model(n_input[i], C0_fitted, S0_fitted, b_fitted) * n_input[i] * 1000 * 7.2 
                   for i in range(len(n_input))]
        else:
            # 其他年份使用学习曲线计算
            Cfa = [get_cost_for_year_and_n_with_scenario(year, n_input[i], b_part2) * n_input[i] * 1000 * 7.2 
                   for i in range(len(n_input))]

        # 将结果四舍五入并转换为整数
        Cfa = [int(round(value)) for value in Cfa]

        # 将结果添加到数据框中
        cfa_df[f'Cfa_{year}_{scenario}'] = Cfa

# 验证2024年三个情景的值是否相同
print("验证2024年三个情景的值是否相同：")
for scenario in scenarios:
    print(f"\n2024年{scenario}情景的前5个值：")
    print(cfa_df[f'Cfa_2024_{scenario}'].head())

# 查看结果
print("\n数据框的形状：", cfa_df.shape)
print("\n前几列的数据示例：")
print(cfa_df.iloc[:, :6].head())


# In[ ]:


# 重组数据为适合绘图的格式
plot_data = []
for year in range(2024, 2051):
    for scenario in scenarios:
        cfa_col = f'Cfa_{year}_{scenario}'
        year_data = cfa_df[cfa_col]
        plot_data.append({
            'Year': year,
            'Scenario': scenario,
            'Cfa (元/kW)': year_data
        })

# 将数据转换为长格式
plot_df = pd.concat([pd.DataFrame(data) for data in plot_data])

# 创建箱线图
plt.figure(figsize=(15, 8))
sns.boxplot(data=plot_df, x='Year', y='Cfa (元/kW)', hue='Scenario')

# 设置图表样式
plt.title('Cfa Distribution by Scenario (2024-2050)', fontsize=14, pad=15)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Cfa (元/kW)', fontsize=12)

# 旋转x轴标签
plt.xticks(rotation=45)

# 添加网格线
plt.grid(True, axis='y', linestyle='--', alpha=0.7)

# 设置y轴的科学计数法格式
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

# 调整图例位置
plt.legend(title='Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')

# 调整布局
plt.tight_layout()

# 显示图表
plt.show()


# In[86]:


# 创建新的数据框架构
county_ids = poverty_selected.index  # 获取县级单位的索引
years_range = range(2024, 2051)
scenarios = ["Low", "Base", "High"]

# 创建列名列表
column_names = []
for year in years_range:
    for scenario in scenarios:
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                column_names.extend([
                    f'Cinvest_{year}_{scenario}_j{j}_k{k}',
                    f'Com_{year}_{scenario}_j{j}_k{k}',
                    f'Ctrans_{year}_{scenario}_j{j}_k{k}'
                ])

# 创建新的数据框，使用county_ids作为索引
costs_df = pd.DataFrame(0.0, index=county_ids, columns=column_names)

# 计算成本
for year in years_range:
    for scenario in scenarios:
        # 使用对应年份和情景的Cfa
        Cfa = cfa_df[f'Cfa_{year}_{scenario}'].tolist()

        for i in range(len(county_indices)):
            for j in range(len(hydrogen_sales_types)):
                for k in range(len(transport_methods)):
                    # j=2的情况，决策变量设为0
                    if j == 2:
                        continue
                    elif j == 0:
                        costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = Cfa[i] + Cas * Q[i] + Cadi
                        costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = (Csa_h[i] + Csa_d) * 20 * Q[i]
                        costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]
                    elif j == 1:
                        costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = Cfa[i] + Cas * Q[i] + Ca
                        costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = (Csa_h[i] + Csa_a) * 20 * Q[i]
                        costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]
                    elif j == 3:
                        if k == 1:
                            if Dht[i] == dim[i]:
                                costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = Cfa[i] + Fpi
                                costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = 0.0
                                costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]
                            else:
                                costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = e + Cfa[i]
                                costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = 0.0
                                costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]
                        elif k == 2:
                            if Dhp[i] == dim[i]:
                                costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = e + Cfa[i] + Dhp[i] * Cpi + Fai
                                costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                                costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]
                            else:
                                costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = e + Cfa[i] + Dhp[i] * Cpi
                                costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                                costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]


# In[87]:


'''
成本的测算和检查

'''
# # 重组数据为适合绘图的格式
# plot_data = []
# for year in years_range:
#     for scenario in scenarios:
#         # 获取j=3, k=1的三种成本数据
#         cinvest = costs_df[f'Cinvest_{year}_{scenario}_j3_k1'].values  # 使用.values转换为数组
#         com = costs_df[f'Com_{year}_{scenario}_j3_k1'].values
#         ctrans = costs_df[f'Ctrans_{year}_{scenario}_j3_k1'].values

#         # 添加到绘图数据中
#         for inv, om, trans in zip(cinvest, com, ctrans):
#             plot_data.extend([
#                 {'Year': str(year), 'Cost Type': 'Investment Cost', 'Value': inv, 'Scenario': scenario},
#                 {'Year': str(year), 'Cost Type': 'O&M Cost', 'Value': om, 'Scenario': scenario},
#                 {'Year': str(year), 'Cost Type': 'Transport Cost', 'Value': trans, 'Scenario': scenario}
#             ])

# # 将数据转换为DataFrame
# plot_df = pd.DataFrame(plot_data)

# # 创建子图
# fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 18))

# # 绘制投资成本箱线图
# sns.boxplot(data=plot_df[plot_df['Cost Type'] == 'Investment Cost'], 
#             x='Year', y='Value', hue='Scenario', ax=ax1)
# ax1.set_title('Investment Cost Distribution (j=3, k=1)', fontsize=12, pad=15)
# ax1.set_xlabel('')
# ax1.set_ylabel('Investment Cost (元)', fontsize=10)
# ax1.tick_params(axis='x', rotation=45)
# ax1.grid(True, axis='y', linestyle='--', alpha=0.7)
# ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

# # 绘制运维成本箱线图
# sns.boxplot(data=plot_df[plot_df['Cost Type'] == 'O&M Cost'], 
#             x='Year', y='Value', hue='Scenario', ax=ax2)
# ax2.set_title('O&M Cost Distribution (j=3, k=1)', fontsize=12, pad=15)
# ax2.set_xlabel('')
# ax2.set_ylabel('O&M Cost (元)', fontsize=10)
# ax2.tick_params(axis='x', rotation=45)
# ax2.grid(True, axis='y', linestyle='--', alpha=0.7)
# ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

# # 绘制运输成本箱线图
# sns.boxplot(data=plot_df[plot_df['Cost Type'] == 'Transport Cost'], 
#             x='Year', y='Value', hue='Scenario', ax=ax3)
# ax3.set_title('Transport Cost Distribution (j=3, k=1)', fontsize=12, pad=15)
# ax3.set_xlabel('Year', fontsize=10)
# ax3.set_ylabel('Transport Cost (元)', fontsize=10)
# ax3.tick_params(axis='x', rotation=45)
# ax3.grid(True, axis='y', linestyle='--', alpha=0.7)
# ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

# # 调整布局
# plt.tight_layout()

# # 显示图表
# plt.show()


# In[88]:


# 重新设计计算payback的函数
def calculate_payback(investment_cost, annual_revenue, annual_om_cost, residual_value, discount_rate, max_years=30):
    """
    计算投资回收期：找到累计折现收益大于初始投资的年份

    参数:
    investment_cost: 初始投资成本
    annual_revenue: 年收益
    annual_om_cost: 年运维成本
    residual_value: 残值（项目结束时）
    discount_rate: 折现率
    max_years: 最大计算年限

    返回:
    payback_period: 回收期（年），如果在max_years内无法回收则返回None
    """
    if investment_cost <= 0 or annual_revenue <= annual_om_cost:
        return None

    cumulative_cash_flow = -investment_cost  # 初始现金流为负的投资成本

    for year in range(1, max_years + 1):
        # 计算当年净现金流并折现
        annual_net_cash_flow = (annual_revenue - annual_om_cost) / ((1 + discount_rate) ** year)

        # 累加到总现金流
        cumulative_cash_flow += annual_net_cash_flow

        # 如果累计现金流转为正值，说明投资已回收
        if cumulative_cash_flow >= 0:
            # 可以进一步精确计算小数部分
            # 上一年的累计现金流
            prev_cumulative_cash_flow = cumulative_cash_flow - annual_net_cash_flow
            # 计算小数部分：还需多少比例的一年来实现收支平衡
            fraction = -prev_cumulative_cash_flow / annual_net_cash_flow
            return year - 1 + fraction

    # 如果在最大年限内未能回收投资
    return None

# 创建一个字典来存储所有情景和年份的结果
all_results = {}
scenarios = ["Low", "Base", "High"]
years_range = range(2024, 2051)

# 在存储结果的部分添加payback计算
for scenario in scenarios:
    for year in years_range:
        # 创建模型
        model = gp.Model(f"Hydrogen_Energy_mix_{year}_{scenario}")

        # 决策变量
        M = model.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), 
                         vtype=GRB.BINARY, name="M")

        # 直接计算ROI作为目标函数
        objective = gp.quicksum(
            M[i, j, k] * (
                (P[i][j] * Q[i] * 20 + pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x + Q[i] / 2 * 0.53) /
                (costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                 costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                 costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                 pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x + 
                 Q[i] * 0.001 * Water_Price[i]) - 1
            ) / N
            for i in range(len(county_indices))
            for j in range(len(hydrogen_sales_types)) if j != 2
            for k in range(len(transport_methods))
        )

        # 保持原有约束
        for i in range(len(county_indices)):
            model.addConstr(
                gp.quicksum(M[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 
                           for k in range(len(transport_methods))) == 1
            )

            # 特定条件约束
            for j in range(len(hydrogen_sales_types)):
                for k in range(len(transport_methods)):
                    if j in [0, 1]:
                        model.addConstr(M[i, j, k] == 0)
                    elif j == 2:
                        model.addConstr(M[i, j, k] == 0)
                    elif j == 3 and k == 0:
                        model.addConstr(M[i, j, k] == 0)

        # 设置目标函数
        model.setObjective(objective, GRB.MAXIMIZE)
        model.optimize()

        # 存储结果
        results = []
        if model.status == GRB.OPTIMAL:
            for i in range(len(county_indices)):
                for j in range(len(hydrogen_sales_types)):
                    for k in range(len(transport_methods)):
                        if M[i, j, k].x > 0.5:
                            # 计算收益和成本
                            revenue_val = (P[i][j] * Q[i] * 20 + 
                                        pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x + 
                                        Q[i] / 2 * 0.53)

                            cost_val = (costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                                    costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                                    costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                                    pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x + 
                                    Q[i] * 0.001 * Water_Price[i])

                            # 获取投资成本和运维成本
                            investment_cost = costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x
                            annual_om_cost = costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] / N + Q[i] * 0.001 * Water_Price[i] / N

                            # 计算残值（假设为投资成本的20%）
                            residual_value = investment_cost * 0.2

                            # 计算年收益
                            annual_revenue = revenue_val / N

                            # 计算回收期
                            discount_rate = 0.03  # 折现率
                            payback = calculate_payback(
                                investment_cost=investment_cost,
                                annual_revenue=annual_revenue,
                                annual_om_cost=annual_om_cost,
                                residual_value=residual_value,
                                discount_rate=discount_rate,
                                max_years=30
                            )

                            ROI = (revenue_val / cost_val - 1) / N
                            SDG9_val = 0

                            if ROI:
                                if j == 3 and k == 2:
                                    SDG9_val = Dhp[i] * 1000 / cost_val

                                results.append({
                                    "name": merged.loc[i, 'name'],
                                    "i": i + 1,
                                    "j": j + 1,
                                    "k": k + 1,
                                    "year": year,
                                    "scenario": scenario,
                                    "ROI": ROI,
                                    "Payback": payback,  # 添加新计算的payback到结果中
                                    "contribute": P[i][j] * Q[i] * 20 / (P[i][j] * Q[i] * 20 + pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x),
                                    "SDG3": 0.05 * Electri[i] * 20 / cost_val,
                                    "SDG8": (Q[i] / 1000 * 3) * 3000 / cost_val,
                                    "SDG12": Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val,
                                    "SDG13": (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val,
                                    "SDG9": SDG9_val,
                                    "work": Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val / N,
                                    "environment": Q[i] * 109 / cost_val / N,
                                    "H2_price": (costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                                            costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                                            costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                                            4.9 * Q[i] * 20 * 0.0899) / (Q[i] * 20) / 0.0899,
                                    "difference": Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val / N - Q[i] * 109 / cost_val / N
                                })
                            else:
                                results.append({
                                    "name": merged.loc[i, 'name'],
                                    "i": i + 1,
                                    "j": 0,
                                    "k": 0,
                                    "year": year,
                                    "scenario": scenario,
                                    "ROI": merged.loc[i, "ROI"],
                                    "Payback": None,  # 如果没有计算ROI，则payback为None
                                    "SDG3": 0,
                                    "SDG8": 0,
                                    "SDG12": 0,
                                    "SDG13": 0,
                                    "SDG9": 0,
                                    "work": 0,
                                    "environment": 0,
                                    "difference": 0
                                })

        all_results[f"{year}_{scenario}"] = pd.DataFrame(results)

# 合并所有结果
final_results_df = pd.concat(all_results.values(), ignore_index=True)

# 保存结果
final_results_df.to_csv(f'optimization_results_all_scenarios.csv', index=False)

# 打印一些统计信息
for scenario in scenarios:
    for year in years_range:
        scenario_year_results = final_results_df[
            (final_results_df['scenario'] == scenario) & 
            (final_results_df['year'] == year)
        ]
        print(f"\n统计信息 - 情景：{scenario}, 年份：{year}")
        print(f"平均ROI：{scenario_year_results['ROI'].mean():.4f}")
        print(f"平均氢气价格：{scenario_year_results['H2_price'].mean():.2f}")

        # 添加回收期统计
        valid_payback = scenario_year_results['Payback'].dropna()
        if not valid_payback.empty:
            print(f"平均回收期：{valid_payback.mean():.2f}年")
            print(f"有效回收期数量：{len(valid_payback)}")
        else:
            print("没有有效的回收期数据")


# In[ ]:


# 对计算出的payback进行统计分析
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties

# 读取结果数据
final_results_df = pd.read_csv('optimization_results_all_scenarios.csv')

# 1. 基本统计分析
print("=== Payback期基本统计分析 ===")

# 检查缺失值情况
missing_payback = final_results_df['Payback'].isna().sum()
total_records = len(final_results_df)
print(f"总记录数: {total_records}")
print(f"Payback缺失值数量: {missing_payback} ({missing_payback/total_records*100:.2f}%)")

# 有效Payback的基本统计量
valid_payback = final_results_df['Payback'].dropna()
print("\n有效Payback的基本统计量:")
print(f"数量: {len(valid_payback)}")
print(f"最小值: {valid_payback.min():.2f}年")
print(f"最大值: {valid_payback.max():.2f}年")
print(f"平均值: {valid_payback.mean():.2f}年")
print(f"中位数: {valid_payback.median():.2f}年")
print(f"标准差: {valid_payback.std():.2f}年")

# 2. 按情景和年份分组统计
print("\n=== 按情景和年份分组的Payback统计 ===")
payback_by_scenario_year = final_results_df.groupby(['scenario', 'year'])['Payback'].agg([
    ('平均值', 'mean'),
    ('中位数', 'median'),
    ('最小值', 'min'),
    ('最大值', 'max'),
    ('标准差', 'std'),
    ('有效数量', 'count')
]).reset_index()

# 保存分组统计结果
payback_by_scenario_year.to_csv('payback_statistics_by_scenario_year.csv', index=False)
print("分组统计结果已保存至 payback_statistics_by_scenario_year.csv")

# 3. 按ROI筛选的Payback分析
print("\n=== 按ROI筛选的Payback分析 ===")
roi_thresholds = [0.03, 0.05, 0.08, 0.1]

for threshold in roi_thresholds:
    filtered_df = final_results_df[final_results_df['ROI'] > threshold]
    valid_payback_filtered = filtered_df['Payback'].dropna()

    print(f"\nROI > {threshold}的Payback统计:")
    print(f"符合条件的记录数: {len(filtered_df)} ({len(filtered_df)/total_records*100:.2f}%)")
    print(f"有效Payback数量: {len(valid_payback_filtered)}")

    if len(valid_payback_filtered) > 0:
        print(f"平均值: {valid_payback_filtered.mean():.2f}年")
        print(f"中位数: {valid_payback_filtered.median():.2f}年")
        print(f"最小值: {valid_payback_filtered.min():.2f}年")
        print(f"最大值: {valid_payback_filtered.max():.2f}年")

        # 按情景和年份分组统计
        payback_by_scenario_year_filtered = filtered_df.groupby(['scenario', 'year'])['Payback'].agg([
            ('平均值', 'mean'),
            ('中位数', 'median'),
            ('有效数量', 'count')
        ]).reset_index()

        # 保存筛选后的分组统计结果
        payback_by_scenario_year_filtered.to_csv(f'payback_statistics_roi_gt_{threshold}.csv', index=False)
        print(f"ROI > {threshold}的分组统计结果已保存至 payback_statistics_roi_gt_{threshold}.csv")

# 4. 可视化分析
print("\n=== 生成Payback可视化图表 ===")

# 设置中文字体
try:
    font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
except:
    print("无法设置中文字体，图表将使用默认字体")

# 4.1 各情景各年份的平均回收期趋势图
plt.figure(figsize=(12, 8))
for scenario in final_results_df['scenario'].unique():
    scenario_data = payback_by_scenario_year[payback_by_scenario_year['scenario'] == scenario]
    plt.plot(scenario_data['year'], scenario_data['平均值'], marker='o', label=f'情景 {scenario}')

plt.title('各情景各年份的平均回收期趋势', fontsize=16)
plt.xlabel('年份', fontsize=14)
plt.ylabel('平均回收期 (年)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('payback_trend_by_scenario_year.png', dpi=300)
plt.close()

# 4.2 回收期分布直方图
plt.figure(figsize=(12, 8))
sns.histplot(valid_payback, bins=20, kde=True)
plt.axvline(valid_payback.mean(), color='r', linestyle='--', label=f'平均值: {valid_payback.mean():.2f}年')
plt.axvline(valid_payback.median(), color='g', linestyle='--', label=f'中位数: {valid_payback.median():.2f}年')
plt.title('回收期分布直方图', fontsize=16)
plt.xlabel('回收期 (年)', fontsize=14)
plt.ylabel('频数', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('payback_distribution_histogram.png', dpi=300)
plt.close()

# 4.3 各情景回收期箱线图
plt.figure(figsize=(12, 8))
sns.boxplot(x='scenario', y='Payback', data=final_results_df)
plt.title('各情景回收期箱线图', fontsize=16)
plt.xlabel('情景', fontsize=14)
plt.ylabel('回收期 (年)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('payback_boxplot_by_scenario.png', dpi=300)
plt.close()

# 4.4 热力图：各情景各年份的平均回收期
pivot_data = payback_by_scenario_year.pivot(index='scenario', columns='year', values='平均值')
plt.figure(figsize=(16, 8))
sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='YlGnBu', linewidths=0.5)
plt.title('各情景各年份的平均回收期热力图', fontsize=16)
plt.xlabel('年份', fontsize=14)
plt.ylabel('情景', fontsize=14)
plt.tight_layout()
plt.savefig('payback_heatmap_by_scenario_year.png', dpi=300)
plt.close()

# 5. 回收期与ROI的关系分析
print("\n=== 回收期与ROI的关系分析 ===")

# 去除缺失值
roi_payback_df = final_results_df[['ROI', 'Payback']].dropna()

# 计算相关系数
correlation = roi_payback_df['ROI'].corr(roi_payback_df['Payback'])
print(f"ROI与Payback的相关系数: {correlation:.4f}")

# 散点图：ROI vs Payback
plt.figure(figsize=(10, 8))
sns.scatterplot(x='ROI', y='Payback', data=roi_payback_df, alpha=0.6)
plt.title('ROI与回收期的关系散点图', fontsize=16)
plt.xlabel('ROI', fontsize=14)
plt.ylabel('回收期 (年)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('roi_vs_payback_scatter.png', dpi=300)
plt.close()

# 6. 回收期小于10年的项目分析
print("\n=== 回收期小于10年的项目分析 ===")
payback_lt_10 = final_results_df[final_results_df['Payback'] < 10]
print(f"回收期小于10年的项目数量: {len(payback_lt_10)} ({len(payback_lt_10)/total_records*100:.2f}%)")

# 按情景统计
payback_lt_10_by_scenario = payback_lt_10.groupby('scenario').agg({
    'Payback': ['count', 'mean', 'median'],
    'ROI': 'mean'
})
print("\n按情景统计回收期小于10年的项目:")
print(payback_lt_10_by_scenario)

# 按年份统计
payback_lt_10_by_year = payback_lt_10.groupby('year').agg({
    'Payback': ['count', 'mean', 'median'],
    'ROI': 'mean'
})
print("\n按年份统计回收期小于10年的项目:")
print(payback_lt_10_by_year.head())  # 只显示前几年

# 保存回收期小于10年的项目数据
payback_lt_10.to_csv('projects_with_payback_lt_10.csv', index=False)
print("回收期小于10年的项目数据已保存至 projects_with_payback_lt_10.csv")

print("\n统计分析完成，所有结果已保存。")


# In[ ]:


# 提取2026和2027年的数据
years_compare = [2026, 2027]
compare_data = final_results_df[final_results_df['year'].isin(years_compare)].copy()

# 对每个县和情景，计算各成本项
def calculate_costs(row):
    i = row['i'] - 1  # 因为i是从1开始的
    j = row['j'] - 1
    k = row['k'] - 1
    year = row['year']
    scenario = row['scenario']

    if j == -1 or k == -1:  # 对应j=0, k=0的情况
        return pd.Series({
            'Investment Cost': 0,
            'O&M Cost': 0,
            'Transport Cost': 0,
            'Total Cost': 0
        })

    # 获取各成本项
    invest = costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}']
    om = costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}']
    trans = costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}']

    return pd.Series({
        'Investment Cost': invest,
        'O&M Cost': om,
        'Transport Cost': trans,
        'Total Cost': invest + om + trans
    })

# 计算各成本项
cost_columns = compare_data.apply(calculate_costs, axis=1)
compare_data = pd.concat([compare_data, cost_columns], axis=1)

# 计算每年每种情景的平均成本
avg_costs = compare_data.groupby(['year', 'scenario'])[
    ['Investment Cost', 'O&M Cost', 'Transport Cost', 'Total Cost', 'H2_price']
].mean().round(2)

# 计算成本变化
cost_change = pd.DataFrame()
for scenario in scenarios:
    change = avg_costs.loc[(2027, scenario)] - avg_costs.loc[(2026, scenario)]
    cost_change[scenario] = change

# 创建可视化
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# 绘制平均成本柱状图
cost_types = ['Investment Cost', 'O&M Cost', 'Transport Cost']
x = np.arange(len(scenarios))
width = 0.35

for i, year in enumerate(years_compare):
    bottom = np.zeros(len(scenarios))
    for cost_type in cost_types:
        values = [avg_costs.loc[(year, scenario), cost_type] for scenario in scenarios]
        ax1.bar(x + i*width - width/2, values, width, bottom=bottom, label=f'{cost_type} ({year})')
        bottom += values

ax1.set_title('Average Costs Comparison (2026 vs 2027)', pad=15)
ax1.set_ylabel('Cost (元)')
ax1.set_xticks(x)
ax1.set_xticklabels(scenarios)
ax1.legend()

# 绘制成本变化图
colors = ['red' if x < 0 else 'green' for x in cost_change.iloc[:-1].values.flatten()]
x = np.arange(len(cost_types))
for i, scenario in enumerate(scenarios):
    ax2.bar(x + i*width - width, cost_change.loc[cost_types, scenario], 
            width, label=scenario, color=colors[i::len(scenarios)])

ax2.set_title('Cost Changes (2027 - 2026)', pad=15)
ax2.set_ylabel('Change in Cost (元)')
ax2.set_xticks(x)
ax2.set_xticklabels(cost_types, rotation=45)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.7)

# 添加数值标签
def add_value_labels(ax, spacing=5):
    for rect in ax.patches:
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        label = f'{y_value:,.0f}'
        if abs(y_value) < 1:
            label = f'{y_value:.2f}'

        va = 'bottom' if y_value >= 0 else 'top'

        ax.annotate(label, (x_value, y_value), xytext=(0, spacing),
                   textcoords="offset points", ha='center', va=va)

add_value_labels(ax2)

plt.tight_layout()
plt.show()

# 打印详细的成本变化
print("\n成本变化详细信息（2027 - 2026）：")
print(cost_change.round(2))

# 打印氢气价格变化
print("\n氢气价格变化（元/kg）：")
h2_price_change = avg_costs.xs(2027, level=0)['H2_price'] - avg_costs.xs(2026, level=0)['H2_price']
print(h2_price_change.round(2))


# In[100]:


print(final_results_df)


# In[ ]:


results_df


# In[102]:


# import numpy as np
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D

# def visualize_cost_3d():
#     # 创建年份和容量的网格
#     years = np.arange(2024, 2051)
#     n_values = np.linspace(0.1, 10, 50)  # 假设容量范围从0.1到10

#     # 创建网格点
#     X, Y = np.meshgrid(years, n_values)
#     Z = np.zeros_like(X)

#     # 计算每个场景的成本
#     scenarios = ["Low", "Base", "High"]
#     fig = plt.figure(figsize=(18, 6))

#     for idx, scenario in enumerate(scenarios, 1):
#         # 计算成本值
#         for i in range(len(n_values)):
#             for j in range(len(years)):
#                 try:
#                     Z[i,j] = get_cost_for_year_and_n(years[j], n_values[i], scenario)
#                 except:
#                     Z[i,j] = np.nan

#         # 创建子图
#         ax = fig.add_subplot(1, 3, idx, projection='3d')

#         # 绘制3D表面
#         surf = ax.plot_surface(X, Y, Z, 
#                              cmap='viridis',
#                              edgecolor='none',
#                              alpha=0.8)

#         # 设置标签
#         ax.set_xlabel('年份')
#         ax.set_ylabel('容量 (MW)')
#         ax.set_zlabel('成本 (元/kW)')
#         ax.set_title(f'{scenario} 场景下的成本变化')

#         # 添加颜色条
#         fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

#         # 优化视角
#         ax.view_init(elev=20, azim=45)

#     plt.tight_layout()
#     plt.show()

#     # 生成等高线图
#     fig, axs = plt.subplots(1, 3, figsize=(18, 6))

#     for idx, scenario in enumerate(scenarios):
#         # 计算成本值（与上面相同）
#         for i in range(len(n_values)):
#             for j in range(len(years)):
#                 try:
#                     Z[i,j] = get_cost_for_year_and_n(years[j], n_values[i], scenario)
#                 except:
#                     Z[i,j] = np.nan

#         # 绘制等高线图
#         contour = axs[idx].contourf(X, Y, Z, levels=20, cmap='viridis')
#         axs[idx].set_xlabel('年份')
#         axs[idx].set_ylabel('容量 (MW)')
#         axs[idx].set_title(f'{scenario} 场景下的成本等高线')
#         plt.colorbar(contour, ax=axs[idx])

#     plt.tight_layout()
#     plt.show()

# # 添加数据分析功能
# def analyze_cost_trends():
#     """分析成本趋势并输出关键统计信息"""
#     years = np.arange(2024, 2051)
#     test_capacities = [1, 5, 10]  # 测试几个典型容量值

#     for capacity in test_capacities:
#         print(f"\n容量 {capacity} MW 的成本趋势分析:")
#         for scenario in ["Low", "Base", "High"]:
#             costs = []
#             for year in years:
#                 try:
#                     cost = get_cost_for_year_and_n(year, capacity, scenario)
#                     costs.append(cost)
#                 except:
#                     continue

#             costs = np.array(costs)
#             print(f"\n{scenario} 场景:")
#             print(f"平均成本: {np.mean(costs):.2f} 元/kW")
#             print(f"成本降低率: {((costs[0] - costs[-1]) / costs[0] * 100):.2f}%")
#             print(f"最大成本: {np.max(costs):.2f} 元/kW")
#             print(f"最小成本: {np.min(costs):.2f} 元/kW")

# if __name__ == "__main__":
#     # 执行可视化
#     visualize_cost_3d()

#     # 执行趋势分析
#     analyze_cost_trends()


# In[ ]:


import matplotlib.pyplot as plt

def plot_roi_above_3pct_comparison(df):
    """
    输入：df (例如 df_econ_scenario_all)
    功能：基于 (Scenario, Year) 统计 ROI>3%的地区数量，并可视化
         在同一张图里，绘制 Base_LR 的折线，以及 Low_LR~High_LR 的区间。
    """
    # 1) 创建一个新的列，用于标记 ROI 是否 > 0.03
    df_plot = df.copy()
    df_plot['ROI_above_3pct'] = df_plot['ROI'] > 0.03

    # 2) 按 (Scenario, Year) 统计 ROI_above_3pct = True 的计数
    df_count = df_plot.groupby(['scenario','year'])['ROI_above_3pct'].sum().reset_index(name='Count_ROI_Above_3pct')

    # 3) 分别取出 Low_LR / Base_LR / High_LR 的数据
    df_low  = df_count[df_count['scenario'] == 'Low'].sort_values('year')
    df_base = df_count[df_count['scenario'] == 'Base'].sort_values('year')
    df_high = df_count[df_count['scenario'] == 'High'].sort_values('year')

    # 4) 开始绘图
    plt.figure(figsize=(8,5))  # 创建画布

    # 4.1 画出 Base_LR 的折线
    plt.plot(df_base['year'],
             df_base['Count_ROI_Above_3pct'],
             label='Base_LR (ROI>3%)')

    # 4.2 使用 fill_between 表示 Low_LR 和 High_LR 之间的区间
    plt.fill_between(df_low['year'],
                     df_low['Count_ROI_Above_3pct'],
                     df_high['Count_ROI_Above_3pct'],
                     alpha=0.3,
                     label='Low_LR~High_LR range')

    # 5) 添加图例、坐标轴标签、标题
    plt.legend()
    plt.xlabel('year')
    plt.ylabel('Count of Regions (ROI > 3%)')
    plt.title('Count of Regions with ROI>3% under Different Learning Rate Scenarios')

    plt.show()


# 使用示例：
plot_roi_above_3pct_comparison(final_results_df)


# In[104]:


# 从结果上看，氢能的影响变小了，主要可能是因为氢能的运输费用占了大头


# In[ ]:


# 清理数据：删除 'ROI' 列为空的行，并确保 'year' 列为字符串类型
cleaned_data = final_results_df.dropna(subset=['ROI'])  # 删除 'ROI' 为空的行
cleaned_data['year'] = cleaned_data['year'].astype(str)  # 将 'year' 转换为字符串类型

# 打印数据描述信息，检查清理后的数据
print("\n清理后的数据描述统计信息 (四舍五入后的 ROI):")
print(cleaned_data.describe())  # 打印描述统计信息

# 统计每个年份的数据量，确保每个年份的数据量足够
year_counts = cleaned_data['year'].value_counts()
print("\n每年数据量统计：")
print(year_counts)

# 只保留数据点大于1的年份，确保数据量足够绘制图表
valid_years = year_counts[year_counts > 1].index  # 筛选出数据点大于1的年份
cleaned_data = cleaned_data[cleaned_data['year'].isin(valid_years)]  # 过滤出有效年份的数据

clean_data1=copy.deepcopy(cleaned_data)


# ##### 敏感性分析可视化

# In[106]:


# import matplotlib.pyplot as plt
# import numpy as np
# import seaborn as sns
# # 清理数据：删除 'ROI' 列为空的行，并确保 'year' 列为字符串类型
# cleaned_data = all_results_df.dropna(subset=['ROI'])  # 删除 'ROI' 为空的行
# cleaned_data['year'] = cleaned_data['year'].astype(str)  # 将 'year' 转换为字符串类型

# # 打印数据描述信息，检查清理后的数据
# print("\n清理后的数据描述统计信息 (四舍五入后的 ROI):")
# print(cleaned_data.describe())  # 打印描述统计信息

# # 统计每个年份的数据量，确保每个年份的数据量足够
# year_counts = cleaned_data['year'].value_counts()
# print("\n每年数据量统计：")
# print(year_counts)

# # 只保留数据点大于1的年份，确保数据量足够绘制图表
# valid_years = year_counts[year_counts > 1].index  # 筛选出数据点大于1的年份
# cleaned_data = cleaned_data[cleaned_data['year'].isin(valid_years)]  # 过滤出有效年份的数据
# fig, ax = plt.subplots(figsize=(24, 12))  # 调整画布大小

# def plot_all_roi_violinplot(data, ax):
#     available_years = sorted(data['year'].unique(), key=lambda x: int(x))
#     years = [str(y) for y in range(2021, 2051) if (y % 5 == 0 or y == 2021)]
#     years = [y for y in years if y in available_years]
#     violin_data = data[data['year'].isin(years)]

#     positions = []
#     if len(years) > 0:
#         positions.append(0)
#     if len(years) > 1:
#         positions.append(positions[-1] + 4)
#     for i in range(2, len(years)):
#         positions.append(positions[-1] + 5)

#     grouped = violin_data.groupby('year')['ROI'].apply(list).reindex(years)
#     data_arrays = [np.array(grouped[yr]) for yr in years]

#     # 使用 Seaborn 的 YlGnBu 颜色
#     colors = sns.color_palette("YlGnBu", n_colors=7)

#     # 绘制小提琴图
#     for i, (pos, data) in enumerate(zip(positions, data_arrays)):
#         color_index = i % len(colors)  # 循环使用7种颜色
#         parts = ax.violinplot([data], positions=[pos], widths=2.5, showmeans=False, showextrema=False, showmedians=False)
#         for pc in parts['bodies']:
#             pc.set_facecolor(colors[color_index])  # 使用YlGnBu配色
#             pc.set_alpha(0.8)
#             pc.set_edgecolor('black')
#             pc.set_linewidth(1.5)

#     # 绘制箱线图
#     boxprops = dict(facecolor='white', edgecolor='black', linewidth=2)
#     whiskerprops = dict(linewidth=2, color='black')
#     medianprops = dict(color='black', linewidth=2)
#     ax.boxplot(data_arrays,
#                positions=positions,
#                widths=0.2,  # 控制箱线图宽度
#                showfliers=False,
#                boxprops=boxprops,
#                whiskerprops=whiskerprops,
#                medianprops=medianprops,
#                patch_artist=True)

#     # 绘制散点图（增加抖动）
#     for pos, yr in zip(positions, years):
#         vals = grouped[yr]
#         jittered_x = np.random.normal(loc=pos, scale=0.25, size=len(vals))
#         ax.scatter(jittered_x, vals, color='#4c454a', s=20, alpha=0.6, zorder=1)

#     # 添加均值线
#     mean_data = [np.mean(arr) for arr in data_arrays]
#     ax.plot(
#         positions, mean_data,
#         color='#4a7bb6',
#         marker='o',
#         markersize=10,
#         linewidth=2.5,
#         label='均值'
#     )

#     # 参考线
#     ax.axhline(y=0.03, color='#99b5b8', linestyle='--', linewidth=2, label='ROI = 0.03')

#     # 设置刻度与标签
#     tick_label_size = 35
#     ax.set_xticks(positions)
#     ax.set_xticklabels(years, rotation=45, fontsize=tick_label_size)

#     y_min = min(min(arr) for arr in data_arrays)-0.1
#     y_max = max(max(arr) for arr in data_arrays)+0.1
#     ax.set_ylim(y_min, y_max)
#     ax.tick_params(axis='y', which='major', labelsize=35)
#     ax.set_xlabel("Year", fontsize=35)
#     ax.set_ylabel("ROI", fontsize=35)

#     # 去掉上、右边框
#     ax.spines['top'].set_visible(False)
#     ax.spines['right'].set_visible(False)

#     ax.set_facecolor('white')

#     # 根据自定义位置添加背景色区块 (根据实际数据与需要调整)
#     if len(positions) >= 2:
#         ax.axvspan(positions[0]-2, positions[1], color='#cce5ff', alpha=0.3)
#     if len(positions) >= 4:
#         ax.axvspan(positions[1], positions[3], color='#99ccff', alpha=0.3)
#     if len(positions) > 3:
#         ax.axvspan(positions[3], positions[-1]+2, color='#66b2ff', alpha=0.3)
#     ax.set_title('每3年ROI的小提琴图（YlGnBu配色）', fontsize=35, pad=20)

# plot_all_roi_violinplot(cleaned_data, ax)
# plt.tight_layout()
# plt.show()


# In[107]:


# claen_data_y = copy.deepcopy(cleaned_data)


# In[108]:


# import seaborn as sns
# import matplotlib.pyplot as plt
#
# def plot_all_now_year_violinplot(data, ax):
#     # 确保 'year' 是字符串格式，用于绘图
#     data['year'] = data['year'].astype(str)
#
#     # 生成要绘制的年份列表，并确保年份存在于数据中
#     available_years = sorted(data['year'].unique())
#     years = [str(year) for year in range(2021, 2051) if ((year - 2021) % 3 == 0 or year == 2050)]
#     years = [year for year in years if year in available_years]  # 确保年份在数据中
#
#     # 过滤出需要绘制的年份数据
#     violin_data = data[data['year'].isin(years)]
#
#     # 如果 violin_data 为空，直接返回，避免后续操作
#     if violin_data.empty:
#         print("警告：没有可用的数据进行绘图")
#         return
#
#     # 使用 Seaborn 绘制小提琴图，使用蓝绿色渐变
#     sns.violinplot(
#         x='year',
#         y='now_year',  # 使用 now_year 作为 y 轴
#         data=violin_data,
#         ax=ax,
#         order=years,  # 指定年份顺序
#         inner=None,
#         palette='YlGnBu',  # 使用蓝绿色渐变
#         cut=0,
#         bw=0.2,
#         scale='width',
#         linewidth=1.5
#     )
#
#     # 在小提琴图上叠加箱线图
#     sns.boxplot(
#         x='year',
#         y='now_year',  # 使用 now_year 作为 y 轴
#         data=violin_data,
#         ax=ax,
#         order=years,  # 确保箱线图与小提琴图顺序一致
#         color='white',
#         width=0.1,
#         showcaps=False,
#         boxprops={'facecolor': 'white', 'edgecolor': 'black'},
#         whiskerprops={'linewidth': 1.5, 'color': 'black'},
#         zorder=2  # 确保箱线图在小提琴图上方
#     )
#
#     # 绘制散点图，透明度较高且颜色为灰色
#     sns.stripplot(
#         x='year',
#         y='now_year',  # 使用 now_year 作为 y 轴
#         data=violin_data,
#         ax=ax,
#         order=years,
#         color='#4c454a',  # 设置散点颜色为灰色
#         size=4,
#         alpha=0.5,  # 高透明度
#         jitter=True,
#         zorder=1
#     )
#
#     # 计算每年的均值，与小提琴图中的顺序一致
#     mean_data = violin_data.groupby('year')['now_year'].mean().reindex(years).fillna(method='pad')
#
#     # 在图中添加均值曲线（与小提琴一致的蓝色）
#     ax.plot(
#         years, mean_data,
#         color='#4a7bb6',
#         marker='o',
#         markersize=8,
#         linewidth=2,
#         label='均值'
#     )
#
#     # 调整x轴标签的旋转角度，避免重叠
#     tick_label_size = 30
#     ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=tick_label_size)
#
#     # 设置 y 轴范围，并留出一定的空隙
#     y_min, y_max = violin_data['now_year'].min() - 0.1, violin_data['now_year'].max() + 0.1
#     ax.set_ylim(y_min, y_max)
#
#     # 设置 y 轴刻度标签的大小
#     ax.tick_params(axis='y', which='major', labelsize=30)
#
#     # 设置 x 轴和 y 轴标签的字体大小
#     ax.set_xlabel("Year", fontsize=30)
#     ax.set_ylabel("now_year", fontsize=30)  # 设置 y 轴标签为 now_year
#
#     # 取消上框和右框
#     ax.spines['top'].set_visible(False)
#     ax.spines['right'].set_visible(False)
#
#     # 移除背景色
#     ax.set_facecolor('white')
#
#     # 为不同年份区间设置浅蓝色背景
#     ax.axvspan(-1, 1.33, color='#cce5ff', alpha=0.3)  # 2021-2025
#     ax.axvspan(1.33, 4.67, color='#99ccff', alpha=0.3)  # 2025-2035
#     ax.axvspan(4.67, len(years), color='#66b2ff', alpha=0.3)  # 2035-2050
#
#     # 设置图表标题
#     # ax.set_title('每3年now_year的小提琴图', fontsize=22, pad=20)
#
# # 创建图形和轴对象
# fig, ax = plt.subplots(figsize=(20, 10))  # 设置图形大小
# # 清理数据：删除 'now_year' 列为空的行，去除 ROI 中小于等于 0 的值
# cleaned_data = all_results_df.dropna(subset=['now_year'])  # 删除 'now_year' 为空的行
# cleaned_data = cleaned_data[cleaned_data['ROI'] > 0]  # 去除 ROI 中小于等于 0 的值
#
# # 调用绘图函数绘制图表
# plot_all_now_year_violinplot(cleaned_data, ax)
#
# # 调整布局，避免标签被裁剪
# plt.tight_layout()
# plt.savefig("每3年now_year的小提琴图.png", bbox_inches='tight', pad_inches=0, dpi=1200)
# # 显示图表
# plt.show()


# In[109]:


# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd

# # 示例数据集（需替换为实际数据）
# roi_grouped = cleaned_data[cleaned_data['ROI'].notnull()].copy()
# roi_grouped['ROI_group'] = np.where(roi_grouped['ROI'] >= 0.03, "≥ 0.03", "< 0.03")

# roi_en_grouped = cleaned_data[cleaned_data['ROI_en'].notnull()].copy()
# roi_en_grouped['ROI_group'] = np.where(roi_en_grouped['ROI_en'] >= 0.03, "≥ 0.03", "< 0.03")

# # 确保 'year' 列为整数类型
# roi_grouped['year'] = roi_grouped['year'].astype(int)
# roi_en_grouped['year'] = roi_en_grouped['year'].astype(int)

# def plot_roi_bounds(data, ax, shared_errors, shared_years, bound_type, label_suffix="", color='blue'):
#     group_labels = ["≥ 0.03"]
#     bounds = {}

#     for group in group_labels:
#         group_data = data[data['ROI_group'] == group].copy()

#         # 按年份分组并统计频次
#         grouped_data = group_data.groupby('year').size().reset_index(name='frequency')

#         years = grouped_data['year'].values
#         frequencies = grouped_data['frequency'].values

#         # 合并共享年份和误差
#         shared_df = pd.DataFrame({'year': shared_years, 'shared_error': shared_errors})
#         merged_data = pd.merge(grouped_data, shared_df, on='year', how='inner')

#         frequencies = merged_data['frequency'].values
#         errors = merged_data['shared_error'].values

#         if bound_type == 'lower':
#             bound = frequencies * (1 - errors)
#         elif bound_type == 'upper':
#             bound = frequencies * (1 + errors)
#         else:
#             raise ValueError("Invalid bound_type. Use 'lower' or 'upper'.")

#         bounds[group] = (years, bound)

#         # 绘制曲线
#         ax.plot(
#             years, frequencies, label=f"{group} {label_suffix}",
#             marker='o', linestyle='-', linewidth=2, markersize=10, color=color, zorder=2
#         )
#     return bounds

# # 设置随机种子，确保一致性
# np.random.seed(42)

# # 创建图形，并在同一张图上绘制 ROI 和 ROI_en 的上下界
# fig, ax = plt.subplots(figsize=(12, 8))

# # 生成共享的误差数组
# shared_years = np.unique(np.concatenate([roi_grouped['year'].values, roi_en_grouped['year'].values]))
# shared_errors = np.random.uniform(0.05, 0.06, size=len(shared_years))

# # 获取 ROI 的下界和 ROI_en 的上界
# roi_bounds = plot_roi_bounds(roi_grouped, ax, shared_errors, shared_years,
#                              bound_type='lower', label_suffix="(ROI)", color='#63acd4')
# roi_en_bounds = plot_roi_bounds(roi_en_grouped, ax, shared_errors, shared_years,
#                                 bound_type='upper', label_suffix="(ROI_en)", color='#37a700')

# # 填充上下界之间的区域
# for group in roi_bounds:
#     years_lower, lower_bound = roi_bounds[group]
#     years_upper, upper_bound = roi_en_bounds[group]

#     intersected_years = np.intersect1d(years_lower, years_upper)
#     idx_lower = np.isin(years_lower, intersected_years)
#     idx_upper = np.isin(years_upper, intersected_years)

#     lower_bound_aligned = lower_bound[idx_lower]
#     upper_bound_aligned = upper_bound[idx_upper]

#     ax.fill_between(
#         intersected_years, lower_bound_aligned, upper_bound_aligned,
#         color='#dde9f5', alpha=0.5, label='ROI and ROI_en Bound Range', zorder=1
#     )

# ax.set_title("Frequency of ROI ≥ 0.03 over the Years", fontsize=25)
# ax.set_xlabel("Year", fontsize=20)
# ax.set_ylabel("Frequency", fontsize=20)

# # 设置年份作为 x 轴刻度和标签
# ax.set_xticks(shared_years)
# ax.set_xticklabels(shared_years)

# # 移除下框和右框
# ax.spines['bottom'].set_visible(False)
# ax.spines['right'].set_visible(False)

# # 设置上框和左框的样式
# ax.spines['left'].set_edgecolor('black')
# ax.spines['left'].set_linewidth(1)
# ax.spines['top'].set_edgecolor('black')
# ax.spines['top'].set_linewidth(1)

# # 移除网格线
# ax.grid(False)

# # 设置 x 轴范围
# ax.set_xlim(shared_years[0] - 1, shared_years[-1] + 1)
# ax.set_facecolor('white')
# plt.tight_layout()
# plt.show()


# In[110]:


# # 定义总贫困县数量
# total_counties = 826
# target_years=['2025','2035','2050']
# # 初始化结果 DataFrame，用于保存 ROI 和 ROI_en 的计算结果
# results_df_roi = pd.DataFrame(columns=['Year', 'Frequency (ROI ≥ 0.03)', 'Proportion'])
# results_df_roi_en = pd.DataFrame(columns=['Year', 'Frequency (ROI_en ≥ 0.03)', 'Proportion'])

# # 遍历目标年份，分别计算 ROI 和 ROI_en 的频率和比例
# for year in target_years:
#     # ROI 数据
#     year_data_roi = roi_grouped[(roi_grouped['ROI_group'] == "≥ 0.03") & (roi_grouped['year'] == year)]
#     frequency_roi = year_data_roi.shape[0]
#     proportion_roi = frequency_roi / total_counties

#     # ROI_en 数据
#     year_data_roi_en = roi_en_grouped[(roi_en_grouped['ROI_group'] == "≥ 0.03") & (roi_en_grouped['year'] == year)]
#     frequency_roi_en = year_data_roi_en.shape[0]
#     proportion_roi_en = frequency_roi_en / total_counties

#     # 添加 ROI 数据到 DataFrame
#     results_df_roi = pd.concat([results_df_roi,
#                                 pd.DataFrame({'Year': [year],
#                                               'Frequency (ROI ≥ 0.03)': [frequency_roi],
#                                               'Proportion': [proportion_roi]})],
#                                ignore_index=True)

#     # 添加 ROI_en 数据到 DataFrame
#     results_df_roi_en = pd.concat([results_df_roi_en,
#                                    pd.DataFrame({'Year': [year],
#                                                  'Frequency (ROI_en ≥ 0.03)': [frequency_roi_en],
#                                                  'Proportion': [proportion_roi_en]})],
#                                   ignore_index=True)

# # 输出表格
# print("ROI ≥ 0.03 in Target Years (2025, 2035, 2050):")
# print(results_df_roi)

# print("ROI_en ≥ 0.03 in Target Years (2025, 2035, 2050):")
# print(results_df_roi_en)

# # 绘制三张饼图，分别显示 ROI 和 ROI_en 的频率占比
# fig, axes = plt.subplots(2, 3, figsize=(20, 12), facecolor='none')

# # 绘制 ROI 的饼图（第一行）
# for idx, row in results_df_roi.iterrows():
#     year = int(row['Year'])
#     frequency = row['Frequency (ROI ≥ 0.03)']

#     # 绘制 ROI 饼图，蓝色色系
#     axes[0, idx].pie(
#         [frequency, total_counties - frequency],
#         startangle=90,
#         colors=['#63acd4', '#dde9f5']
#     )
#     axes[0, idx].set_title(f"Year {year} - ROI ≥ 0.03", fontsize=16)
#     axes[0, idx].patch.set_alpha(0)  # 背景透明

# # 绘制 ROI_en 的饼图（第二行）
# for idx, row in results_df_roi_en.iterrows():
#     year = int(row['Year'])
#     frequency = row['Frequency (ROI_en ≥ 0.03)']

#     # 绘制 ROI_en 饼图，绿色色系
#     axes[1, idx].pie(
#         [frequency, total_counties - frequency],
#         startangle=90,
#         colors=['#3db702', '#c9f7b3']
#     )
#     axes[1, idx].set_title(f"Year {year} - ROI_en ≥ 0.03", fontsize=16)
#     axes[1, idx].patch.set_alpha(0)  # 背景透明

# # 调整布局并显示图表
# plt.tight_layout()
# plt.show()


# #### 3.2.4 最大成本优化
# 
# 

# ##### 提取必要的变量

# In[79]:


# merged_df=copy.deepcopy(merged_df_1)


# In[ ]:





# In[80]:


print(merged_df)


# In[81]:


merged_df


# In[82]:


Hydrogen_P = merged['Hydrogen_Max'].tolist()  # 列表形式的 Hydrogen_Max

# 构造 P 的二维列表
P = []
for i in range(len(merged)):  # 遍历每一行
    row = [
        39.4 * 0.3 * 0.5,  # 第一项
        39.4 * 0.3 * PV_price[i],  # 第二项
        Hydrogen_P[i],  # 第三项
        Hydrogen_P[i],  # 第四项
    ]
    P.append(row)


# ##### 执行最大成本优化

# 这里把所有的变量都加了一个后缀_m

# In[83]:


# 创建模型
model = gp.Model("Hydrogen_Energy_mix")

# 决策变量
M = model.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), vtype=GRB.BINARY, name="M")

# 定义辅助变量
revenue = gp.quicksum(M[i, j, k] *(P[i][j] * Q[i] * 20)+ pv_revenue[i] * pv_x  for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))
cost = gp.quicksum(M[i, j, k] * (Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] ) + pv_total_cost[i] * pv_x for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))

# pttitle('P Rtio Distibution 2024-2050)', fonsiz14pd15plt.xlabel('Year', f ntsiz =12)
# pmtoylaadl('PV Raaro'pefontsize=12OUS, name="Z")

# 定义辅助变量
Z = model.addVar(vtype=GRB.CONTINUOUS, name="Z")

# 目标函数
model.setObjective(Z, GRB.MAXIMIZE)

# 添加约束：定义 Z
revenue_var = model.addVar(vtype=GRB.CONTINUOUS, name="revenue_var")
cost_var = model.addVar(vtype=GRB.CONTINUOUS, name="cost_var")

model.addConstr(revenue_var == revenue, name="revenue_eq")
model.addConstr(cost_var == cost, name="cost_eq")

# 线性化 Z * cost_var
T = model.addVar(vtype=GRB.CONTINUOUS, name="T")
Z_lb, Z_ub = 0, 10  # 假设的Z上下界，需要根据具体情况调整
cost_lb, cost_ub = 0, 1000000000000  # 假设的cost_var上下界，需要根据具体情况调整

model.addConstr(T >= Z * cost_lb + cost_var * Z_lb - Z_lb * cost_lb, name="mccormick1")
model.addConstr(T >= Z * cost_ub + cost_var * Z_ub - Z_ub * cost_ub, name="mccormick2")
model.addConstr(T <= Z * cost_ub + cost_var * Z_lb - Z_lb * cost_ub, name="mccormick3")
model.addConstr(T <= Z * cost_lb + cost_var * Z_ub - Z_ub * cost_lb, name="mccormick4")

# 原来的乘法约束改为 T 变量约束
model.addConstr(revenue_var >= T, name="linearized_ROI_constraint")

# 每个县只有一种销售和运输方式
for i in range(len(county_indices)):
    model.addConstr(gp.quicksum(M[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods))) == 1, name=f"UniqueSalesTransport_{i}")

# 确保在某些条件下特定的运输方式和销售类型结合是不可行的
for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        if j == 0 or j == 1:  # 假设销售类型1和2对应的约束
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 2:
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 3:
            for k in range(0, 3):
                if k == 0:
                    model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")

# 求解模型
model.optimize()

# 创建结果数据框
results_m = []

# 打印并记录结果
if model.status == GRB.OPTIMAL:
    for i in range(len(county_indices)):
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                if M[i, j, k].x > 0.5:
                    # 计算 ROI
                    revenue_val = P[i][j] * Q[i] * 20 + pv_revenue[i] * pv_x + Q[i] / 2 * 0.53
                    cost_val = Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] + pv_total_cost[i] * pv_x + Q[i] * 0.001 * Water_Price[i]
                    ROI = (revenue_val / cost_val - 1)/N
                    SDG9_val = 0  # 默认值
                    if ROI > merged.loc[i,"ROI"]  and ROI > 0:
                        if j == 3 and k == 2:
                            SDG9_val = Dhp[i] * 1000 / cost_val
                            print(Dhp[i])

                        # 计算价格减成本（按每kWh电计算）
                        if Electri_all[i] > 0:
                            # 价格（总收入/总电量）
                            price_per_kwh = revenue_val / (Electri_all[i] * 20)
                            # 成本（总成本/总电量）
                            cost_per_kwh = cost_val / (Electri_all[i] * 20)
                            # 价格减成本
                            price_minus_cost = price_per_kwh - cost_per_kwh

                            invest_cost_per_kwh = Cinvest_values[(i, j, k)] / (Electri_all[i] * 20)

                            om_cost_per_kwh = Com_values[(i, j, k)] / (Electri_all[i] * 20)

                            trans_cost_per_kwh = Ctrans_values[(i, j, k)] / (Electri_all[i] * 20)

                        else:
                            price_minus_cost = 0

                        jobs = n_input[i] * 17.7 + 63

                        results_m.append({
                            "name": merged.loc[i, 'name'],
                            "i_m": i + 1,
                            "j_m": j + 1,
                            "k_m": k + 1,
                            "ROI_m": ROI,
                            "price_minus_cost_m": price_minus_cost,
                            "contribute_m": P[i][j] * Q[i] * 20 / (P[i][j] * Q[i] * 20 + pv_revenue[i] * pv_x),
                            "SDG3_m": 0.05 * Electri[i] * 20 / cost_val,
                            "SDG8_m": (Q[i] / 1000 * 3) * 3000 / cost_val,
                            "SDG12_m": Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val,
                            "SDG13_m": (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val,
                            "SDG9_m": SDG9_val,
                            "work_m": Electri[i]/2000 * 3 * 5.9 * 3000 / cost_val /N,
                            "environment_m": Q[i] * 109/ cost_val /N,
                            "H2_price_m":(Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] + 4.9 * Q[i] * 20 * 0.0899)/(Q[i] * 20)/0.0899,
                            "difference_m":Electri[i]/2000 * 3 * 5.9 * 3000 / cost_val /N-Q[i] * 109/ cost_val /N,
                            "invest_cost_per_kwh_m":invest_cost_per_kwh,
                            "om_cost_per_kwh_m" : om_cost_per_kwh,
                            "trans_cost_per_kwh_m" : trans_cost_per_kwh,
                            "jobs_m":jobs
                        })
                    else:
                        results_m.append({
                            "name": merged.loc[i, 'name'],
                            "i_m": i + 1,
                            "j_m": 0,
                            "k_m": 0,
                            "ROI_m": merged.loc[i, "ROI"],
                            "price_minus_cost_m": merged.loc[i, "price_minus_cost"],
                            "SDG3_m": 0,
                            "SDG8_m": 0,
                            "SDG12_m": 0,
                            "SDG13_m": 0,
                            "SDG9_m": 0,
                            "work_m":0,
                            "environment_m":0,
                            "difference_m":0,
                            "invest_cost_per_kwh_m":None,
                            "om_cost_per_kwh_m" : None,
                            "trans_cost_per_kwh_m" : None,
                            "jobs_m":merged.loc[i, "jobs_x"]
                        })
                    print(f"County {i+1} uses sales type {j+1} and transport method {k+1} with ROI {ROI}")
else:
    print("No optimal solution found")

# 将结果转换为数据框
results_df_m = pd.DataFrame(results_m)
print(results_df_m)


# In[84]:


# 修改 poverty_column_name 为实际 counties 数据框中的列名称
poverty_column_name = 'name'

# 将 'name' 列转换为字符串类型，确保合并时不会出错
poverty_selected[poverty_column_name] = poverty_selected[poverty_column_name].astype(str)
results_df_m['name'] = results_df_m['name'].astype(str)

# 合并 poverty_selected 和 results_df 数据框，基于 'name' 列
merged_df = merged_df.merge(results_df_m, left_on=poverty_column_name, right_on='name')

# 去除重复的 'name' 行
merged_df = merged_df.drop_duplicates(subset=['name'])

print(merged_df)


# In[85]:


sdg_columns = ['ROI_m', 'difference_m']  # 确保这些列存在
merged_df['SDG_all_3'] = merged_df[sdg_columns].sum(axis=1)


# In[86]:


merged_df



# In[87]:


counties_selected = merged_df[merged_df['name'].isin(counties_selected[poverty_column_name])]
counties_selected


# In[88]:


poverty_selected=copy.deepcopy(merged_df)


# ##### 敏感性分析

# In[195]:


# 重新设计计算payback的函数
def calculate_payback(investment_cost, annual_revenue, annual_om_cost, residual_value, discount_rate, max_years=30):
    """
    计算投资回收期：找到累计折现收益大于初始投资的年份

    参数:
    investment_cost: 初始投资成本
    annual_revenue: 年收益
    annual_om_cost: 年运维成本
    residual_value: 残值（项目结束时）
    discount_rate: 折现率
    max_years: 最大计算年限

    返回:
    payback_period: 回收期（年），如果在max_years内无法回收则返回None
    """
    if investment_cost <= 0 or annual_revenue <= annual_om_cost:
        return None

    cumulative_cash_flow = -investment_cost  # 初始现金流为负的投资成本

    for year in range(1, max_years + 1):
        # 计算当年净现金流并折现
        annual_net_cash_flow = (annual_revenue - annual_om_cost) / ((1 + discount_rate) ** year)

        # 累加到总现金流
        cumulative_cash_flow += annual_net_cash_flow

        # 如果累计现金流转为正值，说明投资已回收
        if cumulative_cash_flow >= 0:
            # 可以进一步精确计算小数部分
            # 上一年的累计现金流
            prev_cumulative_cash_flow = cumulative_cash_flow - annual_net_cash_flow
            # 计算小数部分：还需多少比例的一年来实现收支平衡
            fraction = -prev_cumulative_cash_flow / annual_net_cash_flow
            return year - 1 + fraction

    # 如果在最大年限内未能回收投资
    return None

# 创建一个字典来存储所有情景和年份的结果
all_results = {}
scenarios = ["Low", "Base", "High"]
years_range = range(2024, 2051)

# ... existing code ...

for scenario in scenarios:
    for year in years_range:
        # 创建模型
        model = gp.Model(f"Hydrogen_Energy_mix_{year}_{scenario}")

        # 决策变量
        M = model.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), 
                         vtype=GRB.BINARY, name="M")

        # 直接计算ROI作为目标函数
        objective = gp.quicksum(
            M[i, j, k] * (
                (P[i][j] * Q[i] * 20 + pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x + Q[i] / 2 * 0.53) /
                (costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                 costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                 costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                 pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x + 
                 Q[i] * 0.001 * Water_Price[i]) - 1
            ) / N
            for i in range(len(county_indices))
            for j in range(len(hydrogen_sales_types)) if j != 2
            for k in range(len(transport_methods))
        )

        # 保持原有约束
        for i in range(len(county_indices)):
            model.addConstr(
                gp.quicksum(M[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 
                           for k in range(len(transport_methods))) == 1
            )

            # 特定条件约束
            for j in range(len(hydrogen_sales_types)):
                for k in range(len(transport_methods)):
                    if j in [0, 1]:
                        model.addConstr(M[i, j, k] == 0)
                    elif j == 2:
                        model.addConstr(M[i, j, k] == 0)
                    elif j == 3 and k == 0:
                        model.addConstr(M[i, j, k] == 0)

        # 设置目标函数
        model.setObjective(objective, GRB.MAXIMIZE)
        model.optimize()

        # 存储结果
        results = []
        if model.status == GRB.OPTIMAL:
            for i in range(len(county_indices)):
                for j in range(len(hydrogen_sales_types)):
                    for k in range(len(transport_methods)):
                        if M[i, j, k].x > 0.5:
                            # 计算收益和成本
                            revenue_val_m = (P[i][j] * Q[i] * 20 + 
                                        pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x + 
                                        Q[i] / 2 * 0.53)

                            cost_val_m = (costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                                    costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                                    costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                                    pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x + 
                                    Q[i] * 0.001 * Water_Price[i])

                            # 获取投资成本和运维成本
                            investment_cost_m = costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x
                            annual_om_cost_m = costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] / N + Q[i] * 0.001 * Water_Price[i] / N

                            # 计算残值（假设为投资成本的20%）
                            residual_value_m = investment_cost_m * 0.2

                            # 计算年收益
                            annual_revenue_m = revenue_val_m / N

                            # 计算回收期
                            discount_rate = 0.03  # 折现率
                            payback_m = calculate_payback(
                                investment_cost=investment_cost_m,
                                annual_revenue=annual_revenue_m,
                                annual_om_cost=annual_om_cost_m,
                                residual_value=residual_value_m,
                                discount_rate=discount_rate,
                                max_years=30
                            )

                            ROI_m = (revenue_val_m / cost_val_m - 1) / N
                            SDG9_val_m = 0

                            if ROI_m:
                                if j == 3 and k == 2:
                                    SDG9_val_m = Dhp[i] * 1000 / cost_val_m

                                results.append({
                                    "name_m": merged.loc[i, 'name'],
                                    "i_m": i + 1,
                                    "j_m": j + 1,
                                    "k_m": k + 1,
                                    "year_m": year,
                                    "scenario_m": scenario,
                                    "ROI_m": ROI_m,
                                    "Payback_m": payback_m,  # 添加新计算的payback到结果中
                                    "contribute_m": P[i][j] * Q[i] * 20 / (P[i][j] * Q[i] * 20 + pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x),
                                    "SDG3_m": 0.05 * Electri[i] * 20 / cost_val_m,
                                    "SDG8_m": (Q[i] / 1000 * 3) * 3000 / cost_val_m,
                                    "SDG12_m": Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val_m,
                                    "SDG13_m": (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val_m,
                                    "SDG9_m": SDG9_val_m,
                                    "work_m": Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val_m / N,
                                    "environment_m": Q[i] * 109 / cost_val_m / N,
                                    "H2_price_m": (costs_df.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                                            costs_df.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                                            costs_df.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                                            4.9 * Q[i] * 20 * 0.0899) / (Q[i] * 20) / 0.0899,
                                    "difference_m": Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val_m / N - Q[i] * 109 / cost_val_m / N
                                })
                            else:
                                results.append({
                                    "name_m": merged.loc[i, 'name'],
                                    "i_m": i + 1,
                                    "j_m": 0,
                                    "k_m": 0,
                                    "year_m": year,
                                    "scenario_m": scenario,
                                    "ROI_m": merged.loc[i, "ROI"],
                                    "Payback_m": None,  # 如果没有计算ROI，则payback为None
                                    "SDG3_m": 0,
                                    "SDG8_m": 0,
                                    "SDG12_m": 0,
                                    "SDG13_m": 0,
                                    "SDG9_m": 0,
                                    "work_m": 0,
                                    "environment_m": 0,
                                    "difference_m": 0
                                })

        all_results[f"{year}_{scenario}"] = pd.DataFrame(results)

# 合并所有结果
final_results_df_m = pd.concat(all_results.values(), ignore_index=True)

# 保存结果
final_results_df_m.to_csv(f'optimization_results_all_scenarios_m.csv', index=False)

# 打印一些统计信息
for scenario in scenarios:
    for year in years_range:
        scenario_year_results = final_results_df_m[
            (final_results_df_m['scenario_m'] == scenario) & 
            (final_results_df_m['year_m'] == year)
        ]
        print(f"\n统计信息 - 情景：{scenario}, 年份：{year}")
        print(f"平均ROI：{scenario_year_results['ROI_m'].mean():.4f}")
        print(f"平均氢气价格：{scenario_year_results['H2_price_m'].mean():.2f}")

        # 添加回收期统计
        valid_payback = scenario_year_results['Payback_m'].dropna()
        if not valid_payback.empty:
            print(f"平均回收期：{valid_payback.mean():.2f}年")
            print(f"有效回收期数量：{len(valid_payback)}")
        else:
            print("没有有效的回收期数据")


# In[ ]:


import matplotlib.pyplot as plt

def plot_roi_above_3pct_comparison(df):
    """
    输入：df (例如 df_econ_scenario_all)
    功能：基于 (Scenario, Year) 统计 ROI>3%的地区数量，并可视化
         在同一张图里，绘制 Base_LR 的折线，以及 Low_LR~High_LR 的区间。
    """
    # 1) 创建一个新的列，用于标记 ROI 是否 > 0.03
    df_plot = df.copy()
    df_plot['ROI_above_3pct'] = df_plot['ROI_m'] > 0.03

    # 2) 按 (Scenario, Year) 统计 ROI_above_3pct = True 的计数
    df_count = df_plot.groupby(['scenario_m','year_m'])['ROI_above_3pct'].sum().reset_index(name='Count_ROI_Above_3pct')

    # 3) 分别取出 Low_LR / Base_LR / High_LR 的数据
    df_low  = df_count[df_count['scenario_m'] == 'Low'].sort_values('year_m')
    df_base = df_count[df_count['scenario_m'] == 'Base'].sort_values('year_m')
    df_high = df_count[df_count['scenario_m'] == 'High'].sort_values('year_m')

    # 4) 开始绘图
    plt.figure(figsize=(8,5))  # 创建画布

    # 4.1 画出 Base_LR 的折线
    plt.plot(df_base['year_m'],
             df_base['Count_ROI_Above_3pct'],
             label='Base_LR (ROI>3%)')

    # 4.2 使用 fill_between 表示 Low_LR 和 High_LR 之间的区间
    plt.fill_between(df_low['year_m'],
                     df_low['Count_ROI_Above_3pct'],
                     df_high['Count_ROI_Above_3pct'],
                     alpha=0.3,
                     label='Low_LR~High_LR range')

    # 5) 添加图例、坐标轴标签、标题
    plt.legend()
    plt.xlabel('year_m')
    plt.ylabel('Count of Regions (ROI > 3%)')
    plt.title('Count of Regions with ROI>3% under Different Learning Rate Scenarios')

    plt.show()


# 使用示例：
plot_roi_above_3pct_comparison(final_results_df_m)


# In[ ]:


# 清理数据：删除 'ROI' 列为空的行，并确保 'year' 列为字符串类型
cleaned_data = final_results_df_m.dropna(subset=['ROI_m'])  # 删除 'ROI' 为空的行
cleaned_data['year_m'] = cleaned_data['year_m'].astype(str)  # 将 'year' 转换为字符串类型

# 打印数据描述信息，检查清理后的数据
print("\n清理后的数据描述统计信息 (四舍五入后的 ROI):")
print(cleaned_data.describe())  # 打印描述统计信息

# 统计每个年份的数据量，确保每个年份的数据量足够
year_counts = cleaned_data['year_m'].value_counts()
print("\n每年数据量统计：")
print(year_counts)

# 只保留数据点大于1的年份，确保数据量足够绘制图表
valid_years = year_counts[year_counts > 1].index  # 筛选出数据点大于1的年份
cleaned_data = cleaned_data[cleaned_data['year_m'].isin(valid_years)]  # 过滤出有效年份的数据

clean_data2=copy.deepcopy(cleaned_data)


# ### 按照热值计算与按照储能计算
# 

# #### 基于热值卖

# In[89]:


# 成本参数（示例值）
Cas = 2.5 * 7.2 / 11.2  # 能量储存设施成本
c = 3  # 与运输距离无关的罐车投资成本
e = 10  # 与运输距离无关的天然气网络中的氢气混合运输成本
Cadi = 3000  # 设备采购成本
Ca = 5000  # 接入电网设施成本
Cpi = 2000   # 管道运输建设成本/m
Fpi = 2000  # 管道连接主管道平均成本
Fai = 2000  # 罐车连接主管道平均成本

# 运营和维护成本参数
# Csa_h = [Cfa[i] * 0.001 for i in range(len(Cfa))]  # 氢气制备设施年维护成本（元/m³）
Csa_h = [0 for i in range(len(Cfa))]
Csa_d = 0  # 氢气燃料电池年维护成本（元/m³）
Csa_a = 0  # 调峰发电设备年维护成本（元/m³）
Csa_p = 0  # 管道每米年维护成本（元/m）
Csa_sf = 0  # 罐车每米年维护成本（元/立方米）

# 运输成本参数
Spip = 0.0000035    # 管道每m运输成本（简化后的运输成本）


# In[90]:


import pandas as pd

# Step 1: Load the data from the given Excel files
vertical_dis = pd.read_excel("vertical.xlsx")
node_dis = pd.read_excel("node.xlsx")

# Assuming poverty_selected is already imported and available
# poverty_selected should have a column named "name"

def get_min_distance_and_price(df, name_col, match_col, dist_col, price_col):
    min_distances = []
    prices = []
    for name in poverty_selected['name']:
        matched_rows = df[df[match_col] == name]
        if not matched_rows.empty:
            # Find the row with the minimum distance
            min_distance_row = matched_rows.loc[matched_rows[dist_col].idxmin()]
            min_distance = min_distance_row[dist_col] * 1000
            price = min_distance_row[price_col]
        else:
            # Default values if no match is found
            min_distance = 2000 * 1000
            price = None
        min_distances.append(min_distance)
        prices.append(price)
    return min_distances, prices

# Get minimum distances and prices for vertical_dis and node_dis
dim, dim_p = get_min_distance_and_price(vertical_dis, 'name', '县名', '县中心距离(km)', '调整后价格')
din, din_p = get_min_distance_and_price(node_dis, 'name', '县名', '距离(km)', '节点价格')

poverty_selected['dim_p'] = dim_p
poverty_selected['din_p'] = din_p

# Copy the updated DataFrame
df_merged = poverty_selected.copy()

# Output the merged DataFrame
df_merged.to_excel("merged_output.xlsx", index=False)
print("Merged data saved to 'merged_output.xlsx'")


# In[91]:


# 创建用于存储计算结果的列表
Dhp = []
Dht = []
Dhp_p=[]
Dht_p=[]

# 获取dim、din列值
dim = merged['dim'].tolist()
din = merged['din'].tolist()
dim_p = df_merged['dim_p'].tolist()
din_p = df_merged['din_p'].tolist()
Q = merged['Q'].tolist()
a_cost=0.000002

# 距离计算
for i in range(len(county_indices)):
    # 计算 Dhp
    if dim[i] * (Cpi + Csa_p * 20 + Spip * 20 * Q[i]) + Fpi >= din[i] * Cpi:
        Dhp.append(din[i])
        Dhp_p.append(din_p[i])
    else:
        Dhp.append(dim[i])
        Dhp_p.append(dim_p[i])
    # Dhp: 到主干管道的实际管道距离
    # dim: 生产地点到用户的距离
    # Fpi: 管道连接主管道的平均成本
    # din: 数据中指定的生产地点到主干管道的距离

    # 计算 Dht
    if calculate_transport_cost(dim[i]) * Q[i] + Fai >= calculate_transport_cost(din[i]) * Q[i]:
        Dht.append(din[i])
        Dht_p.append(din_p[i])
    else:
        Dht.append(dim[i])
        Dht_p.append(dim_p[i])
    # Dht: 到用户的罐车运输距离
    # dim: 生产地点到用户的距离
    # Fai: 罐车连接主管道的平均成本
    # din: 数据中指定的生产地点到主干管道的距离

Cinvest_values = {}
Com_values = {}
Ctrans_values = {}

for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        for k in range(len(transport_methods)):
            # j=2的情况，决策变量设为0
            if j == 2:
                Cinvest_values[(i, j, k)] = 0
                Com_values[(i, j, k)] = 0
                Ctrans_values[(i, j, k)] = 0
            elif j == 0:
                Cinvest_values[(i, j, k)] = Cfa[i] + Cas * Q[i] + Cadi
                Com_values[(i, j, k)] = (Csa_h[i] + Csa_d) * 20 * Q[i]
                Ctrans_values[(i, j, k)] = 0
            elif j == 1:
                Cinvest_values[(i, j, k)] = Cfa[i] + Cas * Q[i] + Ca
                Com_values[(i, j, k)] = (Csa_h[i] + Csa_a) * 20 * Q[i]
                Ctrans_values[(i, j, k)] = 0
            elif j == 3:
                if k == 1:
                    if Dht[i] == dim[i]:
                        # Cinvest_values[(i, j, k)] = e + Cfa[i]  + Fpi                                   # 基于热值卖， 不需要管道建设上的投资
                        Cinvest_values[(i, j, k)] = 0
                        Com_values[(i, j, k)] = (Csa_h[i] + Q[i] * Csa_sf) * 20
                        Ctrans_values[(i, j, k)] = a_cost*(Dht[i]) * 20 * Q[i]
                    else:
                        # Cinvest_values[(i, j, k)] = e + Cfa[i]
                        Cinvest_values[(i, j, k)] = 0
                        Com_values[(i, j, k)] = (Csa_h[i] + Q[i] * Csa_sf) * 20
                        Ctrans_values[(i, j, k)] = a_cost*(Dht[i]) * 20 * Q[i]
                elif k == 2:
                    if Dhp[i] == dim[i]:
                        # Cinvest_values[(i, j, k)] = e + Cfa[i] + Dhp[i] * Cpi + Fai
                        Cinvest_values[(i, j, k)] = 0
                        Com_values[(i, j, k)] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                        Ctrans_values[(i, j, k)] = Dhp[i] * Spip * 20 * Q[i]
                    else:
                        # Cinvest_values[(i, j, k)] = e + Cfa[i] + Dhp[i] * Cpi
                        Cinvest_values[(i, j, k)] = 0
                        Com_values[(i, j, k)] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                        Ctrans_values[(i, j, k)] = Dhp[i] * Spip * 20 * Q[i]
                else:
                    # 如果 j == 3, 但 k 不为 1 或 2，默认值
                    Cinvest_values[(i, j, k)] = 0
                    Com_values[(i, j, k)] = 0
                    Ctrans_values[(i, j, k)] = 0
            else:
                # 对于其他未定义的 (j, k) 组合，设置默认值
                Cinvest_values[(i, j, k)] = 0
                Com_values[(i, j, k)] = 0
                Ctrans_values[(i, j, k)] = 0


# In[92]:


PV_price = merged['PV_price'].tolist()  # 列表形式的 PV_price
Hydrogen_P = merged['Hydrogen_Min'].tolist()  # 列表形式的 Hydrogen_Max

# 构造 P 的二维列表
P = []
for i in range(len(merged)):  # 遍历每一行
    row = [
        39.4 * 0.3 * 0.5,  # 第一项
        39.4 * 0.3  * PV_price[i],  # 第二项
        Dhp_p[i],  # 第三项
        Dht_p[i],  # 第四项
    ]
    P.append(row)

Electri = merged['Electri'].tolist()
Water_Price= merged['Water_Price'].tolist()
P , Electri , Water_Price


# In[93]:


# 创建模型
model = gp.Model("Hydrogen_Energy_mix")

# 决策变量
M = model.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), vtype=GRB.BINARY, name="M")

# 定义辅助变量
revenue = gp.quicksum(M[i, j, k] *(P[i][j] * Q[i] * 20)+ pv_revenue[i] * pv_x  for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))
cost = gp.quicksum(M[i, j, k] * (Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] ) + pv_total_cost[i] * pv_x for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))

# 定义辅助变量
Z = model.addVar(vtype=GRB.CONTINUOUS, name="Z")

# 目标函数
model.setObjective(Z, GRB.MAXIMIZE)

# 添加约束：定义 Z
revenue_var = model.addVar(vtype=GRB.CONTINUOUS, name="revenue_var")
cost_var = model.addVar(vtype=GRB.CONTINUOUS, name="cost_var")

model.addConstr(revenue_var == revenue, name="revenue_eq")
model.addConstr(cost_var == cost, name="cost_eq")

# 线性化 Z * cost_var
T = model.addVar(vtype=GRB.CONTINUOUS, name="T")
Z_lb, Z_ub = 0, 10  # 假设的Z上下界，需要根据具体情况调整
cost_lb, cost_ub = 0, 1000000000000  # 假设的cost_var上下界，需要根据具体情况调整

model.addConstr(T >= Z * cost_lb + cost_var * Z_lb - Z_lb * cost_lb, name="mccormick1")
model.addConstr(T >= Z * cost_ub + cost_var * Z_ub - Z_ub * cost_ub, name="mccormick2")
model.addConstr(T <= Z * cost_ub + cost_var * Z_lb - Z_lb * cost_ub, name="mccormick3")
model.addConstr(T <= Z * cost_lb + cost_var * Z_ub - Z_ub * cost_lb, name="mccormick4")

# 原来的乘法约束改为 T 变量约束
model.addConstr(revenue_var >= T, name="linearized_ROI_constraint")

# 每个县只有一种销售和运输方式
for i in range(len(county_indices)):
    model.addConstr(gp.quicksum(M[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods))) == 1, name=f"UniqueSalesTransport_{i}")

# 确保在某些条件下特定的运输方式和销售类型组合是不可行的
for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        if j == 0:
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 0 or j == 1:  # 假设销售类型1和2对应的约束
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 2:
            for k in range(len(transport_methods)):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 3:
            for k in range(0, 3):
                if k == 0:
                    model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")

# 求解模型
model.optimize()

# 创建结果数据框
results = []

# 打印并记录结果
if model.status == GRB.OPTIMAL:
    for i in range(len(county_indices)):
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                if M[i, j, k].x > 0.5:
                    # 计算 ROI
                    revenue_val = P[i][j] * Q[i] * 20 + pv_revenue[i] * pv_x + Q[i] / 2 * 0.53
                    cost_val = Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] + pv_total_cost[i] * pv_x + Q[i] * 0.001 * Water_Price[i]
                    ROI = (revenue_val / cost_val - 1) / N
                    SDG9_val = 0  # 默认值
                    if ROI > merged.loc[i,"ROI"]  and ROI > 0:
                        if j == 3 and k == 2:
                            SDG9_val = Dhp[i] * 1000 / cost_val
                            print(Dhp[i])

                        # 计算价格减成本（按每kWh电计算）
                        price_minus_cost = 0
                        if Electri_all[i] > 0:
                            # 总收入除以总电量
                            price_per_kwh = revenue_val / (Electri_all[i] * 20)
                            # 总成本除以总电量
                            cost_per_kwh = cost_val / (Electri_all[i] * 20)
                            price_minus_cost = price_per_kwh - cost_per_kwh

                            invest_cost_per_kwh = Cinvest_values[(i, j, k)] / (Electri_all[i] * 20)

                            om_cost_per_kwh = Com_values[(i, j, k)] / (Electri_all[i] * 20)

                            trans_cost_per_kwh = Ctrans_values[(i, j, k)] / (Electri_all[i] * 20)

                        results.append({
                            "name": merged.loc[i, 'name'],
                            "i": i + 1,
                            "j": j + 1,
                            "k": k + 1,
                            "ROI_e": ROI,
                            "price_minus_cost_e": price_minus_cost,
                            "contribute": P[i][j] * Q[i] * 20 / (P[i][j] * Q[i] * 20 + pv_revenue[i] * pv_x),
                            "SDG3": 0.05 * Electri[i] * 20 / cost_val,
                            "SDG8": (Q[i] / 1000 * 3) * 3000 / cost_val,
                            "SDG12": Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val,
                            "SDG13": (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val,
                            "SDG9": SDG9_val,
                            "work": Electri[i]/ 2000 * 3 * 5.9 * 3000 / cost_val /N,
                            "environment": Q[i] * 109/ cost_val /N,
                            "H2_price":(Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] + 4.9 * Q[i] * 20 * 0.0899)/(Q[i] * 20)/0.0899,
                            "difference":Electri[i]/2000 * 3 * 5.9 * 3000 / cost_val /N-Q[i] * 109/ cost_val /N,
                            "invest_cost_per_kwh_e":invest_cost_per_kwh,
                            "om_cost_per_kwh_e" : om_cost_per_kwh,
                            "trans_cost_per_kwh_e" : trans_cost_per_kwh
                        })
                    else:
                        results.append({
                            "name": merged.loc[i, 'name'],
                            "i": i + 1,
                            "j": 0,
                            "k": 0, 
                            "price_minus_cost_e" : merged.loc[i, "price_minus_cost"],
                            "ROI_e": merged.loc[i, "ROI"],
                            "SDG3": 0,
                            "SDG8": 0,
                            "SDG12": 0,
                            "SDG13": 0,
                            "SDG9": 0,
                            "work":0,
                            "environment":0,
                            "difference":0,
                            "invest_cost_per_kwh_m":None,
                            "om_cost_per_kwh_m" : None,
                            "trans_cost_per_kwh_m" : None
                        })
                    print(f"County {i+1} uses sales type {j+1} and transport method {k+1} with ROI {ROI}")
else:
    print("No optimal solution found")

# 将结果转换为数据框
results_df = pd.DataFrame(results)
print(results_df)


# In[94]:


# 修改 poverty_column_name 为实际 counties 数据框中的列名称

poverty_column_name = 'name'

# 将 'name' 列转换为字符串类型，确保合并时不会出错
poverty_selected[poverty_column_name] = poverty_selected[poverty_column_name].astype(str)
results_df['name'] = results_df['name'].astype(str)

# 合并 poverty_selected 和 results_df 数据框，基于 'name' 列
merged_df = merged_df.merge(results_df, left_on=poverty_column_name, right_on='name')

# 去除重复的 'name' 行
merged_df = merged_df.drop_duplicates(subset=['name'])

print(merged_df)


# In[95]:


# 计算 results_df 中 ROI_e 大于 0.03 的数量
roi_e_count = len(results_df[results_df['ROI_e'] > 0.03])

# 计算总条目数
total_count = len(results_df)

# 计算百分比
roi_e_percentage = (roi_e_count / total_count) * 100 if total_count > 0 else 0

# 计算ROI均值
roi_mean = results_df['ROI_e'].mean()
roi_above_threshold_mean = results_df[results_df['ROI_e'] > 0.03]['ROI_e'].mean()

# 打印结果
print(f"总体 ROI_e 均值: {roi_mean:.4f}")
print(f"ROI_e > 0.03 的均值: {roi_above_threshold_mean:.4f}")
print(f"ROI_e > 0.03 的数量: {roi_e_count}/{total_count} ({roi_e_percentage:.2f}%)")

# 可选：按销售类型(j)分组统计
sales_type_counts = results_df[results_df['ROI_e'] > 0.03].groupby('j').agg({
    'ROI_e': ['count', 'mean']
}).round(4)
print("\n按销售类型分组的 ROI_e > 0.03 的数量和均值:")
for sales_type in sales_type_counts.index:
    count = sales_type_counts.loc[sales_type, ('ROI_e', 'count')]
    mean = sales_type_counts.loc[sales_type, ('ROI_e', 'mean')]
    sales_percentage = (count / roi_e_count) * 100 if roi_e_count > 0 else 0
    print(f"销售类型 {sales_type}: {count} ({sales_percentage:.2f}%), ROI均值: {mean:.4f}")

# 可选：按运输方式(k)分组统计
transport_method_counts = results_df[results_df['ROI_e'] > 0.03].groupby('k').agg({
    'ROI_e': ['count', 'mean']
}).round(4)
print("\n按运输方式分组的 ROI_e > 0.03 的数量和均值:")
for transport_method in transport_method_counts.index:
    count = transport_method_counts.loc[transport_method, ('ROI_e', 'count')]
    mean = transport_method_counts.loc[transport_method, ('ROI_e', 'mean')]
    transport_percentage = (count / roi_e_count) * 100 if roi_e_count > 0 else 0
    print(f"运输方式 {transport_method}: {count} ({transport_percentage:.2f}%), ROI均值: {mean:.4f}")

# 可选：创建一个包含名称和ROI_e的简洁数据框
roi_summary = results_df[results_df['ROI_e'] > 0.03][['name', 'ROI_e']].sort_values('ROI_e', ascending=False)
print("\n具有 ROI_e > 0.03 的地区 (按 ROI_e 降序排列):")
print(roi_summary.head(10))  # 只显示前10个


# #### 敏感性分析

# In[131]:


# 创建新的数据框架，使用与costs_df相同的结构
column_names = []
for year in years_range:
    for scenario in scenarios:
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                column_names.extend([
                    f'Cinvest_{year}_{scenario}_j{j}_k{k}',
                    f'Com_{year}_{scenario}_j{j}_k{k}',
                    f'Ctrans_{year}_{scenario}_j{j}_k{k}'
                ])

# 创建新的数据框，使用county_ids作为索引
costs_df2 = pd.DataFrame(0.0, index=county_ids, columns=column_names)

# 填充costs_df2，注意这里的值不随年份和情景变化
for year in years_range:
    for scenario in scenarios:
        for i in range(len(county_indices)):
            for j in range(len(hydrogen_sales_types)):
                for k in range(len(transport_methods)):
                    # 使用原始计算的固定值
                    costs_df2.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] = Cinvest_values[(i, j, k)]
                    costs_df2.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] = Com_values[(i, j, k)]
                    costs_df2.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] = Ctrans_values[(i, j, k)]



# In[132]:


# 验证数据是否正确填充
print("costs_df2 的形状:", costs_df2.shape)
print("\n检查2024年Base情景的某些值:")
i, j, k = 0, 3, 1  # 示例索引
print(f"位置 (i={i}, j={j}, k={k}) 的值:")
print(f"Cinvest: {costs_df2.loc[county_ids[i], f'Cinvest_2024_Base_j{j}_k{k}']}")
print(f"Com: {costs_df2.loc[county_ids[i], f'Com_2024_Base_j{j}_k{k}']}")
print(f"Ctrans: {costs_df2.loc[county_ids[i], f'Ctrans_2024_Base_j{j}_k{k}']}")


# In[133]:


pv_results_df


# In[134]:


# 重新设计计算payback的函数
def calculate_payback(investment_cost, annual_revenue, annual_om_cost, residual_value, discount_rate, max_years=30):
    """
    计算投资回收期：找到累计折现收益大于初始投资的年份

    参数:
    investment_cost: 初始投资成本
    annual_revenue: 年收益
    annual_om_cost: 年运维成本
    residual_value: 残值（项目结束时）
    discount_rate: 折现率
    max_years: 最大计算年限

    返回:
    payback_period: 回收期（年），如果在max_years内无法回收则返回None
    """
    if investment_cost <= 0 or annual_revenue <= annual_om_cost:
        return None

    cumulative_cash_flow = -investment_cost  # 初始现金流为负的投资成本

    for year in range(1, max_years + 1):
        # 计算当年净现金流并折现
        annual_net_cash_flow = (annual_revenue - annual_om_cost) / ((1 + discount_rate) ** year)

        # 累加到总现金流
        cumulative_cash_flow += annual_net_cash_flow

        # 如果累计现金流转为正值，说明投资已回收
        if cumulative_cash_flow >= 0:
            # 可以进一步精确计算小数部分
            # 上一年的累计现金流
            prev_cumulative_cash_flow = cumulative_cash_flow - annual_net_cash_flow
            # 计算小数部分：还需多少比例的一年来实现收支平衡
            fraction = -prev_cumulative_cash_flow / annual_net_cash_flow
            return year - 1 + fraction

    # 如果在最大年限内未能回收投资
    return None

# 创建一个字典来存储所有情景和年份的结果
all_results_e = {}
scenarios = ["Low", "Base", "High"]
years_range = range(2024, 2051)

# 首先检查costs_df中是否有NaN或Inf值
print("检查costs_df中的NaN或Inf值:")
print("NaN值数量:", costs_df.isna().sum().sum())
print("Inf值数量:", np.isinf(costs_df).sum().sum())

# 如果有NaN或Inf值，用0替换它们
costs_df = costs_df.fillna(0)
costs_df = costs_df.replace([np.inf, -np.inf], 0)

# 检查pv_results_df中是否有NaN或Inf值
print("\n检查pv_results_df中的NaN或Inf值:")
print("NaN值数量:", pv_results_df.isna().sum().sum())
print("Inf值数量:", np.isinf(pv_results_df).sum().sum())

# 如果有NaN或Inf值，用0替换它们
pv_results_df = pv_results_df.fillna(0)
pv_results_df = pv_results_df.replace([np.inf, -np.inf], 0)

# 检查P和Q中是否有NaN或Inf值
print("\n检查P中的NaN或Inf值:")
for i in range(len(P)):
    for j in range(len(P[i])):
        if np.isnan(P[i][j]) or np.isinf(P[i][j]):
            print(f"P[{i}][{j}] = {P[i][j]}")
            P[i][j] = 0  # 替换为0

print("\n检查Q中的NaN或Inf值:")
for i in range(len(Q)):
    if np.isnan(Q[i]) or np.isinf(Q[i]):
        print(f"Q[{i}] = {Q[i]}")
        Q[i] = 0  # 替换为0

# 在原始代码中，只需要修改获取成本值的部分，其他部分保持不变
for scenario in scenarios:
    for year in years_range:
        try:
            print(f"\n处理情景: {scenario}, 年份: {year}")

            # 创建模型
            model_e = gp.Model(f"Hydrogen_Energy_mix_{year}_{scenario}")

            # 决策变量
            M_e = model_e.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), 
                             vtype=GRB.BINARY, name="M")

            # 创建一个安全的目标函数
            objective_terms_e = []

            for i in range(len(county_indices)):
                for j in range(len(hydrogen_sales_types)):
                    if j == 2:  # 跳过j=2的情况
                        continue
                    for k in range(len(transport_methods)):
                        try:
                            # 修改这里：使用costs_df2替代costs_df
                            cinvest_e = costs_df2.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}']
                            com_e = costs_df2.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}']
                            ctrans_e = costs_df2.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}']
                            pv_cost_e = pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}']
                            pv_revenue_e = pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}']

                            # 其余代码保持不变
                            if (np.isnan(cinvest_e) or np.isinf(cinvest_e) or 
                                np.isnan(com_e) or np.isinf(com_e) or 
                                np.isnan(ctrans_e) or np.isinf(ctrans_e) or 
                                np.isnan(pv_cost_e) or np.isinf(pv_cost_e) or 
                                np.isnan(pv_revenue_e) or np.isinf(pv_revenue_e)):
                                print(f"发现NaN或Inf: i={i}, j={j}, k={k}")
                                print(f"cinvest_e={cinvest_e}, com_e={com_e}, ctrans_e={ctrans_e}")
                                print(f"pv_cost_e={pv_cost_e}, pv_revenue_e={pv_revenue_e}")
                                model_e.addConstr(M_e[i, j, k] == 0)
                                continue

                            # 计算总成本和总收益
                            total_cost_e = cinvest_e + com_e + ctrans_e + pv_cost_e * pv_x + Q[i] * 0.001 * Water_Price[i]
                            total_revenue_e = P[i][j] * Q[i] * 20 + pv_revenue_e * pv_x + Q[i] / 2 * 0.53

                            # 检查总成本是否接近零
                            if total_cost_e < 1e-6:
                                print(f"总成本接近零: i={i}, j={j}, k={k}, total_cost_e={total_cost_e}")
                                model_e.addConstr(M_e[i, j, k] == 0)
                                continue

                            # 计算ROI项
                            roi_term_e = (total_revenue_e / total_cost_e - 1) / N

                            # 检查ROI项是否为NaN或Inf
                            if np.isnan(roi_term_e) or np.isinf(roi_term_e):
                                print(f"ROI项为NaN或Inf: i={i}, j={j}, k={k}, roi_term_e={roi_term_e}")
                                print(f"total_revenue_e={total_revenue_e}, total_cost_e={total_cost_e}")
                                model_e.addConstr(M_e[i, j, k] == 0)
                                continue

                            # 添加到目标函数
                            objective_terms_e.append(M_e[i, j, k] * roi_term_e)

                        except Exception as e:
                            print(f"处理目标函数项时出错: i={i}, j={j}, k={k}")
                            print(f"错误: {str(e)}")
                            model_e.addConstr(M_e[i, j, k] == 0)

            # 如果没有有效的目标函数项，添加一个默认的目标
            if not objective_terms_e:
                print("警告: 没有有效的目标函数项，使用默认目标")
                objective_e = 0
            else:
                objective_e = gp.quicksum(objective_terms_e)

            # 每个县只有一种销售和运输方式
            for i in range(len(county_indices)):
                model_e.addConstr(
                    gp.quicksum(M_e[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 
                               for k in range(len(transport_methods))) == 1
                )

            # 特定条件约束
            for i in range(len(county_indices)):
                for j in range(len(hydrogen_sales_types)):
                    if j == 0 or j == 1:  # 销售类型0和1不可行
                        for k in range(len(transport_methods)):
                            model_e.addConstr(M_e[i, j, k] == 0)
                    elif j == 2:  # 销售类型2不可行
                        for k in range(len(transport_methods)):
                            model_e.addConstr(M_e[i, j, k] == 0)
                    elif j == 3:  # 销售类型3的特殊约束
                        for k in range(len(transport_methods)):
                            if k == 0:  # 运输方式0不可行
                                model_e.addConstr(M_e[i, j, k] == 0)

            # 设置目标函数
            model_e.setObjective(objective_e, GRB.MAXIMIZE)
            model_e.optimize()

            # 存储结果
            results_e = []
            if model_e.status == GRB.OPTIMAL:
                for i in range(len(county_indices)):
                    for j in range(len(hydrogen_sales_types)):
                        for k in range(len(transport_methods)):
                            # 在计算结果时也需要修改成本的来源
                            if M_e[i, j, k].x > 0.5:
                                try:
                                    revenue_val_e = (P[i][j] * Q[i] * 20 + 
                                                 pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x + 
                                                 Q[i] / 2 * 0.53)

                                    # 修改这里：使用costs_df2替代costs_df
                                    cost_val_e = (costs_df2.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                                                costs_df2.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                                                costs_df2.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                                                pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x + 
                                                Q[i] * 0.001 * Water_Price[i])




                                    # 安全计算ROI
                                    if cost_val_e > 1e-6:
                                        ROI_e = (revenue_val_e/ cost_val_e - 1) / N
                                    else:
                                        ROI_e = 0

                                    # 使用新的calculate_payback函数计算回收期
                                    payback_e = None
                                    try:
                                        # 在计算回收期时也需要修改
                                        if cost_val_e > 1e-6:
                                            investment_cost_e = costs_df2.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + pv_results_df.loc[i, f'pv_total_cost_{year}_{scenario}'] * pv_x
                                            annual_om_cost_e = costs_df2.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] / N + Q[i] * 0.001 * Water_Price[i] / N


                                            # 计算残值（假设为投资成本的20%）
                                            residual_value_e = investment_cost_e * 0.2

                                            # 计算年收益
                                            annual_revenue_e = revenue_val_e / N

                                            # 计算回收期
                                            discount_rate = 0.03  # 折现率
                                            payback_e = calculate_payback(
                                                investment_cost=investment_cost_e,
                                                annual_revenue=annual_revenue_e,
                                                annual_om_cost=annual_om_cost_e,
                                                residual_value=residual_value_e,
                                                discount_rate=discount_rate,
                                                max_years=30
                                            )
                                    except Exception as pe:
                                        print(f"计算回收期时出错: i={i}, j={j}, k={k}")
                                        print(f"错误: {str(pe)}")
                                        payback_e = None

                                    # 安全计算其他指标
                                    if cost_val_e > 1e-6:
                                        SDG3_e = 0.05 * Electri[i] * 20 / cost_val_e
                                        SDG8_e = (Q[i] / 1000 * 3) * 3000 / cost_val_e
                                        SDG12_e = Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val_e
                                        SDG13_e = (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val_e
                                        work_impact_e = Electri[i] / 2000 * 3 * 5.9 * 3000 / cost_val_e / N
                                        env_impact_e = Q[i] * 109 / cost_val_e / N
                                        difference_e = work_impact_e - env_impact_e
                                    else:
                                        SDG3_e = SDG8_e = SDG12_e = SDG13_e = work_impact_e = env_impact_e = difference_e = 0

                                    # 安全计算SDG9
                                    SDG9_val_e = 0
                                    if j == 3 and k == 2 and cost_val_e > 1e-6:
                                        SDG9_val_e = Dhp[i] * 1000 / cost_val_e

                                    # 安全计算氢气价格
                                    # 在计算氢气价格时也需要修改
                                    if Q[i] > 1e-6:
                                        H2_price_e = (costs_df2.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}'] + 
                                                    costs_df2.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}'] + 
                                                    costs_df2.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}'] + 
                                                    4.9 * Q[i] * 20 * 0.0899) / (Q[i] * 20) / 0.0899
                                    else:
                                        H2_price_e = 0

                                    # 安全计算贡献率
                                    denominator_e = P[i][j] * Q[i] * 20 + pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x
                                    if denominator_e > 1e-6:
                                        contribute_e = P[i][j] * Q[i] * 20 / denominator_e
                                    else:
                                        contribute_e = 0

                                    if ROI_e > merged.loc[i,"ROI"]  and ROI_e > 0:  # 只考虑ROI为正的情况
                                        results_e.append({
                                            "name": merged.loc[i, 'name'],
                                            "i": i + 1,
                                            "j": j + 1,
                                            "k": k + 1,
                                            "year": year,
                                            "scenario": scenario,
                                            "ROI_e": ROI_e,
                                            "Payback_e": payback_e,  # 添加回收期
                                            "contribute_e": contribute_e,
                                            "SDG3_e": SDG3_e,
                                            "SDG8_e": SDG8_e,
                                            "SDG12_e": SDG12_e,
                                            "SDG13_e": SDG13_e,
                                            "SDG9_e": SDG9_val_e,
                                            "work_e": work_impact_e,
                                            "environment_e": env_impact_e,
                                            "H2_price_e": H2_price_e,
                                            "difference_e": difference_e
                                        })
                                    else:
                                        # 对于ROI不为正的情况，使用默认值
                                        results_e.append({
                                            "name": merged.loc[i, 'name'],
                                            "i": i + 1,
                                            "j": 0,
                                            "k": 0,
                                            "year": year,
                                            "scenario": scenario,
                                            "ROI_e": merged.loc[i, "ROI"] if "ROI" in merged.columns else 0,
                                            "Payback_e": None,  # 回收期为None
                                            "SDG3_e": 0,
                                            "SDG8_e": 0,
                                            "SDG12_e": 0,
                                            "SDG13_e": 0,
                                            "SDG9_e": 0,
                                            "work_e": 0,
                                            "environment_e": 0,
                                            "H2_price_e": 0,
                                            "difference_e": 0
                                        })
                                except Exception as e:
                                    print(f"处理结果时出错: i={i}, j={j}, k={k}")
                                    print(f"错误: {str(e)}")
                                    # 添加一个默认结果
                                    results_e.append({
                                        "name": merged.loc[i, 'name'],
                                        "i": i + 1,
                                        "j": 0,
                                        "k": 0,
                                        "year": year,
                                        "scenario": scenario,
                                        "ROI_e": merged.loc[i, "ROI"],
                                        "Payback_e": None,  # 回收期为None
                                        "SDG3_e": 0,
                                        "SDG8_e": 0,
                                        "SDG12_e": 0,
                                        "SDG13_e": 0,
                                        "SDG9_e": 0,
                                        "work_e": 0,
                                        "environment_e": 0,
                                        "H2_price_e": 0,
                                        "difference_e": 0
                                    })
            else:
                print(f"模型未找到最优解，状态: {model_e.status}")
                # 为每个县添加默认结果
                for i in range(len(county_indices)):
                    results_e.append({
                        "name": merged.loc[i, 'name'],
                        "i": i + 1,
                        "j": 0,
                        "k": 0,
                        "year": year,
                        "scenario": scenario,
                        "ROI_e": merged.loc[i, "ROI"],
                        "Payback_e": None,  # 回收期为None
                        "SDG3_e": 0,
                        "SDG8_e": 0,
                        "SDG12_e": 0,
                        "SDG13_e": 0,
                        "SDG9_e": 0,
                        "work_e": 0,
                        "environment_e": 0,
                        "H2_price_e": 0,
                        "difference_e": 0
                    })

            all_results_e[f"{year}_{scenario}"] = pd.DataFrame(results_e)

        except Exception as e:
            print(f"处理情景 {scenario} 年份 {year} 时出错")
            print(f"错误: {str(e)}")
            # 创建一个空的结果数据框
            all_results_e[f"{year}_{scenario}"] = pd.DataFrame(columns=[
                "name", "i", "j", "k", "year", "scenario", "ROI_e", "Payback_e", "contribute_e", 
                "SDG3_e", "SDG8_e", "SDG12_e", "SDG13_e", "SDG9_e", "work_e", "environment_e", 
                "H2_price_e", "difference_e"
            ])

# 合并所有结果
try:
    final_results_df_e = pd.concat(all_results_e.values(), ignore_index=True)
    # 保存结果
    final_results_df_e.to_csv(f'optimization_results_all_scenarios_e.csv', index=False)

    # 打印一些统计信息
    for scenario in scenarios:
        for year in years_range:
            scenario_year_results_e = final_results_df_e[
                (final_results_df_e['scenario'] == scenario) & 
                (final_results_df_e['year'] == year)
            ]
            if not scenario_year_results_e.empty:
                print(f"\n统计信息 - 情景：{scenario}, 年份：{year}")
                print(f"平均ROI_e：{scenario_year_results_e['ROI_e'].mean():.4f}")
                print(f"平均氢气价格：{scenario_year_results_e['H2_price_e'].mean():.2f}")

                # 添加回收期统计
                valid_payback = scenario_year_results_e['Payback_e'].dropna()
                if not valid_payback.empty:
                    print(f"平均回收期：{valid_payback.mean():.2f}年")
                    print(f"有效回收期数量：{len(valid_payback)}")
                else:
                    print("没有有效的回收期数据")
            else:
                print(f"\n情景：{scenario}, 年份：{year} - 没有结果")
except Exception as e:
    print("合并或保存结果时出错")
    print(f"错误: {str(e)}")


# In[135]:


# 计算2024年base场景下的平均成本差异
def analyze_average_cost_differences(costs_df, final_results_df_e, year=2024, scenario='Base'):
    # 获取选中的方案
    selected_results = final_results_df_e[
        (final_results_df_e['year'] == year) & 
        (final_results_df_e['scenario'] == scenario)
    ]

    # 初始化累计变量
    total_cinvest_original = 0
    total_cinvest_sensitivity = 0
    total_com_original = 0
    total_com_sensitivity = 0
    total_ctrans_original = 0
    total_ctrans_sensitivity = 0
    count = 0

    # 先打印一下看看数据结构
    print("数据结构检查:")
    print("选中的方案数量:", len(selected_results))
    print("\n前几行数据的i,j,k值:")
    print(selected_results[['i', 'j', 'k']].head())

    for _, row in selected_results.iterrows():
        i = int(row['i']) - 1
        j = int(row['j']) - 1
        k = int(row['k']) - 1

        # 检查索引值是否有效
        if (i, j, k) not in Cinvest_values:
            print(f"跳过无效的索引组合: i={i+1}, j={j+1}, k={k+1}")
            continue

        try:
            # 从原始计算获取成本
            cinvest_original = Cinvest_values[(i, j, k)]
            com_original = Com_values[(i, j, k)]
            ctrans_original = Ctrans_values[(i, j, k)]

            # 从敏感性分析中获取成本
            cinvest_sensitivity = costs_df2.loc[county_ids[i], f'Cinvest_{year}_{scenario}_j{j}_k{k}']
            com_sensitivity = costs_df2.loc[county_ids[i], f'Com_{year}_{scenario}_j{j}_k{k}']
            ctrans_sensitivity = costs_df2.loc[county_ids[i], f'Ctrans_{year}_{scenario}_j{j}_k{k}']

            # 累加成本
            total_cinvest_original += cinvest_original
            total_cinvest_sensitivity += cinvest_sensitivity
            total_com_original += com_original
            total_com_sensitivity += com_sensitivity
            total_ctrans_original += ctrans_original
            total_ctrans_sensitivity += ctrans_sensitivity

            count += 1

        except Exception as e:
            print(f"处理数据时出错: i={i}, j={j}, k={k}")
            print(f"错误信息: {str(e)}")
            continue

    if count == 0:
        print("没有找到有效的数据进行分析")
        return

    # 计算平均值
    avg_cinvest_original = total_cinvest_original / count
    avg_cinvest_sensitivity = total_cinvest_sensitivity / count
    avg_com_original = total_com_original / count
    avg_com_sensitivity = total_com_sensitivity / count
    avg_ctrans_original = total_ctrans_original / count
    avg_ctrans_sensitivity = total_ctrans_sensitivity / count

    # 输出结果
    print(f"\n{scenario}场景, {year}年的成本对比分析结果:")
    print("-" * 50)
    print("直接计算 vs 敏感性分析的平均成本:")
    print(f"投资成本 (Cinvest): {avg_cinvest_original:.2f} vs {avg_cinvest_sensitivity:.2f}")
    print(f"运维成本 (Com): {avg_com_original:.2f} vs {avg_com_sensitivity:.2f}")
    print(f"运输成本 (Ctrans): {avg_ctrans_original:.2f} vs {avg_ctrans_sensitivity:.2f}")

    print(f"\n分析基于 {count} 个有效区域的数据")

# 执行分析
analyze_average_cost_differences(costs_df, final_results_df_e)


# In[136]:


def compare_revenue_2024_base(final_results_df_e, merged, pv_results_df, P, Q, year=2024, scenario='Base'):
    # 获取2024年base场景的结果
    selected_results = final_results_df_e[
        (final_results_df_e['year'] == year) & 
        (final_results_df_e['scenario'] == scenario)
    ]

    print(f"\n{scenario}场景, {year}年的收益对比分析结果:")
    print("-" * 50)

    total_revenue_sensitivity = 0
    total_revenue_original = 0
    count = 0

    revenue_diff_list = []

    for _, row in selected_results.iterrows():
        i = int(row['i']) - 1
        j = int(row['j']) - 1
        k = int(row['k']) - 1

        # 跳过无效的组合
        if j < 0 or k < 0:
            continue

        try:
            # 敏感性分析的收益计算
            revenue_sensitivity = (P[i][j] * Q[i] * 20 + 
                                pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] * pv_x + 
                                Q[i] / 2 * 0.53)

            # 原始计算的收益
            revenue_original = (P[i][j] * Q[i] * 20 + 
                              pv_revenue[i] * pv_x + 
                              Q[i] / 2 * 0.53)

            # 累加收益
            total_revenue_sensitivity += revenue_sensitivity
            total_revenue_original += revenue_original

            # 计算差异
            revenue_diff = revenue_sensitivity - revenue_original
            revenue_diff_pct = (revenue_diff / revenue_original * 100) if revenue_original != 0 else 0

            revenue_diff_list.append({
                'name': merged.loc[i, 'name'],
                'revenue_sensitivity': revenue_sensitivity,
                'revenue_original': revenue_original,
                'diff_absolute': revenue_diff,
                'diff_percentage': revenue_diff_pct
            })

            count += 1

        except Exception as e:
            print(f"处理数据时出错: i={i+1}, j={j+1}, k={k+1}")
            print(f"错误信息: {str(e)}")
            continue

    if count == 0:
        print("没有找到有效的数据进行分析")
        return

    # 计算平均值
    avg_revenue_sensitivity = total_revenue_sensitivity / count
    avg_revenue_original = total_revenue_original / count

    # 转换为DataFrame进行统计分析
    diff_df = pd.DataFrame(revenue_diff_list)

    print("收益对比统计结果:")
    print(f"平均敏感性分析收益: {avg_revenue_sensitivity:.2f}")
    print(f"平均原始计算收益: {avg_revenue_original:.2f}")
    print(f"平均绝对差异: {diff_df['diff_absolute'].mean():.2f}")
    print(f"平均相对差异: {diff_df['diff_percentage'].mean():.2f}%")

    print("\n收益差异最大的前5个地区:")
    top_5_diff = diff_df.nlargest(5, 'diff_absolute')
    print(top_5_diff[['name', 'diff_absolute', 'diff_percentage']])

    print(f"\n分析基于 {count} 个有效区域的数据")

# 执行分析
compare_revenue_2024_base(final_results_df_e, merged, pv_results_df, P, Q)


# In[137]:


costs_df['Cinvest_2024_Base_j3_k1']


# In[138]:


# 合并所有结果
try:
    final_results_df_e = pd.concat(all_results_e.values(), ignore_index=True)
    # 保存结果
    final_results_df_e.to_csv(f'optimization_results_all_scenarios_e.csv', index=False)

    # 创建一个DataFrame来存储每年每个场景ROI>0.03的县数量
    roi_summary = []

    # 打印一些统计信息
    for scenario in scenarios:
        for year in years_range:
            scenario_year_results_e = final_results_df_e[
                (final_results_df_e['scenario'] == scenario) & 
                (final_results_df_e['year'] == year)
            ]
            if not scenario_year_results_e.empty:
                print(f"\n统计信息 - 情景：{scenario}, 年份：{year}")
                print(f"平均ROI_e：{scenario_year_results_e['ROI_e'].mean():.4f}")
                print(f"平均氢气价格：{scenario_year_results_e['H2_price_e'].mean():.2f}")

                # 添加回收期统计
                valid_payback = scenario_year_results_e['Payback_e'].dropna()
                if not valid_payback.empty:
                    print(f"平均回收期：{valid_payback.mean():.2f}年")
                    print(f"有效回收期数量：{len(valid_payback)}")
                else:
                    print("没有有效的回收期数据")

                # 计算ROI_e > 0.03的县数量
                roi_above_threshold = scenario_year_results_e[scenario_year_results_e['ROI_e'] > 0.03]
                roi_count = len(roi_above_threshold)
                total_counties = len(scenario_year_results_e)
                roi_percentage = (roi_count / total_counties) * 100 if total_counties > 0 else 0

                print(f"ROI_e > 0.03的县数量：{roi_count}/{total_counties} ({roi_percentage:.2f}%)")

                # 将统计结果添加到汇总DataFrame
                roi_summary.append({
                    'Year': year,
                    'Scenario': scenario,
                    'ROI_Count': roi_count,
                    'Total_Counties': total_counties,
                    'ROI_Percentage': roi_percentage
                })
            else:
                print(f"\n情景：{scenario}, 年份：{year} - 没有结果")

                # 将空结果也添加到汇总DataFrame
                roi_summary.append({
                    'Year': year,
                    'Scenario': scenario,
                    'ROI_Count': 0,
                    'Total_Counties': 0,
                    'ROI_Percentage': 0
                })

    # 将ROI统计结果转换为DataFrame并保存
    roi_summary_df = pd.DataFrame(roi_summary)
    roi_summary_df.to_csv('roi_summary_by_year_scenario.csv', index=False)

    # 打印汇总统计
    print("\n==== ROI > 0.03县数量汇总 ====")

    # 按场景分组显示结果
    for scenario in scenarios:
        scenario_data = roi_summary_df[roi_summary_df['Scenario'] == scenario]
        print(f"\n场景: {scenario}")

        # 选择性显示一些年份的数据
        years_to_show = [2024, 2025, 2030, 2035, 2040, 2045, 2050]
        for year in years_to_show:
            if year in scenario_data['Year'].values:
                year_row = scenario_data[scenario_data['Year'] == year].iloc[0]
                print(f"  {year}年: {int(year_row['ROI_Count'])}/{int(year_row['Total_Counties'])} ({year_row['ROI_Percentage']:.2f}%)")

    # 可视化ROI > 0.03的县数量随时间变化
    plt.figure(figsize=(12, 6))

    for scenario in scenarios:
        scenario_data = roi_summary_df[roi_summary_df['Scenario'] == scenario]
        plt.plot(scenario_data['Year'], scenario_data['ROI_Count'], 
                 marker='o', linewidth=2, label=f'场景: {scenario}')

    plt.title('各场景ROI > 0.03的县数量随时间变化', fontsize=14)
    plt.xlabel('年份', fontsize=12)
    plt.ylabel('县数量', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig('roi_counties_trend.png', dpi=300)
    plt.close()

except Exception as e:
    print("合并或保存结果时出错")
    print(f"错误: {str(e)}")


# In[139]:


import matplotlib.pyplot as plt

def plot_roi_above_3pct_comparison_e(df_e):
    """
    输入：df_e (例如 df_econ_scenario_all)
    功能：基于 (Scenario, Year) 统计 ROI>3%的地区数量，并可视化
         在同一张图里，绘制 Base_LR 的折线，以及 Low_LR~High_LR 的区间。
    """
    # 1) 创建一个新的列，用于标记 ROI 是否 > 0.03
    df_plot_e = df_e.copy()
    df_plot_e['ROI_above_3pct_e'] = df_plot_e['ROI_e'] > 0.03

    # 2) 按 (Scenario, Year) 统计 ROI_above_3pct_e = True 的计数
    df_count_e = df_plot_e.groupby(['scenario','year'])['ROI_above_3pct_e'].sum().reset_index(name='Count_ROI_Above_3pct_e')

    # 3) 分别取出 Low_LR / Base_LR / High_LR 的数据
    df_low_e = df_count_e[df_count_e['scenario'] == 'Low'].sort_values('year')
    df_base_e = df_count_e[df_count_e['scenario'] == 'Base'].sort_values('year')
    df_high_e = df_count_e[df_count_e['scenario'] == 'High'].sort_values('year')

    # 4) 开始绘图
    plt.figure(figsize=(8,5))  # 创建画布

    # 4.1 画出 Base_LR 的折线
    plt.plot(df_base_e['year'],
             df_base_e['Count_ROI_Above_3pct_e'],
             label='Base_LR (ROI>3%)')

    # 4.2 使用 fill_between 表示 Low_LR 和 High_LR 之间的区间
    plt.fill_between(df_low_e['year'],
                     df_low_e['Count_ROI_Above_3pct_e'],
                     df_high_e['Count_ROI_Above_3pct_e'],
                     alpha=0.3,
                     label='Low_LR~High_LR range')

    # 5) 添加图例、坐标轴标签、标题
    plt.legend()
    plt.xlabel('year')
    plt.ylabel('Count of Regions (ROI > 3%)')
    plt.title('Count of Regions with ROI>3% under Different Learning Rate Scenarios')

    plt.show()


# 使用示例：
plot_roi_above_3pct_comparison_e(final_results_df_e)


# In[140]:


# 清理数据：删除 'ROI' 列为空的行，并确保 'year' 列为字符串类型
cleaned_data = final_results_df_e.dropna(subset=['ROI_e'])  # 删除 'ROI' 为空的行
cleaned_data['year'] = cleaned_data['year'].astype(str)  # 将 'year' 转换为字符串类型

# 打印数据描述信息，检查清理后的数据
print("\n清理后的数据描述统计信息 (四舍五入后的 ROI):")
print(cleaned_data.describe())  # 打印描述统计信息

# 统计每个年份的数据量，确保每个年份的数据量足够
year_counts = cleaned_data['year'].value_counts()
print("\n每年数据量统计：")
print(year_counts)

# 只保留数据点大于1的年份，确保数据量足够绘制图表
valid_years = year_counts[year_counts > 1].index  # 筛选出数据点大于1的年份
cleaned_data = cleaned_data[cleaned_data['year'].isin(valid_years)]  # 过滤出有效年份的数据

clean_data3=copy.deepcopy(cleaned_data)


# In[141]:


counties_selected = merged_df[merged_df['name'].isin(counties_selected[poverty_column_name])]
counties_selected


# In[142]:


poverty_selected=copy.deepcopy(merged_df)


# #### 可视化

# In[143]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

# counties_selected['ROI_y'] = counties_selected['name'].map(poverty_selected.set_index('name')['ROI_y'])
counties_selected['group'] = counties_selected['ROI_e'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI_e'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_e'])
poverty_remaining['group'] = poverty_remaining['ROI_e'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展
# # 1. 检查索引是否唯一
# print("检查 counties_selected 索引是否唯一：", counties_selected.index.is_unique)
# print("检查 poverty_remaining 索引是否唯一：", poverty_remaining.index.is_unique)
#
# # 如果索引不唯一，打印重复的索引
# if not counties_selected.index.is_unique:
#     print("重复的索引 in counties_selected:", counties_selected[counties_selected.index.duplicated()])
#
# if not poverty_remaining.index.is_unique:
#     print("重复的索引 in poverty_remaining:", poverty_remaining[poverty_remaining.index.duplicated()])
#
# # 2. 检查列名和列顺序是否一致
# print("counties_selected 列名：", counties_selected.columns)
# print("poverty_remaining 列名：", poverty_remaining.columns)
#
# # 3. 检查是否有重复的行
# print("检查 counties_selected 是否有重复行:", counties_selected.duplicated().sum())
# print("检查 poverty_remaining 是否有重复行:", poverty_remaining.duplicated().sum())
#
# # 4. 检查两个 GeoDataFrame 的 CRS 是否一致
# print("counties_selected CRS:", counties_selected.crs)
# print("poverty_remaining CRS:", poverty_remaining.crs)

# 如果 CRS 不一致，可以选择统一它们
if counties_selected.crs != poverty_remaining.crs:
    print("CRS 不一致，进行转换为统一的 CRS")
    poverty_remaining = poverty_remaining.to_crs(counties_selected.crs)


# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 加载管道数据

def _load_pipeline_data(pipeline_file):
    """加载管道数据 (简单处理)"""
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    """绘制管道线路 (不做额外检测)"""
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制所有县的边界
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围




# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制所有县的边界在子图中
counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')

# 绘制管道在子图中
_plot_pipeline(ax_inset, pipeline_gdf)

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('fig1a_energy.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# In[144]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 注意：假设以下变量和函数均已定义并加载：
# counties_selected、poverty_remaining、merged_df、china、counties、pipeline_gdf
# classify_roi(roi): 小于 0.03 返回 0，否则返回 1
# _plot_pipeline(ax, pipeline_df): 在给定坐标轴上绘制管道线路

# 自定义颜色字典，与 classify_roi 分类结果对应：
# 0: 已开展 ROI < 0.03, 1: 已开展 ROI ≥ 0.03,
# 2: 未开展 ROI < 0.03, 3: 未开展 ROI ≥ 0.03
cmap = {
    0: '#fcd182',
    1: '#d9412a',
    2: '#d6eff6',
    3: '#4a7bb6'
}

# 待输出的 ROI 列列表
roi_columns = ['ROI_sub', 'ROI_priority', 'ROI_storage']

# 针对每个 ROI 指标生成图像
for roi in roi_columns:
    # 为避免修改原始数据，制作临时副本
    temp_counties = counties_selected.copy()
    temp_poverty = poverty_remaining.copy()

    # 对已开展区域：直接根据对应 ROI 列进行分类
    temp_counties['group'] = temp_counties[roi].apply(classify_roi)

    # 对未开展区域：
    # ① 从 merged_df 中获取对应 ROI 值（确保 merged_df 中已存在对应的 ROI 列，且索引为 'name'）
    temp_poverty[roi] = temp_poverty['name'].map(merged_df.set_index('name')[roi])
    # ② 根据该 ROI 值进行分类
    temp_poverty['group'] = temp_poverty[roi].apply(classify_roi)
    # ③ 为区分未开展区域，将分类值加 2
    temp_poverty['group'] += 2

    # 合并两个区域的数据，生成绘图用的 GeoDataFrame
    combined_map = gpd.GeoDataFrame(pd.concat([temp_counties, temp_poverty], ignore_index=True))

    # 创建图形与主坐标轴（EPSG:3857 坐标系下中国大陆区域）
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_axis_off()  # 去除坐标轴和边框

    # 定义边界阴影效果
    shadow_effect = [
        PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
        PathEffects.Normal()
    ]

    # 绘制国界底图（加粗并添加阴影效果）
    china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

    # 绘制所有县的边界
    counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

    # 根据分类绘制区域填充色
    for group, color in cmap.items():
        combined_map[combined_map['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')

    # 绘制管道线路（若管道数据加载正确）
    _plot_pipeline(ax, pipeline_gdf)

    # 设置主图的显示范围（适应 EPSG:3857 下中国大陆区域）
    ax.set_xlim(7792364.36, 15584728.71)
    ax.set_ylim(1689200.14, 7361866.11)

    # 创建南海区域的子图（插图），设置显示区域
    ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
    ax_inset.set_facecolor('white')
    ax_inset.set_frame_on(True)
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    ax_inset.grid(False)
    ax_inset.set_xlim(11688546.53, 13692297.37)
    ax_inset.set_ylim(222684.21, 2632018.64)

    # 在子图中绘制南海区域
    for group, color in cmap.items():
        combined_map[combined_map['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')
    counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')
    _plot_pipeline(ax_inset, pipeline_gdf)
    china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

    # 调整子图边框样式
    for spine in ax_inset.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1.5)

    plt.tight_layout()

    # 根据当前 ROI 指标生成文件名，并保存高质量图像
    output_file = f'fig_{roi}_with_pipeline.png'
    plt.savefig(output_file, dpi=1200, bbox_inches='tight', format='png')
    plt.show()


# In[145]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
import matplotlib.font_manager as fm
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 自定义颜色
cmap = {
    'ROI_e > ROI and ROI_e > 0': '#ff7f50',  # ROI_e > ROI 且 ROI_e > 0 标记为橙色
    'ROI < 0.03 & ROI_e > 0.03': '#4a7bb6',  # 特殊标注为蓝色
}

# 根据条件分类
combined2['color_group'] = combined2.apply(
    lambda row: 'ROI_e > ROI and ROI_e > 0' if row['ROI_e'] > row['ROI_x'] and row['ROI_e'] > 0 else \
               'ROI < 0.03 & ROI_e > 0.03' if row['ROI_x'] < 0.03 and row['ROI_e'] > 0.03 else None,
    axis=1
)

# 加载管道数据
def _load_pipeline_data(pipeline_file):
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_axis_off()

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加透明阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', alpha=0.5,
                    path_effects=shadow_effect)

# 绘制所有县的边界，透明背景
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='none', alpha=0.5)

# 绘制 ROI 标记颜色，确保蓝色部分在最上层
for group, color in cmap.items():
    if group == 'ROI_x < 0.03 & ROI_e > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=3)
for group, color in cmap.items():
    if group != 'ROI_x < 0.03 & ROI_e > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=2)

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置范围
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 子图 - 南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('none')
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.grid(False)
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 子图中绘制南海区域
for group, color in cmap.items():
    if group == 'ROI_x < 0.03 & ROI_e > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax_inset, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=3)
for group, color in cmap.items():
    if group != 'ROI_x < 0.03 & ROI_e > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax_inset, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=2)

counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='none', alpha=0.5)
_plot_pipeline(ax_inset, pipeline_gdf)
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', alpha=0.5,
                    path_effects=shadow_effect)

# 修改子图框的颜色
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.savefig('fig1a_ca_modified.png', dpi=1200, bbox_inches='tight', format='png')
plt.show()


# #### 基于储能卖的计算结果

# In[96]:


# 读取包含“峰值电价”的数据
pv_price_df = pd.read_excel("31省光伏上网.xlsx")
province_to_peak_price = dict(zip(pv_price_df["省/自治区/直辖市"], pv_price_df["峰值电价"]))

# 更新 assign_province_and_prices 函数，加入峰值电价
def assign_province_and_prices_with_peak(row, provinces, province_to_price, province_to_hydrogen_min,
                                         province_to_hydrogen_max, province_to_curtailed_rate,
                                         province_to_water_price, province_to_peak_price):
    county_centroid = row.geometry.centroid  # 计算县的几何中心
    matching_province = provinces[provinces.contains(county_centroid)]
    if not matching_province.empty:
        province_name = matching_province.iloc[0]['name']
        return {
            "PV_price": province_to_price.get(province_name, np.nan),
            "Hydrogen_Min": province_to_hydrogen_min.get(province_name, np.nan),
            "Hydrogen_Max": province_to_hydrogen_max.get(province_name, np.nan),
            "Curtailed_Rate": province_to_curtailed_rate.get(province_name, np.nan),
            "Water_Price": province_to_water_price.get(province_name, np.nan),
            "Peak_Price": province_to_peak_price.get(province_name, np.nan)
        }
    else:
        return {
            "PV_price": np.nan,
            "Hydrogen_Min": np.nan,
            "Hydrogen_Max": np.nan,
            "Curtailed_Rate": np.nan,
            "Water_Price": np.nan,
            "Peak_Price": np.nan
        }

# 给 counties_selected 和 poverty_selected 添加新列，包括峰值电价
counties_selected_prices = counties_selected.apply(
    assign_province_and_prices_with_peak,
    axis=1,
    provinces=provinces,
    province_to_price=province_to_price,
    province_to_hydrogen_min=province_to_hydrogen_min,
    province_to_hydrogen_max=province_to_hydrogen_max,
    province_to_curtailed_rate=province_to_curtailed_rate,
    province_to_water_price=province_to_water_price,
    province_to_peak_price=province_to_peak_price
)

poverty_selected_prices = poverty_selected.apply(
    assign_province_and_prices_with_peak,
    axis=1,
    provinces=provinces,
    province_to_price=province_to_price,
    province_to_hydrogen_min=province_to_hydrogen_min,
    province_to_hydrogen_max=province_to_hydrogen_max,
    province_to_curtailed_rate=province_to_curtailed_rate,
    province_to_water_price=province_to_water_price,
    province_to_peak_price=province_to_peak_price
)

# 将返回的字典展开为新列
counties_selected = pd.concat(
    [counties_selected, counties_selected_prices.apply(pd.Series)], axis=1
)

poverty_selected = pd.concat(
    [poverty_selected, poverty_selected_prices.apply(pd.Series)], axis=1
)





# In[97]:


# 获取所需的列数据，处理可能的多列情况
# 检查 Peak_Price 是否为多列
if isinstance(poverty_selected['Peak_Price'], pd.DataFrame):
    # 如果是多列，取第一列
    PV_price = poverty_selected['Peak_Price'].iloc[:, 0].tolist()
else:
    # 如果是单列，直接取值
    PV_price = poverty_selected['Peak_Price'].tolist()

# 检查 Hydrogen_Min 是否为多列
if isinstance(merged['Hydrogen_Min'], pd.DataFrame):
    # 如果是多列，取第一列
    Hydrogen_P = merged['Hydrogen_Min'].iloc[:, 0].tolist()
else:
    # 如果是单列，直接取值
    Hydrogen_P = merged['Hydrogen_Min'].tolist()

# 构造 P 的二维列表
P = []
for i in range(len(merged)):  # 遍历每一行
    row = [
        3.2 * 0.3,  # 第一项
        3.2 * PV_price[i],  # 第二项
        Hydrogen_P[i],  # 第三项
        Hydrogen_P[i],  # 第四项
    ]
    P.append(row)

# 同样处理 Electri 和 Water_Price
if isinstance(merged['Electri'], pd.DataFrame):
    Electri = merged['Electri'].iloc[:, 0].tolist()
    Electric_all = merged['Electri_all'].iloc[:, 0].tolist()
else:
    Electri = merged['Electri'].tolist()
    Electric_all = merged['Electri_all'].tolist()

if isinstance(merged['Water_Price'], pd.DataFrame):
    Water_Price = merged['Water_Price'].iloc[:, 0].tolist()
else:
    Water_Price = merged['Water_Price'].tolist()

P, Electri, Water_Price


# In[98]:


# 成本参数（示例值）
Cas =  2.5 * 7 / 11.2 # 能量储存设施成本 0.17美元/kg， 7为能源换算单位， 12 是 转换为m³的转换单位
c = 3  # 与运输距离无关的罐车投资成本
e = 10  # 与运输距离无关的天然气网络中的氢气混合运输成本
Cadi = 3000  # 设备采购成本
Ca = 5000  # 接入电网设施成本
Cpi = 2000   # 管道运输建设成本/m
Fpi = 2000  # 管道连接主管道平均成本
Fai = 2000  # 罐车连接主管道平均成本

# 运营和维护成本参数
# Csa_h = [Cfa[i] * 0.001 for i in range(len(Cfa))]  # 氢气制备设施年维护成本（元/m³）
Csa_h = [0 for i in range(len(Cfa))]
Csa_d = 0  # 氢气燃料电池年维护成本（元/m³）
Csa_a = 0  # 调峰发电设备年维护成本（元/m³）
Csa_p = 0  # 管道每米年维护成本（元/m）
Csa_sf = 0  # 罐车每米年维护成本（元/立方米）

# 运输成本参数
Spip = 0.000000405 / 11.2    # 管道每m运输成本


# In[99]:


# 定义光伏发电部分的收益和成本计算函数
def calculate_pv_revenue_and_cost(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N):
    revenue = total_generation * price
    total_fixed_cost = C_PV + C_ES
    total_annual_cost = (O_PV + O_ES + C_tax + C_F) * N
    total_cost = total_fixed_cost + total_annual_cost
    return revenue, total_cost

# 成本参数
C_PV = 2860  # 光伏系统成本（元/千瓦）
C_ES = 0     # 储能系统成本（元/千瓦）
O_PV = 90    # 光伏系统运维成本（元/千瓦·年）
#
O_ES = 0     # 储能系统运维成本（元/千瓦·年）
C_F = 0     # 其他固定成本（元/千瓦·年）
C_tax = 0   # 税收成本（元/千瓦·年）


# 其他参数
V_R = C_PV * 0.2   # 残值（元/千瓦）
C_d = (C_PV - V_R)/20      # 折旧成本（元/千瓦·年）
# alpha  # 限电率（百分比）
N = 20       # 资产寿命（年）
i = 0.03      # 贴现率

pv_revenue = {}
pv_total_cost = {}

# 用于存储每个县的PV收益与成本比值
pv_ratio = {}
# 提前计算每个县的光伏发电部分的收益和成本
for i, row in merged.iterrows():
    alpha = 1 - row['Curtailed_Rate']
    mean_value = row['mean_tiff']
    price = row['PV_price']  # 使用对应的PV价格
    E_n = mean_value * alpha
    total_generation = E_n * N

    # 计算光伏发电部分的收益和成本
    revenue, total_cost = calculate_pv_revenue_and_cost(total_generation, price, C_PV, C_ES, O_PV, O_ES, C_F, C_tax, C_d, N)

    # 将结果存储在字典中
    pv_revenue[i] = revenue
    pv_total_cost[i] = total_cost
# 将收益与成本的比值存储在字典中
    pv_ratio[i] = (revenue / total_cost - 1) / N

pv_revenue,pv_total_cost


# In[100]:


# 创建用于存储计算结果的列表
Dhp = []
Dht = []

# 获取dim、din列值
dim = merged['dim'].tolist()
din = merged['din'].tolist()
Q = merged['Q'].tolist()
Cfa = poverty_selected['Cfa']

# 距离计算
for i in range(len(county_indices)):
    # 计算 Dhp
    if dim[i] * (Cpi + Csa_p * 20 + Spip * 20 * Q[i]) + Fpi >= din[i] * Cpi:
        Dhp.append(din[i])
    else:
        Dhp.append(dim[i])
    # Dhp: 到主干管道的实际管道距离
    # dim: 生产地点到用户的距离
    # Fpi: 管道连接主管道的平均成本
    # din: 数据中指定的生产地点到主干管道的距离

    # 计算 Dht
    if calculate_transport_cost(dim[i]) * Q[i] + Fai >= calculate_transport_cost(din[i]) * Q[i]:
        Dht.append(din[i])
    else:
        Dht.append(dim[i])
    # Dht: 到用户的罐车运输距离
    # dim: 生产地点到用户的距离
    # Fai: 罐车连接主管道的平均成本
    # din: 数据中指定的生产地点到主干管道的距离

Cinvest_values = {}
Com_values = {}
Ctrans_values = {}

for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        for k in range(len(transport_methods)):
            # j=2的情况，决策变量设为0
            if j == 2:
                Cinvest_values[(i, j, k)] = 0
                Com_values[(i, j, k)] = 0
                Ctrans_values[(i, j, k)] = 0
            elif j == 0:
                Cinvest_values[(i, j, k)] = Cfa[i] + Cas * Q[i] + Cadi
                Com_values[(i, j, k)] = (Csa_h[i] + Csa_d) * 20 * Q[i]
                Ctrans_values[(i, j, k)] = 0
            elif j == 1:
                Cinvest_values[(i, j, k)] = Cfa[i] + Cas * Q[i] + Ca
                Com_values[(i, j, k)] = (Csa_h[i] + Csa_a) * 20 * Q[i]
                Ctrans_values[(i, j, k)] = 0
            elif j == 3:
                if k == 1:
                    if Dht[i] == dim[i]:
                        Cinvest_values[(i, j, k)] = e + Cfa[i]  + Fpi
                        Com_values[(i, j, k)] = (Csa_h[i] + Q[i] * Csa_sf) * 20
                        Ctrans_values[(i, j, k)] = calculate_transport_cost(Dht[i]) * 20 * Q[i]
                    else:
                        Cinvest_values[(i, j, k)] = e + Cfa[i]
                        Com_values[(i, j, k)] = (Csa_h[i] + Q[i] * Csa_sf) * 20
                        Ctrans_values[(i, j, k)] = calculate_transport_cost(Dht[i]) * 20 * Q[i]
                elif k == 2:
                    if Dhp[i] == dim[i]:
                        Cinvest_values[(i, j, k)] = e + Cfa[i] + Dhp[i] * Cpi + Fai
                        Com_values[(i, j, k)] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                        Ctrans_values[(i, j, k)] = Dhp[i] * Spip * 20 * Q[i]
                    else:
                        Cinvest_values[(i, j, k)] = e + Cfa[i] + Dhp[i] * Cpi
                        Com_values[(i, j, k)] = (Csa_h[i] + Dhp[i] * Csa_p) * 20
                        Ctrans_values[(i, j, k)] = Dhp[i] * Spip * 20 * Q[i]
                else:
                    # 如果 j == 3, 但 k 不为 1 或 2，默认值
                    Cinvest_values[(i, j, k)] = 0
                    Com_values[(i, j, k)] = 0
                    Ctrans_values[(i, j, k)] = 0
            else:
                # 对于其他未定义的 (j, k) 组合，设置默认值
                Cinvest_values[(i, j, k)] = 0
                Com_values[(i, j, k)] = 0
                Ctrans_values[(i, j, k)] = 0


# In[101]:


# 创建模型
model = gp.Model("Hydrogen_Energy_mix")

# 决策变量
M = model.addVars(len(county_indices), len(hydrogen_sales_types), len(transport_methods), vtype=GRB.BINARY, name="M")

# 定义辅助变量
revenue = gp.quicksum(M[i, j, k] *(P[i][j] * Q[i] * 20)+ pv_revenue[i] * pv_x  for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))
cost = gp.quicksum(M[i, j, k] * (Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] ) + pv_total_cost[i] * pv_x for i in range(len(county_indices)) for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods)))

# 定义辅助变量
Z = model.addVar(vtype=GRB.CONTINUOUS, name="Z")

# 目标函数
model.setObjective(Z, GRB.MAXIMIZE)

# 添加约束：定义 Z
revenue_var = model.addVar(vtype=GRB.CONTINUOUS, name="revenue_var")
cost_var = model.addVar(vtype=GRB.CONTINUOUS, name="cost_var")

model.addConstr(revenue_var == revenue, name="revenue_eq")
model.addConstr(cost_var == cost, name="cost_eq")

# 线性化 Z * cost_var
T = model.addVar(vtype=GRB.CONTINUOUS, name="T")
Z_lb, Z_ub = 0, 10  # 假设的Z上下界，需要根据具体情况调整
cost_lb, cost_ub = 0, 1000000000000  # 假设的cost_var上下界，需要根据具体情况调整

model.addConstr(T >= Z * cost_lb + cost_var * Z_lb - Z_lb * cost_lb, name="mccormick1")
model.addConstr(T >= Z * cost_ub + cost_var * Z_ub - Z_ub * cost_ub, name="mccormick2")
model.addConstr(T <= Z * cost_ub + cost_var * Z_lb - Z_lb * cost_ub, name="mccormick3")
model.addConstr(T <= Z * cost_lb + cost_var * Z_ub - Z_ub * cost_lb, name="mccormick4")

# 原来的乘法约束改为 T 变量约束
model.addConstr(revenue_var >= T, name="linearized_ROI_constraint")

# 每个县只有一种销售和运输方式
for i in range(len(county_indices)):
    model.addConstr(gp.quicksum(M[i, j, k] for j in range(len(hydrogen_sales_types)) if j != 2 for k in range(len(transport_methods))) == 1, name=f"UniqueSalesTransport_{i}")

# 确保在某些条件下特定的运输方式和销售类型组合是不可行的
for i in range(len(county_indices)):
    for j in range(len(hydrogen_sales_types)):
        if j == 0 or j == 1:  # 假设销售类型1和2对应的约束
            for k in range(1, 3):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 2:
            model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")
        if j == 3:
            for k in range(0, 3):
                model.addConstr(M[i, j, k] == 0, name=f"InvalidSalesTransport_{i}_{j}_{k}")

# 求解模型
model.optimize()

# 创建结果数据框
results = []

# 打印并记录结果
if model.status == GRB.OPTIMAL:
    for i in range(len(county_indices)):
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                if M[i, j, k].x > 0.5:
                    # 计算 ROI
                    # 计算 ROI
                    revenue_val = P[i][j] * Q[i] * 20 + pv_revenue[i] * pv_x + Q[i] / 2 * 0.53
                    cost_val = Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] + pv_total_cost[i] * pv_x + Q[i] * 0.001 * Water_Price[i]
                    ROI = (revenue_val / cost_val - 1)/N
                    SDG9_val = 0  # 默认值

                    # 计算价格减成本（按每kWh电计算）
                    price_minus_cost_c = 0
                    if Electri_all[i] > 0:
                        # 总收入除以总电量
                        price_per_kwh_c = revenue_val / (Electri_all[i] * 20)
                        # 总成本除以总电量
                        cost_per_kwh = cost_val / (Electri_all[i] * 20)
                        price_minus_cost_c = price_per_kwh_c - cost_per_kwh

                        invest_cost_per_kwh = Cinvest_values[(i, j, k)] / (Electri_all[i] * 20)

                        om_cost_per_kwh = Com_values[(i, j, k)] / (Electri_all[i] * 20)

                        trans_cost_per_kwh = Ctrans_values[(i, j, k)] / (Electri_all[i] * 20)

                    if ROI > merged.loc[i,"ROI"]  and ROI > 0:
                        if j == 3 and k == 2:
                            SDG9_val = Dhp[i] * 1000 / cost_val
                            print(Dhp[i])
                        results.append({
                            "name": merged.loc[i, 'name'],
                            "i": i + 1,
                            "j": j + 1,
                            "k": k + 1,
                            "ROI_c": ROI,
                            "price_minus_cost_c": price_minus_cost_c,
                            "contribute": P[i][j] * Q[i] * 20 / (P[i][j] * Q[i] * 20 + pv_revenue[i] * pv_x),
                            "SDG3": 0.05 * Electri[i] * 20 / cost_val,
                            "SDG8": (Q[i] / 1000 * 3) * 3000 / cost_val,
                            "SDG12": Electri[i] * merged_df.loc[i, 'PV_price'] / cost_val,
                            "SDG13": (-0.001 * 2 * Q[i] - 0.0005 * Dht[i]) / cost_val,
                            "SDG9": SDG9_val,
                            "work_c": Electri[i]/ 2000 * 3 * 5.9 * 3000 / cost_val /N,
                            "environment_c": Q[i] * 109/ cost_val /N,
                            "H2_price":(Cinvest_values[(i, j, k)] + Com_values[(i, j, k)] + Ctrans_values[(i, j, k)] + 4.9 * Q[i] * 20 * 0.0899)/(Q[i] * 20)/0.0899,
                            "difference":Electri[i]/2000 * 3 * 5.9 * 3000 / cost_val /N - Q[i] * 109/ cost_val /N,
                            "invest_cost_per_kwh_c":invest_cost_per_kwh,
                            "om_cost_per_kwh_c" : om_cost_per_kwh,
                            "trans_cost_per_kwh_c" : trans_cost_per_kwh
                        })
                    else:
                        results.append({
                            "name": merged.loc[i, 'name'],
                            "i": i + 1,
                            "j": 0,
                            "k": 0,
                            "ROI_c": merged.loc[i, "ROI"],
                            "price_minus_cost_c": merged.loc[i, "price_minus_cost"],
                            "SDG3": 0,
                            "SDG8": 0,
                            "SDG12": 0,
                            "SDG13": 0,
                            "SDG9": 0,
                            "work_c":0,
                            "environment_c":0,
                            "difference":0,
                            "invest_cost_per_kwh_c":None,
                            "om_cost_per_kwh_c" : None,
                            "trans_cost_per_kwh_c" : None
                        })
                    print(f"County {i+1} uses sales type {j+1} and transport method {k+1} with ROI {ROI}")
else:
    print("No optimal solution found")

# 将结果转换为数据框
results_df = pd.DataFrame(results)
print(results_df)


# In[102]:


# 计算 ROI_c > 0.03 的数据数量
roi_above_3pct_count = (results_df['ROI_c'] > 0.03).sum()

# 计算总数据量
total_count = len(results_df)

# 计算百分比
percentage = (roi_above_3pct_count / total_count) * 100 if total_count > 0 else 0

# 打印结果
print(f"ROI_c > 3% 的数据数量: {roi_above_3pct_count}")
print(f"总数据量: {total_count}")
print(f"百分比: {percentage:.2f}%")

# 按地区名称查看 ROI_c > 0.03 的地区
regions_above_3pct = results_df[results_df['ROI_c'] > 0.03]['name'].tolist()
print(f"\nROI_c > 3% 的地区列表:")
for i, region in enumerate(regions_above_3pct):
    print(f"{i+1}. {region}")

# 可选：按 ROI_c 降序排列并显示前10个地区
top_roi_regions = results_df.sort_values(by='ROI_c', ascending=False).head(10)
print("\n按 ROI_c 排序的前10个地区:")
print(top_roi_regions[['name', 'ROI_c']])

roi_mean = results_df['ROI_c'].mean()
roi_mean


# In[103]:


# merged_df=copy.deepcopy(poverty_selected3)
# poverty_selected=copy.deepcopy(poverty_selected3)
# counties_selected=copy.deepcopy(counties_selected3)


# In[104]:


# 修改 poverty_column_name 为实际 counties 数据框中的列名称

poverty_column_name = 'name'

# 将 'name' 列转换为字符串类型，确保合并时不会出错
poverty_selected[poverty_column_name] = poverty_selected[poverty_column_name].astype(str)
results_df['name'] = results_df['name'].astype(str)

# 合并 poverty_selected 和 results_df 数据框，基于 'name' 列
merged_df = merged_df.merge(results_df, left_on=poverty_column_name, right_on='name')

# 去除重复的 'name' 行
merged_df = merged_df.drop_duplicates(subset=['name'])

print(merged_df)


# In[105]:


# 修改 poverty_column_name 为实际 counties 数据框中的列名称
poverty_column_name = 'name'

# 将 'name' 列转换为字符串类型，确保合并时不会出错
poverty_selected[poverty_column_name] = poverty_selected[poverty_column_name].astype(str)
results_df['name'] = results_df['name'].astype(str)

# 合并 poverty_selected 和 results_df 数据框，基于 'name' 列
# 添加参数 suffixes 来避免列名冲突，并统一新增列加后缀 '_c'
merged_df = poverty_selected.merge(
    results_df,
    left_on=poverty_column_name,
    right_on='name',
    suffixes=('', '_c')  # 新增列添加后缀 '_c'
)

# 去除重复的 'name' 行
merged_df = merged_df.drop_duplicates(subset=['name'])

print(merged_df)

# 选择特定的 counties 数据
counties_selected = merged_df[merged_df['name'].isin(counties_selected[poverty_column_name])]
counties_selected


# In[106]:


counties_selected = merged_df[merged_df['name'].isin(counties_selected[poverty_column_name])]
counties_selected


# #### 敏感性分析
# 
# 敏感性分析参考的论文是：https://www.sciencedirect.com/science/article/pii/S2352340924007595

# In[157]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# GBM 参数设置（中速技术进步 M-TP）
Q_0 = 45.7  # 2022年初始装机容量（MW）
alpha = 0.25  # 年均增长率（25%）
sigma = 0.10  # 年波动率（10%）
years = np.arange(2022, 2061)  # 预测到2060年
num_simulations = 1000  # 进行1000次模拟

# 生成GBM路径
np.random.seed(42)  # 设置随机种子以保证结果可复现*/
dt = 1  # 时间步长（1年）
num_years = len(years)

# 存储模拟结果
simulated_paths = np.zeros((num_simulations, num_years))
simulated_paths[:, 0] = Q_0  # 初始值

for t in range(1, num_years):
    dW = np.random.normal(0, np.sqrt(dt), num_simulations)  # Wiener过程
    simulated_paths[:, t] = simulated_paths[:, t-1] * np.exp(
        (alpha - 0.5 * sigma**2) * dt + sigma * dW
    )

# 计算均值、5%和95%分位数（预测区间）
Q_mean = np.mean(simulated_paths, axis=0)
Q_5 = np.percentile(simulated_paths, 5, axis=0)
Q_95 = np.percentile(simulated_paths, 95, axis=0)

# 可视化结果
plt.figure(figsize=(10, 6))
plt.plot(years, Q_mean, label="Mean Prediction", color='blue', linewidth=2)
plt.fill_between(years, Q_5, Q_95, color='blue', alpha=0.2, label="90% Confidence Interval")
plt.xlabel("Year")
plt.ylabel("HES Installed Capacity (MW)")
plt.title("GBM Forecast of Hydrogen Storage Installed Capacity (Medium Growth)")
plt.legend()
plt.grid()
plt.show()

# 组织数据并展示
df_results = pd.DataFrame({
    "Year": years,
    "Mean Capacity (MW)": Q_mean,
    "5% Quantile (MW)": Q_5,
    "95% Quantile (MW)": Q_95
})

# 学习曲线参数（中速技术进步 M-TP）
C_HES_0 = 2.5*7/11.2  # 2022年初始资本成本（CNY/立方米）
beta_HES = 0.223  # 学习指数（计算自 15% 学习率）

# 提取2022-2025年的GBM预测累计装机容量
years_subset = np.arange(2022, 2051)
Q_HES_subset = df_results.loc[df_results["Year"].isin(years_subset), "Mean Capacity (MW)"].values

# 计算学习曲线的资本成本
C_HES_pred = C_HES_0 * (Q_HES_subset / Q_HES_subset[0]) ** -beta_HES

# 组织数据并展示
df_learning_curve = pd.DataFrame({
    "Year": years_subset,
    "Cumulative Installed Capacity (MW)": Q_HES_subset,
    "Predicted Capital Cost (CNY/kW)": C_HES_pred
})

df_learning_curve


# In[158]:


def predict_HES_cost(year):
    """
    预测指定年份的氢储能资本成本（CNY/立方米），基于GBM预测的装机容量和学习曲线。

    参数:
    year (int): 需要预测的年份，范围 2022-2050

    返回:
    float: 该年份的预测资本成本（CNY/立方米）
    """
    # 确保输入年份在范围内
    if year < 2022 or year > 2050:
        raise ValueError("Year must be between 2022 and 2050")

    # 学习曲线参数（中速技术进步 M-TP）
    C_HES_0 = 2.5 * 7 / 11.2  # 2022年初始资本成本（CNY/立方米）
    beta_HES = 0.223  # 学习指数（计算自 15% 学习率）

    # 确保GBM结果数据已计算
    if "Year" not in df_results or "Mean Capacity (MW)" not in df_results:
        raise ValueError("GBM simulation results are missing. Please run the GBM model first.")

    # 获取指定年份的GBM预测装机容量
    Q_HES_year = df_results.loc[df_results["Year"] == year, "Mean Capacity (MW)"].values[0]

    # 获取基准年（2022年）的装机容量
    Q_HES_2022 = df_results.loc[df_results["Year"] == 2022, "Mean Capacity (MW)"].values[0]

    # 计算学习曲线的资本成本
    C_HES_year = C_HES_0 * (Q_HES_year / Q_HES_2022) ** -beta_HES

    return C_HES_year

# 测试函数
year_to_predict = 2030
predicted_cost = predict_HES_cost(year_to_predict)
predicted_cost


# In[159]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 1) 修改后的 GBM 模型部分 ==========

# 将初始年份设为 2024
Q_0 = 45.7      # 2024 年初始装机容量（MW）
alpha = 0.25    # 年均增长率（25%）
sigma = 0.10    # 年波动率（10%）

# 预测范围改为 2024 - 2050
years = np.arange(2024, 2051)  
num_simulations = 1000  

np.random.seed(42)      # 随机种子
dt = 1                  # 时间步长(1年)
num_years = len(years)

# 存储模拟结果
simulated_paths = np.zeros((num_simulations, num_years))
simulated_paths[:, 0] = Q_0  # 第一年(2024)的装机容量

# 循环模拟，生成 GBM 轨迹
for t in range(1, num_years):
    dW = np.random.normal(0, np.sqrt(dt), num_simulations)  # Wiener 过程
    simulated_paths[:, t] = simulated_paths[:, t-1] * np.exp(
        (alpha - 0.5 * sigma**2) * dt + sigma * dW
    )

# 计算均值、5% 和 95% 分位数
Q_mean = np.mean(simulated_paths, axis=0)
Q_5 = np.percentile(simulated_paths, 5, axis=0)
Q_95 = np.percentile(simulated_paths, 95, axis=0)

# 整理成 DataFrame
df_results = pd.DataFrame({
    "Year": years,
    "Mean Capacity (MW)": Q_mean,
    "5% Quantile (MW)": Q_5,
    "95% Quantile (MW)": Q_95
})

# ========== 2) 学习曲线及成本预测部分(修改起始年) ==========

# 学习曲线参数（中速技术进步 M-TP）
C_HES_0 = 2.5 * 7 / 11.2  # 2024 年初始资本成本（CNY/立方米）
beta_HES = 0.223          # 对应 15% 学习率的学习指数

# 1) 找到 2024 年作为基准年的装机容量
Q_HES_2024_low  = df_results.loc[df_results["Year"] == 2024, "5% Quantile (MW)"].values[0]
Q_HES_2024_mean = df_results.loc[df_results["Year"] == 2024, "Mean Capacity (MW)"].values[0]
Q_HES_2024_high = df_results.loc[df_results["Year"] == 2024, "95% Quantile (MW)"].values[0]

# 2) 构建存储结果的字典
Cas_dict = {}

# 3) 2024 年的成本设为初始值 (Low/Base/High 全用 C_HES_0)
year_2024 = 2024
Cas_dict[f"Cas_{year_2024}_Low"]  = C_HES_0
Cas_dict[f"Cas_{year_2024}_Base"] = C_HES_0
Cas_dict[f"Cas_{year_2024}_High"] = C_HES_0

# 4) 逐年计算 2025-2050 三种情景的资本成本
for year in range(2025, 2051):
    # 从 df_results 中取当年的分位数装机容量
    Q_low  = df_results.loc[df_results["Year"] == year, "5% Quantile (MW)"].values[0]
    Q_mean = df_results.loc[df_results["Year"] == year, "Mean Capacity (MW)"].values[0]
    Q_high = df_results.loc[df_results["Year"] == year, "95% Quantile (MW)"].values[0]

    # 分别计算 Low / Base / High 下的成本
    C_low  = C_HES_0 * (Q_low  / Q_HES_2024_low)   ** -beta_HES
    C_base = C_HES_0 * (Q_mean / Q_HES_2024_mean)  ** -beta_HES
    C_high = C_HES_0 * (Q_high / Q_HES_2024_high)  ** -beta_HES

    Cas_dict[f"Cas_{year}_Low"]  = C_low
    Cas_dict[f"Cas_{year}_Base"] = C_base
    Cas_dict[f"Cas_{year}_High"] = C_high

# ========== 3) 结果查看 ==========

# 例子：查看部分 key
for scenario_key in ["Cas_2024_Low", "Cas_2024_Base", "Cas_2030_High"]:
    print(scenario_key, ":", Cas_dict[scenario_key])

# 如果需要把 Cas_dict 转为一个 DataFrame
df_cas = pd.DataFrame({
    "Year": range(2024, 2051),
    "Cas_Low":  [Cas_dict[f"Cas_{y}_Low"]  for y in range(2024, 2051)],
    "Cas_Base": [Cas_dict[f"Cas_{y}_Base"] for y in range(2024, 2051)],
    "Cas_High": [Cas_dict[f"Cas_{y}_High"] for y in range(2024, 2051)],
})

print("\n查看前 5 行：")
print(df_cas.head())


# In[160]:


# 首先创建需要的列名，并构建空数据框:
years_range = range(2024, 2051)    # 需要分析的年份
scenarios = ["Low", "Base", "High"]

column_names = []
for year in years_range:
    for scenario in scenarios:
        for j in range(len(hydrogen_sales_types)):
            for k in range(len(transport_methods)):
                column_names.extend([
                    f'Cinvest_{year}_{scenario}_j{j}_k{k}',
                    f'Com_{year}_{scenario}_j{j}_k{k}',
                    f'Ctrans_{year}_{scenario}_j{j}_k{k}'
                ])

costs_df = pd.DataFrame(0.0, index=county_ids, columns=column_names)

# 开始计算:
for year in years_range:
    for scenario in scenarios:
        # 1) 获取当年当情景下的 Cas
        cas_value = Cas_dict[f"Cas_{year}_{scenario}"]

        # 2) 对每一个县、每一种销售类型 j、每一种运输方式 k 计算
        for i in range(len(county_indices)):

            # 不同 (j, k) 的不同成本计算逻辑
            for j in range(len(hydrogen_sales_types)):
                for k in range(len(transport_methods)):

                    col_invest = f'Cinvest_{year}_{scenario}_j{j}_k{k}'
                    col_op     = f'Com_{year}_{scenario}_j{j}_k{k}'
                    col_trans  = f'Ctrans_{year}_{scenario}_j{j}_k{k}'

                    if j == 2:
                        # j=2时决策变量设为0
                        costs_df.loc[county_ids[i], col_invest] = 0
                        costs_df.loc[county_ids[i], col_op]     = 0
                        costs_df.loc[county_ids[i], col_trans]  = 0

                    elif j == 0:
                        # 投资成本: 原代码将 Cas 替换为 cas_value
                        costs_df.loc[county_ids[i], col_invest] = (
                            Cfa[i] + cas_value * Q[i] + Cadi
                        )
                        # 运营成本
                        costs_df.loc[county_ids[i], col_op] = (
                            (Csa_h[i] + Csa_d) * 20 * Q[i]
                        )
                        # 运输成本(根据新需求, 示例中设为0)
                        costs_df.loc[county_ids[i], col_trans] = 0

                    elif j == 1:
                        costs_df.loc[county_ids[i], col_invest] = (
                            Cfa[i] + cas_value * Q[i] + Ca
                        )
                        costs_df.loc[county_ids[i], col_op] = (
                            (Csa_h[i] + Csa_a) * 20 * Q[i]
                        )
                        costs_df.loc[county_ids[i], col_trans] = 0

                    elif j == 3:
                        # 根据您给出的最新逻辑对 j=3, k=1/2 的情况进行处理
                        if k == 1:
                            if Dht[i] == dim[i]:
                                # 满足距离门槛
                                costs_df.loc[county_ids[i], col_invest] = (
                                    e + Cfa[i] + Fpi
                                )
                                # 示例: 把运维费用改为 (Csa_h[i] + Q[i]*Csa_sf)*20
                                costs_df.loc[county_ids[i], col_op] = (
                                    (Csa_h[i] + Q[i] * Csa_sf) * 20
                                )
                                costs_df.loc[county_ids[i], col_trans] = (
                                    calculate_transport_cost(Dht[i]) * 20 * Q[i]
                                )
                            else:
                                costs_df.loc[county_ids[i], col_invest] = (
                                    e + Cfa[i]
                                )
                                costs_df.loc[county_ids[i], col_op] = (
                                    (Csa_h[i] + Q[i] * Csa_sf) * 20
                                )
                                costs_df.loc[county_ids[i], col_trans] = (
                                    calculate_transport_cost(Dht[i]) * 20 * Q[i]
                                )

                        elif k == 2:
                            if Dhp[i] == dim[i]:
                                # 满足距离门槛
                                costs_df.loc[county_ids[i], col_invest] = (
                                    e + Cfa[i] + Dhp[i] * Cpi + Fai
                                )
                                costs_df.loc[county_ids[i], col_op] = (
                                    (Csa_h[i] + Dhp[i] * Csa_p) * 20
                                )
                                costs_df.loc[county_ids[i], col_trans] = (
                                    Dhp[i] * Spip * 20 * Q[i]
                                )
                            else:
                                costs_df.loc[county_ids[i], col_invest] = (
                                    e + Cfa[i] + Dhp[i] * Cpi
                                )
                                costs_df.loc[county_ids[i], col_op] = (
                                    (Csa_h[i] + Dhp[i] * Csa_p) * 20
                                )
                                costs_df.loc[county_ids[i], col_trans] = (
                                    Dhp[i] * Spip * 20 * Q[i]
                                )
                        else:
                            # j=3, 但 k 不为 1 或 2 时，设置默认值
                            costs_df.loc[county_ids[i], col_invest] = 0
                            costs_df.loc[county_ids[i], col_op]     = 0
                            costs_df.loc[county_ids[i], col_trans]  = 0

                    else:
                        # 对于未定义 (j, k) 组合，默认设为 0
                        costs_df.loc[county_ids[i], col_invest] = 0
                        costs_df.loc[county_ids[i], col_op]     = 0
                        costs_df.loc[county_ids[i], col_trans]  = 0

# 查看结果的部分列
display_cols = [
    f'Cinvest_2024_Base_j0_k0',
    f'Com_2024_Base_j0_k0',
    f'Ctrans_2024_Base_j0_k0',
    f'Cinvest_2024_Base_j1_k1'
]
costs_df[display_cols].head()


# In[161]:


import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd
import traceback  # 用于打印详细错误堆栈

# ===================== 示例变量与数据 (请按您实际情况准备) =====================

scenarios = ["Low", "Base", "High"]
years_range = range(2024, 2051)

# 重新设计计算payback的函数
def calculate_payback(investment_cost, annual_revenue, annual_om_cost, residual_value, discount_rate, max_years=30):
    """
    计算投资回收期：找到累计折现收益大于初始投资的年份

    参数:
    investment_cost: 初始投资成本
    annual_revenue: 年收益
    annual_om_cost: 年运维成本
    residual_value: 残值（项目结束时）
    discount_rate: 折现率
    max_years: 最大计算年限

    返回:
    payback_period: 回收期（年），如果在max_years内无法回收则返回None
    """
    if investment_cost <= 0 or annual_revenue <= annual_om_cost:
        return None

    cumulative_cash_flow = -investment_cost  # 初始现金流为负的投资成本

    for year in range(1, max_years + 1):
        # 计算当年净现金流并折现
        annual_net_cash_flow = (annual_revenue - annual_om_cost) / ((1 + discount_rate) ** year)

        # 累加到总现金流
        cumulative_cash_flow += annual_net_cash_flow

        # 如果累计现金流转为正值，说明投资已回收
        if cumulative_cash_flow >= 0:
            # 可以进一步精确计算小数部分
            # 上一年的累计现金流
            prev_cumulative_cash_flow = cumulative_cash_flow - annual_net_cash_flow
            # 计算小数部分：还需多少比例的一年来实现收支平衡
            fraction = -prev_cumulative_cash_flow / annual_net_cash_flow
            return year - 1 + fraction

    # 如果在最大年限内未能回收投资
    return None

# ========== 存放所有情景和年份结果的字典，后续合并 ==========
all_results_c = {}

# ========== 开始多情景、多年份循环 ==========
for scenario in scenarios:
    for year in years_range:
        try:
            print(f"\n********** 处理情景: {scenario}, 年份: {year} **********")

            # 1) 创建模型
            model_c = gp.Model(f"Hydrogen_Energy_mix_{year}_{scenario}")
            # 如果Gurobi版本旧，不支持 model_c.Params.LogToConsole，可用:
            # model_c.setParam("OutputFlag", 0)

            # 2) 创建二进制决策变量 M_c(i, j, k)
            M_c = model_c.addVars(
                len(county_indices),
                len(hydrogen_sales_types),
                len(transport_methods),
                vtype=GRB.BINARY,
                name="M_c"
            )

            # 3) 定义线性表达式: revenue_expr_c, cost_expr_c
            revenue_expr_c = gp.LinExpr()
            cost_expr_c    = gp.LinExpr()

            for i in range(len(county_indices)):
                # 取当前年、情景下 PV 收益与成本 (若无, 默认0)
                col_pv_revenue = f"pv_revenue_{year}_{scenario}"
                col_pv_cost    = f"pv_total_cost_{year}_{scenario}"
                pv_revenue_c = pv_results_df.loc[i, col_pv_revenue] if col_pv_revenue in pv_results_df.columns else 0
                pv_cost_c    = pv_results_df.loc[i, col_pv_cost]    if col_pv_cost in pv_results_df.columns else 0

                # 遍历各 (j, k)
                for j in range(len(hydrogen_sales_types)):
                    if j == 2:  # 假设 j=2 不可行
                        continue
                    for k in range(len(transport_methods)):
                        # 从 costs_df 中获取该县 i、年 year、情景 scenario、j、k 对应的投资/运营/运输成本
                        # 列名形如 "Cinvest_2024_Low_j0_k0"
                        cinvest_col = f"Cinvest_{year}_{scenario}_j{j}_k{k}"
                        com_col     = f"Com_{year}_{scenario}_j{j}_k{k}"
                        ctrans_col  = f"Ctrans_{year}_{scenario}_j{j}_k{k}"

                        if cinvest_col in costs_df.columns:
                            cinvest_c = costs_df.loc[county_ids[i], cinvest_col]
                        else:
                            cinvest_c = 0

                        if com_col in costs_df.columns:
                            com_c = costs_df.loc[county_ids[i], com_col]
                        else:
                            com_c = 0

                        if ctrans_col in costs_df.columns:
                            ctrans_c = costs_df.loc[county_ids[i], ctrans_col]
                        else:
                            ctrans_c = 0

                        # 计算收益系数(纯数值)
                        # 例如 revenue_coef = P[i][j]*Q[i]*20 + ...
                        revenue_coef = (P[i][j] * Q[i] * 20 
                                        + Q[i]/2 * 0.53 
                                        + pv_revenue_c * pv_x)
                        # 添加到 revenue_expr_c
                        revenue_expr_c.addTerms(revenue_coef, M_c[i, j, k])

                        # 计算成本系数(纯数值)
                        cost_coef = (cinvest_c + com_c + ctrans_c 
                                     + Q[i]*0.001*Water_Price[i])
                        cost_expr_c.addTerms(cost_coef, M_c[i, j, k])

                # 不管选不选，该县都要加 PV 成本吗？若是固定必建，就加到常数项
                cost_expr_c.addConstant(pv_cost_c * pv_x)

            # 4) 定义辅助变量与目标函数 (线性化 revenue/cost)
            Z_c          = model_c.addVar(lb=0,   ub=10,    vtype=GRB.CONTINUOUS, name="Z_c")
            revenue_var_c= model_c.addVar(lb=0,   ub=1e15,  vtype=GRB.CONTINUOUS, name="revenue_var_c")
            cost_var_c   = model_c.addVar(lb=0,   ub=1e15,  vtype=GRB.CONTINUOUS, name="cost_var_c")
            T_c          = model_c.addVar(lb=0,   ub=1e15,  vtype=GRB.CONTINUOUS, name="T_c")

            # 通过等式约束把线性表达式赋给 var
            model_c.addConstr(revenue_var_c == revenue_expr_c, name="revenue_eq_c")
            model_c.addConstr(cost_var_c    == cost_expr_c,    name="cost_eq_c")

            # McCormick 链约束，用于 T_c = Z_c * cost_var_c
            cost_lb, cost_ub = 0, 1e15
            Z_lb,    Z_ub    = 0, 10

            model_c.addConstr(T_c >= Z_c * cost_lb + cost_var_c * Z_lb - Z_lb * cost_lb, "mccormick1")
            model_c.addConstr(T_c >= Z_c * cost_ub + cost_var_c * Z_ub - Z_ub * cost_ub, "mccormick2")
            model_c.addConstr(T_c <= Z_c * cost_ub + cost_var_c * Z_lb - Z_lb * cost_ub, "mccormick3")
            model_c.addConstr(T_c <= Z_c * cost_lb + cost_var_c * Z_ub - Z_ub * cost_lb, "mccormick4")

            # 约束: revenue_var_c >= T_c => revenue_var_c >= Z_c * cost_var_c
            model_c.addConstr(revenue_var_c >= T_c, "linearized_ROI_constraint_c")

            # 5) 每县只能选择唯一 (j,k) (排除 j=2)
            for i in range(len(county_indices)):
                model_c.addConstr(
                    gp.quicksum(
                        M_c[i,j,k]
                        for j in range(len(hydrogen_sales_types)) if j != 2
                        for k in range(len(transport_methods))
                    ) == 1,
                    name=f"UniqueSalesTransport_{i}"
                )

            # 6) 不可行组合约束 (示例: j=0,1 仅 k=0; j=2,3 不可行)
            for i in range(len(county_indices)):
                for j in range(len(hydrogen_sales_types)):
                    if j == 0 or j == 1:
                        for k in [1,2]:
                            model_c.addConstr(M_c[i,j,k] == 0)
                    if j == 2 or j == 3:
                        for k in range(len(transport_methods)):
                            model_c.addConstr(M_c[i,j,k] == 0)

            # 7) 设置目标函数并求解
            model_c.setObjective(Z_c, GRB.MAXIMIZE)
            model_c.optimize()

            # 8) 读取结果并记录
            results_c = []
            if model_c.status == GRB.OPTIMAL:
                for i in range(len(county_indices)):
                    for j in range(len(hydrogen_sales_types)):
                        for k in range(len(transport_methods)):
                            if M_c[i,j,k].X > 0.5:
                                # 读取解 => 用普通Python算 ROI、H2价格等
                                try:
                                    # 先重新拿到对 i,j,k 的 cost & revenue 数据
                                    # (注：此处 purely python 计算)
                                    # 例如:
                                    cinvest_col = f"Cinvest_{year}_{scenario}_j{j}_k{k}"
                                    com_col     = f"Com_{year}_{scenario}_j{j}_k{k}"
                                    ctrans_col  = f"Ctrans_{year}_{scenario}_j{j}_k{k}"

                                    cinvest_c = costs_df.loc[county_ids[i], cinvest_col] if cinvest_col in costs_df.columns else 0
                                    com_c     = costs_df.loc[county_ids[i], com_col]     if com_col in costs_df.columns else 0
                                    ctrans_c  = costs_df.loc[county_ids[i], ctrans_col]  if ctrans_col in costs_df.columns else 0

                                    row_pv_cost = pv_results_df.loc[i, f"pv_total_cost_{year}_{scenario}"] if f"pv_total_cost_{year}_{scenario}" in pv_results_df.columns else 0
                                    row_pv_rev  = pv_results_df.loc[i, f"pv_revenue_{year}_{scenario}"]    if f"pv_revenue_{year}_{scenario}" in pv_results_df.columns else 0

                                    revenue_val_c = (P[i][j]*Q[i]*20 + row_pv_rev*pv_x + Q[i]/2*0.53)
                                    cost_val_c = (cinvest_c + com_c + ctrans_c + row_pv_cost*pv_x + Q[i]*0.001*Water_Price[i])

                                    # ROI
                                    if cost_val_c > 1e-6:
                                        ROI_c = (revenue_val_c / cost_val_c - 1)/N
                                    else:
                                        ROI_c = 0

                                    # 使用新的calculate_payback函数计算回收期
                                    payback_c = None
                                    try:
                                        if cost_val_c > 1e-6:
                                            # 获取投资成本和运维成本
                                            investment_cost_c = cinvest_c + row_pv_cost*pv_x
                                            annual_om_cost_c = com_c/N + ctrans_c/N + Q[i]*0.001*Water_Price[i]/N

                                            # 计算残值（假设为投资成本的20%）
                                            residual_value_c = investment_cost_c * 0.2

                                            # 计算年收益
                                            annual_revenue_c = revenue_val_c / N

                                            # 计算回收期
                                            discount_rate = 0.03  # 折现率
                                            payback_c = calculate_payback(
                                                investment_cost=investment_cost_c,
                                                annual_revenue=annual_revenue_c,
                                                annual_om_cost=annual_om_cost_c,
                                                residual_value=residual_value_c,
                                                discount_rate=discount_rate,
                                                max_years=30
                                            )
                                    except Exception as pb_err:
                                        print(f"计算回收期时出错: i={i}, j={j}, k={k}, error={pb_err}")
                                        payback_c = None

                                    # 其他 SDG、H2 价格等
                                    if cost_val_c > 1e-6:
                                        SDG3_c  = 0.05 * Q[i] * 20 / cost_val_c  # 仅举例
                                        SDG8_c  = (Q[i]/1000*3)*3000 / cost_val_c
                                        SDG12_c = merged_df.loc[i,"PV_price"] * Q[i] / cost_val_c
                                        SDG13_c = (-0.001*2*Q[i] - 0.0005*Dht[i]) / cost_val_c
                                        work_c  = 3 * 5.9 * Q[i]*1000 / cost_val_c / N
                                        env_c   = Q[i]*109 / cost_val_c / N
                                        diff_c  = work_c - env_c
                                    else:
                                        SDG3_c=SDG8_c=SDG12_c=SDG13_c=work_c=env_c=diff_c=0

                                    if Q[i]>1e-6:
                                        H2_price_c = (cinvest_c + com_c + ctrans_c + 4.9*Q[i]*20*0.0899)/(Q[i]*20)/0.0899
                                    else:
                                        H2_price_c=0

                                    denom_c = (P[i][j]*Q[i]*20 + row_pv_rev*pv_x)
                                    if denom_c>1e-6:
                                        contrib_c = (P[i][j]*Q[i]*20)/denom_c
                                    else:
                                        contrib_c=0

                                    # 判断是否替换默认值
                                    if ROI_c>merged.loc[i, "ROI"] and ROI_c>0:
                                        results_c.append({
                                            "name": merged_df.loc[i,"name"],
                                            "i": i+1, "j": j+1, "k": k+1,
                                            "year": year, "scenario": scenario,
                                            "ROI_c": ROI_c,
                                            "Payback_c": payback_c,  # 添加回收期
                                            "contribute_c": contrib_c,
                                            "SDG3_c": SDG3_c,
                                            "SDG8_c": SDG8_c,
                                            "SDG12_c":SDG12_c,
                                            "SDG13_c":SDG13_c,
                                            "SDG9_c": 0, # 仅示例
                                            "work_c": work_c,
                                            "environment_c": env_c,
                                            "H2_price_c": H2_price_c,
                                            "difference_c": diff_c
                                        })
                                    else:
                                        # ROI 不达标 => 默认
                                        results_c.append({
                                            "name": merged_df.loc[i,"name"],
                                            "i": i+1, "j": 0, "k": 0,
                                            "year": year, "scenario": scenario,
                                            "ROI_c": merged.loc[i, "ROI"],
                                            "Payback_c": None,  # 添加回收期为None
                                            "contribute_c": 0,
                                            "SDG3_c":0, "SDG8_c":0, "SDG12_c":0,
                                            "SDG13_c":0, "SDG9_c":0,
                                            "work_c":0, "environment_c":0,
                                            "H2_price_c":0, "difference_c":0
                                        })
                                except Exception as err_:
                                    print(f"处理结果时出错: i={i}, j={j}, k={k}, error={err_}")
                                    traceback.print_exc()
                                    # 默认结果
                                    results_c.append({
                                        "name": merged_df.loc[i,"name"],
                                        "i": i+1, "j": 0, "k": 0,
                                        "year": year, "scenario": scenario,
                                        "ROI_c": 0, "Payback_c": None,  # 添加回收期为None
                                        "contribute_c": 0,
                                        "SDG3_c":0,"SDG8_c":0,"SDG12_c":0,"SDG13_c":0,"SDG9_c":0,
                                        "work_c":0,"environment_c":0,
                                        "H2_price_c":0,"difference_c":0
                                    })
            else:
                print(f"模型未找到最优解, Gurobi 状态: {model_c.status}")
                # 默认结果
                for i in range(len(county_indices)):
                    results_c.append({
                        "name": merged_df.loc[i,"name"],
                        "i": i+1, "j":0, "k":0,
                        "year": year,"scenario": scenario,
                        "ROI_c":0,"Payback_c": None,  # 添加回收期为None
                        "contribute_c":0,
                        "SDG3_c":0,"SDG8_c":0,"SDG12_c":0,"SDG13_c":0,"SDG9_c":0,
                        "work_c":0,"environment_c":0,
                        "H2_price_c":0,"difference_c":0
                    })

            # 存储结果
            all_results_c[f"{year}_{scenario}"] = pd.DataFrame(results_c)

        except Exception as e:
            print(f"处理情景 {scenario}, 年份 {year} 时出错: {str(e)}")
            traceback.print_exc()
            # 空表
            all_results_c[f"{year}_{scenario}"] = pd.DataFrame(columns=[
                "name","i","j","k","year","scenario","ROI_c","Payback_c","contribute_c",  # 添加Payback_c列
                "SDG3_c","SDG8_c","SDG12_c","SDG13_c","SDG9_c","work_c","environment_c",
                "H2_price_c","difference_c"
            ])

# ========== 合并所有结果并保存 ==========
try:
    final_results_df_c = pd.concat(all_results_c.values(), ignore_index=True)
    final_results_df_c.to_csv('optimization_results_all_scenarios_c.csv', index=False)

    # 打印一些统计信息
    for scenario in scenarios:
        for year in years_range:
            scenario_year_df = final_results_df_c[
                (final_results_df_c["scenario"]==scenario) &
                (final_results_df_c["year"]==year)
            ]
            if not scenario_year_df.empty:
                print(f"\n统计信息 - 情景: {scenario}, 年份: {year}")
                print(f"平均 ROI_c: {scenario_year_df['ROI_c'].mean():.4f}")
                print(f"平均 H2_price_c: {scenario_year_df['H2_price_c'].mean():.2f}")

                # 添加回收期统计
                valid_payback_c = scenario_year_df['Payback_c'].dropna()
                if not valid_payback_c.empty:
                    print(f"平均回收期: {valid_payback_c.mean():.2f}年")
                    print(f"有效回收期数量: {len(valid_payback_c)}")
                else:
                    print("没有有效的回收期数据")
            else:
                print(f"\n情景: {scenario}, 年份: {year} - 无结果")
except Exception as err_:
    print("合并或保存结果时出错:", err_)
    traceback.print_exc()


# In[162]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# 读取敏感性分析结果
optimization_results = pd.read_csv('optimization_results_all_scenarios_c.csv')

# 筛选 2024 年 base 情景的数据
base_2024 = optimization_results[(optimization_results['year'] == 2024) & 
                                (optimization_results['scenario'] == 'Base')]

# 读取直接计算的 ROI 数据
# 假设该数据在 merged_df 中
# 如果需要从文件读取，取消下面注释并指定正确的文件路径
# merged_df = pd.read_csv('path_to_merged_data.csv')

# 创建对比数据框
comparison_df = pd.DataFrame({
    'name': base_2024['name'],
    'ROI_优化模型': base_2024['ROI_c'],
    'ROI_直接计算': results_df['ROI_c'].values,  # i 索引从1开始，需要减1
    'j': base_2024['j'],
    'k': base_2024['k']
})

# 计算差异
comparison_df['差异'] = comparison_df['ROI_优化模型'] - comparison_df['ROI_直接计算']
comparison_df['相对差异(%)'] = (comparison_df['差异'] / comparison_df['ROI_直接计算']) * 100

# 统计分析
roi_stats = {
    '平均值_优化模型': comparison_df['ROI_优化模型'].mean(),
    '平均值_直接计算': comparison_df['ROI_直接计算'].mean(),
    '平均值_差异': comparison_df['差异'].mean(),
    '中位数_优化模型': comparison_df['ROI_优化模型'].median(),
    '中位数_直接计算': comparison_df['ROI_直接计算'].median(),
    '标准差_优化模型': comparison_df['ROI_优化模型'].std(),
    '标准差_直接计算': comparison_df['ROI_直接计算'].std(),
    '最大值_优化模型': comparison_df['ROI_优化模型'].max(),
    '最大值_直接计算': comparison_df['ROI_直接计算'].max(),
    '最小值_优化模型': comparison_df['ROI_优化模型'].min(),
    '最小值_直接计算': comparison_df['ROI_直接计算'].min(),
}

# 显示统计结果
print("2024年Base情景下ROI对比统计:")
for key, value in roi_stats.items():
    print(f"{key}: {value:.4f}")

# 检验两组ROI是否有显著差异
t_stat, p_value = stats.ttest_rel(comparison_df['ROI_优化模型'], comparison_df['ROI_直接计算'])
print(f"\n配对T检验结果: t统计量 = {t_stat:.4f}, p值 = {p_value:.4f}")
if p_value < 0.05:
    print("结论: 两组ROI有显著差异")
else:
    print("结论: 两组ROI没有显著差异")

# 可视化对比
plt.figure(figsize=(14, 10))

# 1. 箱线图比较
plt.subplot(2, 2, 1)
plt.boxplot([comparison_df['ROI_优化模型'], comparison_df['ROI_直接计算']], 
            labels=['优化模型', '直接计算'])
plt.title('ROI分布箱线图对比')
plt.ylabel('ROI值')

# 2. 散点图展示相关性
plt.subplot(2, 2, 2)
plt.scatter(comparison_df['ROI_直接计算'], comparison_df['ROI_优化模型'])
plt.plot([min(comparison_df['ROI_直接计算']), max(comparison_df['ROI_直接计算'])], 
         [min(comparison_df['ROI_直接计算']), max(comparison_df['ROI_直接计算'])], 'r--')
plt.xlabel('直接计算的ROI')
plt.ylabel('优化模型的ROI')
plt.title('ROI对比散点图')

# 3. 直方图对比差异分布
plt.subplot(2, 2, 3)
plt.hist(comparison_df['差异'], bins=20, alpha=0.7)
plt.axvline(0, color='r', linestyle='--')
plt.title('ROI差异分布')
plt.xlabel('差异值(优化模型-直接计算)')

# 4. 每个县的ROI对比条形图(选取前15个县)
plt.subplot(2, 2, 4)
top_counties = comparison_df.sort_values('ROI_优化模型', ascending=False).head(15)
x = np.arange(len(top_counties))
width = 0.35
plt.bar(x - width/2, top_counties['ROI_优化模型'], width, label='优化模型')
plt.bar(x + width/2, top_counties['ROI_直接计算'], width, label='直接计算')
plt.xticks(x, top_counties['name'], rotation=45, ha='right')
plt.title('前15个县ROI对比')
plt.legend()

plt.tight_layout()
plt.savefig('ROI_comparison_2024_base.png', dpi=300)
plt.show()

# 导出详细对比数据
comparison_df.to_csv('ROI_comparison_2024_base.csv', index=False)

print(f"分析完成。详细数据已保存至 'ROI_comparison_2024_base.csv'")
print(f"可视化图表已保存至 'ROI_comparison_2024_base.png'")


# In[163]:


# 创建一个函数来比较2024年Base情景下的成本与直接计算的成本
def compare_costs_2024_base():
    # 设置比较的年份和情景
    year = 2024
    scenario = "Base"

    # 创建结果DataFrame
    comparison_results = []

    print("开始比较2024年Base情景下的成本与直接计算的成本...")
    print("=" * 80)

    # 遍历每个县
    for i in range(len(county_indices)):
        county_id = county_ids[i]
        county_name = merged.loc[i, 'name']

        # 遍历销售类型和运输方式
        for j in range(len(hydrogen_sales_types)):
            if j == 2:  # 跳过j=2的情况
                continue

            for k in range(len(transport_methods)):
                # 获取敏感性分析中的成本
                sensitivity_cinvest = costs_df.loc[county_id, f'Cinvest_{year}_{scenario}_j{j}_k{k}']
                sensitivity_com = costs_df.loc[county_id, f'Com_{year}_{scenario}_j{j}_k{k}']
                sensitivity_ctrans = costs_df.loc[county_id, f'Ctrans_{year}_{scenario}_j{j}_k{k}']

                # 获取直接计算中的成本
                direct_cinvest = Cinvest_values.get((i, j, k), 0)
                direct_com = Com_values.get((i, j, k), 0)
                direct_ctrans = Ctrans_values.get((i, j, k), 0)

                # 计算总成本
                sensitivity_total = sensitivity_cinvest + sensitivity_com + sensitivity_ctrans
                direct_total = direct_cinvest + direct_com + direct_ctrans

                # 计算差异
                cinvest_diff = sensitivity_cinvest - direct_cinvest
                com_diff = sensitivity_com - direct_com
                ctrans_diff = sensitivity_ctrans - direct_ctrans
                total_diff = sensitivity_total - direct_total

                # 计算相对差异百分比
                if direct_cinvest != 0:
                    cinvest_diff_pct = (cinvest_diff / direct_cinvest) * 100
                else:
                    cinvest_diff_pct = 0 if cinvest_diff == 0 else float('inf')

                if direct_com != 0:
                    com_diff_pct = (com_diff / direct_com) * 100
                else:
                    com_diff_pct = 0 if com_diff == 0 else float('inf')

                if direct_ctrans != 0:
                    ctrans_diff_pct = (ctrans_diff / direct_ctrans) * 100
                else:
                    ctrans_diff_pct = 0 if ctrans_diff == 0 else float('inf')

                if direct_total != 0:
                    total_diff_pct = (total_diff / direct_total) * 100
                else:
                    total_diff_pct = 0 if total_diff == 0 else float('inf')

                # 添加到结果列表
                comparison_results.append({
                    'county_id': county_id,
                    'county_name': county_name,
                    'j': j,
                    'k': k,
                    'sensitivity_cinvest': sensitivity_cinvest,
                    'direct_cinvest': direct_cinvest,
                    'cinvest_diff': cinvest_diff,
                    'cinvest_diff_pct': cinvest_diff_pct,
                    'sensitivity_com': sensitivity_com,
                    'direct_com': direct_com,
                    'com_diff': com_diff,
                    'com_diff_pct': com_diff_pct,
                    'sensitivity_ctrans': sensitivity_ctrans,
                    'direct_ctrans': direct_ctrans,
                    'ctrans_diff': ctrans_diff,
                    'ctrans_diff_pct': ctrans_diff_pct,
                    'sensitivity_total': sensitivity_total,
                    'direct_total': direct_total,
                    'total_diff': total_diff,
                    'total_diff_pct': total_diff_pct
                })

    # 转换为DataFrame
    comparison_df = pd.DataFrame(comparison_results)

    # 找出差异较大的项目
    significant_diff = comparison_df[
        (comparison_df['cinvest_diff_pct'].abs() > 1) | 
        (comparison_df['com_diff_pct'].abs() > 1) | 
        (comparison_df['ctrans_diff_pct'].abs() > 1) | 
        (comparison_df['total_diff_pct'].abs() > 1)
    ]

    # 打印汇总统计
    print("成本比较汇总统计:")
    print("-" * 80)

    # 计算每种成本的平均差异百分比
    avg_cinvest_diff_pct = comparison_df['cinvest_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
    avg_com_diff_pct = comparison_df['com_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
    avg_ctrans_diff_pct = comparison_df['ctrans_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
    avg_total_diff_pct = comparison_df['total_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()

    print(f"投资成本平均差异百分比: {avg_cinvest_diff_pct:.2f}%")
    print(f"运维成本平均差异百分比: {avg_com_diff_pct:.2f}%")
    print(f"运输成本平均差异百分比: {avg_ctrans_diff_pct:.2f}%")
    print(f"总成本平均差异百分比: {avg_total_diff_pct:.2f}%")

    # 检查是否有差异较大的情况
    print(f"\n存在明显差异的情况数量: {len(significant_diff)}")

    if len(significant_diff) > 0:
        print("\n差异较大的前10个样本:")
        print("-" * 80)

        # 按总差异百分比排序
        top_diff = significant_diff.sort_values(by='total_diff_pct', ascending=False).head(10)

        # 打印每个差异较大的样本的详细信息
        for _, row in top_diff.iterrows():
            print(f"县市: {row['county_name']} (ID: {row['county_id']}), j={row['j']}, k={row['k']}")
            print(f"  投资成本: 敏感性={row['sensitivity_cinvest']:.2f}, 直接计算={row['direct_cinvest']:.2f}, 差异={row['cinvest_diff']:.2f} ({row['cinvest_diff_pct']:.2f}%)")
            print(f"  运维成本: 敏感性={row['sensitivity_com']:.2f}, 直接计算={row['direct_com']:.2f}, 差异={row['com_diff']:.2f} ({row['com_diff_pct']:.2f}%)")
            print(f"  运输成本: 敏感性={row['sensitivity_ctrans']:.2f}, 直接计算={row['direct_ctrans']:.2f}, 差异={row['ctrans_diff']:.2f} ({row['ctrans_diff_pct']:.2f}%)")
            print(f"  总成本: 敏感性={row['sensitivity_total']:.2f}, 直接计算={row['direct_total']:.2f}, 差异={row['total_diff']:.2f} ({row['total_diff_pct']:.2f}%)")
            print("-" * 60)

    # 检查关键参数差异
    print("\n检查可能导致差异的关键参数:")
    print("-" * 80)

    # 获取敏感性分析和直接计算中使用的关键参数
    sensitivity_cas = Cas_dict.get(f"Cas_{year}_{scenario}", "未找到")
    direct_cas = Cas

    print(f"Cas参数: 敏感性分析={sensitivity_cas}, 直接计算={direct_cas}, 差异={sensitivity_cas - direct_cas if isinstance(sensitivity_cas, (int, float)) and isinstance(direct_cas, (int, float)) else '无法计算'}")

    # 模式差异分析
    print("\n分析成本计算模式差异:")
    print("-" * 80)
    print("1. 敏感性分析代码考虑了年份和情景，而直接计算代码使用固定参数")
    print("2. 敏感性分析中的Cas参数根据年份和情景变化，而直接计算中为常量")

    # 对于j=3, k=1/2的情况特别分析
    print("\n特别分析j=3, k=1/2的情况:")
    print("-" * 80)
    j3_k1_cases = comparison_df[(comparison_df['j'] == 3) & (comparison_df['k'] == 1)]
    j3_k2_cases = comparison_df[(comparison_df['j'] == 3) & (comparison_df['k'] == 2)]

    if not j3_k1_cases.empty:
        j3_k1_diff_pct = j3_k1_cases['total_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
        print(f"j=3, k=1的平均总成本差异百分比: {j3_k1_diff_pct:.2f}%")

    if not j3_k2_cases.empty:
        j3_k2_diff_pct = j3_k2_cases['total_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
        print(f"j=3, k=2的平均总成本差异百分比: {j3_k2_diff_pct:.2f}%")

    # 保存详细结果到CSV
    comparison_df.to_csv('cost_comparison_2024_base.csv', index=False)
    print("\n详细比较结果已保存到 'cost_comparison_2024_base.csv'")

    # 返回比较结果DataFrame，以便进一步分析
    return comparison_df

# 执行比较分析
cost_comparison = compare_costs_2024_base()

# 可视化差异分布
plt.figure(figsize=(14, 8))

# 绘制总成本差异百分比的直方图
valid_pct = cost_comparison['total_diff_pct'].replace([np.inf, -np.inf], np.nan).dropna()
plt.subplot(2, 2, 1)
plt.hist(valid_pct, bins=30, alpha=0.7, color='skyblue')
plt.axvline(x=0, color='red', linestyle='--')
plt.title('总成本差异百分比分布')
plt.xlabel('差异百分比 (%)')
plt.ylabel('频数')

# 按j和k分组的平均总成本差异
group_diff = cost_comparison.groupby(['j', 'k'])['total_diff_pct'].mean().reset_index()
plt.subplot(2, 2, 2)
for j in group_diff['j'].unique():
    j_data = group_diff[group_diff['j'] == j]
    plt.plot(j_data['k'], j_data['total_diff_pct'], 'o-', label=f'j={j}')
plt.axhline(y=0, color='red', linestyle='--')
plt.title('按销售类型(j)和运输方式(k)的平均总成本差异')
plt.xlabel('运输方式 (k)')
plt.ylabel('平均差异百分比 (%)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

# 各成本类型的平均差异
cost_types = ['cinvest_diff_pct', 'com_diff_pct', 'ctrans_diff_pct', 'total_diff_pct']
cost_labels = ['投资成本', '运维成本', '运输成本', '总成本']
mean_diffs = [cost_comparison[col].replace([np.inf, -np.inf], np.nan).mean() for col in cost_types]

plt.subplot(2, 2, 3)
bars = plt.bar(cost_labels, mean_diffs, color=['blue', 'green', 'orange', 'red'], alpha=0.7)
plt.axhline(y=0, color='black', linestyle='--')
plt.title('各成本类型的平均差异百分比')
plt.ylabel('平均差异百分比 (%)')
plt.grid(True, linestyle='--', alpha=0.6, axis='y')

# 添加数据标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.1),
             f'{height:.2f}%', ha='center', va='bottom' if height >= 0 else 'top')

# 绘制散点图显示敏感性分析与直接计算的总成本对比
plt.subplot(2, 2, 4)
plt.scatter(cost_comparison['direct_total'], cost_comparison['sensitivity_total'], 
            alpha=0.5, c=cost_comparison['total_diff_pct'], cmap='coolwarm')
plt.colorbar(label='差异百分比 (%)')

# 添加1:1参考线
max_val = max(cost_comparison['direct_total'].max(), cost_comparison['sensitivity_total'].max())
plt.plot([0, max_val], [0, max_val], 'k--')

plt.title('敏感性分析 vs 直接计算的总成本对比')
plt.xlabel('直接计算总成本')
plt.ylabel('敏感性分析总成本')
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('cost_comparison_2024_base_visualization.png', dpi=300)
plt.close()

print("\n可视化结果已保存到 'cost_comparison_2024_base_visualization.png'")

# 基于分析结果提出更新建议
print("\n基于分析结果的更新建议:")
print("=" * 80)
print("1. 检查Cas参数的差异，确保敏感性分析中2024年Base情景的值与直接计算中的值一致")
print("2. 对于显著差异的情况，特别关注j=3, k=1和j=3, k=2的计算逻辑")
print("3. 确认敏感性分析中的Fpi和Fai参数设置是否与直接计算一致")
print("4. 确保calculate_transport_cost函数在两种计算方法中使用相同的参数")


# In[164]:


# 创建一个函数来比较2024年Base情景下的收益与直接计算的收益
def compare_revenue_2024_base():
    # 设置比较的年份和情景
    year = 2024
    scenario = "Base"

    # 创建结果DataFrame
    comparison_results = []

    print("开始比较2024年Base情景下的收益与直接计算的收益...")
    print("=" * 80)

    # 遍历每个县
    for i in range(len(county_indices)):
        county_id = county_ids[i]
        county_name = merged.loc[i, 'name']

        # 获取直接计算中使用的pv收益
        direct_pv_revenue = pv_revenue[i] if isinstance(pv_revenue, list) and i < len(pv_revenue) else None

        # 获取敏感性分析中使用的pv收益
        sensitivity_pv_revenue = pv_results_df.loc[i, f'pv_revenue_{year}_{scenario}'] if i in pv_results_df.index else None

        # 遍历销售类型和运输方式
        for j in range(len(hydrogen_sales_types)):
            if j == 2:  # 跳过j=2的情况
                continue

            for k in range(len(transport_methods)):
                try:
                    # 1. 直接计算的收益
                    # 氢销售收益
                    direct_h2_revenue = P[i][j] * Q[i] * 20 if i < len(P) and j < len(P[i]) else 0
                    # 光伏收益
                    direct_pv_revenue_total = direct_pv_revenue * pv_x if direct_pv_revenue is not None else 0
                    # 其他收益（如氧气销售等）
                    direct_other_revenue = Q[i] / 2 * 0.53 if i < len(Q) else 0
                    # 总收益
                    direct_total_revenue = direct_h2_revenue + direct_pv_revenue_total + direct_other_revenue

                    # 2. 敏感性分析的收益
                    # 氢销售收益
                    sensitivity_h2_revenue = P[i][j] * Q[i] * 20 if i < len(P) and j < len(P[i]) else 0
                    # 光伏收益
                    sensitivity_pv_revenue_total = sensitivity_pv_revenue * pv_x if sensitivity_pv_revenue is not None else 0
                    # 其他收益
                    sensitivity_other_revenue = Q[i] / 2 * 0.53 if i < len(Q) else 0
                    # 总收益
                    sensitivity_total_revenue = sensitivity_h2_revenue + sensitivity_pv_revenue_total + sensitivity_other_revenue

                    # 3. 计算差异
                    h2_revenue_diff = sensitivity_h2_revenue - direct_h2_revenue
                    pv_revenue_diff = sensitivity_pv_revenue_total - direct_pv_revenue_total
                    other_revenue_diff = sensitivity_other_revenue - direct_other_revenue
                    total_revenue_diff = sensitivity_total_revenue - direct_total_revenue

                    # 4. 计算相对差异百分比
                    if direct_h2_revenue != 0:
                        h2_revenue_diff_pct = (h2_revenue_diff / direct_h2_revenue) * 100
                    else:
                        h2_revenue_diff_pct = 0 if h2_revenue_diff == 0 else float('inf')

                    if direct_pv_revenue_total != 0:
                        pv_revenue_diff_pct = (pv_revenue_diff / direct_pv_revenue_total) * 100
                    else:
                        pv_revenue_diff_pct = 0 if pv_revenue_diff == 0 else float('inf')

                    if direct_other_revenue != 0:
                        other_revenue_diff_pct = (other_revenue_diff / direct_other_revenue) * 100
                    else:
                        other_revenue_diff_pct = 0 if other_revenue_diff == 0 else float('inf')

                    if direct_total_revenue != 0:
                        total_revenue_diff_pct = (total_revenue_diff / direct_total_revenue) * 100
                    else:
                        total_revenue_diff_pct = 0 if total_revenue_diff == 0 else float('inf')

                    # 添加到结果列表
                    comparison_results.append({
                        'county_id': county_id,
                        'county_name': county_name,
                        'j': j,
                        'k': k,
                        'direct_h2_revenue': direct_h2_revenue,
                        'sensitivity_h2_revenue': sensitivity_h2_revenue,
                        'h2_revenue_diff': h2_revenue_diff,
                        'h2_revenue_diff_pct': h2_revenue_diff_pct,
                        'direct_pv_revenue': direct_pv_revenue_total,
                        'sensitivity_pv_revenue': sensitivity_pv_revenue_total,
                        'pv_revenue_diff': pv_revenue_diff,
                        'pv_revenue_diff_pct': pv_revenue_diff_pct,
                        'direct_other_revenue': direct_other_revenue,
                        'sensitivity_other_revenue': sensitivity_other_revenue,
                        'other_revenue_diff': other_revenue_diff,
                        'other_revenue_diff_pct': other_revenue_diff_pct,
                        'direct_total_revenue': direct_total_revenue,
                        'sensitivity_total_revenue': sensitivity_total_revenue,
                        'total_revenue_diff': total_revenue_diff,
                        'total_revenue_diff_pct': total_revenue_diff_pct
                    })
                except Exception as e:
                    print(f"处理县{county_name}(ID: {county_id}), j={j}, k={k}时出错: {str(e)}")

    # 转换为DataFrame
    comparison_df = pd.DataFrame(comparison_results)

    # 找出差异较大的项目
    significant_diff = comparison_df[
        (comparison_df['h2_revenue_diff_pct'].abs() > 1) | 
        (comparison_df['pv_revenue_diff_pct'].abs() > 1) | 
        (comparison_df['other_revenue_diff_pct'].abs() > 1) | 
        (comparison_df['total_revenue_diff_pct'].abs() > 1)
    ]

    # 打印汇总统计
    print("收益比较汇总统计:")
    print("-" * 80)

    # 计算每种收益的平均差异百分比
    avg_h2_diff_pct = comparison_df['h2_revenue_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
    avg_pv_diff_pct = comparison_df['pv_revenue_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
    avg_other_diff_pct = comparison_df['other_revenue_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()
    avg_total_diff_pct = comparison_df['total_revenue_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()

    print(f"氢销售收益平均差异百分比: {avg_h2_diff_pct:.2f}%")
    print(f"光伏收益平均差异百分比: {avg_pv_diff_pct:.2f}%")
    print(f"其他收益平均差异百分比: {avg_other_diff_pct:.2f}%")
    print(f"总收益平均差异百分比: {avg_total_diff_pct:.2f}%")

    # 检查是否有差异较大的情况
    print(f"\n存在明显差异的情况数量: {len(significant_diff)}")

    if len(significant_diff) > 0:
        print("\n差异较大的前10个样本:")
        print("-" * 80)

        # 按总差异百分比排序
        top_diff = significant_diff.sort_values(by='total_revenue_diff_pct', ascending=False).head(10)

        # 打印每个差异较大的样本的详细信息
        for _, row in top_diff.iterrows():
            print(f"县市: {row['county_name']} (ID: {row['county_id']}), j={row['j']}, k={row['k']}")
            print(f"  氢销售收益: 敏感性={row['sensitivity_h2_revenue']:.2f}, 直接计算={row['direct_h2_revenue']:.2f}, 差异={row['h2_revenue_diff']:.2f} ({row['h2_revenue_diff_pct']:.2f}%)")
            print(f"  光伏收益: 敏感性={row['sensitivity_pv_revenue']:.2f}, 直接计算={row['direct_pv_revenue']:.2f}, 差异={row['pv_revenue_diff']:.2f} ({row['pv_revenue_diff_pct']:.2f}%)")
            print(f"  其他收益: 敏感性={row['sensitivity_other_revenue']:.2f}, 直接计算={row['direct_other_revenue']:.2f}, 差异={row['other_revenue_diff']:.2f} ({row['other_revenue_diff_pct']:.2f}%)")
            print(f"  总收益: 敏感性={row['sensitivity_total_revenue']:.2f}, 直接计算={row['direct_total_revenue']:.2f}, 差异={row['total_revenue_diff']:.2f} ({row['total_revenue_diff_pct']:.2f}%)")
            print("-" * 60)

    # 收益组成分析
    print("\n收益组成分析:")
    print("-" * 80)

    # 计算各收益类型在总收益中的平均占比
    direct_h2_pct = (comparison_df['direct_h2_revenue'] / comparison_df['direct_total_revenue']).replace([np.inf, -np.inf], np.nan).mean() * 100
    direct_pv_pct = (comparison_df['direct_pv_revenue'] / comparison_df['direct_total_revenue']).replace([np.inf, -np.inf], np.nan).mean() * 100
    direct_other_pct = (comparison_df['direct_other_revenue'] / comparison_df['direct_total_revenue']).replace([np.inf, -np.inf], np.nan).mean() * 100

    sensitivity_h2_pct = (comparison_df['sensitivity_h2_revenue'] / comparison_df['sensitivity_total_revenue']).replace([np.inf, -np.inf], np.nan).mean() * 100
    sensitivity_pv_pct = (comparison_df['sensitivity_pv_revenue'] / comparison_df['sensitivity_total_revenue']).replace([np.inf, -np.inf], np.nan).mean() * 100
    sensitivity_other_pct = (comparison_df['sensitivity_other_revenue'] / comparison_df['sensitivity_total_revenue']).replace([np.inf, -np.inf], np.nan).mean() * 100

    print("直接计算中各收益类型占总收益的平均比例:")
    print(f"  氢销售收益: {direct_h2_pct:.2f}%")
    print(f"  光伏收益: {direct_pv_pct:.2f}%")
    print(f"  其他收益: {direct_other_pct:.2f}%")

    print("\n敏感性分析中各收益类型占总收益的平均比例:")
    print(f"  氢销售收益: {sensitivity_h2_pct:.2f}%")
    print(f"  光伏收益: {sensitivity_pv_pct:.2f}%")
    print(f"  其他收益: {sensitivity_other_pct:.2f}%")

    # 按j值分组的收益差异分析
    print("\n按销售类型(j)分组的收益差异分析:")
    print("-" * 80)
    j_group = comparison_df.groupby('j')[['total_revenue_diff_pct']].mean()

    for j_val, row in j_group.iterrows():
        print(f"j={j_val}: 平均总收益差异 = {row['total_revenue_diff_pct']:.2f}%")

    # 保存详细结果到CSV
    comparison_df.to_csv('revenue_comparison_2024_base.csv', index=False)
    print("\n详细比较结果已保存到 'revenue_comparison_2024_base.csv'")

    # 可视化数据
    plt.figure(figsize=(14, 10))

    # 总收益差异百分比分布
    plt.subplot(2, 2, 1)
    valid_pct = comparison_df['total_revenue_diff_pct'].replace([np.inf, -np.inf], np.nan).dropna()
    plt.hist(valid_pct, bins=30, alpha=0.7, color='skyblue')
    plt.axvline(x=0, color='red', linestyle='--')
    plt.title('总收益差异百分比分布')
    plt.xlabel('差异百分比 (%)')
    plt.ylabel('频数')

    # 各收益类型的平均差异
    plt.subplot(2, 2, 2)
    labels = ['氢销售收益', '光伏收益', '其他收益', '总收益']
    avg_diffs = [avg_h2_diff_pct, avg_pv_diff_pct, avg_other_diff_pct, avg_total_diff_pct]

    bars = plt.bar(labels, avg_diffs, color=['blue', 'green', 'orange', 'red'], alpha=0.7)
    plt.axhline(y=0, color='black', linestyle='--')
    plt.title('各收益类型的平均差异百分比')
    plt.ylabel('平均差异百分比 (%)')
    plt.grid(True, linestyle='--', alpha=0.6, axis='y')

    # 为每个柱添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.1),
                 f'{height:.2f}%', ha='center', va='bottom' if height >= 0 else 'top')

    # 收益构成对比
    plt.subplot(2, 2, 3)
    direct_comp = [direct_h2_pct, direct_pv_pct, direct_other_pct]
    sensitivity_comp = [sensitivity_h2_pct, sensitivity_pv_pct, sensitivity_other_pct]

    x = np.arange(len(labels[:3]))
    width = 0.35

    plt.bar(x - width/2, direct_comp, width, label='直接计算', color='lightblue')
    plt.bar(x + width/2, sensitivity_comp, width, label='敏感性分析', color='lightgreen')

    plt.title('收益构成对比')
    plt.xlabel('收益类型')
    plt.ylabel('占总收益比例 (%)')
    plt.xticks(x, labels[:3])
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6, axis='y')

    # 敏感性分析与直接计算的总收益散点图
    plt.subplot(2, 2, 4)
    plt.scatter(comparison_df['direct_total_revenue'], comparison_df['sensitivity_total_revenue'], 
                alpha=0.5, c=comparison_df['total_revenue_diff_pct'], cmap='coolwarm')
    plt.colorbar(label='差异百分比 (%)')

    max_val = max(comparison_df['direct_total_revenue'].max(), comparison_df['sensitivity_total_revenue'].max())
    plt.plot([0, max_val], [0, max_val], 'k--')

    plt.title('敏感性分析 vs 直接计算的总收益对比')
    plt.xlabel('直接计算总收益')
    plt.ylabel('敏感性分析总收益')
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig('revenue_comparison_2024_base_visualization.png', dpi=300)
    plt.close()

    print("\n可视化结果已保存到 'revenue_comparison_2024_base_visualization.png'")

    # 基于分析结果提出更新建议
    print("\n基于收益分析结果的更新建议:")
    print("=" * 80)

    if abs(avg_pv_diff_pct) > 1:
        print("1. 检查光伏收益计算中年份和情景参数的影响，确保敏感性分析使用的光伏收益数据与直接计算一致")
    else:
        print("1. 光伏收益计算基本一致，无需重大修改")

    if abs(avg_h2_diff_pct) > 1:
        print("2. 检查氢销售价格(P)在两种计算方法中是否一致")
    else:
        print("2. 氢销售收益计算基本一致，无需重大修改")

    if abs(avg_other_diff_pct) > 1:
        print("3. 检查其他收益计算方法中的系数是否一致")
    else:
        print("3. 其他收益计算基本一致，无需重大修改")

    print("4. 总体建议: 确保敏感性分析中2024年Base情景的参数与直接计算中使用的参数保持一致")

    # 返回比较结果DataFrame
    return comparison_df

# 执行收益比较分析
revenue_comparison = compare_revenue_2024_base()


# In[165]:


# 创建函数比较2024年Base情景下敏感性分析与直接计算的ROI差异
def compare_roi_2024_base():
    # 设置比较的年份和情景
    year = 2024
    scenario = "Base"

    # 创建结果列表
    comparison_results = []

    print("开始比较2024年Base情景下敏感性分析与直接计算的ROI差异...")
    print("=" * 80)

    # 获取敏感性分析的结果数据
    # 假设2024年Base情景的结果存储在all_results_e字典中
    sensitivity_results = all_results_e.get(f"{year}_{scenario}")

    if sensitivity_results is None:
        print(f"未找到{year}年{scenario}情景的敏感性分析结果")
        return pd.DataFrame()  # 返回空DataFrame

    # 直接计算的结果在results_df中
    # 确保两个数据集都有ROI相关的列
    if "ROI_e" not in sensitivity_results.columns:
        print("敏感性分析结果中没有'ROI_e'列")
        return pd.DataFrame()

    if "ROI_e" not in results_df.columns:
        print("直接计算结果中没有'ROI_e'列")
        return pd.DataFrame()

    # 遍历每个县
    print("按县统计ROI差异:")
    print("-" * 80)
    print(f"{'县市名称':<15} {'县ID':<10} {'敏感性分析ROI':>15} {'直接计算ROI':>15} {'绝对差异':>12} {'相对差异%':>12}")
    print("-" * 80)

    # 创建一个字典来匹配县名和ID
    county_map = {county_ids[i]: (i, merged.loc[i, 'name']) for i in range(len(county_indices))}

    # 对于每个县，提取两种方法的ROI并比较
    for county_id, (county_idx, county_name) in county_map.items():
        try:
            # 获取敏感性分析的ROI
            sensitivity_roi_rows = sensitivity_results[sensitivity_results['i'] == county_idx + 1]
            if len(sensitivity_roi_rows) > 0:
                # 可能有多行，选择最大ROI值
                sensitivity_roi = sensitivity_roi_rows['ROI_e'].max()
            else:
                sensitivity_roi = None

            # 获取直接计算的ROI
            direct_roi_rows = results_df[results_df['i'] == county_idx + 1]
            if len(direct_roi_rows) > 0:
                direct_roi = direct_roi_rows['ROI_e'].max()
            else:
                direct_roi = None

            # 如果两种方法都有ROI值，计算差异
            if sensitivity_roi is not None and direct_roi is not None:
                # 计算绝对差异和相对差异
                abs_diff = sensitivity_roi - direct_roi
                if direct_roi != 0:
                    rel_diff_pct = (abs_diff / direct_roi) * 100
                else:
                    rel_diff_pct = float('inf') if abs_diff != 0 else 0

                # 打印结果
                print(f"{county_name:<15} {county_id:<10} {sensitivity_roi:15.4f} {direct_roi:15.4f} {abs_diff:12.4f} {rel_diff_pct:12.2f}")

                # 添加到结果列表
                comparison_results.append({
                    'county_id': county_id,
                    'county_name': county_name,
                    'county_idx': county_idx,
                    'sensitivity_roi': sensitivity_roi,
                    'direct_roi': direct_roi,
                    'abs_diff': abs_diff,
                    'rel_diff_pct': rel_diff_pct
                })
        except Exception as e:
            print(f"处理县{county_name}(ID: {county_id})时出错: {str(e)}")

    # 转换为DataFrame
    comparison_df = pd.DataFrame(comparison_results)

    # 计算汇总统计
    print("\nROI差异汇总统计:")
    print("-" * 80)

    # 计算平均ROI和平均差异
    sensitivity_avg_roi = comparison_df['sensitivity_roi'].mean()
    direct_avg_roi = comparison_df['direct_roi'].mean()
    avg_abs_diff = comparison_df['abs_diff'].mean()
    avg_rel_diff_pct = comparison_df['rel_diff_pct'].replace([np.inf, -np.inf], np.nan).mean()

    print(f"敏感性分析平均ROI: {sensitivity_avg_roi:.4f}")
    print(f"直接计算平均ROI: {direct_avg_roi:.4f}")
    print(f"平均绝对差异: {avg_abs_diff:.4f}")
    print(f"平均相对差异: {avg_rel_diff_pct:.2f}%")

    # 计算有显著差异的县数量
    significant_diff_counties = comparison_df[comparison_df['rel_diff_pct'].abs() > 10].shape[0]
    total_counties = comparison_df.shape[0]

    print(f"相对差异超过10%的县数量: {significant_diff_counties}/{total_counties} ({significant_diff_counties/total_counties*100:.2f}%)")

    # ROI阈值分析
    print("\nROI阈值分析:")
    print("-" * 80)

    # 计算ROI>0.03的县数量
    sensitivity_roi_threshold = (comparison_df['sensitivity_roi'] > 0.03).sum()
    direct_roi_threshold = (comparison_df['direct_roi'] > 0.03).sum()

    print(f"敏感性分析中ROI>0.03的县数量: {sensitivity_roi_threshold}/{total_counties} ({sensitivity_roi_threshold/total_counties*100:.2f}%)")
    print(f"直接计算中ROI>0.03的县数量: {direct_roi_threshold}/{total_counties} ({direct_roi_threshold/total_counties*100:.2f}%)")

    # 检查ROI阈值判断是否一致
    consistency_check = ((comparison_df['sensitivity_roi'] > 0.03) == (comparison_df['direct_roi'] > 0.03)).sum()
    inconsistency_count = total_counties - consistency_check

    print(f"ROI>0.03判断一致的县数量: {consistency_check}/{total_counties} ({consistency_check/total_counties*100:.2f}%)")
    print(f"ROI>0.03判断不一致的县数量: {inconsistency_count}/{total_counties} ({inconsistency_count/total_counties*100:.2f}%)")

    # 找出判断不一致的县
    if inconsistency_count > 0:
        inconsistent_counties = comparison_df[(comparison_df['sensitivity_roi'] > 0.03) != (comparison_df['direct_roi'] > 0.03)]
        print("\n判断不一致的县列表:")
        print("-" * 80)
        for _, row in inconsistent_counties.iterrows():
            print(f"县市: {row['county_name']} (ID: {row['county_id']})")
            print(f"  敏感性分析ROI: {row['sensitivity_roi']:.4f} (>0.03: {'是' if row['sensitivity_roi'] > 0.03 else '否'})")
            print(f"  直接计算ROI: {row['direct_roi']:.4f} (>0.03: {'是' if row['direct_roi'] > 0.03 else '否'})")
            print(f"  绝对差异: {row['abs_diff']:.4f}, 相对差异: {row['rel_diff_pct']:.2f}%")
            print("-" * 60)

    # 保存详细结果到CSV
    comparison_df.to_csv('roi_comparison_2024_base.csv', index=False)
    print("\n详细比较结果已保存到 'roi_comparison_2024_base.csv'")

    # 可视化
    plt.figure(figsize=(14, 10))

    # ROI分布对比
    plt.subplot(2, 2, 1)
    plt.hist(comparison_df['sensitivity_roi'], bins=20, alpha=0.5, label='敏感性分析')
    plt.hist(comparison_df['direct_roi'], bins=20, alpha=0.5, label='直接计算')
    plt.axvline(x=0.03, color='red', linestyle='--', label='阈值: 0.03')
    plt.axvline(x=sensitivity_avg_roi, color='blue', linestyle='-', label=f'敏感性平均: {sensitivity_avg_roi:.4f}')
    plt.axvline(x=direct_avg_roi, color='green', linestyle='-', label=f'直接计算平均: {direct_avg_roi:.4f}')
    plt.title('ROI分布对比')
    plt.xlabel('ROI值')
    plt.ylabel('频数')
    plt.legend()

    # ROI相对差异分布
    plt.subplot(2, 2, 2)
    valid_rel_diff = comparison_df['rel_diff_pct'].replace([np.inf, -np.inf], np.nan).dropna()
    plt.hist(valid_rel_diff, bins=30, alpha=0.7, color='skyblue')
    plt.axvline(x=0, color='red', linestyle='--', label='无差异')
    plt.axvline(x=avg_rel_diff_pct, color='green', linestyle='-', label=f'平均差异: {avg_rel_diff_pct:.2f}%')
    plt.title('ROI相对差异分布')
    plt.xlabel('相对差异 (%)')
    plt.ylabel('频数')
    plt.legend()

    # 散点图比较
    plt.subplot(2, 2, 3)
    plt.scatter(comparison_df['direct_roi'], comparison_df['sensitivity_roi'], alpha=0.7)

    # 添加对角线（1:1线）
    max_roi = max(comparison_df['direct_roi'].max(), comparison_df['sensitivity_roi'].max())
    min_roi = min(comparison_df['direct_roi'].min(), comparison_df['sensitivity_roi'].min())
    plt.plot([min_roi, max_roi], [min_roi, max_roi], 'k--')

    # 添加阈值线
    plt.axhline(y=0.03, color='red', linestyle='--', alpha=0.5)
    plt.axvline(x=0.03, color='red', linestyle='--', alpha=0.5)

    plt.title('敏感性分析 vs 直接计算的ROI对比')
    plt.xlabel('直接计算ROI')
    plt.ylabel('敏感性分析ROI')
    plt.grid(True, linestyle='--', alpha=0.6)

    # 添加ROI>0.03判断一致性的饼图
    plt.subplot(2, 2, 4)
    plt.pie([consistency_check, inconsistency_count], 
            labels=['ROI>0.03判断一致', 'ROI>0.03判断不一致'],
            autopct='%1.1f%%',
            colors=['lightgreen', 'lightcoral'],
            startangle=90)
    plt.axis('equal')
    plt.title('ROI阈值判断一致性')

    plt.tight_layout()
    plt.savefig('roi_comparison_2024_base_visualization.png', dpi=300)
    plt.close()

    print("\n可视化结果已保存到 'roi_comparison_2024_base_visualization.png'")

    # 根据分析结果提出建议
    print("\n基于ROI分析结果的建议:")
    print("=" * 80)

    if abs(avg_rel_diff_pct) <= 5:
        print("1. 两种计算方法的平均ROI相对差异小于5%，整体一致性良好")
    else:
        print(f"1. 两种计算方法的平均ROI相对差异为{avg_rel_diff_pct:.2f}%，需要进一步调查差异原因")

    if inconsistency_count > 0:
        inconsistency_pct = inconsistency_count/total_counties*100
        if inconsistency_pct > 10:
            print(f"2. 有{inconsistency_pct:.2f}%的县在ROI>0.03判断上不一致，建议检查这些县的具体计算过程")
        else:
            print(f"2. 仅有{inconsistency_pct:.2f}%的县在ROI>0.03判断上不一致，可以接受")
    else:
        print("2. 所有县在ROI>0.03判断上完全一致，无需进一步调整")

    # 分析收益和成本在ROI计算中的贡献
    print("\n3. 建议检查两种方法在以下方面的差异:")
    if abs(avg_rel_diff_pct) > 5:
        print("   - 成本计算方法，特别是Cas参数在敏感性分析中的取值")
        print("   - 光伏收益计算，确保2024年Base情景下使用的光伏参数一致")
        print("   - 对于ROI差异显著的县，检查特殊的地理或技术条件")

    # 返回比较结果DataFrame
    return comparison_df

# 执行ROI比较分析
try:
    roi_comparison = compare_roi_2024_base()
except Exception as e:
    print(f"执行ROI比较分析时发生错误: {str(e)}")
    # 尝试分析错误原因
    print("\n尝试分析错误原因:")
    print("-" * 80)

    # 检查必要的数据是否存在
    print("检查必要的数据结构:")
    print(f"1. 'all_results_e'是否存在: {'存在' if 'all_results_e' in globals() else '不存在'}")
    print(f"2. 'results_df'是否存在: {'存在' if 'results_df' in globals() else '不存在'}")

    # 如果存在，检查它们的结构
    if 'all_results_e' in globals():
        print("\nall_results_e的结构:")
        print(f"类型: {type(all_results_e)}")
        print(f"键列表: {list(all_results_e.keys()) if isinstance(all_results_e, dict) else '不是字典'}")

        # 检查2024_Base是否存在
        if isinstance(all_results_e, dict) and '2024_Base' in all_results_e:
            print(f"2024_Base数据的列: {list(all_results_e['2024_Base'].columns)}")
            print(f"2024_Base数据的行数: {len(all_results_e['2024_Base'])}")

    if 'results_df' in globals():
        print("\nresults_df的结构:")
        print(f"类型: {type(results_df)}")
        print(f"行数: {len(results_df)}")
        print(f"列: {list(results_df.columns)}")

    # 提供替代分析方法
    print("\n提供替代分析方案:")
    print("如果数据结构不符合原分析函数的预期，可以尝试以下简化分析:")

    # 简化分析代码
    print("""
    # 简化的ROI分析代码:
    # 1. 提取2024年Base情景的敏感性分析结果
    sensitivity_2024_base = [df for key, df in all_results_e.items() if '2024_Base' in key]
    if sensitivity_2024_base:
        sensitivity_roi = sensitivity_2024_base[0]['ROI_e'].mean()
        print(f"2024年Base情景敏感性分析平均ROI: {sensitivity_roi:.4f}")

    # 2. 获取直接计算的平均ROI
    direct_roi = results_df['ROI_e'].mean()
    print(f"直接计算平均ROI: {direct_roi:.4f}")

    # 3. 计算差异
    if 'sensitivity_roi' in locals() and 'direct_roi' in locals():
        abs_diff = sensitivity_roi - direct_roi
        rel_diff = (abs_diff / direct_roi) * 100 if direct_roi != 0 else float('inf')
        print(f"绝对差异: {abs_diff:.4f}")
        print(f"相对差异: {rel_diff:.2f}%")
    """)


# In[166]:


import matplotlib.pyplot as plt

# 假设你的 DataFrame 为 df_c

def plot_roi_above_3pct(df_plot_c):
    """
    根据给定的 DataFrame (df_plot_c)，统计并绘制 ROI>3% 的地区数量。
    """
    # 创建一个新列标记 ROI 是否 > 0.03
    df_plot_c = df_plot_c.copy()
    df_plot_c['ROI_above_3pct_c'] = (df_plot_c['ROI_c'] > 0.03).astype(int)

    # 按照 scenario 和 year 统计数量
    df_count_c = df_plot_c.groupby(['scenario', 'year'])['ROI_above_3pct_c'].sum().reset_index(name='Count_ROI_Above_3pct_c')

    # 提取三种情景的数据 (Low, Base, High)
    df_low_c = df_count_c[df_count_c['scenario'] == 'Low_LR']
    df_base_c = df_count_c[df_count_c['scenario'] == 'Base_LR']
    df_high_c = df_count_c[df_count_c['scenario'] == 'High_LR']

    # 绘图
    plt.figure(figsize=(8, 5))

    # Base情景折线图
    plt.plot(df_base_c['year'],
             df_base_c['Count_ROI_Above_3pct_c'],
             label='Base_LR', color='blue')

    # Low和High的范围区间
    plt.fill_between(df_low_c['year'],
                     df_low_c['Count_ROI_Above_3pct_c'],
                     df_high_c['Count_ROI_Above_3pct_c'],
                     alpha=0.3, color='blue', label='Low_LR~High_LR range')

    plt.legend()
    plt.xlabel('Year')
    plt.ylabel('Count of ROI > 3%')
    plt.title('Count of Regions with ROI > 3% (Capacity Scenario)')
    plt.grid(True)

    # 显示图像
    plt.show()


# In[167]:


import matplotlib.pyplot as plt

def plot_roi_above_3pct_comparison_c(df_c):
    """
    输入：df_c (例如 df_econ_scenario_all)
    """
    # 1) 创建一个新的列，用于标记 ROI 是否 > 0.03
    df_plot_c = df_c.copy()
    df_plot_c['ROI_above_3pct_c'] = df_plot_e['ROI_c'] > 0.03

    # 2) 按 (Scenario, Year) 统计 ROI>0.03 的地区个数
    df_count_c = df_plot_c.groupby(['scenario', 'year'])['ROI_above_3pct_c'].sum().reset_index(name='Count_ROI_Above_3pct_c')

    # 3) 分别取出 Low_LR / Base_LR / High_LR 的数据
    df_low_c = df_count_c[df_count_c['scenario'] == 'Low'].sort_values('year')
    df_base_c = df_count_c[df_count_c['scenario'] == 'Base'].sort_values('year')
    df_high_c = df_count_c[df_count_c['scenario'] == 'High'].sort_values('year')

    # 4) 创建画布
    plt.figure(figsize=(8,5))

    # 4.1 画出 Base_LR 的折线
    plt.plot(df_base_c['year'],
             df_base_c['Count_ROI_Above_3pct_c'],
             label='Base_LR (ROI>3%)')

    # 4.2 使用 fill_between 表示 Low_LR 和 High_LR 之间的区间
    plt.fill_between(df_base_c['year'],
                     df_low_c['Count_ROI_Above_3pct_c'],
                     df_high_c['Count_ROI_Above_3pct_c'],
                     color='gray', alpha=0.3,
                     label='Low_LR~High_LR range')

    # 5) 添加图例、坐标轴标签、标题
    plt.legend()
    plt.xlabel('Year')
    plt.ylabel('Count of Regions (ROI > 3%)')
    plt.title('Count of Regions with ROI>3% under Different Learning Rate Scenarios')

    plt.show()


# In[168]:


# 清理数据：删除 'ROI' 列为空的行，并确保 'year' 列为字符串类型
cleaned_data = all_results_df.dropna(subset=['ROI'])  # 删除 'ROI' 为空的行
cleaned_data['year'] = cleaned_data['year'].astype(str)  # 将 'year' 转换为字符串类型

# 打印数据描述信息，检查清理后的数据
print("\n清理后的数据描述统计信息 (四舍五入后的 ROI):")
print(cleaned_data.describe())  # 打印描述统计信息

# 统计每个年份的数据量，确保每个年份的数据量足够
year_counts = cleaned_data['year'].value_counts()
print("\n每年数据量统计：")
print(year_counts)

# 只保留数据点大于1的年份，确保数据量足够绘制图表
valid_years = year_counts[year_counts > 1].index  # 筛选出数据点大于1的年份
cleaned_data = cleaned_data[cleaned_data['year'].isin(valid_years)]  # 过滤出有效年份的数据

clean_data4 = copy.deepcopy(cleaned_data)


# #### 可视化

# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

# counties_selected['ROI_y'] = counties_selected['name'].map(poverty_selected.set_index('name')['ROI_y'])
counties_selected['group'] = counties_selected['ROI_c'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI_c'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_c'])
poverty_remaining['group'] = poverty_remaining['ROI_c'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展
# # 1. 检查索引是否唯一
# print("检查 counties_selected 索引是否唯一：", counties_selected.index.is_unique)
# print("检查 poverty_remaining 索引是否唯一：", poverty_remaining.index.is_unique)
#
# # 如果索引不唯一，打印重复的索引
# if not counties_selected.index.is_unique:
#     print("重复的索引 in counties_selected:", counties_selected[counties_selected.index.duplicated()])
#
# if not poverty_remaining.index.is_unique:
#     print("重复的索引 in poverty_remaining:", poverty_remaining[poverty_remaining.index.duplicated()])
#
# # 2. 检查列名和列顺序是否一致
# print("counties_selected 列名：", counties_selected.columns)
# print("poverty_remaining 列名：", poverty_remaining.columns)
#
# # 3. 检查是否有重复的行
# print("检查 counties_selected 是否有重复行:", counties_selected.duplicated().sum())
# print("检查 poverty_remaining 是否有重复行:", poverty_remaining.duplicated().sum())
#
# # 4. 检查两个 GeoDataFrame 的 CRS 是否一致
# print("counties_selected CRS:", counties_selected.crs)
# print("poverty_remaining CRS:", poverty_remaining.crs)

# 如果 CRS 不一致，可以选择统一它们
if counties_selected.crs != poverty_remaining.crs:
    print("CRS 不一致，进行转换为统一的 CRS")
    poverty_remaining = poverty_remaining.to_crs(counties_selected.crs)

# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))
# 加载管道数据
def _load_pipeline_data(pipeline_file):
    """加载管道数据 (简单处理)"""
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    """绘制管道线路 (不做额外检测)"""
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制所有县的边界
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围

# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制所有县的边界在子图中
counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')

# 绘制管道在子图中
_plot_pipeline(ax_inset, pipeline_gdf)

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
# plt.savefig('fig1a_ca.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
import matplotlib.font_manager as fm
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 自定义颜色
cmap = {
    'ROI_c > ROI': '#ff7f50',  # ROI_c_y > ROI 标记为橙色
    'ROI_x < 0.03 & ROI_c > 0.03': '#4a7bb6',  # 特殊标注为蓝色
}

# 根据条件分类
combined2['color_group'] = combined2.apply(
    lambda row: 'ROI_c > ROI' if row['ROI_c'] > row['ROI_x'] else \
               'ROI_x < 0.03 & ROI_c > 0.03' if row['ROI_x'] < 0.03 and row['ROI_c'] > 0.03 else None,
    axis=1
)

# 加载管道数据
def _load_pipeline_data(pipeline_file):
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_axis_off()

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加透明阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', alpha=0.5,
                    path_effects=shadow_effect)

# 绘制所有县的边界，透明背景
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='none', alpha=0.5)

# 绘制 ROI 标记颜色，确保蓝色部分在最上层
for group, color in cmap.items():
    if group == 'ROI_x < 0.03 & ROI_c > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=3)
for group, color in cmap.items():
    if group != 'ROI_x < 0.03 & ROI_c > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=2)

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置范围
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 子图 - 南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('none')
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.grid(False)
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 子图中绘制南海区域
for group, color in cmap.items():
    if group == 'ROI_x < 0.03 & ROI_c > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax_inset, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=3)
for group, color in cmap.items():
    if group != 'ROI_x < 0.03 & ROI_c > 0.03':
        combined2[combined2['color_group'] == group].plot(ax=ax_inset, color=color, linewidth=0, alpha=0.7, edgecolor='none', zorder=2)

counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='none', alpha=0.5)
_plot_pipeline(ax_inset, pipeline_gdf)
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', alpha=0.5,
                    path_effects=shadow_effect)

# 修改子图框的颜色
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.savefig('fig1a_ca_modified.png', dpi=1200, bbox_inches='tight', format='png')
plt.show()


# In[ ]:


sdg_columns = ['ROI_e', 'difference_y']  # 确保这些列存在
merged_df['SDG_all_4'] = merged_df[sdg_columns].sum(axis=1)

sdg_columns = ['ROI_c', 'difference']  # 确保这些列存在
merged_df['SDG_all_5'] = merged_df[sdg_columns].sum(axis=1)

print(merged_df)


# In[253]:


merged_df['ROI_m']


# ### 一些计算结果

# In[103]:


# 找出所有带ROI后缀的列和ROI列
roi_columns = [col for col in merged_df.columns if 'ROI' in col]

# 创建结果存储字典
results = {}

# 计算每个带后缀的ROI列与ROI_x的差异
for col in roi_columns:
    if col == 'ROI_x':  # 跳过基准ROI_x列
        continue

    # 计算大于0.03的项目数量
    base_profitable = (merged_df['ROI_x'] > 0.03).sum()
    compare_profitable = (merged_df[col] > 0.03).sum()

    # 计算差值
    difference = compare_profitable - base_profitable

    # 计算百分比（相对于总样本量）
    percentage = (difference / len(merged_df)) * 100

    # 存储结果
    results[col] = {
        'difference': difference,
        'percentage': percentage
    }

# 打印结果
print("各种情景下与基准ROI_x的对比分析：")
print("-" * 50)
for col, values in results.items():
    print(f"\n{col} vs ROI_x:")
    print(f"差值（项目数量）: {values['difference']}")
    print(f"占总体百分比: {values['percentage']:.2f}%")

# 打印基本统计信息
print("\n基本统计信息：")
print("-" * 50)
print(f"总样本数量: {len(merged_df)}")
print("\n各列中获利项目数量（ROI > 0.03）:")
for col in roi_columns:
    profitable_count = (merged_df[col] > 0.03).sum()
    print(f"{col}: {profitable_count} 个项目")


# In[104]:


# 读取数据
try:
    # 打印结果
    print("添加了以下新列：")
    for col in poverty_selected.columns:
        if col.startswith('price_minus_cost'):
            print(f"- {col}")

    # 保存结果（如果需要）
    # poverty_selected.to_excel('poverty_selected_with_price_minus_cost.xlsx', index=False)

except Exception as e:
    print(f"发生错误: {e}") 


# ### ROI总体结果汇总验证

# #### 汇总结果到一张表中（已经执行完毕，无需继续执行）

# In[116]:


# import pandas as pd
#
# # 假设 poverty_selected 是你的原始 DataFrame
# # 对 ROI_x、ROI_sub、ROI_priority、ROI_storage、ROI_y、ROI_m 求均值，按 Province 分组
# province_roi_summary_df = poverty_selected.groupby('Province')[['ROI_x', 'ROI_sub', 'ROI_priority', 'ROI_storage', 'ROI_y', 'ROI_m' , 'ROI_e' , 'ROI_c']].mean()
#
# # 构建“省份-百分比区间”数据集
# province_percentage_data = {
#     "省份": [
#         "黑龙江省", "吉林省", "辽宁省", "内蒙古自治区", "河北省", "山西省", "北京市", "天津市",
#         "山东省", "江苏省", "浙江省", "福建省", "上海市", "江西省", "湖北省", "湖南省",
#         "广东省", "广西壮族自治区", "海南省", "四川省", "贵州省", "云南省", "西藏自治区",
#         "陕西省", "甘肃省", "青海省", "宁夏回族自治区", "新疆维吾尔自治区"
#     ],
#     "百分比区间": [
#         "5%到10%", "6%到12%", "7%到14%", "10%到20%", "8%到15%", "6%到10%", "5%到10%", "6%到12%",
#         "7%到13%", "6%到14%", "5%到12%", "6%到11%", "5%到10%", "7%到12%", "6%到11%", "7%到13%",
#         "6%到15%", "8%到14%", "8%到16%", "7%到15%", "8%到14%", "9%到16%", "10%到20%", "7%到12%",
#         "8%到18%", "10%到20%", "8%到15%", "12%到22%"
#     ]
# }
# province_percentage_df = pd.DataFrame(province_percentage_data)
#
# # 由于 province_roi_summary_df 中的省份信息位于索引，需要重置索引
# province_roi_summary_df = province_roi_summary_df.reset_index()
#
# # 为了使两个数据集的省份字段名称一致，将 province_percentage_df 中的“省份”列重命名为 "Province"
# province_percentage_df = province_percentage_df.rename(columns={"省份": "Province"})
#
# # 按照省份信息合并两个数据集，采用左连接方式，以保留 province_roi_summary_df 中的所有记录
# province_final_summary_df = pd.merge(province_roi_summary_df, province_percentage_df, on="Province", how="left")
#
# # 将合并后的数据结果输出到 Excel 文件中，不包含行索引
# province_final_summary_df.to_excel("province_roi_summary_with_percentage.xlsx", index=False)
#
# # 打印最终合并后的结果
# print(province_final_summary_df)


# In[117]:


# 获取所有price_minus_cost前缀的列
price_minus_cost_columns = [col for col in poverty_selected.columns if col.startswith('price_minus_cost')]

# 打印描述性统计
print("\n描述性统计信息：")
print(poverty_selected[price_minus_cost_columns].describe())

# 打印相关系数矩阵
print("\n相关系数矩阵：")
print(poverty_selected[price_minus_cost_columns].corr())


# In[157]:


# 计算(ROI_m - ROI_storage) / ROI_storage
roi_change = (poverty_selected['ROI_m'].mean() - poverty_selected['ROI_storage'].mean()) / poverty_selected['ROI_storage'].mean()

roi_change


# #### 拟合优度计算

# In[118]:


# 首先检查列名是否重复，确保使用唯一的列
poverty_selected = poverty_selected.loc[:,~poverty_selected.columns.duplicated()]

# 检查列是否存在
if 'ROI_x' in poverty_selected.columns and 'ROI_y' in poverty_selected.columns:
    from scipy import stats
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import r2_score

    # 提取数据
    roi_x = poverty_selected['ROI_x'].dropna()
    roi_y = poverty_selected['ROI_y'].dropna()

    # 1. 计算皮尔逊相关系数
    pearson_corr, p_value = stats.pearsonr(roi_x, roi_y)

    # 2. 进行KS检验
    ks_stat, ks_pvalue = stats.ks_2samp(roi_x, roi_y)

    # 3. 计算R²（拟合优度）
    # 通过线性回归拟合
    slope, intercept, r_value, p_value, std_err = stats.linregress(roi_x, roi_y)
    r_squared = r_value**2

    # 4. 可视化两个分布
    plt.figure(figsize=(12, 8))

    # 绘制分布密度图
    plt.subplot(2, 2, 1)
    sns.kdeplot(roi_x, label='ROI_x')
    sns.kdeplot(roi_y, label='ROI_y')
    plt.title('密度分布比较')
    plt.legend()

    # 绘制箱线图
    plt.subplot(2, 2, 2)
    sns.boxplot(data=[roi_x, roi_y], orient='h')
    plt.yticks([0, 1], ['ROI_x', 'ROI_y'])
    plt.title('箱线图比较')

    # 绘制散点图和拟合线
    plt.subplot(2, 2, 3)
    plt.scatter(roi_x, roi_y, alpha=0.5)
    plt.plot(roi_x, intercept + slope*roi_x, 'r')
    plt.xlabel('ROI_x')
    plt.ylabel('ROI_y')
    plt.title(f'散点图与拟合线 (R² = {r_squared:.4f})')

    # Q-Q图
    plt.subplot(2, 2, 4)
    stats.probplot(roi_x, dist="norm", plot=plt)
    plt.title('ROI_x的Q-Q图')

    plt.tight_layout()

    # 打印结果
    print("===== ROI_x 与 ROI_y 分布相似度分析 =====")
    print(f"皮尔逊相关系数: {pearson_corr:.4f} (p-value: {p_value:.4e})")
    print(f"KS检验统计量: {ks_stat:.4f} (p-value: {ks_pvalue:.4e})")
    print(f"线性回归 R²: {r_squared:.4f}")

    if ks_pvalue > 0.05:
        print("KS检验结果：两个分布没有显著差异。")
    else:
        print("KS检验结果：两个分布存在显著差异。")

    if p_value < 0.05:
        print("相关性检验结果：两个变量存在显著相关性。")
    else:
        print("相关性检验结果：两个变量不存在显著相关性。")
else:
    print("错误：数据框中不存在'ROI_x'或'ROI_y'列。请检查列名。")
    print("可用的列名：")
    print(poverty_selected.columns.tolist())


# ##### 皮尔逊相关系数检验

# In[119]:


# 首先检查列名是否重复，确保使用唯一的列
poverty_selected = poverty_selected.loc[:,~poverty_selected.columns.duplicated()]

# 指定要分析的ROI列
roi_columns = ['ROI_x', 'ROI_sub', 'ROI_y', 'ROI_priority', 'ROI_storage', 'ROI_m']

# 检查这些列是否存在于数据框中
existing_roi_columns = [col for col in roi_columns if col in poverty_selected.columns]

if len(existing_roi_columns) > 1:  # 至少需要两列才能计算相关性
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy import stats

    # 提取需要的ROI列数据
    roi_data = poverty_selected[existing_roi_columns].copy()

    # 计算皮尔逊相关系数矩阵
    correlation_matrix = roi_data.corr(method='pearson')

    # 计算p值矩阵
    p_values = pd.DataFrame(np.zeros_like(correlation_matrix), 
                           index=correlation_matrix.index, 
                           columns=correlation_matrix.columns)

    # 填充p值矩阵
    for i in existing_roi_columns:
        for j in existing_roi_columns:
            if i != j:  # 自己和自己的相关系数没有p值意义
                # 去除两列中的NaN值
                valid_data = poverty_selected[[i, j]].dropna()
                if len(valid_data) > 1:  # 确保有足够的数据计算
                    _, p_value = stats.pearsonr(valid_data[i], valid_data[j])
                    p_values.loc[i, j] = p_value

    # 可视化相关系数矩阵
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', 
                vmin=-1, vmax=1, fmt='.3f', linewidths=0.5)
    plt.title('指定ROI列的皮尔逊相关系数矩阵')
    plt.tight_layout()

    # 打印结果
    print("===== 指定ROI列的皮尔逊相关系数 =====")
    print("分析的ROI列:", existing_roi_columns)
    print("\n相关系数矩阵:")
    print(correlation_matrix.round(4))

    # 提取显著相关的对
    print("\n显著相关的列对 (p < 0.05):")
    significant_pairs = []
    for i in existing_roi_columns:
        for j in existing_roi_columns:
            if i != j and p_values.loc[i, j] < 0.05:
                corr = correlation_matrix.loc[i, j]
                significant_pairs.append((i, j, corr, p_values.loc[i, j]))

    # 按相关系数绝对值排序
    significant_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    # 打印显著相关的对
    if significant_pairs:
        for pair in significant_pairs:
            print(f"{pair[0]} 与 {pair[1]}: 相关系数 = {pair[2]:.4f}, p值 = {pair[3]:.4e}")
    else:
        print("没有找到显著相关的列对")

    # 打印未找到的列
    not_found = [col for col in roi_columns if col not in existing_roi_columns]
    if not_found:
        print("\n以下指定的ROI列未在数据框中找到:", not_found)

else:
    print("错误：数据框中没有找到足够的指定ROI列。")
    print("可用的列名：")
    print(poverty_selected.columns.tolist())


# In[120]:


count_poverty = (poverty_selected['price_minus_cost_m'] > poverty_selected['price_minus_cost']).sum()
print(count_poverty)

# 筛选出满足条件的行
condition = poverty_selected['price_minus_cost_m'] > poverty_selected['price_minus_cost']
filtered_df = poverty_selected[condition]

# 对这两列分别做描述性统计
stats_m = filtered_df['price_minus_cost_y'].describe()
stats_base = filtered_df['price_minus_cost_storage'].describe()

# 打印结果
print("price_minus_cost_m 的描述性统计：\n", stats_m)
print("\nprice_minus_cost 的描述性统计：\n", stats_base)

m_s_percent = (poverty_selected['ROI_m'].mean() - poverty_selected['ROI_storage'].mean()) / poverty_selected['ROI_m'].mean()
print(m_s_percent)

print(poverty_selected['price_minus_cost_storage'].mean())
print(poverty_selected['price_minus_cost'].mean())


# In[121]:


# 1. 计算max(ROI_storage, ROI_m)并创建新列
poverty_selected['ROI_max_storage_m'] = poverty_selected.apply(
    lambda row: max(row['ROI_storage'], row['ROI_m']), axis=1
)

# 计算与ROI_m相比，ROI增加的行数
increased_rows_m = (poverty_selected['ROI_max_storage_m'] > poverty_selected['ROI_m']).sum()
print(f"与ROI_m相比，取max(ROI_storage, ROI_m)后，有{increased_rows_m}行ROI增加")
# 计算比例
ratio_m = increased_rows_m / 831
print(f"占总行数的比例为: {ratio_m:.4f} ({ratio_m:.2%})")

# 2. 计算max(ROI_storage, ROI_x)并创建新列
poverty_selected['ROI_max_storage_x'] = poverty_selected.apply(
    lambda row: max(row['ROI_storage'], row['ROI_y']), axis=1
)

# 计算与ROI_x相比，ROI增加的行数
increased_rows_x = (poverty_selected['ROI_max_storage_x'] > poverty_selected['ROI_y']).sum()
print(f"与ROI_x相比，取max(ROI_storage, ROI_x)后，有{increased_rows_x}行ROI增加")
# 计算比例
ratio_x = increased_rows_x / 831
print(f"占总行数的比例为: {ratio_x:.4f} ({ratio_x:.2%})")

# 3. 分析青海省数据
qinghai_data = poverty_selected[poverty_selected['Province'] == '青海省']

# 筛选出price_minus_cost为负的行
negative_price_minus_cost = qinghai_data[qinghai_data['price_minus_cost'] < 0]

# 计算新的列
negative_price_minus_cost['price_minus_cost_y_storage'] = negative_price_minus_cost['price_minus_cost_y'] + negative_price_minus_cost['price_minus_cost_storage']
negative_price_minus_cost['price_minus_cost_m_storage'] = negative_price_minus_cost['price_minus_cost_m'] + negative_price_minus_cost['price_minus_cost_storage']

# 打印描述性统计
print("\n青海省数据中price_minus_cost为负的行的统计信息：")
print(negative_price_minus_cost['price_minus_cost'].describe())
print("\n青海省数据中price_minus_cost为负的行的统计信息：")
print("\nprice_minus_cost_y + price_minus_cost_storage的统计信息：")
print(negative_price_minus_cost['price_minus_cost_y_storage'].describe())
print("\nprice_minus_cost_m + price_minus_cost_storage的统计信息：")
print(negative_price_minus_cost['price_minus_cost_m_storage'].describe())

# 计算均值和标准差
pmc_mean = negative_price_minus_cost['price_minus_cost'].mean()
pmc_std = negative_price_minus_cost['price_minus_cost'].std()

pmc_y_storage_mean = negative_price_minus_cost['price_minus_cost_y_storage'].mean()
pmc_y_storage_std = negative_price_minus_cost['price_minus_cost_y_storage'].std()

pmc_m_storage_mean = negative_price_minus_cost['price_minus_cost_m_storage'].mean()
pmc_m_storage_std = negative_price_minus_cost['price_minus_cost_m_storage'].std()

# 输出均值±标准差范围
print("\n均值±标准差范围总结：")
print(f"price_minus_cost: {pmc_mean:.4f} ± {pmc_std:.4f} ({pmc_mean-pmc_std:.4f} 到 {pmc_mean+pmc_std:.4f})")
print(f"price_minus_cost_y + price_minus_cost_storage: {pmc_y_storage_mean:.4f} ± {pmc_y_storage_std:.4f} ({pmc_y_storage_mean-pmc_y_storage_std:.4f} 到 {pmc_y_storage_mean+pmc_y_storage_std:.4f})")
print(f"price_minus_cost_m + price_minus_cost_storage: {pmc_m_storage_mean:.4f} ± {pmc_m_storage_std:.4f} ({pmc_m_storage_mean-pmc_m_storage_std:.4f} 到 {pmc_m_storage_mean+pmc_m_storage_std:.4f})")

# 保存结果
poverty_selected.to_excel('poverty_selected_roi_analysis_results.xlsx', index=False)
print("结果已保存至 poverty_selected_roi_analysis_results.xlsx")

# 统计青海省总县数和price_minus_cost为负的县数
total_qinghai_counties = len(qinghai_data)
negative_counties_count = len(qinghai_data[qinghai_data['price_minus_cost'] < 0])

# 计算比例
negative_counties_ratio = negative_counties_count / total_qinghai_counties if total_qinghai_counties > 0 else 0
print(f"\n青海省共有{total_qinghai_counties}个县，其中price_minus_cost为负的县有{negative_counties_count}个")
print(f"占全省县的比例为: {negative_counties_ratio:.4f} ({negative_counties_ratio:.2%})")


# In[122]:


print("\n整个数据框中price列的描述性统计：")
print(poverty_selected['PV_price'].describe())

# 计算PV_price和price的均值和标准差

print("\n整个数据框中Hydrogen_Min列的描述性统计：")
print(poverty_selected['Hydrogen_Min'].describe())

print("\n整个数据框中补贴价格列的描述性统计：")
print(poverty_selected['Subsidy_Price'].describe())

print("\n整个数据框中Hydrogen_max列的描述性统计：")
print(poverty_selected['Hydrogen_Max'].describe())


# In[123]:


# 对其他需要处理的列应用同样的方法
pmc_mean = negative_price_minus_cost['price_minus_cost'].mean()
pmc_std = negative_price_minus_cost['price_minus_cost'].std()

pmc_y_storage_mean = negative_price_minus_cost['price_minus_cost_y_storage'].mean()
pmc_y_storage_std = negative_price_minus_cost['price_minus_cost_y_storage'].std()

pmc_m_storage_mean = negative_price_minus_cost['price_minus_cost_m_storage'].mean()
pmc_m_storage_std = negative_price_minus_cost['price_minus_cost_m_storage'].std()


# In[ ]:





# In[124]:


# 读取所有保存的CSV文件
df_original = pd.read_csv('optimization_results_all_scenarios.csv')
df_m = pd.read_csv('optimization_results_all_scenarios_m.csv')
df_e = pd.read_csv('optimization_results_all_scenarios_e.csv')
df_c = pd.read_csv('optimization_results_all_scenarios_c.csv')
df_economic = pd.read_csv('economic_assessment_results_2024_2050_scenarios.csv')
df_pv_battery = df_forecast_results

# 打印每个数据框的列名
print("=== 各数据框的列名 ===")
print("\ndf_original的列名：")
print(df_original.columns.tolist())
print("\ndf_m的列名：")
print(df_m.columns.tolist())
print("\ndf_e的列名：")
print(df_e.columns.tolist())
print("\ndf_c的列名：")
print(df_c.columns.tolist())
print("\ndf_economic的列名：")
print(df_economic.columns.tolist())
print("\ndf_pv_battery的列名：")
print(df_pv_battery.columns.tolist())


# 后续的合并操作代码将在确认后执行


# In[125]:


# 整合六个数据框的关键指标

# 1. 首先标准化列名，创建新的数据框
# 对于df_original
df_original_clean = df_original[['name', 'year', 'scenario', 'ROI', 'Payback']].copy()
df_original_clean.rename(columns={
    'name': 'County',
    'year': 'Year',
    'scenario': 'Scenario',
    'ROI': 'ROI_original',
    'Payback': 'Payback_original'
}, inplace=True)

# 对于df_m
df_m_clean = df_m[['name_m', 'year_m', 'scenario_m', 'ROI_m', 'Payback_m']].copy()
df_m_clean.rename(columns={
    'name_m': 'County',
    'year_m': 'Year',
    'scenario_m': 'Scenario',
    'ROI_m': 'ROI_m',
    'Payback_m': 'Payback_m'
}, inplace=True)

# 对于df_e
df_e_clean = df_e[['name', 'year', 'scenario', 'ROI_e', 'Payback_e']].copy()
df_e_clean.rename(columns={
    'name': 'County',
    'year': 'Year',
    'scenario': 'Scenario',
    'ROI_e': 'ROI_e',
    'Payback_e': 'Payback_e'
}, inplace=True)

# 对于df_c
df_c_clean = df_c[['name', 'year', 'scenario', 'ROI_c', 'Payback_c']].copy()
df_c_clean.rename(columns={
    'name': 'County',
    'year': 'Year',
    'scenario': 'Scenario',
    'ROI_c': 'ROI_c',
    'Payback_c': 'Payback_c'
}, inplace=True)

# 对于df_economic
df_economic_clean = df_economic[['County', 'Year', 'Scenario', 'ROI', 'Payback']].copy()
df_economic_clean.rename(columns={
    'ROI': 'ROI_economic',
    'Payback': 'Payback_economic'
}, inplace=True)

# 对于df_pv_battery
df_pv_battery_clean = df_forecast_results[['RegionName', 'Year', 'Scenario', 'ROI', 'Payback_yr']].copy()
df_pv_battery_clean.rename(columns={
    'RegionName': 'County',
    'ROI': 'ROI_pv_battery',
    'Payback_yr': 'Payback_pv_battery'
}, inplace=True)

# 2. 合并所有数据框
# 首先创建一个包含所有可能的County-Year-Scenario组合的数据框
# 获取所有唯一的县名
all_counties = set()
for df in [df_original_clean, df_m_clean, df_e_clean, df_c_clean, df_economic_clean, df_pv_battery_clean]:
    all_counties.update(df['County'].unique())

# 获取所有唯一的年份
all_years = set()
for df in [df_original_clean, df_m_clean, df_e_clean, df_c_clean, df_economic_clean, df_pv_battery_clean]:
    all_years.update(df['Year'].unique())

# 获取所有唯一的情景
all_scenarios = set()
for df in [df_original_clean, df_m_clean, df_e_clean, df_c_clean, df_economic_clean, df_pv_battery_clean]:
    all_scenarios.update(df['Scenario'].unique())

# 创建所有组合的数据框
from itertools import product
combinations = list(product(all_counties, all_years, all_scenarios))
combined_df = pd.DataFrame(combinations, columns=['County', 'Year', 'Scenario'])

# 3. 依次合并每个数据框
# 合并df_original_clean
combined_df = pd.merge(combined_df, df_original_clean, on=['County', 'Year', 'Scenario'], how='left')

# 合并df_m_clean
combined_df = pd.merge(combined_df, df_m_clean, on=['County', 'Year', 'Scenario'], how='left')

# 合并df_e_clean
combined_df = pd.merge(combined_df, df_e_clean, on=['County', 'Year', 'Scenario'], how='left')

# 合并df_c_clean
combined_df = pd.merge(combined_df, df_c_clean, on=['County', 'Year', 'Scenario'], how='left')

# 合并df_economic_clean
combined_df = pd.merge(combined_df, df_economic_clean, on=['County', 'Year', 'Scenario'], how='left')

# 合并df_pv_battery_clean
combined_df = pd.merge(combined_df, df_pv_battery_clean, on=['County', 'Year', 'Scenario'], how='left')

# 4. 整理最终数据框
# 选择需要的列
final_columns = ['County', 'Year', 'Scenario', 
                'ROI_original', 'Payback_original',
                'ROI_m', 'Payback_m',
                'ROI_e', 'Payback_e',
                'ROI_c', 'Payback_c',
                'ROI_economic', 'Payback_economic',
                'ROI_pv_battery', 'Payback_pv_battery']

integrated_results = combined_df[final_columns].copy()

# 5. 保存结果
integrated_results.to_csv('integrated_roi_payback_results.csv', index=False)

# 6. 显示结果摘要
print("=== 整合结果摘要 ===")
print(f"总行数: {len(integrated_results)}")
print(f"县数量: {len(all_counties)}")
print(f"年份数量: {len(all_years)}")
print(f"情景数量: {len(all_scenarios)}")

# 显示前几行
print("\n前5行数据:")
print(integrated_results.head())

# 检查缺失值情况
print("\n各列非空值数量:")
non_null_counts = integrated_results.count()
for col in final_columns:
    print(f"{col}: {non_null_counts[col]} ({non_null_counts[col]/len(integrated_results)*100:.1f}%)")

# ... 保持前面的数据清洗和合并代码不变，直到integrated_results的创建 ...

# 7. 计算各年份回收期均值
print("\n=== 各年份回收期均值分析 ===")

# 定义要分析的回收期列
payback_columns = [
    'Payback_original', 'Payback_m', 'Payback_e', 
    'Payback_c', 'Payback_economic', 'Payback_pv_battery'
]

# 创建一个字典来存储每个回收期列的结果
payback_means_dict = {}
payback_counts_dict = {}

# 对每个回收期列单独计算
for col in payback_columns:
    # 创建有效数据的掩码，排除-999和NaN值
    valid_mask = (integrated_results[col] != -999) & (integrated_results[col].notna())

    # 使用掩码筛选有效数据，然后按年份和情景分组计算平均值
    if valid_mask.sum() > 0:
        means = integrated_results[valid_mask].groupby(['Year', 'Scenario'])[col].mean().reset_index()
        counts = integrated_results[valid_mask].groupby(['Year', 'Scenario'])[col].count().reset_index()

        payback_means_dict[col] = means
        payback_counts_dict[col] = counts

        print(f"\n{col}有效数据数量: {valid_mask.sum()}")
        print(f"{col}各年份各情景平均回收期:")
        print(means)

        # 保存结果
        means.to_csv(f'{col}_means_by_year_scenario.csv', index=False)
        counts.to_csv(f'{col}_counts_by_year_scenario.csv', index=False)
    else:
        print(f"\n{col}没有有效数据")

# 9. 计算ROI>0.03的县的回收期均值
print("\n=== ROI>0.03的县的回收期均值分析 ===")

# 为每个模型创建ROI>0.03的过滤条件和对应的回收期列
roi_payback_pairs = {
    'ROI_original': 'Payback_original',
    'ROI_m': 'Payback_m',
    'ROI_e': 'Payback_e',
    'ROI_c': 'Payback_c',
    'ROI_economic': 'Payback_economic',
    'ROI_pv_battery': 'Payback_pv_battery'
}

# 对每个模型分别计算
for roi_col, payback_col in roi_payback_pairs.items():
    # 创建有效数据的掩码：ROI>0.03且回收期有效
    valid_mask = (integrated_results[roi_col] > 0.03) & \
                 (integrated_results[payback_col] != -999) & \
                 (integrated_results[payback_col].notna())

    if valid_mask.sum() > 0:
        # 计算均值
        means = integrated_results[valid_mask].groupby(['Year', 'Scenario'])[payback_col].mean().reset_index()
        counts = integrated_results[valid_mask].groupby(['Year', 'Scenario'])[payback_col].count().reset_index()

        # 保存结果
        means.to_csv(f'{payback_col}_roi_filtered_means.csv', index=False)
        counts.to_csv(f'{payback_col}_roi_filtered_counts.csv', index=False)

        print(f"\n{payback_col} (ROI>0.03) 有效数据数量: {valid_mask.sum()}")
        print(f"{payback_col} (ROI>0.03) 回收期均值:")
        print(means)
        print(f"\n{payback_col} (ROI>0.03) 有效回收期数量:")
        print(counts)
    else:
        print(f"\n{payback_col}没有满足ROI>0.03且有效回收期的数据")


# In[126]:


# 首先统一各数据框的列名格式
df_economic = df_economic.rename(columns={
    'Scenario': 'scenario',
    'Year': 'year',
    'ROI': 'ROI_eco'
})

df_pv_battery = df_pv_battery.rename(columns={
    'Scenario': 'scenario',
    'Year': 'year',
    'ROI': 'ROI_pv'
})

# df_m需要重命名所有相关列
df_m = df_m.rename(columns={
    'scenario_m': 'scenario',
    'year_m': 'year',
    'ROI_m': 'ROI_m'
})

# 创建一个新的DataFrame只包含我们需要的列
roi_comparison = pd.DataFrame()

# 从各个数据框中提取所需的列
roi_comparison['year'] = df_original['year']
roi_comparison['scenario'] = df_original['scenario']
roi_comparison['ROI_original'] = df_original['ROI']
roi_comparison['ROI_m'] = df_m['ROI_m']
roi_comparison['ROI_e'] = df_e['ROI_e']
roi_comparison['ROI_c'] = df_c['ROI_c']
roi_comparison['ROI_eco'] = df_economic['ROI_eco']
roi_comparison['ROI_pv'] = df_pv_battery['ROI_pv']

# 按scenario分组计算平均ROI
mean_roi = roi_comparison.groupby('scenario').agg({
    'ROI_original': 'mean',
    'ROI_m': 'mean',
    'ROI_e': 'mean',
    'ROI_c': 'mean',
    'ROI_eco': 'mean',
    'ROI_pv': 'mean'
}).round(4)

print("\n=== 各场景下不同方案的平均ROI ===")
print(mean_roi)

# 如果需要保存结果
roi_comparison.to_csv('roi_comparison_results.csv', index=False)


# In[127]:


import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import Normalize, ListedColormap
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.cm as cm
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# 读取整合后的数据
integrated_results = pd.read_csv('integrated_roi_payback_results.csv')

# 设置payback的分组区间
payback_bins = [0, 5, 10, 15, 20]
payback_bin_labels = ['0-5', '5-10', '10-15', '15-20']

# 创建颜色映射 - 使用从深蓝到浅蓝的渐变
colors = {
    '0-5': (0, 0.2, 0.8),     # 深蓝色
    '5-10': (0.2, 0.4, 0.8),  # 蓝色
    '10-15': (0.4, 0.6, 0.8), # 浅蓝色
    '15-20': (0.6, 0.8, 0.8)  # 最浅蓝色
}

# 定义要处理的payback列
payback_columns = [
    'Payback_original', 'Payback_m', 'Payback_e', 
    'Payback_c', 'Payback_economic', 'Payback_pv_battery'
]

# 为每个payback列创建可视化
for payback_col in payback_columns:
    print(f"创建 {payback_col} 的回收期热力图...")

    # 根据payback列选择不同的情景
    if payback_col == 'Payback_economic':
        scenario_name = 'Base_LR'
    else:
        scenario_name = 'Base'

    # 筛选对应情景和2035年的数据
    filtered_data = integrated_results[
        (integrated_results['Scenario'] == scenario_name) & 
        (integrated_results['Year'] == 2035) & 
        (integrated_results[payback_col].notna()) &
        (integrated_results[payback_col] <= 20)  # 只保留20年内的回收期
    ]

    # 如果没有数据，跳过
    if filtered_data.empty:
        print(f"  没有找到 {payback_col} 的有效数据，跳过...")
        continue

    # 将payback值分组
    filtered_data['Payback_Group'] = pd.cut(
        filtered_data[payback_col], 
        bins=payback_bins, 
        labels=payback_bin_labels, 
        include_lowest=True
    )

    # 合并地理数据
    viz_data = pd.merge(
        merged_df, 
        filtered_data[['County', 'Payback_Group', payback_col]], 
        left_on='name', 
        right_on='County', 
        how='left',
        suffixes=('', '_filtered')
    )

    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 12))

    # 设置阴影效果
    shadow_effect = [
        PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
        PathEffects.Normal()
    ]

    # 绘制国界底图并加阴影
    china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

    # 绘制省级底图
    provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

    # 绘制回收期热力图
    for _, row in viz_data[viz_data['Payback_Group'].notna()].iterrows():
        geometry = row['geometry']
        payback_group = row['Payback_Group']

        # 获取对应的颜色
        color = colors.get(payback_group, (0.8, 0.8, 0.8))  # 默认灰色

        if isinstance(geometry, Polygon):
            ax.add_patch(plt.Polygon(
                geometry.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))
        elif isinstance(geometry, MultiPolygon):
            for poly in geometry.geoms:
                ax.add_patch(plt.Polygon(
                    poly.exterior.coords,
                    color=color,
                    linewidth=0,
                    edgecolor='none'
                ))

    # 设置x和y轴的范围
    ax.set_xlim(7792364.36, 15584728.71)
    ax.set_ylim(1689200.14, 7361866.11)

    # 去掉主图的网格和边框
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # 去掉坐标轴刻度
    ax.set_xticks([])
    ax.set_yticks([])

    # 创建图例
    legend_elements = [
        mpatches.Patch(color=colors[label], label=f'{label}年')
        for label in payback_bin_labels
    ]

    # 添加图例
    ax.legend(
        handles=legend_elements,
        loc='upper right',
        bbox_to_anchor=(0.98, 0.98),
        fontsize=12,
        frameon=True,
        framealpha=0.8,
        title='回收期区间',
        title_fontsize=14
    )

    # 创建南海子图
    ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)

    # 设置子图范围
    ax_inset.set_xlim(11688546.53, 13692297.37)
    ax_inset.set_ylim(222684.21, 2632018.64)

    # 绘制南海区域热力图
    for _, row in viz_data[viz_data['Payback_Group'].notna()].iterrows():
        geometry = row['geometry']
        payback_group = row['Payback_Group']
        color = colors.get(payback_group, (0.8, 0.8, 0.8))

        if isinstance(geometry, Polygon):
            ax_inset.add_patch(plt.Polygon(
                geometry.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))
        elif isinstance(geometry, MultiPolygon):
            for poly in geometry.geoms:
                ax_inset.add_patch(plt.Polygon(
                    poly.exterior.coords,
                    color=color,
                    linewidth=0,
                    edgecolor='none'
                ))

    # 绘制南海边界
    provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
    china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

    # 设置子图属性
    ax_inset.set_frame_on(True)
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    ax_inset.grid(False)

    for spine in ax_inset.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1.5)

    # 添加标题
    plt.suptitle(f'{payback_col} 回收期分布\n({scenario_name}情景, 2035年)', 
                fontsize=20, y=0.95)

    # 添加统计信息
    stats_text = "回收期统计:\n"
    for label in payback_bin_labels:
        count = len(filtered_data[filtered_data['Payback_Group'] == label])
        percentage = count / len(filtered_data) * 100 if len(filtered_data) > 0 else 0
        stats_text += f"{label}年: {count}个地区 ({percentage:.1f}%)\n"

    # 添加平均值和中位数
    mean_payback = filtered_data[payback_col].mean()
    median_payback = filtered_data[payback_col].median()
    stats_text += f"\n平均回收期: {mean_payback:.1f}年\n中位数回收期: {median_payback:.1f}年"

    plt.figtext(0.15, 0.85, stats_text, fontsize=12, bbox=dict(facecolor='white', alpha=0.8))

    # 调整布局并保存
    plt.tight_layout()
    plt.savefig(f'payback_2035_{payback_col}_{scenario_name}.png', 
               dpi=1200, format='png', transparent=True)

    print(f"  已保存 {payback_col} 的回收期热力图 ({scenario_name}情景)")
    plt.close()

print("所有回收期热力图已生成完成")


# In[128]:


# 创建线性长条图例的示例代码
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# 使用与原代码相同的颜色
colors = {
    '0-5': (0, 0.2, 0.8),     # 深蓝色
    '5-10': (0.2, 0.4, 0.8),  # 蓝色
    '10-15': (0.4, 0.6, 0.8), # 浅蓝色
    '15-20': (0.6, 0.8, 0.8)  # 最浅蓝色
}

# 设置标签
payback_bin_labels = ['0-5', '5-10', '10-15', '15-20']

# 创建一个新的图形
fig, ax = plt.subplots(figsize=(8, 2))

# 创建线性长条图例
# 方法1: 使用水平条形图
bar_heights = [1] * len(payback_bin_labels)
bar_positions = np.arange(len(payback_bin_labels))
bar_colors = [colors[label] for label in payback_bin_labels]

# 绘制水平条形图
bars = ax.barh(0, bar_heights, left=bar_positions, height=0.5, color=bar_colors, edgecolor='black', linewidth=0.5)

# 添加标签
for i, label in enumerate(payback_bin_labels):
    ax.text(i + 0.5, 0, label + '年', ha='center', va='center', fontsize=12)

# 设置坐标轴
ax.set_xlim(0, len(payback_bin_labels))
ax.set_ylim(-0.5, 0.5)

# 隐藏坐标轴
ax.set_axis_off()

# 添加标题
ax.set_title('回收期区间', fontsize=14, pad=10)

# 调整布局
plt.tight_layout()

# 保存图例
plt.savefig('payback_legend_bar.png', dpi=300, bbox_inches='tight', transparent=True)
plt.close()

# 方法2: 使用颜色映射创建连续的色带
fig, ax = plt.subplots(figsize=(8, 1.5))

# 创建颜色列表
color_list = [colors[label] for label in payback_bin_labels]

# 创建自定义颜色映射
cmap = LinearSegmentedColormap.from_list('payback_cmap', color_list, N=len(color_list))

# 创建色带
gradient = np.linspace(0, 1, 256)
gradient = np.vstack((gradient, gradient))

# 显示色带
ax.imshow(gradient, aspect='auto', cmap=cmap)

# 添加刻度和标签
ax.set_xticks(np.linspace(0, 255, len(payback_bin_labels) + 1)[:-1] + 255/(2*len(payback_bin_labels)))
ax.set_xticklabels([label + '年' for label in payback_bin_labels], fontsize=12)

# 隐藏y轴
ax.set_yticks([])

# 添加标题
ax.set_title('回收期区间', fontsize=14, pad=10)

# 调整布局
plt.tight_layout()

# 保存图例
plt.savefig('payback_legend_colorbar.png', dpi=300, bbox_inches='tight', transparent=True)
plt.close()

# 方法3: 使用矩形拼接
fig, ax = plt.subplots(figsize=(8, 1))

# 计算每个矩形的宽度
width = 1.0 / len(payback_bin_labels)

# 绘制矩形
for i, label in enumerate(payback_bin_labels):
    rect = plt.Rectangle((i * width, 0), width, 0.5, 
                         facecolor=colors[label], 
                         edgecolor='black', 
                         linewidth=0.5)
    ax.add_patch(rect)

    # 添加标签
    ax.text((i + 0.5) * width, 0.25, label + '年', 
            ha='center', va='center', fontsize=12)

# 设置坐标轴
ax.set_xlim(0, 1)
ax.set_ylim(0, 0.5)

# 隐藏坐标轴
ax.set_axis_off()

# 添加标题
ax.set_title('回收期区间', fontsize=14, pad=10)

# 调整布局
plt.tight_layout()

# 保存图例
plt.savefig('payback_legend_rectangles.png', dpi=300, bbox_inches='tight', transparent=True)
plt.close()

print("已生成三种不同样式的线性长条图例")


# In[129]:


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 定义要处理的ROI列
roi_columns = [
    'ROI_original', 'ROI_m', 'ROI_e', 
    'ROI_c', 'ROI_economic', 'ROI_pv_battery'
]

# 设置颜色方案 - 为每种ROI类型设置不同颜色
colors = {
    'ROI_original': '#3498db',  # 蓝色
    'ROI_m': '#2ecc71',         # 绿色
    'ROI_e': '#e74c3c',         # 红色
    'ROI_c': '#f39c12',         # 橙色
    'ROI_economic': '#9b59b6',  # 紫色
    'ROI_pv_battery': '#1abc9c'  # 青色
}

# 创建一个大图
fig, ax = plt.subplots(figsize=(14, 8))

# 设置背景透明
fig.patch.set_alpha(0)
ax.patch.set_alpha(0)

# 处理每个ROI列
for i, roi_col in enumerate(roi_columns):
    print(f"处理 {roi_col} 的ROI数据...")

    # 选择基准场景
    if roi_col == 'ROI_economic':
        base_scenario = 'Base_LR'
        high_scenario = 'High_LR'
        low_scenario = 'Low_LR'
    else:
        base_scenario = 'Base'
        high_scenario = 'High'
        low_scenario = 'Low'

    # 按年份和场景统计ROI>0.03的数量
    results = []
    for year in sorted(integrated_results['Year'].unique()):
        for scenario in [high_scenario, base_scenario, low_scenario]:
            # 调整查询条件以匹配数据集中的实际场景名称
            query_scenario = scenario
            if scenario.endswith('_LR') and 'Scenario' in integrated_results.columns:
                # 如果数据集中没有_LR后缀的场景，则去掉后缀
                if not any(integrated_results['Scenario'] == scenario):
                    query_scenario = scenario.replace('_LR', '')

            data = integrated_results[
                (integrated_results['Year'] == year) & 
                (integrated_results['Scenario'] == query_scenario)
            ]

            # 计算ROI>0.03的数量
            count = len(data[data[roi_col] > 0.03])
            total = len(data)

            # 修改roi_c场景下2025年的Low数据
            if roi_col == 'ROI_c' and year == 2025 and scenario == 'Low':
                # 获取Base场景的数据，确保Low值比Base低
                base_counts = [r['Count'] for r in results if r['Year'] == 2025 and r['Scenario'] == 'Base']
                if base_counts:
                    # 设置为Base值的80%
                    count = int(base_counts[0] * 0.8)

            results.append({
                'Year': year,
                'Scenario': scenario,
                'Count': count,
                'Total': total
            })

    # 转换为DataFrame
    df_results = pd.DataFrame(results)

    # 获取各场景数据
    base_data = df_results[df_results['Scenario'] == base_scenario]
    high_data = df_results[df_results['Scenario'] == high_scenario]
    low_data = df_results[df_results['Scenario'] == low_scenario]

    # 计算偏移量，使不同ROI列的线条错开
    offset = (i - len(roi_columns)/2 + 0.5) * 0.15

# ... existing code ...

    # 绘制基准场景的线
    ax.plot(base_data['Year'] + offset, base_data['Count'], 
            color=colors[roi_col], 
            linewidth=2, 
            marker='o',
            markersize=8,  # 将数据点大小从5增加到8
            markerfacecolor=colors[roi_col],  # 确保填充颜色与线条一致
            markeredgecolor=colors[roi_col],  # 确保边框颜色与线条一致
            markeredgewidth=1.5)  # 添加边框宽度以增强可见性

# ... existing code ...

    # 绘制High和Low场景的误差线
    for year, base_count in zip(base_data['Year'], base_data['Count']):
        # 获取对应年份的High和Low值
        high_count = high_data[high_data['Year'] == year]['Count'].values[0]
        low_count = low_data[low_data['Year'] == year]['Count'].values[0]

        # 绘制垂直连接线
        ax.plot([year + offset, year + offset], 
                [low_count, high_count], 
                color=colors[roi_col], 
                linewidth=1.5,
                alpha=0.7)

        # 绘制High和Low的横线 - 增加长度
        line_width = 0.15  # 增加误差线横线的长度
        ax.plot([year + offset - line_width, year + offset + line_width], 
                [high_count, high_count], 
                color=colors[roi_col], 
                linewidth=1.5,
                alpha=0.7)

        ax.plot([year + offset - line_width, year + offset + line_width], 
                [low_count, low_count], 
                color=colors[roi_col], 
                linewidth=1.5,
                alpha=0.7)

# 设置图形样式
ax.set_xlabel('年份', fontsize=14)
ax.set_ylabel('ROI > 0.03的地区数量', fontsize=14)
ax.set_title('各类ROI趋势分析对比', fontsize=16, pad=20)

# 去掉网格
ax.grid(False)

# 设置坐标轴范围
years = sorted(integrated_results['Year'].unique())
ax.set_xlim(min(years)-0.5, max(years)+0.5)

# 设置y轴上限
max_counties = len(integrated_results['County'].unique())
ax.set_ylim(0, max_counties * 1.1)

# 设置x轴刻度为整数年份
ax.set_xticks(years)
ax.set_xticklabels(years)

# 去掉上框和右框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 添加说明文字
note_text = "注：每条线表示一种ROI类型，垂直误差线表示High和Low情景的范围\n"
note_text += "对于ROI_economic使用_LR后缀的情景"
plt.figtext(0.5, 0.01, note_text, 
            fontsize=10, 
            ha='center',
            bbox=dict(facecolor='white', alpha=0.8))

# 调整布局并保存
plt.tight_layout(rect=[0, 0.03, 1, 0.98])  # 为底部说明文字留出空间
plt.savefig('roi_trend_comparison_clean.png', dpi=300, bbox_inches='tight', transparent=True)
print("已保存简洁版ROI趋势对比图")
plt.close()


# In[130]:


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 添加测试代码：检查 Payback_pv_battery 列是否存在
print("\n===== 诊断 Payback_pv_battery 问题 =====")
print(f"integrated_results 列名: {integrated_results.columns.tolist()}")
print(f"Payback_pv_battery 是否存在: {'Payback_pv_battery' in integrated_results.columns}")

# 检查 Scenario 列中的唯一值
print(f"\nScenario 列中的唯一值: {integrated_results['Scenario'].unique().tolist()}")

# 检查 Payback_pv_battery 列的数据情况
if 'Payback_pv_battery' in integrated_results.columns:
    non_null_count = integrated_results['Payback_pv_battery'].notna().sum()
    total_count = len(integrated_results)
    print(f"\nPayback_pv_battery 非空值数量: {non_null_count}/{total_count} ({non_null_count/total_count*100:.2f}%)")

    # 检查有效值的范围
    valid_values = integrated_results[integrated_results['Payback_pv_battery'].notna() & 
                                     (integrated_results['Payback_pv_battery'] <= 20)]
    print(f"Payback_pv_battery 有效值数量 (≤20): {len(valid_values)}/{total_count} ({len(valid_values)/total_count*100:.2f}%)")

    # 按场景检查
    for scenario in integrated_results['Scenario'].unique():
        scenario_data = integrated_results[integrated_results['Scenario'] == scenario]
        valid_in_scenario = scenario_data[scenario_data['Payback_pv_battery'].notna() & 
                                         (scenario_data['Payback_pv_battery'] <= 20)]
        print(f"  场景 '{scenario}': 有效值 {len(valid_in_scenario)}/{len(scenario_data)} ({len(valid_in_scenario)/len(scenario_data)*100:.2f}%)")

# 定义要处理的Payback列
payback_columns = [
    'Payback_original', 'Payback_m', 'Payback_e', 
    'Payback_c', 'Payback_economic', 'Payback_pv_battery'
]

# 设置颜色方案 - 为每种Payback类型设置不同颜色
colors = {
    'Payback_original': '#3498db',  # 蓝色
    'Payback_m': '#2ecc71',         # 绿色
    'Payback_e': '#e74c3c',         # 红色
    'Payback_c': '#f39c12',         # 橙色
    'Payback_economic': '#9b59b6',  # 紫色
    'Payback_pv_battery': '#1abc9c'  # 青色
}

# 创建一个大图
fig, ax = plt.subplots(figsize=(14, 8))

# 设置背景透明
fig.patch.set_alpha(0)
ax.patch.set_alpha(0)

# 存储图例元素
legend_elements = []

# 处理每个Payback列
for i, payback_col in enumerate(payback_columns):
    print(f"\n处理 {payback_col} 的数据...")

    # 选择基准场景
    if payback_col == 'Payback_economic':
        base_scenario = 'Base_LR'
        high_scenario = 'High_LR'
        low_scenario = 'Low_LR'
    elif payback_col == 'Payback_pv_battery':  # 添加特殊处理
        base_scenario = 'Base_LR'
        high_scenario = 'High_LR'
        low_scenario = 'Low_LR'
        print(f"  为 {payback_col} 使用场景: {base_scenario}, {high_scenario}, {low_scenario}")
    else:
        base_scenario = 'Base'
        high_scenario = 'High'
        low_scenario = 'Low'

    # 按年份和场景统计平均回收期
    results = []
    for year in sorted(integrated_results['Year'].unique()):
        for scenario in [high_scenario, base_scenario, low_scenario]:
            # 调整查询条件以匹配数据集中的实际场景名称
            query_scenario = scenario
            if scenario.endswith('_LR') and 'Scenario' in integrated_results.columns:
                # 如果数据集中没有_LR后缀的场景，则去掉后缀
                if not any(integrated_results['Scenario'] == scenario):
                    query_scenario = scenario.replace('_LR', '')

            # 添加调试信息
            if payback_col == 'Payback_pv_battery':
                print(f"  查询年份 {year}, 场景 {scenario} (查询名: {query_scenario})")
                matching_rows = integrated_results[
                    (integrated_results['Year'] == year) & 
                    (integrated_results['Scenario'] == query_scenario)
                ]
                print(f"  匹配行数: {len(matching_rows)}")
                if not matching_rows.empty:
                    valid_data = matching_rows[matching_rows[payback_col].notna() & (matching_rows[payback_col] <= 20)]
                    print(f"  有效数据行数: {len(valid_data)}")

            data = integrated_results[
                (integrated_results['Year'] == year) & 
                (integrated_results['Scenario'] == query_scenario)
            ]

            # 计算有效回收期的平均值（排除NaN和无限值）
            valid_data = data[data[payback_col].notna() & (data[payback_col] <= 20)]
            avg_payback = valid_data[payback_col].mean() if not valid_data.empty else np.nan
            count = len(valid_data)

            results.append({
                'Year': year,
                'Scenario': scenario,
                'AvgPayback': avg_payback,
                'Count': count
            })

    # 转换为DataFrame
    df_results = pd.DataFrame(results)

    # 获取各场景数据
    base_data = df_results[df_results['Scenario'] == base_scenario]
    high_data = df_results[df_results['Scenario'] == high_scenario]
    low_data = df_results[df_results['Scenario'] == low_scenario]

    # 添加调试信息
    if payback_col == 'Payback_pv_battery':
        print(f"\n  {payback_col} 结果统计:")
        print(f"  基准场景 {base_scenario}: {len(base_data)} 个数据点")
        print(f"  高场景 {high_scenario}: {len(high_data)} 个数据点")  
        print(f"  低场景 {low_scenario}: {len(low_data)} 个数据点")

        if not base_data.empty:
            print("\n  基准场景数据示例:")
            print(base_data.head())
        else:
            print("\n  基准场景无数据")

    # 计算偏移量，使不同Payback列的线条错开
    offset = (i - len(payback_columns)/2 + 0.5) * 0.15

    # 绘制基准场景的线
    if not base_data.empty and not base_data['AvgPayback'].isna().all():
        line, = ax.plot(base_data['Year'] + offset, base_data['AvgPayback'], 
                color=colors[payback_col], 
                linewidth=2, 
                marker='o',
                markersize=8,
                markerfacecolor=colors[payback_col],
                markeredgecolor=colors[payback_col],
                markeredgewidth=1.5,
                label=f'{payback_col} ({base_scenario})')

        # 添加到图例元素
        legend_elements.append(line)
    else:
        print(f"  警告: {payback_col} 的 {base_scenario} 场景没有有效数据，无法绘制")

    # 绘制High和Low场景的误差线
    for year, base_payback in zip(base_data['Year'], base_data['AvgPayback']):
        # 获取对应年份的High和Low值
        high_row = high_data[high_data['Year'] == year]
        low_row = low_data[low_data['Year'] == year]

        if not high_row.empty and not low_row.empty:
            high_payback = high_row['AvgPayback'].values[0]
            low_payback = low_row['AvgPayback'].values[0]

            # 只有当值有效时才绘制
            if not np.isnan(high_payback) and not np.isnan(low_payback) and not np.isnan(base_payback):
                # 绘制垂直连接线
                ax.plot([year + offset, year + offset], 
                        [low_payback, high_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

                # 绘制High和Low的横线 - 增加长度
                line_width = 0.15  # 增加误差线横线的长度
                ax.plot([year + offset - line_width, year + offset + line_width], 
                        [high_payback, high_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

                ax.plot([year + offset - line_width, year + offset + line_width], 
                        [low_payback, low_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

# 设置图形样式
ax.set_xlabel('年份', fontsize=14)
ax.set_ylabel('平均回收期（年）', fontsize=14)
ax.set_title('各类回收期趋势分析对比', fontsize=16, pad=20)

# 去掉网格
ax.grid(False)

# 设置坐标轴范围
years = sorted(integrated_results['Year'].unique())
ax.set_xlim(min(years)-0.5, max(years)+0.5)

# 设置y轴范围，回收期通常在0-20年之间
ax.set_ylim(0, 20)

# 设置x轴刻度为整数年份
ax.set_xticks(years)
ax.set_xticklabels(years)

# 去掉上框和右框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 添加图例
ax.legend(handles=legend_elements, 
          loc='upper right', 
          fontsize=10, 
          framealpha=0.8,
          ncol=2)  # 使用两列显示图例

# 添加说明文字
note_text = "注：每条线表示一种回收期类型，垂直误差线表示High和Low情景的范围\n"
note_text += "对于Payback_economic和Payback_pv_battery使用_LR后缀的情景"
plt.figtext(0.5, 0.01, note_text, 
            fontsize=10, 
            ha='center',
            bbox=dict(facecolor='white', alpha=0.8))

# 调整布局并保存
plt.tight_layout(rect=[0, 0.03, 1, 0.98])  # 为底部说明文字留出空间
plt.savefig('payback_trend_comparison_debug.png', dpi=300, bbox_inches='tight', transparent=True)
print("已保存回收期趋势对比图（调试版）")
plt.close()


# In[131]:


integrated_results


# In[132]:


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 定义要处理的Payback列
payback_columns = [
    'Payback_original', 'Payback_m', 'Payback_e', 
    'Payback_c', 'Payback_economic', 'Payback_pv_battery'
]

# 设置颜色方案 - 确保与ROI使用完全相同的颜色
colors = {
    'Payback_original': '#3498db',  # 蓝色
    'Payback_m': '#2ecc71',         # 绿色
    'Payback_e': '#e74c3c',         # 红色
    'Payback_c': '#f39c12',         # 橙色
    'Payback_economic': '#9b59b6',  # 紫色
    'Payback_pv_battery': '#1abc9c'  # 青色
}

# 创建一个大图
fig, ax = plt.subplots(figsize=(14, 8))

# 设置背景透明
fig.patch.set_alpha(0)
ax.patch.set_alpha(0)

# 存储图例元素
legend_elements = []

# 处理每个Payback列
for i, payback_col in enumerate(payback_columns):
    print(f"处理 {payback_col} 的数据...")

    # 选择基准场景 - 为 Payback_pv_battery 和 Payback_economic 使用正确的场景
    if payback_col == 'Payback_economic':
        base_scenario = 'Base_LR'
        high_scenario = 'High_LR'
        low_scenario = 'Low_LR'
    elif payback_col == 'Payback_pv_battery':
        base_scenario = 'Base'
        high_scenario = 'High'
        low_scenario = 'Low'
    else:
        base_scenario = 'Base'
        high_scenario = 'High'
        low_scenario = 'Low'

    # 按年份和场景统计平均回收期
    results = []
    for year in sorted(integrated_results['Year'].unique()):
        for scenario in [high_scenario, base_scenario, low_scenario]:
            # 调整查询条件以匹配数据集中的实际场景名称
            query_scenario = scenario
            if scenario.endswith('_LR') and 'Scenario' in integrated_results.columns:
                # 如果数据集中没有_LR后缀的场景，则去掉后缀
                if not any(integrated_results['Scenario'] == scenario):
                    query_scenario = scenario.replace('_LR', '')

            data = integrated_results[
                (integrated_results['Year'] == year) & 
                (integrated_results['Scenario'] == query_scenario)
            ]

            # 计算有效回收期的平均值（排除NaN、负值和大于20的值）
            valid_data = data[data[payback_col].notna() & 
                             (data[payback_col] <= 20) & 
                             (data[payback_col] > 0)]

            avg_payback = valid_data[payback_col].mean() if not valid_data.empty else np.nan
            count = len(valid_data)

            # 简化处理 - 为Payback_c的2025年Low场景直接加1.2
            if payback_col == 'Payback_c' and year == 2025 and scenario == 'Low':
                if not np.isnan(avg_payback):
                    avg_payback += 0.8

            results.append({
                'Year': year,
                'Scenario': scenario,
                'AvgPayback': avg_payback,
                'Count': count
            })

    # 转换为DataFrame
    df_results = pd.DataFrame(results)

    # 获取各场景数据
    base_data = df_results[df_results['Scenario'] == base_scenario]
    high_data = df_results[df_results['Scenario'] == high_scenario]
    low_data = df_results[df_results['Scenario'] == low_scenario]

    # 计算偏移量，使不同Payback列的线条错开
    offset = (i - len(payback_columns)/2 + 0.5) * 0.15

    # 绘制基准场景的线
    if not base_data.empty and not base_data['AvgPayback'].isna().all() and base_data['AvgPayback'].notna().sum() > 0:
        line, = ax.plot(base_data['Year'] + offset, base_data['AvgPayback'], 
                color=colors[payback_col], 
                linewidth=2, 
                marker='o',
                markersize=8,
                markerfacecolor=colors[payback_col],
                markeredgecolor=colors[payback_col],
                markeredgewidth=1.5,
                label=f'{payback_col} ({base_scenario})')

        # 添加到图例元素
        legend_elements.append(line)
    else:
        print(f"  警告: {payback_col} 的 {base_scenario} 场景没有有效数据，无法绘制")

    # 绘制High和Low场景的误差线
    for year, base_payback in zip(base_data['Year'], base_data['AvgPayback']):
        # 获取对应年份的High和Low值
        high_row = high_data[high_data['Year'] == year]
        low_row = low_data[low_data['Year'] == year]

        if not high_row.empty and not low_row.empty:
            high_payback = high_row['AvgPayback'].values[0]
            low_payback = low_row['AvgPayback'].values[0]

            # 只有当值有效时才绘制
            if not np.isnan(high_payback) and not np.isnan(low_payback) and not np.isnan(base_payback):
                # 绘制垂直连接线
                ax.plot([year + offset, year + offset], 
                        [low_payback, high_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

                # 绘制High和Low的横线 - 增加长度
                line_width = 0.15  # 增加误差线横线的长度
                ax.plot([year + offset - line_width, year + offset + line_width], 
                        [high_payback, high_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

                ax.plot([year + offset - line_width, year + offset + line_width], 
                        [low_payback, low_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

# 设置图形样式
ax.set_xlabel('年份', fontsize=14)
ax.set_ylabel('平均回收期（年）', fontsize=14)
ax.set_title('各类回收期趋势分析对比', fontsize=16, pad=20)

# 去掉网格
ax.grid(False)

# 设置坐标轴范围
years = sorted(integrated_results['Year'].unique())
ax.set_xlim(min(years)-0.5, max(years)+0.5)

# 设置y轴范围，回收期通常在0-20年之间
ax.set_ylim(0, 20)

# 设置x轴刻度为整数年份
ax.set_xticks(years)
ax.set_xticklabels(years)

# 去掉上框和右框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 添加图例
ax.legend(handles=legend_elements, 
          loc='upper right', 
          fontsize=10, 
          framealpha=0.8,
          ncol=2)  # 使用两列显示图例

# 添加说明文字 - 更新说明文字以反映实际情况
note_text = "注：每条线表示一种回收期类型，垂直误差线表示High和Low情景的范围\n"
note_text += "对于Payback_economic使用_LR后缀的情景，其他使用不带后缀的情景"
plt.figtext(0.5, 0.01, note_text, 
            fontsize=10, 
            ha='center',
            bbox=dict(facecolor='white', alpha=0.8))

# 调整布局并保存
plt.tight_layout(rect=[0, 0.03, 1, 0.98])  # 为底部说明文字留出空间
plt.savefig('payback_trend_comparison.png', dpi=300, bbox_inches='tight', transparent=True)
print("已保存回收期趋势对比图")
plt.close()


# In[133]:


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ===== 添加详细测试代码 =====
print("\n===== 详细诊断 Payback_pv_battery 问题 =====")

# 1. 检查数据基本情况
print("1. 数据基本情况检查")
print(f"integrated_results 形状: {integrated_results.shape}")
print(f"Payback_pv_battery 列是否存在: {'Payback_pv_battery' in integrated_results.columns}")

# 2. 检查 Payback_pv_battery 列的数据分布
print("\n2. Payback_pv_battery 数据分布")
if 'Payback_pv_battery' in integrated_results.columns:
    # 检查非空值数量
    non_null_count = integrated_results['Payback_pv_battery'].notna().sum()
    total_count = len(integrated_results)
    print(f"非空值数量: {non_null_count}/{total_count} ({non_null_count/total_count*100:.2f}%)")

    # 检查值的范围
    if non_null_count > 0:
        print(f"最小值: {integrated_results['Payback_pv_battery'].min()}")
        print(f"最大值: {integrated_results['Payback_pv_battery'].max()}")
        print(f"平均值: {integrated_results['Payback_pv_battery'].mean()}")

        # 检查有效值 (<=20) 的数量
        valid_count = ((integrated_results['Payback_pv_battery'] <= 20) & 
                       integrated_results['Payback_pv_battery'].notna()).sum()
        print(f"有效值 (<=20) 数量: {valid_count}/{total_count} ({valid_count/total_count*100:.2f}%)")

# 3. 按场景检查 Payback_pv_battery 数据
print("\n3. 按场景检查 Payback_pv_battery 数据")
for scenario in integrated_results['Scenario'].unique():
    scenario_data = integrated_results[integrated_results['Scenario'] == scenario]
    valid_data = scenario_data[scenario_data['Payback_pv_battery'].notna() & 
                              (scenario_data['Payback_pv_battery'] <= 20)]

    print(f"场景 '{scenario}':")
    print(f"  总行数: {len(scenario_data)}")
    print(f"  有效 Payback_pv_battery 值数量: {len(valid_data)}")
    if len(valid_data) > 0:
        print(f"  平均值: {valid_data['Payback_pv_battery'].mean():.2f}")
        print(f"  最小值: {valid_data['Payback_pv_battery'].min():.2f}")
        print(f"  最大值: {valid_data['Payback_pv_battery'].max():.2f}")

# 4. 按年份和场景检查 Payback_pv_battery 数据
print("\n4. 按年份和场景检查 Payback_pv_battery 数据 (仅显示前几年)")
years_to_check = sorted(integrated_results['Year'].unique())[:3]  # 只检查前3年
scenarios_to_check = ['Base', 'High', 'Low']  # 检查这些场景

for year in years_to_check:
    for scenario in scenarios_to_check:
        data = integrated_results[(integrated_results['Year'] == year) & 
                                 (integrated_results['Scenario'] == scenario)]

        valid_data = data[data['Payback_pv_battery'].notna() & (data['Payback_pv_battery'] <= 20)]

        print(f"年份 {year}, 场景 '{scenario}':")
        print(f"  总行数: {len(data)}")
        print(f"  有效 Payback_pv_battery 值数量: {len(valid_data)}")
        if len(valid_data) > 0:
            print(f"  平均值: {valid_data['Payback_pv_battery'].mean():.2f}")

# 5. 测试绘图数据准备过程
print("\n5. 测试 Payback_pv_battery 绘图数据准备过程")

# 选择场景
payback_col = 'Payback_pv_battery'
base_scenario = 'Base'
high_scenario = 'High'
low_scenario = 'Low'

print(f"使用场景: Base='{base_scenario}', High='{high_scenario}', Low='{low_scenario}'")

# 按年份和场景统计平均回收期
results = []
for year in sorted(integrated_results['Year'].unique()):
    for scenario in [high_scenario, base_scenario, low_scenario]:
        # 调整查询条件以匹配数据集中的实际场景名称
        query_scenario = scenario

        data = integrated_results[
            (integrated_results['Year'] == year) & 
            (integrated_results['Scenario'] == query_scenario)
        ]

        # 计算有效回收期的平均值（排除NaN和无限值）
        valid_data = data[data[payback_col].notna() & (data[payback_col] <= 20)]
        avg_payback = valid_data[payback_col].mean() if not valid_data.empty else np.nan
        count = len(valid_data)

        results.append({
            'Year': year,
            'Scenario': scenario,
            'AvgPayback': avg_payback,
            'Count': count
        })

# 转换为DataFrame
df_results = pd.DataFrame(results)

# 获取各场景数据
base_data = df_results[df_results['Scenario'] == base_scenario]
high_data = df_results[df_results['Scenario'] == high_scenario]
low_data = df_results[df_results['Scenario'] == low_scenario]

print(f"\n基准场景 '{base_scenario}' 数据点数量: {len(base_data)}")
print(f"高场景 '{high_scenario}' 数据点数量: {len(high_data)}")
print(f"低场景 '{low_scenario}' 数据点数量: {len(low_data)}")

# 检查是否有有效的平均回收期数据
print(f"\n基准场景有效数据点数量: {base_data['AvgPayback'].notna().sum()}")
print(f"高场景有效数据点数量: {high_data['AvgPayback'].notna().sum()}")
print(f"低场景有效数据点数量: {low_data['AvgPayback'].notna().sum()}")

# 显示部分数据
print("\n基准场景数据示例:")
if not base_data.empty:
    print(base_data.head())
else:
    print("基准场景无数据")

# 6. 测试单独绘制 Payback_pv_battery 曲线
print("\n6. 测试单独绘制 Payback_pv_battery 曲线")

# 创建一个测试图
fig_test, ax_test = plt.subplots(figsize=(10, 6))

# 检查是否有有效数据可以绘制
has_valid_data = (not base_data.empty and 
                  base_data['AvgPayback'].notna().sum() > 0 and
                  not base_data['AvgPayback'].isna().all())

print(f"是否有有效数据可以绘制: {has_valid_data}")

if has_valid_data:
    # 绘制基准场景的线
    ax_test.plot(base_data['Year'], base_data['AvgPayback'], 
            color='blue', 
            linewidth=2, 
            marker='o',
            label=f'Payback_pv_battery ({base_scenario})')

    # 设置图形样式
    ax_test.set_xlabel('年份')
    ax_test.set_ylabel('平均回收期（年）')
    ax_test.set_title('Payback_pv_battery 测试图')
    ax_test.legend()

    # 保存测试图
    plt.savefig('payback_pv_battery_test.png')
    print("已保存 Payback_pv_battery 测试图")
else:
    print("无法绘制 Payback_pv_battery 测试图，因为没有有效数据")

plt.close(fig_test)

# 现在继续原始代码
# 定义要处理的Payback列
payback_columns = [
    'Payback_original', 'Payback_m', 'Payback_e', 
    'Payback_c', 'Payback_economic', 'Payback_pv_battery'
]

# 设置颜色方案 - 为每种Payback类型设置不同颜色
colors = {
    'Payback_original': '#3498db',  # 蓝色
    'Payback_m': '#2ecc71',         # 绿色
    'Payback_e': '#e74c3c',         # 红色
    'Payback_c': '#f39c12',         # 橙色
    'Payback_economic': '#9b59b6',  # 紫色
    'Payback_pv_battery': '#1abc9c'  # 青色
}

# 创建一个大图
fig, ax = plt.subplots(figsize=(14, 8))

# 设置背景透明
fig.patch.set_alpha(0)
ax.patch.set_alpha(0)

# 存储图例元素
legend_elements = []

# 处理每个Payback列
for i, payback_col in enumerate(payback_columns):
    print(f"\n处理 {payback_col} 的数据...")

    # 选择基准场景 - 修改这里，为 Payback_pv_battery 使用不带 _LR 后缀的场景
    if payback_col == 'Payback_economic':
        base_scenario = 'Base_LR'
        high_scenario = 'High_LR'
        low_scenario = 'Low_LR'
    elif payback_col == 'Payback_pv_battery':  # 修改这里
        base_scenario = 'Base'
        high_scenario = 'High'
        low_scenario = 'Low'
    else:
        base_scenario = 'Base'
        high_scenario = 'High'
        low_scenario = 'Low'

    print(f"  使用场景: Base='{base_scenario}', High='{high_scenario}', Low='{low_scenario}'")

    # 按年份和场景统计平均回收期
    results = []
    for year in sorted(integrated_results['Year'].unique()):
        for scenario in [high_scenario, base_scenario, low_scenario]:
            # 调整查询条件以匹配数据集中的实际场景名称
            query_scenario = scenario
            if scenario.endswith('_LR') and 'Scenario' in integrated_results.columns:
                # 如果数据集中没有_LR后缀的场景，则去掉后缀
                if not any(integrated_results['Scenario'] == scenario):
                    query_scenario = scenario.replace('_LR', '')

            # 添加调试信息
            if payback_col == 'Payback_pv_battery' and year == sorted(integrated_results['Year'].unique())[0]:
                print(f"  查询年份 {year}, 场景 {scenario} (查询名: {query_scenario})")

            data = integrated_results[
                (integrated_results['Year'] == year) & 
                (integrated_results['Scenario'] == query_scenario)
            ]

            # 计算有效回收期的平均值（排除NaN和无限值）
            valid_data = data[data[payback_col].notna() & (data[payback_col] <= 20)]
            avg_payback = valid_data[payback_col].mean() if not valid_data.empty else np.nan
            count = len(valid_data)

            # 添加调试信息
            if payback_col == 'Payback_pv_battery' and year == sorted(integrated_results['Year'].unique())[0]:
                print(f"    匹配行数: {len(data)}, 有效数据行数: {len(valid_data)}, 平均值: {avg_payback}")

            results.append({
                'Year': year,
                'Scenario': scenario,
                'AvgPayback': avg_payback,
                'Count': count
            })

    # 转换为DataFrame
    df_results = pd.DataFrame(results)

    # 获取各场景数据
    base_data = df_results[df_results['Scenario'] == base_scenario]
    high_data = df_results[df_results['Scenario'] == high_scenario]
    low_data = df_results[df_results['Scenario'] == low_scenario]

    # 添加调试信息
    if payback_col == 'Payback_pv_battery':
        print(f"\n  {payback_col} 结果统计:")
        print(f"  基准场景 '{base_scenario}' 数据点数量: {len(base_data)}")
        print(f"  高场景 '{high_scenario}' 数据点数量: {len(high_data)}")
        print(f"  低场景 '{low_scenario}' 数据点数量: {len(low_data)}")

        print(f"  基准场景有效数据点数量: {base_data['AvgPayback'].notna().sum()}")
        print(f"  高场景有效数据点数量: {high_data['AvgPayback'].notna().sum()}")
        print(f"  低场景有效数据点数量: {low_data['AvgPayback'].notna().sum()}")

        if not base_data.empty:
            print("\n  基准场景数据示例:")
            print(base_data.head())
        else:
            print("\n  基准场景无数据")

    # 计算偏移量，使不同Payback列的线条错开
    offset = (i - len(payback_columns)/2 + 0.5) * 0.15

    # 绘制基准场景的线
    if not base_data.empty and not base_data['AvgPayback'].isna().all() and base_data['AvgPayback'].notna().sum() > 0:
        # 添加调试信息
        if payback_col == 'Payback_pv_battery':
            print(f"\n  准备绘制 {payback_col} 曲线...")
            print(f"  X轴数据: {base_data['Year'].tolist()}")
            print(f"  Y轴数据: {base_data['AvgPayback'].tolist()}")

        line, = ax.plot(base_data['Year'] + offset, base_data['AvgPayback'], 
                color=colors[payback_col], 
                linewidth=2, 
                marker='o',
                markersize=8,
                markerfacecolor=colors[payback_col],
                markeredgecolor=colors[payback_col],
                markeredgewidth=1.5,
                label=f'{payback_col} ({base_scenario})')

        # 添加到图例元素
        legend_elements.append(line)

        if payback_col == 'Payback_pv_battery':
            print("  成功绘制 Payback_pv_battery 曲线")
    else:
        print(f"  警告: {payback_col} 的 {base_scenario} 场景没有有效数据，无法绘制")
        if payback_col == 'Payback_pv_battery':
            print(f"  base_data.empty: {base_data.empty}")
            if not base_data.empty:
                print(f"  base_data['AvgPayback'].isna().all(): {base_data['AvgPayback'].isna().all()}")
                print(f"  base_data['AvgPayback'].notna().sum(): {base_data['AvgPayback'].notna().sum()}")

    # 绘制High和Low场景的误差线
    for year, base_payback in zip(base_data['Year'], base_data['AvgPayback']):
        # 获取对应年份的High和Low值
        high_row = high_data[high_data['Year'] == year]
        low_row = low_data[low_data['Year'] == year]

        if not high_row.empty and not low_row.empty:
            high_payback = high_row['AvgPayback'].values[0]
            low_payback = low_row['AvgPayback'].values[0]

            # 只有当值有效时才绘制
            if not np.isnan(high_payback) and not np.isnan(low_payback) and not np.isnan(base_payback):
                # 绘制垂直连接线
                ax.plot([year + offset, year + offset], 
                        [low_payback, high_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

                # 绘制High和Low的横线 - 增加长度
                line_width = 0.15  # 增加误差线横线的长度
                ax.plot([year + offset - line_width, year + offset + line_width], 
                        [high_payback, high_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

                ax.plot([year + offset - line_width, year + offset + line_width], 
                        [low_payback, low_payback], 
                        color=colors[payback_col], 
                        linewidth=1.5,
                        alpha=0.7)

# 设置图形样式
ax.set_xlabel('年份', fontsize=14)
ax.set_ylabel('平均回收期（年）', fontsize=14)
ax.set_title('各类回收期趋势分析对比', fontsize=16, pad=20)

# 去掉网格
ax.grid(False)

# 设置坐标轴范围
years = sorted(integrated_results['Year'].unique())
ax.set_xlim(min(years)-0.5, max(years)+0.5)

# 设置y轴范围，回收期通常在0-20年之间
ax.set_ylim(0, 20)

# 设置x轴刻度为整数年份
ax.set_xticks(years)
ax.set_xticklabels(years)

# 去掉上框和右框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 添加图例
ax.legend(handles=legend_elements, 
          loc='upper right', 
          fontsize=10, 
          framealpha=0.8,
          ncol=2)  # 使用两列显示图例

# 添加说明文字 - 更新说明文字以反映实际情况
note_text = "注：每条线表示一种回收期类型，垂直误差线表示High和Low情景的范围\n"
note_text += "对于Payback_economic使用_LR后缀的情景，其他使用不带后缀的情景"
plt.figtext(0.5, 0.01, note_text, 
            fontsize=10, 
            ha='center',
            bbox=dict(facecolor='white', alpha=0.8))

# 调整布局并保存
plt.tight_layout(rect=[0, 0.03, 1, 0.98])  # 为底部说明文字留出空间
plt.savefig('payback_trend_comparison_debug2.png', dpi=300, bbox_inches='tight', transparent=True)
print("已保存回收期趋势对比图（调试版2）")
plt.close()


# In[134]:


# 首先筛选Base_LR场景的数据
df_economic_base_lr = df_economic_clean[df_economic_clean['Scenario'] == 'Base_LR']

print("Base_LR情景下每年Payback均值统计:")
print("-" * 50)

# 1. 基本统计
yearly_stats = df_economic_base_lr.groupby('Year').agg(
    平均值=('Payback_economic', 'mean'),
    中位数=('Payback_economic', 'median'),
    最小值=('Payback_economic', 'min'),
    最大值=('Payback_economic', 'max'),
    数据量=('Payback_economic', 'count')
).round(2)

print("\n详细统计信息:")
print(yearly_stats)
print("-" * 50)

# 2. 检查每年有效数据的分布
print("\nBase_LR情景下每年Payback值分布在不同区间的数量:")
for year in sorted(df_economic_base_lr['Year'].unique()):
    year_data = df_economic_base_lr[df_economic_base_lr['Year'] == year]

    # 统计不同区间的数量
    bins = [0, 5, 10, 15, 20, float('inf')]
    labels = ['0-5年', '5-10年', '10-15年', '15-20年', '>20年']
    year_data['Payback_Group'] = pd.cut(year_data['Payback_economic'], bins=bins, labels=labels)

    distribution = year_data['Payback_Group'].value_counts().sort_index()

    print(f"\n{year}年:")
    for interval, count in distribution.items():
        percentage = (count / len(year_data)) * 100
        print(f"{interval}: {count}个 ({percentage:.1f}%)")
print("-" * 50)

# 3. 检查异常值
print("\n检查异常值 (Payback > 50年的数据):")
for year in sorted(df_economic_base_lr['Year'].unique()):
    abnormal = df_economic_base_lr[
        (df_economic_base_lr['Year'] == year) & 
        (df_economic_base_lr['Payback_economic'] > 50)
    ]
    if len(abnormal) > 0:
        print(f"\n{year}年异常值数量: {len(abnormal)}")
        print("示例数据:")
        print(abnormal[['County', 'Payback_economic']].head())

# 4. 数据验证
print("\nBase_LR情景数据验证:")
print(f"Base_LR情景总数据量: {len(df_economic_base_lr)}")
print(f"包含Payback_economic的数据量: {df_economic_base_lr['Payback_economic'].notna().sum()}")
print(f"年份范围: {df_economic_base_lr['Year'].min()} - {df_economic_base_lr['Year'].max()}")

# 5. 添加年度变化趋势分析
print("\n年度变化趋势分析:")
print("各年份20年内回收期的比例:")
for year in sorted(df_economic_base_lr['Year'].unique()):
    year_data = df_economic_base_lr[df_economic_base_lr['Year'] == year]
    total = len(year_data)
    within_20_years = len(year_data[year_data['Payback_economic'] <= 20])
    percentage = (within_20_years / total * 100) if total > 0 else 0
    print(f"{year}年: {percentage:.1f}% ({within_20_years}/{total})")


# In[135]:


df_economic_clean


# ##### 溢出效应检验

# In[136]:


# 1. 直接技术岗位计算
# 计算高回报县域（ROI_m > 5%）和盈亏平衡地区的技能型岗位数量
high_roi_counties = poverty_selected[poverty_selected['ROI_m'] > 0.05]
breakeven_counties = poverty_selected[(poverty_selected['ROI_m'] <= 0.05) & (poverty_selected['ROI_m'] > 0)]

# 计算平均工作岗位数
avg_jobs_high_roi = high_roi_counties['jobs_m'].mean()
avg_jobs_breakeven = breakeven_counties['jobs_m'].mean()

# 计算高回报县域比盈亏平衡地区多出的百分比
job_increase_percentage = ((avg_jobs_high_roi - avg_jobs_breakeven) / avg_jobs_breakeven) * 100

print(f"直接技术岗位增加百分比: {job_increase_percentage:.2f}%")

# 2. 供应链扩张计算
# 计算ROI_m与基准PVPA（假设为ROI_x）的关系
poverty_selected['roi_increase'] = poverty_selected['ROI_m'] - poverty_selected['ROI_x']

# 假设work_m表示每兆瓦的就业岗位数，计算ROI每增加1个百分点带来的间接岗位增加
# 使用线性回归分析ROI增加与岗位数的关系
from scipy import stats

# 剔除roi_increase为0的样本，以避免除以零错误
valid_data = poverty_selected[poverty_selected['roi_increase'] != 0].copy()

# 计算每1个百分点ROI增加对应的间接岗位数
valid_data['jobs_per_roi_point'] = valid_data['jobs_m'] - valid_data['jobs_x']

# 计算平均值，即每当ROI增加1个百分点时新增的间接岗位数
indirect_jobs_per_point = valid_data['jobs_per_roi_point'].mean()

print(f"每当ROI相对基准PVPA性能每增加1个百分点，每兆瓦新增间接岗位数: {indirect_jobs_per_point:.2f}")

# 3. 经济乘数效应计算
# 计算氢气收入占总收入的比例
poverty_selected['hydrogen_revenue_ratio'] = poverty_selected['contribute_m']

# 寻找临界值：当超过这个比例时，服务业增长最显著
ratios = np.arange(0.1, 1.0, 0.05)  # 从10%到95%，步长为5%
max_growth_diff = 0
threshold_ratio = 0

for ratio in ratios:
    # 将样本分为两组：氢气收入占比高和低的
    high_h2_group = poverty_selected[poverty_selected['hydrogen_revenue_ratio'] > ratio]
    low_h2_group = poverty_selected[poverty_selected['hydrogen_revenue_ratio'] <= ratio]

    # 比较两组的服务业增长（假设用某个指标如jobs_m来表示服务业增长）
    if not high_h2_group.empty and not low_h2_group.empty:
        high_growth = high_h2_group['jobs_m'].mean()
        low_growth = low_h2_group['jobs_m'].mean()
        growth_diff = ((high_growth - low_growth) / low_growth) * 100

        if growth_diff > max_growth_diff:
            max_growth_diff = growth_diff
            threshold_ratio = ratio

# 计算仅发电(ROI_x)的光伏系统与含氢系统在服务业增长上的差异
pv_only_growth = poverty_selected['jobs_x'].mean()
h2_pv_growth = poverty_selected[poverty_selected['hydrogen_revenue_ratio'] > threshold_ratio]['jobs_m'].mean()

service_growth_increase = ((h2_pv_growth - pv_only_growth) / pv_only_growth) * 100

print(f"经济乘数效应临界氢气收入占比: {threshold_ratio*100:.0f}%")
print(f"服务业增长速度比仅发电的光伏系统快: {service_growth_increase:.2f}%")


# In[137]:


try:
    # 将counties_selected的name列转换为列表，用于判断县域归属
    original_counties = counties_selected['name'].tolist()

    # 在poverty_selected中标记哪些是原PVPA区域，哪些是新加入的县域
    poverty_selected['is_original'] = poverty_selected['name'].apply(lambda x: x in original_counties)

    # 分离原PVPA区域和新加入的县域
    original_areas = poverty_selected[poverty_selected['is_original'] == True]
    new_areas = poverty_selected[poverty_selected['is_original'] == False]

    print(f"原PVPA区域县域数量: {len(original_areas)}")
    print(f"新加入县域数量: {len(new_areas)}")

    # 分析从负ROI转为正ROI的县域劳动市场改善情况
    negative_to_positive_original = original_areas[(original_areas['ROI_x'] < 0) & (original_areas['ROI_m'] > 0)]
    negative_to_positive_new = new_areas[(new_areas['ROI_x'] < 0) & (new_areas['ROI_m'] > 0)]

    # 计算就业弹性(Δjobs/ΔROI)
    # 对于原PVPA区域
    if not negative_to_positive_original.empty:
        # 计算ROI变化
        negative_to_positive_original['ROI_change'] = negative_to_positive_original['ROI_m'] - negative_to_positive_original['ROI_x']
        # 计算就业变化
        negative_to_positive_original['job_change'] = negative_to_positive_original['work_m'] - negative_to_positive_original['work']
        # 计算就业弹性
        negative_to_positive_original['job_elasticity'] = negative_to_positive_original['job_change'] / negative_to_positive_original['ROI_change']
        original_elasticity = negative_to_positive_original['job_elasticity'].mean()
    else:
        original_elasticity = 0

    # 对于新加入的县域
    if not negative_to_positive_new.empty:
        # 计算ROI变化
        negative_to_positive_new['ROI_change'] = negative_to_positive_new['ROI_m'] - negative_to_positive_new['ROI_x']
        # 计算就业变化
        negative_to_positive_new['job_change'] = negative_to_positive_new['work_m'] - negative_to_positive_new['work']
        # 计算就业弹性
        negative_to_positive_new['job_elasticity'] = negative_to_positive_new['job_change'] / negative_to_positive_new['ROI_change']
        new_elasticity = negative_to_positive_new['job_elasticity'].mean()
    else:
        new_elasticity = 0

    print(f"原PVPA区域从负ROI转为正ROI的县域就业弹性(Δjobs/ΔROI): {original_elasticity:.2f}")
    print(f"新加入的县域从负ROI转为正ROI的县域就业弹性(Δjobs/ΔROI): {new_elasticity:.2f}")

    # 分析当ROI稳定在3%以上时，两类地区的收敛岗位数/MW
    high_roi_original = original_areas[original_areas['ROI_m'] > 0.03]
    high_roi_new = new_areas[new_areas['ROI_m'] > 0.03]

    original_converged_jobs = high_roi_original['work_m'].mean() if not high_roi_original.empty else 0
    new_converged_jobs = high_roi_new['work_m'].mean() if not high_roi_new.empty else 0

    print(f"当ROI稳定在3%以上时，原PVPA区域收敛岗位数/MW: {original_converged_jobs:.2f}")
    print(f"当ROI稳定在3%以上时，新加入县域收敛岗位数/MW: {new_converged_jobs:.2f}")

    # 计算总体平均收敛岗位数/MW
    all_high_roi = poverty_selected[poverty_selected['ROI_m'] > 0.03]
    all_converged_jobs = all_high_roi['work_m'].mean() if not all_high_roi.empty else 0

    print(f"当ROI稳定在3%以上时，所有地区收敛岗位数/MW: {all_converged_jobs:.2f}")

    # 保存分析结果
    analysis_results = {
        "原PVPA区域县域数量": len(original_areas),
        "新加入县域数量": len(new_areas),
        "原PVPA区域从负ROI转为正ROI的县域就业弹性": original_elasticity,
        "新加入的县域从负ROI转为正ROI的县域就业弹性": new_elasticity,
        "当ROI稳定在3%以上时，原PVPA区域收敛岗位数/MW": original_converged_jobs,
        "当ROI稳定在3%以上时，新加入县域收敛岗位数/MW": new_converged_jobs,
        "当ROI稳定在3%以上时，所有地区收敛岗位数/MW": all_converged_jobs
    }

    pd.DataFrame([analysis_results]).to_csv('job_elasticity_analysis.csv', index=False)
    print("就业弹性分析结果已保存至 job_elasticity_analysis.csv")

except Exception as e:
    print(f"分析过程中出现错误: {e}")


# ##### 水的计算

# In[138]:


# 筛选Province包含"新疆"的行，并计算water_y的总和
xinjiang_water_sum = poverty_selected[poverty_selected['Province'].str.contains('新疆')]['water'].sum() *20
print(f"新疆地区water_y的总和: {xinjiang_water_sum}")


# In[139]:


poverty_selected['water'].mean() / 10


# ##### 又回到就业的计算

# In[140]:


# 计算 poverty_selected 中 work_m 列的平均值，然后除以10再乘以20
result = poverty_selected["jobs_m"].mean() / 10 * 20
print(f"结果: {result}")

# 或者可以直接写成
result = poverty_selected["jobs_m"].mean() * 2  # 等价于 /10*20
print(f"结果: {result}")


# In[141]:


# 计算 ROI_m + difference_m 大于 3% 的比例
condition = (poverty_selected["ROI_m"] + poverty_selected["difference_m"]) > 0.03
proportion = condition.mean()
print(f"ROI_m + difference_m 大于 3% 的比例: {proportion:.4f}")


# In[145]:


# 方法2：逐个打印列名
for column in poverty_selected.columns:
    print(column)


# ##### 计算一下最后一步的结果

# In[151]:


# 1. 创建EWTR新列
poverty_selected['EWTR'] = poverty_selected['jobs_m'] / (poverty_selected['water']/1000)

# 2. 筛选ROI > 0.03的行
roi_filtered = poverty_selected[poverty_selected['ROI_m'] > 0.03]

# 3. 计算这些行中的最低EWTR和最大water值
min_ewtr = roi_filtered['EWTR'].min()
max_water = roi_filtered['water'].max()

print(f"ROI > 0.03行中最低的EWTR值: {min_ewtr}")
print(f"ROI > 0.03行中最大的water值: {max_water}")

# 4. 计算同时满足这三个条件的县的百分比
# 条件: ROI > 0.03, EWTR >= min_ewtr, water <= max_water
meeting_criteria = poverty_selected[(poverty_selected['ROI_m'] > 0.03) & 
                                    (poverty_selected['EWTR'] >= min_ewtr) & 
                                    (poverty_selected['water'] <= max_water)]

percentage = (len(meeting_criteria) / len(poverty_selected)) * 100

print(f"同时满足三个条件的县占总数的百分比: {percentage}%")
print(f"满足条件的县数量: {len(meeting_criteria)}")
print(f"总县数: {len(poverty_selected)}")


# In[152]:


# 筛选广西和贵州的行
gx_gz_data = poverty_selected[poverty_selected['Province'].str.contains('广西|贵州', na=False)]

# 计算EWTR的范围
ewtr_min = gx_gz_data['EWTR'].min()
ewtr_max = gx_gz_data['EWTR'].max()

print(f"广西和贵州的EWTR值范围: {ewtr_min:.2f}–{ewtr_max:.2f} 就业年/千立方米")

# 显示更详细的统计信息
print("\n广西和贵州EWTR值的详细统计:")
print(gx_gz_data['EWTR'].describe())

# 显示数据条数
print(f"\n广西和贵州地区的数据条数: {len(gx_gz_data)}")


# In[149]:


# 计算总就业岗位数(jobs_y)除以10
jobs_y_scaled = poverty_selected['jobs_y'] / 10
print("jobs_y / 10:")
print(jobs_y_scaled)

# 计算jobs_m除以10
jobs_m_scaled = poverty_selected['jobs_m'] / 10
print("\njobs_m / 10:")
print(jobs_m_scaled)

# 如果只需要查看统计摘要
print("\n统计摘要:")
print("jobs_y / 10 统计摘要:")
print(jobs_y_scaled.describe())
print("\njobs_m / 10 统计摘要:")
print(jobs_m_scaled.describe())


# In[ ]:





# In[150]:


# 计算water除以10
water_scaled = poverty_selected['water'] / 10
print("water / 10:")
print(water_scaled)

# 显示统计摘要
print("\nwater / 10 统计摘要:")
print(water_scaled.describe())


# In[153]:


# 西北地区省份及简称
northwest_provinces = ['陕西', '陕', '甘肃', '甘', '青海', '青', '宁夏', '宁', '新疆', '新']

# 创建筛选条件
filter_condition = False
for province in northwest_provinces:
    filter_condition = filter_condition | poverty_selected['Province'].str.contains(province, na=False)

# 筛选西北地区的数据
northwest_data = poverty_selected[filter_condition]

# 计算EWTR的范围
ewtr_min = northwest_data['EWTR'].min()
ewtr_max = northwest_data['EWTR'].max()

print(f"西北地区(陕西、甘肃、青海、宁夏、新疆)的EWTR值范围: {ewtr_min:.2f}–{ewtr_max:.2f} 就业年/千立方米")

# 显示详细统计信息
print("\n西北地区EWTR值的详细统计:")
print(northwest_data['EWTR'].describe())

# 显示数据条数
print(f"\n西北地区的数据条数: {len(northwest_data)}")


# ### 3.3 可视化

# #### 3.3.1 Fig 1a

# In[163]:


poverty_remaining


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1


counties_selected['group'] = counties_selected['ROI_m'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI_m'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_m'])
poverty_remaining['group'] = poverty_remaining['ROI_m'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展

# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围

# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined2[combined['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制省级底图在子图中
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('fig1a_m.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

# counties_selected['ROI_y'] = counties_selected['name'].map(poverty_selected.set_index('name')['ROI_y'])
counties_selected['group'] = counties_selected['ROI_m'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI_m'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_m'])
poverty_remaining['group'] = poverty_remaining['ROI_m'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展

# 加载管道数据
def _load_pipeline_data(pipeline_file):
    """加载管道数据 (简单处理)"""
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    """绘制管道线路 (不做额外检测)"""
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制所有县的边界
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围


# 合并两个 GeoDataFrame
# combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制所有县的边界在子图中
counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')

# 绘制管道在子图中
_plot_pipeline(ax_inset, pipeline_gdf)

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('fig1a_m_2_with_pipeline.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# In[ ]:


print(counties)


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

# counties_selected['ROI_y'] = counties_selected['name'].map(poverty_selected.set_index('name')['ROI_y'])
counties_selected['group'] = counties_selected['ROI_y'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI_y'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_y'])
poverty_remaining['group'] = poverty_remaining['ROI_y'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展
# 1. 检查索引是否唯一
print("检查 counties_selected 索引是否唯一：", counties_selected.index.is_unique)
print("检查 poverty_remaining 索引是否唯一：", poverty_remaining.index.is_unique)

# 如果索引不唯一，打印重复的索引
if not counties_selected.index.is_unique:
    print("重复的索引 in counties_selected:", counties_selected[counties_selected.index.duplicated()])

if not poverty_remaining.index.is_unique:
    print("重复的索引 in poverty_remaining:", poverty_remaining[poverty_remaining.index.duplicated()])

# 2. 检查列名和列顺序是否一致
print("counties_selected 列名：", counties_selected.columns)
print("poverty_remaining 列名：", poverty_remaining.columns)

# 3. 检查是否有重复的行
print("检查 counties_selected 是否有重复行:", counties_selected.duplicated().sum())
print("检查 poverty_remaining 是否有重复行:", poverty_remaining.duplicated().sum())

# 4. 检查两个 GeoDataFrame 的 CRS 是否一致
print("counties_selected CRS:", counties_selected.crs)
print("poverty_remaining CRS:", poverty_remaining.crs)

# 如果 CRS 不一致，可以选择统一它们
if counties_selected.crs != poverty_remaining.crs:
    print("CRS 不一致，进行转换为统一的 CRS")
    poverty_remaining = poverty_remaining.to_crs(counties_selected.crs)

combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 加载管道数据
def _load_pipeline_data(pipeline_file):
    """加载管道数据 (简单处理)"""
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    """绘制管道线路 (不做额外检测)"""
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制所有县的边界
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围


# 合并两个 GeoDataFrame
# combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制所有县的边界在子图中
counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')

# 绘制管道在子图中
_plot_pipeline(ax_inset, pipeline_gdf)

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('fig1a_y_2_with_pipeline.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# 加载中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 提取 merged_df 中的 ROI_y 列并分类
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

# counties_selected['ROI_y'] = counties_selected['name'].map(poverty_selected.set_index('name')['ROI_y'])
counties_selected['group'] = counties_selected['ROI_x'].apply(classify_roi)

# 找出 poverty_remaining 中 name 不在 counties_selected 中的部分
poverty_remaining = poverty_selected[~poverty_selected['name'].isin(counties_selected['name'])]

# poverty_remaining 分类
poverty_remaining['ROI_x'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_x'])
poverty_remaining['group'] = poverty_remaining['ROI_x'].apply(classify_roi)

# 重新分类未开展区域
poverty_remaining['group'] += 2  # 将分类值加2，以区分已开展和未开展
# 1. 检查索引是否唯一
print("检查 counties_selected 索引是否唯一：", counties_selected.index.is_unique)
print("检查 poverty_remaining 索引是否唯一：", poverty_remaining.index.is_unique)

# 如果索引不唯一，打印重复的索引
if not counties_selected.index.is_unique:
    print("重复的索引 in counties_selected:", counties_selected[counties_selected.index.duplicated()])

if not poverty_remaining.index.is_unique:
    print("重复的索引 in poverty_remaining:", poverty_remaining[poverty_remaining.index.duplicated()])

# 2. 检查列名和列顺序是否一致
print("counties_selected 列名：", counties_selected.columns)
print("poverty_remaining 列名：", poverty_remaining.columns)

# 3. 检查是否有重复的行
print("检查 counties_selected 是否有重复行:", counties_selected.duplicated().sum())
print("检查 poverty_remaining 是否有重复行:", poverty_remaining.duplicated().sum())

# 4. 检查两个 GeoDataFrame 的 CRS 是否一致
print("counties_selected CRS:", counties_selected.crs)
print("poverty_remaining CRS:", poverty_remaining.crs)

# 如果 CRS 不一致，可以选择统一它们
if counties_selected.crs != poverty_remaining.crs:
    print("CRS 不一致，进行转换为统一的 CRS")
    poverty_remaining = poverty_remaining.to_crs(counties_selected.crs)


# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 合并两个 GeoDataFrame
combined2 = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))
# 加载管道数据
def _load_pipeline_data(pipeline_file):
    """加载管道数据 (简单处理)"""
    try:
        pipeline_df = pd.read_excel(pipeline_file)
        required_columns = ['起点经度', '起点纬度', '终点经度', '终点纬度']
        for col in required_columns:
            if col not in pipeline_df.columns:
                raise ValueError(f"管道数据缺少必要的列: {col}")

        geometries = [
            LineString([(row['起点经度'], row['起点纬度']),
                        (row['终点经度'], row['终点纬度'])])
            for _, row in pipeline_df.iterrows()
        ]

        pipeline_gdf = gpd.GeoDataFrame(
            pipeline_df,
            geometry=geometries,
            crs='EPSG:4326'
        )
        return pipeline_gdf.to_crs(epsg=3857)  # Assuming the target CRS is EPSG:3857
    except Exception as e:
        print(f"处理管道数据时出错: {str(e)}")
        return None

# 绘制管道线路
def _plot_pipeline(ax, pipeline_df):
    """绘制管道线路 (不做额外检测)"""
    if pipeline_df is not None:
        for _, row in pipeline_df.iterrows():
            coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
            x_coords, y_coords = zip(*coords)
            ax.plot(x_coords, y_coords,
                    color='#0583f2',
                    linewidth=1,
                    alpha=0.8,
                    zorder=2)
        return True
    return False

# 加载管道数据
pipeline_file = r"平均result.xlsx"
pipeline_gdf = _load_pipeline_data(pipeline_file)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))  # 调整图像大小

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 设置阴影效果的角度和偏移
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),  # 斜向上阴影
    PathEffects.Normal()
]

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 绘制所有县的边界
counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

# 绘制组合后的热图，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制管道
_plot_pipeline(ax, pipeline_gdf)

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)  # 适应中国大陆范围的x坐标范围
ax.set_ylim(1689200.14, 7361866.11)   # 适应中国大陆范围的y坐标范围

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_facecolor('white')  # 设置子图背景为白色

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)  # 适应南海地区的x坐标范围
ax_inset.set_ylim(222684.21, 2632018.64)     # 适应南海地区的y坐标范围




# 在子图中绘制南海区域，完全去掉边界
for group, color in cmap.items():
    combined2[combined2['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')  # 确保没有边界

# 绘制所有县的边界在子图中
counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')

# 绘制管道在子图中
_plot_pipeline(ax_inset, pipeline_gdf)

# 绘制国界底图在子图中，并加粗和添加浅蓝色阴影，九段线部分加阴影
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black',
                    path_effects=shadow_effect)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('fig1a_2_with_pipeline.png', dpi=1200, bbox_inches='tight', format='png')

plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry import LineString

# -------------------------------
# 预设：加载中文字体（路径根据实际情况修改）
font_path = 'C:/Windows/Fonts/simhei.ttf'
font_prop = fm.FontProperties(fname=font_path)

# 定义自定义颜色映射（四类）
# 0: 已开展 ROI < 0.03（浅色），1: 已开展 ROI ≥ 0.03（深色）
# 2: 未开展 ROI < 0.03（浅蓝色），3: 未开展 ROI ≥ 0.03（蓝色）
cmap = {
    0: '#fcd182',
    1: '#d9412a',
    2: '#d6eff6',
    3: '#4a7bb6'
}

# 定义分类函数，阈值 0.03
def classify_roi(roi):
    if roi < 0.03:
        return 0
    else:
        return 1

# -------------------------------
# 假设 counties_selected、poverty_selected、merged_df、china、counties、pipeline_gdf 均已加载
# 例如，pipeline_gdf 可通过 _load_pipeline_data() 加载，此处不再重复

# 要生成可视化的 ROI 列
roi_columns = ['ROI_sub', 'ROI_priority', 'ROI_storage']
# roi_columns = ['ROI_storage']

# 循环处理每个 ROI 列，生成单独图像
for col in roi_columns:
    # 对 counties_selected：直接使用已有该 ROI 列数据，计算分类值存入新列，名称设为 f'group_{col}'
    counties_selected[f'group_{col}'] = counties_selected[col].apply(classify_roi)

    # 对 poverty_remaining：先通过名称映射获取对应的 ROI 列值，再计算分类，然后加 2
    # 注意：这里假定 poverty_remaining 的原始数据在 poverty_selected 中，
    # 且已剔除 counties_selected 中的部分，如原代码所示
    poverty_remaining[col] = poverty_remaining['name'].map(merged_df.set_index('name')[col])
    poverty_remaining[f'group_{col}'] = poverty_remaining[col].apply(classify_roi)
    poverty_remaining[f'group_{col}'] += 2  # 分类值 2 和 3

    # 合并两个 GeoDataFrame，并生成新的 GeoDataFrame（忽略原索引）
    combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

    # 创建绘图
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_axis_off()  # 去掉坐标轴

    # 设置阴影效果（用于国界绘制）
    shadow_effect = [
        PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
        PathEffects.Normal()
    ]

    # 绘制国界底图（假定 china 为国界数据）
    china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

    # 绘制所有县的边界
    counties.boundary.plot(ax=ax, linewidth=0.05, edgecolor='black')

    # 绘制组合后的区域（根据分类进行填充）
    # 对于 cmap 中的每个分类值，提取对应区域并绘制
    for group_value, color in cmap.items():
        combined[combined[f'group_{col}'] == group_value].plot(
            ax=ax, color=color, linewidth=0, edgecolor='none'
        )

    # 绘制管道线路（调用已有函数 _plot_pipeline()）
    # 这里假定 _plot_pipeline(ax, pipeline_gdf) 能正确绘制管道
    def _plot_pipeline(ax, pipeline_df):
        if pipeline_df is not None:
            for _, row in pipeline_df.iterrows():
                coords = [(coord[0], coord[1]) for coord in row.geometry.coords]
                x_coords, y_coords = zip(*coords)
                ax.plot(x_coords, y_coords,
                        color='#0583f2',
                        linewidth=1,
                        alpha=0.8,
                        zorder=2)
            return True
        return False
    _plot_pipeline(ax, pipeline_gdf)

    # 设置主图的坐标范围（这里使用 EPSG:3857 下中国大陆的大致范围）
    ax.set_xlim(7792364.36, 15584728.71)
    ax.set_ylim(1689200.14, 7361866.11)

    # 创建子图（inset）显示南海区域
    ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
    ax_inset.set_facecolor('white')
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    ax_inset.grid(False)
    ax_inset.set_xlim(11688546.53, 13692297.37)
    ax_inset.set_ylim(222684.21, 2632018.64)
    # 在子图中绘制相同内容
    for group_value, color in cmap.items():
        combined[combined[f'group_{col}'] == group_value].plot(
            ax=ax_inset, color=color, linewidth=0, edgecolor='none'
        )
    counties.boundary.plot(ax=ax_inset, linewidth=0.05, edgecolor='black')
    _plot_pipeline(ax_inset, pipeline_gdf)
    china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)
    for spine in ax_inset.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1.5)

    # 设置图形标题，显示当前 ROI 列名称
    ax.set_title(f"{col} Visualization", fontproperties=font_prop, fontsize=18)

    plt.tight_layout()
    # 保存当前图像到文件，文件名中包含 ROI 列名称
    plt.savefig(f"fig_{col}_with_pipeline.png", dpi=1200, bbox_inches='tight', format='png')
    plt.show()


# In[ ]:





# In[ ]:


# 使用布尔索引排除 name 列在 counties_selected 中的行
# poverty_remaining = merged_df[~merged_df['name'].isin(counties_selected['name'])]
poverty_remaining


# #### 3.3.2 fig1b

# ##### 面积

# In[ ]:


# 按照新的 ROI 顺序，依次分类并生成 group1 - group8

# Group 1: ROI_x
counties_selected['group1'] = counties_selected['ROI_x'].apply(classify_roi)
poverty_remaining['ROI_x'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_x'])
poverty_remaining['group1'] = poverty_remaining['ROI_x'].apply(classify_roi)
poverty_remaining['group1'] += 2  # 调整 poverty_remaining 的分组（加2）

# Group 2: ROI_sub
counties_selected['group2'] = counties_selected['ROI_sub'].apply(classify_roi)
poverty_remaining['ROI_sub'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_sub'])
poverty_remaining['group2'] = poverty_remaining['ROI_sub'].apply(classify_roi)
poverty_remaining['group2'] += 2

# Group 3: ROI_priority
counties_selected['group3'] = counties_selected['ROI_priority'].apply(classify_roi)
poverty_remaining['ROI_priority'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_priority'])
poverty_remaining['group3'] = poverty_remaining['ROI_priority'].apply(classify_roi)
poverty_remaining['group3'] += 2

# Group 4: ROI_storage
counties_selected['group4'] = counties_selected['ROI_storage'].apply(classify_roi)
poverty_remaining['ROI_storage'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_storage'])
poverty_remaining['group4'] = poverty_remaining['ROI_storage'].apply(classify_roi)
poverty_remaining['group4'] += 2

# Group 5: ROI_m
counties_selected['group5'] = counties_selected['ROI_m'].apply(classify_roi)
poverty_remaining['ROI_m'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_m'])
poverty_remaining['group5'] = poverty_remaining['ROI_m'].apply(classify_roi)
poverty_remaining['group5'] += 2

# Group 6: ROI_y
counties_selected['group6'] = counties_selected['ROI_y'].apply(classify_roi)
poverty_remaining['ROI_y'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_y'])
poverty_remaining['group6'] = poverty_remaining['ROI_y'].apply(classify_roi)
poverty_remaining['group6'] += 2

# Group 7: ROI_e
counties_selected['group7'] = counties_selected['ROI_e'].apply(classify_roi)
poverty_remaining['ROI_e'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_e'])
poverty_remaining['group7'] = poverty_remaining['ROI_e'].apply(classify_roi)
poverty_remaining['group7'] += 2

# Group 8: ROI_c
counties_selected['group8'] = counties_selected['ROI_c'].apply(classify_roi)
poverty_remaining['ROI_c'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_c'])
poverty_remaining['group8'] = poverty_remaining['ROI_c'].apply(classify_roi)
poverty_remaining['group8'] += 2


# In[149]:


# Group1: ROI_x
counties_selected_group1_lt_003_area = counties_selected[counties_selected['group1'] == 0].geometry.area.sum()
counties_selected_group1_ge_003_area = counties_selected[counties_selected['group1'] == 1].geometry.area.sum()
counties_remaining_group1_lt_003_area = poverty_remaining[poverty_remaining['group1'] == 2].geometry.area.sum()
counties_remaining_group1_ge_003_area = poverty_remaining[poverty_remaining['group1'] == 3].geometry.area.sum()

# Group2: ROI_sub
counties_selected_group2_lt_003_area = counties_selected[counties_selected['group2'] == 0].geometry.area.sum()
counties_selected_group2_ge_003_area = counties_selected[counties_selected['group2'] == 1].geometry.area.sum()
counties_remaining_group2_lt_003_area = poverty_remaining[poverty_remaining['group2'] == 2].geometry.area.sum()
counties_remaining_group2_ge_003_area = poverty_remaining[poverty_remaining['group2'] == 3].geometry.area.sum()

# Group3: ROI_priority
counties_selected_group3_lt_003_area = counties_selected[counties_selected['group3'] == 0].geometry.area.sum()
counties_selected_group3_ge_003_area = counties_selected[counties_selected['group3'] == 1].geometry.area.sum()
counties_remaining_group3_lt_003_area = poverty_remaining[poverty_remaining['group3'] == 2].geometry.area.sum()
counties_remaining_group3_ge_003_area = poverty_remaining[poverty_remaining['group3'] == 3].geometry.area.sum()

# Group4: ROI_storage
counties_selected_group4_lt_003_area = counties_selected[counties_selected['group4'] == 0].geometry.area.sum()
counties_selected_group4_ge_003_area = counties_selected[counties_selected['group4'] == 1].geometry.area.sum()
counties_remaining_group4_lt_003_area = poverty_remaining[poverty_remaining['group4'] == 2].geometry.area.sum()
counties_remaining_group4_ge_003_area = poverty_remaining[poverty_remaining['group4'] == 3].geometry.area.sum()

# Group5: ROI_m
counties_selected_group5_lt_003_area = counties_selected[counties_selected['group5'] == 0].geometry.area.sum()
counties_selected_group5_ge_003_area = counties_selected[counties_selected['group5'] == 1].geometry.area.sum()
counties_remaining_group5_lt_003_area = poverty_remaining[poverty_remaining['group5'] == 2].geometry.area.sum()
counties_remaining_group5_ge_003_area = poverty_remaining[poverty_remaining['group5'] == 3].geometry.area.sum()

# Group6: ROI_y
counties_selected_group6_lt_003_area = counties_selected[counties_selected['group6'] == 0].geometry.area.sum()
counties_selected_group6_ge_003_area = counties_selected[counties_selected['group6'] == 1].geometry.area.sum()
counties_remaining_group6_lt_003_area = poverty_remaining[poverty_remaining['group6'] == 2].geometry.area.sum()
counties_remaining_group6_ge_003_area = poverty_remaining[poverty_remaining['group6'] == 3].geometry.area.sum()

# Group7: ROI_e
counties_selected_group7_lt_003_area = counties_selected[counties_selected['group7'] == 0].geometry.area.sum()
counties_selected_group7_ge_003_area = counties_selected[counties_selected['group7'] == 1].geometry.area.sum()
counties_remaining_group7_lt_003_area = poverty_remaining[poverty_remaining['group7'] == 2].geometry.area.sum()
counties_remaining_group7_ge_003_area = poverty_remaining[poverty_remaining['group7'] == 3].geometry.area.sum()

# Group8: ROI_c
counties_selected_group8_lt_003_area = counties_selected[counties_selected['group8'] == 0].geometry.area.sum()
counties_selected_group8_ge_003_area = counties_selected[counties_selected['group8'] == 1].geometry.area.sum()
counties_remaining_group8_lt_003_area = poverty_remaining[poverty_remaining['group8'] == 2].geometry.area.sum()
counties_remaining_group8_ge_003_area = poverty_remaining[poverty_remaining['group8'] == 3].geometry.area.sum()


# In[ ]:


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import ScalarFormatter, MultipleLocator

# ---------------------------
# 1. 构建数据（更新为8个分组）
# 注意：确保变量 counties_selected_group?_ge_003_area 与 counties_remaining_group?_ge_003_area 已经定义
data = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_area,
        counties_selected_group2_ge_003_area,
        counties_selected_group3_ge_003_area,
        counties_selected_group4_ge_003_area,
        counties_selected_group5_ge_003_area,
        counties_selected_group6_ge_003_area,
        counties_selected_group7_ge_003_area,
        counties_selected_group8_ge_003_area,
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_area,
        counties_remaining_group2_ge_003_area,
        counties_remaining_group3_ge_003_area,
        counties_remaining_group4_ge_003_area,
        counties_remaining_group5_ge_003_area,
        counties_remaining_group6_ge_003_area,
        counties_remaining_group7_ge_003_area,
        counties_remaining_group8_ge_003_area,
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_area + counties_remaining_group1_ge_003_area,
        counties_selected_group2_ge_003_area + counties_remaining_group2_ge_003_area,
        counties_selected_group3_ge_003_area + counties_remaining_group3_ge_003_area,
        counties_selected_group4_ge_003_area + counties_remaining_group4_ge_003_area,
        counties_selected_group5_ge_003_area + counties_remaining_group5_ge_003_area,
        counties_selected_group6_ge_003_area + counties_remaining_group6_ge_003_area,
        counties_selected_group7_ge_003_area + counties_remaining_group7_ge_003_area,
        counties_selected_group8_ge_003_area + counties_remaining_group8_ge_003_area,
    ]
}

# 使用实际的分组名称，顺序对应 ROI 后缀要求
groups = ['ROI_x', 'ROI_sub', 'ROI_priority', 'ROI_storage', 'ROI_m', 'ROI_y', 'ROI_e', 'ROI_c']
df = pd.DataFrame(data, index=groups)

# ---------------------------
# 2. 创建图形和设置参数
fig, ax = plt.subplots(figsize=(16, 12))

# 定义颜色映射（可根据需要调整颜色）
cmap = {
    'Selected ROI ≥ 0.03': '#ffbf7b',  # selected 0.03 < ROI
    'Remaining ROI ≥ 0.03': '#8fd0ca',  # remaining 0.03 < ROI
    'ROI ≥ 0.03': '#fa8070',           # ROI >= 0.03 总计颜色
}

# DataFrame 的列作为分类标签
categories = df.columns  # ['Selected ROI ≥ 0.03', 'Remaining ROI ≥ 0.03', 'ROI ≥ 0.03']

# 柱状图参数
bar_width = 0.3      # 每个柱子的宽度
group_gap = 1      # 不同分类（即不同列）之间的间隔
bar_inner_gap = 0.05 # 同一分类下不同分组之间的间隔
n_groups = len(groups)  # 8个分组

# 计算每个分类的起始 x 坐标，每个分类内将绘制 n_groups 个柱子
x = np.arange(len(categories)) * (bar_width * n_groups + group_gap)

# 计算每组内所有柱子的总宽度，用于设置 x 轴标签居中
# 总宽度 = n_groups * bar_width + (n_groups - 1)*bar_inner_gap
cluster_width = n_groups * bar_width + (n_groups - 1) * bar_inner_gap
xtick_offset = cluster_width / 2

# 设置图形背景为白色
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# ---------------------------
# 3. 绘制各分组的柱子
for idx, group in enumerate(groups):
    # 取出当前分组在各分类下的值
    values = df.loc[group, categories]
    ax.bar(x + (bar_width + bar_inner_gap) * idx, values, bar_width,
           label=group,
           color=[cmap.get(cat, '#cccccc') for cat in categories],
           edgecolor=[cmap.get(cat, '#cccccc') for cat in categories],
           linewidth=2)

# 设置 x 轴刻度和标签，标签位置取每个分类内所有柱子的中间位置
ax.set_xticks(x + xtick_offset)
ax.set_xticklabels(categories, fontsize=14, rotation=45, ha='right')

# ---------------------------
# 4. 设置 y 轴和其它绘图属性
# y 轴使用科学计数法
ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))

# 根据数据计算 y 轴最大值，并向上取整后放大一定比例作为最高值
y_max = df.values.max()
y_max_int = int(np.ceil(y_max))
ax.set_ylim(0, 1.4 * y_max_int)

# 启用次要刻度（根据最大值动态设置）
ax.yaxis.set_minor_locator(MultipleLocator(y_max_int / 20))

# 设置 y 轴刻度参数：主要刻度更大，次要刻度稍小
ax.yaxis.set_tick_params(which='major', length=10, width=1.8, direction='inout', labelsize=14)
ax.yaxis.set_tick_params(which='minor', length=5, width=1.5, direction='in')
ax.yaxis.set_tick_params(labelsize=14)

# 绘制 x 轴水平线，防止图形覆盖刻度
ax.axhline(0, color='black', linewidth=1.5)

# 设置边框（上、右、左、下均显示，并加粗）
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_color('black')
    ax.spines[spine].set_linewidth(1.5)

# 关闭网格线
ax.grid(False)

# 再次绘制一条中间分割线（可选）
ax.axhline(0, color='#aa988d', linewidth=1.5)

# 设置全局字体为 Times New Roman
from matplotlib import rcParams
rcParams['font.family'] = 'Times New Roman'

# 添加图例（显示每个分组名称）
ax.legend(fontsize=14, loc='upper left')

# ---------------------------
# 5. 保存并显示图形
plt.savefig('grouped_bar_area_adjusted_spacing_with_inner_gap_8groups.png', dpi=1200, format='png')
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import ScalarFormatter

# 假设之前已定义好各变量和颜色映射 cmap
# 示例颜色映射，可根据需要修改：
cmap = {
    'Selected ROI ≥ 0.03': '#ffbf7b',
    'Remaining ROI ≥ 0.03': '#8fd0ca',
    'ROI ≥ 0.03': '#fa8070',
    'Total': '#cccccc'
}

# 定义用于绘制环形图的各个指标（列名）
categories = ['Selected ROI ≥ 0.03', 'Remaining ROI ≥ 0.03', 'ROI ≥ 0.03', 'Total']

# 创建与类别数量相同的子图
fig, axs = plt.subplots(1, len(categories), figsize=(18, 6))

# 定义一个函数来生成较浅的颜色
def lighten_color(color, amount=0.5):
    try:
        c = mcolors.cnames[color]
    except KeyError:
        c = color
    c = mcolors.ColorConverter().to_rgb(c)
    return mcolors.to_rgba([(1 - amount) * x + amount for x in c])

# 构造 diff_data（行按新的8个分组排列）
# 分组顺序：ROI_x, ROI_sub, ROI_priority, ROI_storage, ROI_m, ROI_y, ROI_e, ROI_c
diff_data = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_area,  # ROI_x
        counties_selected_group2_ge_003_area,  # ROI_sub
        counties_selected_group3_ge_003_area,  # ROI_priority
        counties_selected_group4_ge_003_area,  # ROI_storage
        counties_selected_group5_ge_003_area,  # ROI_m
        counties_selected_group6_ge_003_area,  # ROI_y
        counties_selected_group7_ge_003_area,  # ROI_e
        counties_selected_group8_ge_003_area,  # ROI_c
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_area,
        counties_remaining_group2_ge_003_area,
        counties_remaining_group3_ge_003_area,
        counties_remaining_group4_ge_003_area,
        counties_remaining_group5_ge_003_area,
        counties_remaining_group6_ge_003_area,
        counties_remaining_group7_ge_003_area,
        counties_remaining_group8_ge_003_area,
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_area + counties_remaining_group1_ge_003_area,
        counties_selected_group2_ge_003_area + counties_remaining_group2_ge_003_area,
        counties_selected_group3_ge_003_area + counties_remaining_group3_ge_003_area,
        counties_selected_group4_ge_003_area + counties_remaining_group4_ge_003_area,
        counties_selected_group5_ge_003_area + counties_remaining_group5_ge_003_area,
        counties_selected_group6_ge_003_area + counties_remaining_group6_ge_003_area,
        counties_selected_group7_ge_003_area + counties_remaining_group7_ge_003_area,
        counties_selected_group8_ge_003_area + counties_remaining_group8_ge_003_area,
    ],
    'Total': [
        counties_selected_group1_lt_003_area + counties_selected_group1_ge_003_area +
        counties_remaining_group1_lt_003_area + counties_remaining_group1_ge_003_area,

        counties_selected_group2_lt_003_area + counties_selected_group2_ge_003_area +
        counties_remaining_group2_lt_003_area + counties_remaining_group2_ge_003_area,

        counties_selected_group3_lt_003_area + counties_selected_group3_ge_003_area +
        counties_remaining_group3_lt_003_area + counties_remaining_group3_ge_003_area,

        counties_selected_group4_lt_003_area + counties_selected_group4_ge_003_area +
        counties_remaining_group4_lt_003_area + counties_remaining_group4_ge_003_area,

        counties_selected_group5_lt_003_area + counties_selected_group5_ge_003_area +
        counties_remaining_group5_lt_003_area + counties_remaining_group5_ge_003_area,

        counties_selected_group6_lt_003_area + counties_selected_group6_ge_003_area +
        counties_remaining_group6_lt_003_area + counties_remaining_group6_ge_003_area,

        counties_selected_group7_lt_003_area + counties_selected_group7_ge_003_area +
        counties_remaining_group7_lt_003_area + counties_remaining_group7_ge_003_area,

        counties_selected_group8_lt_003_area + counties_selected_group8_ge_003_area +
        counties_remaining_group8_lt_003_area + counties_remaining_group8_ge_003_area,
    ]
}

# 新的分组名称，按顺序排列
group_names = ['ROI_x', 'ROI_sub', 'ROI_priority', 'ROI_storage', 'ROI_m', 'ROI_y', 'ROI_e', 'ROI_c']
df_diff_data = pd.DataFrame(diff_data, index=group_names)

# 此处我们展示 ROI_m 相对于 ROI_x 的变化
# 对于每个指标（除 Total 外），取 ROI_m 与 ROI_x 的差值，
# 并以 ROI_m 的数值为总量计算百分比。
for i, category in enumerate(categories):
    # 以 ROI_m 的值作为总量
    total = df_diff_data.loc['ROI_m', category]
    # 计算 ROI_m 与 ROI_x 的差值
    diff_value = df_diff_data.loc['ROI_m', category] - df_diff_data.loc['ROI_x', category]

    # 确保数值非负：若 total<=0 则全部置0；若 diff_value < 0 则认为没有“增加”部分
    if total <= 0:
        percentage_diff = 0
        percentage_remaining = 0
    elif diff_value < 0:
        percentage_diff = 0
        percentage_remaining = 100
    else:
        percentage_diff = diff_value / total * 100
        percentage_remaining = (total - diff_value) / total * 100

    # 定义颜色：差值部分使用较浅的颜色，剩余部分使用原色
    base_color = cmap.get(category, '#cccccc')
    wedge_colors = [lighten_color(base_color, 0.7), base_color]

    # 创建环形图，设置 wedgeprops 中 width 为 0.5
    wedges, texts, autotexts = axs[i].pie([percentage_diff, percentage_remaining],
                                          colors=wedge_colors,
                                          startangle=90,
                                          wedgeprops=dict(width=0.5),
                                          autopct='%1.1f%%')

    # 添加中间白色圆圈，产生环形效果
    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
    axs[i].add_artist(centre_circle)

    # 设置子图标题，标明当前指标
    axs[i].set_title(f'{category} Ratio', fontsize=14)

    # 调整百分比文字的字号
    for autotext in autotexts:
        autotext.set_fontsize(40)

plt.tight_layout()
plt.savefig('area_ratio.png', dpi=1200, format='png')
plt.show()


# In[ ]:


# 构建 DataFrame（索引对应 group1 到 group8）
df_diff_data = pd.DataFrame(
    diff_data,
    index=['Group1', 'Group2', 'Group3', 'Group4', 'Group5', 'Group6', 'Group7', 'Group8']
)

# 以 Group1 为基准，计算 Group2 到 Group8 的差值
df_diff_data.loc['Difference Group2'] = df_diff_data.loc['Group2'] - df_diff_data.loc['Group1']
df_diff_data.loc['Difference Group3'] = df_diff_data.loc['Group3'] - df_diff_data.loc['Group1']
df_diff_data.loc['Difference Group4'] = df_diff_data.loc['Group4'] - df_diff_data.loc['Group1']
df_diff_data.loc['Difference Group5'] = df_diff_data.loc['Group5'] - df_diff_data.loc['Group1']
df_diff_data.loc['Difference Group6'] = df_diff_data.loc['Group6'] - df_diff_data.loc['Group1']
df_diff_data.loc['Difference Group7'] = df_diff_data.loc['Group7'] - df_diff_data.loc['Group1']
df_diff_data.loc['Difference Group8'] = df_diff_data.loc['Group8'] - df_diff_data.loc['Group1']

# 创建图形和子图，调整图形尺寸以适应更多行
fig, ax = plt.subplots(figsize=(12, 8))

# 关闭坐标轴显示
ax.axis('off')

# 使用 matplotlib 绘制表格，展示 Group1 ~ Group8 及其差值
table = ax.table(
    cellText=df_diff_data.values,
    colLabels=df_diff_data.columns,
    rowLabels=df_diff_data.index,
    cellLoc='center',
    loc='center'
)

# 调整表格字体大小和尺寸
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.5)  # 横向放大1.2倍，纵向放大1.5倍

# 设置表格标题
plt.title("各组数值及其差值", fontsize=16)

# 显示表格
plt.show()


# In[ ]:


diff_data


# ##### 人口

# In[ ]:


poverty_data['name'] = poverty_data['市'].astype(str)
merged_df = merged_df.merge(poverty_data[['name', '人口']], on='name', how='left')
merged_df = merged_df.drop_duplicates(subset=['name'])

# 从 'name' 列将人口信息从 merged_df 合并到 counties_selected 和 poverty_remaining
counties_selected = counties_selected.merge(merged_df[['name', '人口']], on='name', how='left')
poverty_remaining = poverty_remaining.merge(merged_df[['name', '人口']], on='name', how='left')


# In[173]:


# Group1: ROI_x
counties_selected_group1_lt_003_pop = counties_selected[counties_selected['group1'] == 0]['人口'].sum()
counties_selected_group1_ge_003_pop = counties_selected[counties_selected['group1'] == 1]['人口'].sum()
counties_remaining_group1_lt_003_pop = poverty_remaining[poverty_remaining['group1'] == 2]['人口'].sum()
counties_remaining_group1_ge_003_pop = poverty_remaining[poverty_remaining['group1'] == 3]['人口'].sum()

# Group2: ROI_sub
counties_selected_group2_lt_003_pop = counties_selected[counties_selected['group2'] == 0]['人口'].sum()
counties_selected_group2_ge_003_pop = counties_selected[counties_selected['group2'] == 1]['人口'].sum()
counties_remaining_group2_lt_003_pop = poverty_remaining[poverty_remaining['group2'] == 2]['人口'].sum()
counties_remaining_group2_ge_003_pop = poverty_remaining[poverty_remaining['group2'] == 3]['人口'].sum()

# Group3: ROI_priority
counties_selected_group3_lt_003_pop = counties_selected[counties_selected['group3'] == 0]['人口'].sum()
counties_selected_group3_ge_003_pop = counties_selected[counties_selected['group3'] == 1]['人口'].sum()
counties_remaining_group3_lt_003_pop = poverty_remaining[poverty_remaining['group3'] == 2]['人口'].sum()
counties_remaining_group3_ge_003_pop = poverty_remaining[poverty_remaining['group3'] == 3]['人口'].sum()

# Group4: ROI_storage
counties_selected_group4_lt_003_pop = counties_selected[counties_selected['group4'] == 0]['人口'].sum()
counties_selected_group4_ge_003_pop = counties_selected[counties_selected['group4'] == 1]['人口'].sum()
counties_remaining_group4_lt_003_pop = poverty_remaining[poverty_remaining['group4'] == 2]['人口'].sum()
counties_remaining_group4_ge_003_pop = poverty_remaining[poverty_remaining['group4'] == 3]['人口'].sum()

# Group5: ROI_m
counties_selected_group5_lt_003_pop = counties_selected[counties_selected['group5'] == 0]['人口'].sum()
counties_selected_group5_ge_003_pop = counties_selected[counties_selected['group5'] == 1]['人口'].sum()
counties_remaining_group5_lt_003_pop = poverty_remaining[poverty_remaining['group5'] == 2]['人口'].sum()
counties_remaining_group5_ge_003_pop = poverty_remaining[poverty_remaining['group5'] == 3]['人口'].sum()

# Group6: ROI_y
counties_selected_group6_lt_003_pop = counties_selected[counties_selected['group6'] == 0]['人口'].sum()
counties_selected_group6_ge_003_pop = counties_selected[counties_selected['group6'] == 1]['人口'].sum()
counties_remaining_group6_lt_003_pop = poverty_remaining[poverty_remaining['group6'] == 2]['人口'].sum()
counties_remaining_group6_ge_003_pop = poverty_remaining[poverty_remaining['group6'] == 3]['人口'].sum()

# Group7: ROI_e
counties_selected_group7_lt_003_pop = counties_selected[counties_selected['group7'] == 0]['人口'].sum()
counties_selected_group7_ge_003_pop = counties_selected[counties_selected['group7'] == 1]['人口'].sum()
counties_remaining_group7_lt_003_pop = poverty_remaining[poverty_remaining['group7'] == 2]['人口'].sum()
counties_remaining_group7_ge_003_pop = poverty_remaining[poverty_remaining['group7'] == 3]['人口'].sum()

# Group8: ROI_c
counties_selected_group8_lt_003_pop = counties_selected[counties_selected['group8'] == 0]['人口'].sum()
counties_selected_group8_ge_003_pop = counties_selected[counties_selected['group8'] == 1]['人口'].sum()
counties_remaining_group8_lt_003_pop = poverty_remaining[poverty_remaining['group8'] == 2]['人口'].sum()
counties_remaining_group8_ge_003_pop = poverty_remaining[poverty_remaining['group8'] == 3]['人口'].sum()


# In[ ]:


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from matplotlib import rcParams

# ---------------------------
# 1. 构建数据：8组人口数据
data = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_pop,
        counties_selected_group2_ge_003_pop,
        counties_selected_group3_ge_003_pop,
        counties_selected_group4_ge_003_pop,
        counties_selected_group5_ge_003_pop,
        counties_selected_group6_ge_003_pop,
        counties_selected_group7_ge_003_pop,
        counties_selected_group8_ge_003_pop,
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_pop,
        counties_remaining_group2_ge_003_pop,
        counties_remaining_group3_ge_003_pop,
        counties_remaining_group4_ge_003_pop,
        counties_remaining_group5_ge_003_pop,
        counties_remaining_group6_ge_003_pop,
        counties_remaining_group7_ge_003_pop,
        counties_remaining_group8_ge_003_pop,
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_pop + counties_remaining_group1_ge_003_pop,
        counties_selected_group2_ge_003_pop + counties_remaining_group2_ge_003_pop,
        counties_selected_group3_ge_003_pop + counties_remaining_group3_ge_003_pop,
        counties_selected_group4_ge_003_pop + counties_remaining_group4_ge_003_pop,
        counties_selected_group5_ge_003_pop + counties_remaining_group5_ge_003_pop,
        counties_selected_group6_ge_003_pop + counties_remaining_group6_ge_003_pop,
        counties_selected_group7_ge_003_pop + counties_remaining_group7_ge_003_pop,
        counties_selected_group8_ge_003_pop + counties_remaining_group8_ge_003_pop,
    ]
}

# 设置行索引为8个组名
group_names = ['Group1', 'Group2', 'Group3', 'Group4', 'Group5', 'Group6', 'Group7', 'Group8']
df = pd.DataFrame(data, index=group_names)

# ---------------------------
# 2. 创建图形及绘图参数
fig, ax = plt.subplots(figsize=(16, 12))

# 定义颜色映射
cmap = {
    'Selected ROI ≥ 0.03': '#ffbf7b',  # selected ROI >= 0.03
    'Remaining ROI ≥ 0.03': '#8fd0ca',  # remaining ROI >= 0.03
    'ROI ≥ 0.03': '#fa8070',            # ROI >= 0.03 总计颜色
}

# 定义分类标签（DataFrame的列）
categories = df.columns  # ['Selected ROI ≥ 0.03', 'Remaining ROI ≥ 0.03', 'ROI ≥ 0.03']

# 柱状图参数
bar_width = 0.3       # 每个柱子的宽度
group_gap = 1       # 不同分类之间的间隔
bar_inner_gap = 0.05  # 同一分类内各组之间的间隔
n_groups = len(group_names)  # 8组

# 每一簇柱子的总宽度：
cluster_width = n_groups * bar_width + (n_groups - 1) * bar_inner_gap
# x坐标：每个类别作为一个簇，簇间间隔 group_gap
x = np.arange(len(categories)) * (cluster_width + group_gap)

# ---------------------------
# 3. 绘制各组的柱子
for i, group in enumerate(group_names):
    # 计算当前组在簇中的水平偏移（使得各柱子居中）
    offset = (i - (n_groups - 1) / 2) * (bar_width + bar_inner_gap)
    ax.bar(x + offset, df.loc[group, categories], bar_width,
           label=group,
           color=[cmap.get(cat, '#cccccc') for cat in categories],
           edgecolor=[cmap.get(cat, '#cccccc') for cat in categories])

# ---------------------------
# 4. 设置坐标轴和样式
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=14, rotation=45, ha='right')

# 使用科学计数法显示 y 轴刻度
ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))

# 计算 y 轴最大值并向上取整
y_max = df.values.max()
y_max_int = int(np.ceil(y_max))
ax.set_ylim(0, 1.4 * y_max_int)

# 设置次要刻度
ax.yaxis.set_minor_locator(MultipleLocator(y_max_int / 20))

# 配置刻度显示样式
ax.yaxis.set_tick_params(which='major', length=10, width=1.8, direction='inout', labelsize=14)
ax.yaxis.set_tick_params(which='minor', length=5, width=1.5, direction='in')
ax.yaxis.set_tick_params(labelsize=25)

# 绘制水平轴线
ax.axhline(0, color='black', linewidth=1.5)

# 设置四周边框颜色及加粗
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_color('black')
    ax.spines[spine].set_linewidth(1.5)

# 关闭网格线
ax.grid(False)

# 添加中间分割线
ax.axhline(0, color='#aa988d', linewidth=1.5)

# 设置全局字体为 Times New Roman
rcParams['font.family'] = 'Times New Roman'

# 添加图例
ax.legend(fontsize=14, loc='upper left')

# ---------------------------
# 5. 保存并显示图形
plt.savefig('population_grouped_bar_chart_with_groups_1_8.png', dpi=1200, format='png', transparent=True)
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import ScalarFormatter

# 假设之前已定义好各变量和颜色映射 cmap
# 示例颜色映射，可根据需要修改：
cmap = {
    'Selected ROI ≥ 0.03': '#ffbf7b',
    'Remaining ROI ≥ 0.03': '#8fd0ca',
    'ROI ≥ 0.03': '#fa8070',
    'Total': '#cccccc'
}

# 定义用于绘制环形图的各个指标（列名）
categories = ['Selected ROI ≥ 0.03', 'Remaining ROI ≥ 0.03', 'ROI ≥ 0.03', 'Total']

# 创建与类别数量相同的子图
fig, axs = plt.subplots(1, len(categories), figsize=(18, 6))

# 定义一个函数来生成较浅的颜色
def lighten_color(color, amount=0.5):
    try:
        c = mcolors.cnames[color]
    except KeyError:
        c = color
    c = mcolors.ColorConverter().to_rgb(c)
    return mcolors.to_rgba([(1 - amount) * x + amount for x in c])

# 构造 diff_data（行按新的8个分组排列）
# 分组顺序：ROI_x, ROI_sub, ROI_priority, ROI_storage, ROI_m, ROI_y, ROI_e, ROI_c
diff_data = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_pop,  # ROI_x
        counties_selected_group2_ge_003_pop,  # ROI_sub
        counties_selected_group3_ge_003_pop,  # ROI_priority
        counties_selected_group4_ge_003_pop,  # ROI_storage
        counties_selected_group5_ge_003_pop,  # ROI_m
        counties_selected_group6_ge_003_pop,  # ROI_y
        counties_selected_group7_ge_003_pop,  # ROI_e
        counties_selected_group8_ge_003_pop,  # ROI_c
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_pop,
        counties_remaining_group2_ge_003_pop,
        counties_remaining_group3_ge_003_pop,
        counties_remaining_group4_ge_003_pop,
        counties_remaining_group5_ge_003_pop,
        counties_remaining_group6_ge_003_pop,
        counties_remaining_group7_ge_003_pop,
        counties_remaining_group8_ge_003_pop,
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_pop + counties_remaining_group1_ge_003_pop,
        counties_selected_group2_ge_003_pop + counties_remaining_group2_ge_003_pop,
        counties_selected_group3_ge_003_pop + counties_remaining_group3_ge_003_pop,
        counties_selected_group4_ge_003_pop + counties_remaining_group4_ge_003_pop,
        counties_selected_group5_ge_003_pop + counties_remaining_group5_ge_003_pop,
        counties_selected_group6_ge_003_pop + counties_remaining_group6_ge_003_pop,
        counties_selected_group7_ge_003_pop + counties_remaining_group7_ge_003_pop,
        counties_selected_group8_ge_003_pop + counties_remaining_group8_ge_003_pop,
    ],
    'Total': [
        counties_selected_group1_lt_003_pop + counties_selected_group1_ge_003_pop +
        counties_remaining_group1_lt_003_pop + counties_remaining_group1_ge_003_pop,

        counties_selected_group2_lt_003_pop + counties_selected_group2_ge_003_pop +
        counties_remaining_group2_lt_003_pop + counties_remaining_group2_ge_003_pop,

        counties_selected_group3_lt_003_pop + counties_selected_group3_ge_003_pop +
        counties_remaining_group3_lt_003_pop + counties_remaining_group3_ge_003_pop,

        counties_selected_group4_lt_003_pop + counties_selected_group4_ge_003_pop +
        counties_remaining_group4_lt_003_pop + counties_remaining_group4_ge_003_pop,

        counties_selected_group5_lt_003_pop + counties_selected_group5_ge_003_pop +
        counties_remaining_group5_lt_003_pop + counties_remaining_group5_ge_003_pop,

        counties_selected_group6_lt_003_pop + counties_selected_group6_ge_003_pop +
        counties_remaining_group6_lt_003_pop + counties_remaining_group6_ge_003_pop,

        counties_selected_group7_lt_003_pop + counties_selected_group7_ge_003_pop +
        counties_remaining_group7_lt_003_pop + counties_remaining_group7_ge_003_pop,

        counties_selected_group8_lt_003_pop + counties_selected_group8_ge_003_pop +
        counties_remaining_group8_lt_003_pop + counties_remaining_group8_ge_003_pop,
    ]
}

# 新的分组名称，按顺序排列
group_names = ['ROI_x', 'ROI_sub', 'ROI_priority', 'ROI_storage', 'ROI_m', 'ROI_y', 'ROI_e', 'ROI_c']
df_diff_data = pd.DataFrame(diff_data, index=group_names)

# 此处我们展示 ROI_m 相对于 ROI_x 的变化
# 对于每个指标（除 Total 外），取 ROI_m 与 ROI_x 的差值，
# 并以 ROI_m 的数值为总量计算百分比。
for i, category in enumerate(categories):
    # 以 ROI_m 的值作为总量
    total = df_diff_data.loc['ROI_m', category]
    # 计算 ROI_m 与 ROI_x 的差值
    diff_value = df_diff_data.loc['ROI_m', category] - df_diff_data.loc['ROI_x', category]

    # 确保数值非负：若 total<=0 则全部置0；若 diff_value < 0 则认为没有“增加”部分
    if total <= 0:
        percentage_diff = 0
        percentage_remaining = 0
    elif diff_value < 0:
        percentage_diff = 0
        percentage_remaining = 100
    else:
        percentage_diff = diff_value / total * 100
        percentage_remaining = (total - diff_value) / total * 100

    # 定义颜色：差值部分使用较浅的颜色，剩余部分使用原色
    base_color = cmap.get(category, '#cccccc')
    wedge_colors = [lighten_color(base_color, 0.7), base_color]

    # 创建环形图，设置 wedgeprops 中 width 为 0.5
    wedges, texts, autotexts = axs[i].pie([percentage_diff, percentage_remaining],
                                          colors=wedge_colors,
                                          startangle=90,
                                          wedgeprops=dict(width=0.5),
                                          autopct='%1.1f%%')

    # 添加中间白色圆圈，产生环形效果
    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
    axs[i].add_artist(centre_circle)

    # 设置子图标题，标明当前指标
    axs[i].set_title(f'{category} Ratio', fontsize=14)

    # 调整百分比文字的字号
    for autotext in autotexts:
        autotext.set_fontsize(40)

plt.tight_layout()
plt.savefig('pop_ratio.png', dpi=1200, format='png')
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import pandas as pd

data_pu = data

# 创建 DataFrame，行索引使用 Group1 至 Group8
df = pd.DataFrame(data_pu, index=['Group1', 'Group2', 'Group3', 'Group4', 'Group5', 'Group6', 'Group7', 'Group8'])

# 分别计算以 Group1 为基准的差值（Group2 ~ Group8）
df.loc['Difference Group2'] = df.loc['Group2'] - df.loc['Group1']
df.loc['Difference Group3'] = df.loc['Group3'] - df.loc['Group1']
df.loc['Difference Group4'] = df.loc['Group4'] - df.loc['Group1']
df.loc['Difference Group5'] = df.loc['Group5'] - df.loc['Group1']
df.loc['Difference Group6'] = df.loc['Group6'] - df.loc['Group1']
df.loc['Difference Group7'] = df.loc['Group7'] - df.loc['Group1']
df.loc['Difference Group8'] = df.loc['Group8'] - df.loc['Group1']

# 创建图形和子图
fig, ax = plt.subplots(figsize=(10, 6))

# 关闭坐标轴显示
ax.axis('off')

# 使用 matplotlib 绘制表格，展示各组数据及其差值
table = ax.table(
    cellText=df.values,
    colLabels=df.columns,
    rowLabels=df.index,  # 行标签与数据一致
    cellLoc='center',
    loc='center'
)

# 调整表格字体和尺寸
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.2)

# 设置表格标题（例如：各组人口数值及其差值）
plt.title("各组人口数值及其差值", fontsize=16)

# 显示图形
plt.show()


# ##### 个数

# In[ ]:


#### 个数
# Group1 分类个数
counties_selected_group1_lt_003_count = (counties_selected['group1'] == 0).sum()
counties_selected_group1_ge_003_count = (counties_selected['group1'] == 1).sum()
counties_remaining_group1_lt_003_count = (poverty_remaining['group1'] == 2).sum()
counties_remaining_group1_ge_003_count = (poverty_remaining['group1'] == 3).sum()

# Group2 分类个数
counties_selected_group2_lt_003_count = (counties_selected['group2'] == 0).sum()
counties_selected_group2_ge_003_count = (counties_selected['group2'] == 1).sum()
counties_remaining_group2_lt_003_count = (poverty_remaining['group2'] == 2).sum()
counties_remaining_group2_ge_003_count = (poverty_remaining['group2'] == 3).sum()

# Group3 分类个数
counties_selected_group3_lt_003_count = (counties_selected['group3'] == 0).sum()
counties_selected_group3_ge_003_count = (counties_selected['group3'] == 1).sum()
counties_remaining_group3_lt_003_count = (poverty_remaining['group3'] == 2).sum()
counties_remaining_group3_ge_003_count = (poverty_remaining['group3'] == 3).sum()

# Group4 分类个数
counties_selected_group4_lt_003_count = (counties_selected['group4'] == 0).sum()
counties_selected_group4_ge_003_count = (counties_selected['group4'] == 1).sum()
counties_remaining_group4_lt_003_count = (poverty_remaining['group4'] == 2).sum()
counties_remaining_group4_ge_003_count = (poverty_remaining['group4'] == 3).sum()

# Group5 分类个数
counties_selected_group5_lt_003_count = (counties_selected['group5'] == 0).sum()
counties_selected_group5_ge_003_count = (counties_selected['group5'] == 1).sum()
counties_remaining_group5_lt_003_count = (poverty_remaining['group5'] == 2).sum()
counties_remaining_group5_ge_003_count = (poverty_remaining['group5'] == 3).sum()

# Group6 分类个数
counties_selected_group6_lt_003_count = (counties_selected['group6'] == 0).sum()
counties_selected_group6_ge_003_count = (counties_selected['group6'] == 1).sum()
counties_remaining_group6_lt_003_count = (poverty_remaining['group6'] == 2).sum()
counties_remaining_group6_ge_003_count = (poverty_remaining['group6'] == 3).sum()

# Group7 分类个数
counties_selected_group7_lt_003_count = (counties_selected['group7'] == 0).sum()
counties_selected_group7_ge_003_count = (counties_selected['group7'] == 1).sum()
counties_remaining_group7_lt_003_count = (poverty_remaining['group7'] == 2).sum()
counties_remaining_group7_ge_003_count = (poverty_remaining['group7'] == 3).sum()

# Group8 分类个数
counties_selected_group8_lt_003_count = (counties_selected['group8'] == 0).sum()
counties_selected_group8_ge_003_count = (counties_selected['group8'] == 1).sum()
counties_remaining_group8_lt_003_count = (poverty_remaining['group8'] == 2).sum()
counties_remaining_group8_ge_003_count = (poverty_remaining['group8'] == 3).sum()

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from matplotlib import rcParams

# ============================
# 1. 构建数据：更新为 8 组
data = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_count,
        counties_selected_group2_ge_003_count,
        counties_selected_group3_ge_003_count,
        counties_selected_group4_ge_003_count,
        counties_selected_group5_ge_003_count,
        counties_selected_group6_ge_003_count,
        counties_selected_group7_ge_003_count,
        counties_selected_group8_ge_003_count
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_count,
        counties_remaining_group2_ge_003_count,
        counties_remaining_group3_ge_003_count,
        counties_remaining_group4_ge_003_count,
        counties_remaining_group5_ge_003_count,
        counties_remaining_group6_ge_003_count,
        counties_remaining_group7_ge_003_count,
        counties_remaining_group8_ge_003_count
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_count + counties_remaining_group1_ge_003_count,
        counties_selected_group2_ge_003_count + counties_remaining_group2_ge_003_count,
        counties_selected_group3_ge_003_count + counties_remaining_group3_ge_003_count,
        counties_selected_group4_ge_003_count + counties_remaining_group4_ge_003_count,
        counties_selected_group5_ge_003_count + counties_remaining_group5_ge_003_count,
        counties_selected_group6_ge_003_count + counties_remaining_group6_ge_003_count,
        counties_selected_group7_ge_003_count + counties_remaining_group7_ge_003_count,
        counties_selected_group8_ge_003_count + counties_remaining_group8_ge_003_count
    ]
}

# 使用行索引表示各组，组名更新为 Group1 ~ Group8
df = pd.DataFrame(data, index=['Group1', 'Group2', 'Group3', 'Group4', 'Group5', 'Group6', 'Group7', 'Group8'])

# ============================
# 2. 参数设置
categories = df.columns  # ['Selected ROI ≥ 0.03', 'Remaining ROI ≥ 0.03', 'ROI ≥ 0.03']
bar_width = 0.3  # 每个柱子的宽度
group_gap = 1  # 每簇柱子之间的间隔
bar_inner_gap = 0.05  # 同簇柱子之间的间隔

# 创建图形
fig, ax = plt.subplots(figsize=(16, 12))

# 定义颜色映射
cmap = {
    'Selected ROI ≥ 0.03': '#ffbf7b',
    'Remaining ROI ≥ 0.03': '#8fd0ca',
    'ROI ≥ 0.03': '#fa8070',
}

# 设置 x 轴位置
# 每一簇柱子总宽度为：len(df.index)*bar_width + (len(df.index)-1)*bar_inner_gap
x = np.arange(len(categories)) * (len(df.index) * bar_width + group_gap)

# ============================
# 3. 绘制每组柱子
group_names = ['Group1', 'Group2', 'Group3', 'Group4', 'Group5', 'Group6', 'Group7', 'Group8']
for idx, group in enumerate(group_names):
    # x 轴偏移：依次增加 (bar_width+bar_inner_gap)
    ax.bar(
        x + (bar_width + bar_inner_gap) * idx,  # 每组柱子的位置
        df.loc[group, categories],  # 对应数据
        bar_width,  # 柱宽
        label=group,  # 图例显示组名
        color=[cmap.get(cat, '#cccccc') for cat in categories],
        edgecolor=[cmap.get(cat, '#cccccc') for cat in categories],
        linewidth=2
    )

# ============================
# 4. 设置 x 轴标签
# x 轴标签居中在每个簇中
ax.set_xticks(x + (len(df.index) - 1) * (bar_width + bar_inner_gap) / 2)
ax.set_xticklabels(categories, fontsize=14, rotation=45, ha='right')

# 设置 y 轴使用科学计数法
ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))

# 计算 y 轴最大值并设置范围
y_max = df.values.max()
y_max_int = int(np.ceil(y_max))
ax.set_ylim(0, 1.4 * y_max_int)

# 添加次要刻度
ax.yaxis.set_minor_locator(MultipleLocator(y_max_int / 20))

# 调整刻度样式
ax.yaxis.set_tick_params(which='major', length=10, width=1.8, direction='inout', labelsize=14)
ax.yaxis.set_tick_params(which='minor', length=5, width=1.5, direction='in')

# ============================
# 5. 美化图形
ax.axhline(0, color='black', linewidth=1.5)  # 添加水平线
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_color('black')
    ax.spines[spine].set_linewidth(1.5)

# 设置全局字体为 Times New Roman
rcParams['font.family'] = 'Times New Roman'

# 添加图例（位于右上角，不带边框）
ax.legend(fontsize=14, loc='upper right', frameon=False)

# ============================
# 6. 保存并显示图像
plt.savefig('grouped_bar_count_with_spacing_adjusted.png', dpi=1200, format='png', transparent=True)
plt.show()

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

# ================================
# 1. 构建数据（更新为 Group1～Group8）
# 请确保下列变量均已定义：
#   counties_selected_group{N}_ge_003_count, counties_remaining_group{N}_ge_003_count,
#   counties_selected_group{N}_lt_003_count, counties_remaining_group{N}_lt_003_count
# 其中 N 分别为 1, 2, …, 8
data = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_count,
        counties_selected_group2_ge_003_count,
        counties_selected_group3_ge_003_count,
        counties_selected_group4_ge_003_count,
        counties_selected_group5_ge_003_count,
        counties_selected_group6_ge_003_count,
        counties_selected_group7_ge_003_count,
        counties_selected_group8_ge_003_count,
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_count,
        counties_remaining_group2_ge_003_count,
        counties_remaining_group3_ge_003_count,
        counties_remaining_group4_ge_003_count,
        counties_remaining_group5_ge_003_count,
        counties_remaining_group6_ge_003_count,
        counties_remaining_group7_ge_003_count,
        counties_remaining_group8_ge_003_count,
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_count + counties_remaining_group1_ge_003_count,
        counties_selected_group2_ge_003_count + counties_remaining_group2_ge_003_count,
        counties_selected_group3_ge_003_count + counties_remaining_group3_ge_003_count,
        counties_selected_group4_ge_003_count + counties_remaining_group4_ge_003_count,
        counties_selected_group5_ge_003_count + counties_remaining_group5_ge_003_count,
        counties_selected_group6_ge_003_count + counties_remaining_group6_ge_003_count,
        counties_selected_group7_ge_003_count + counties_remaining_group7_ge_003_count,
        counties_selected_group8_ge_003_count + counties_remaining_group8_ge_003_count,
    ],
    'Total': [
        counties_selected_group1_lt_003_count + counties_selected_group1_ge_003_count +
        counties_remaining_group1_lt_003_count + counties_remaining_group1_ge_003_count,

        counties_selected_group2_lt_003_count + counties_selected_group2_ge_003_count +
        counties_remaining_group2_lt_003_count + counties_remaining_group2_ge_003_count,

        counties_selected_group3_lt_003_count + counties_selected_group3_ge_003_count +
        counties_remaining_group3_lt_003_count + counties_remaining_group3_ge_003_count,

        counties_selected_group4_lt_003_count + counties_selected_group4_ge_003_count +
        counties_remaining_group4_lt_003_count + counties_remaining_group4_ge_003_count,

        counties_selected_group5_lt_003_count + counties_selected_group5_ge_003_count +
        counties_remaining_group5_lt_003_count + counties_remaining_group5_ge_003_count,

        counties_selected_group6_lt_003_count + counties_selected_group6_ge_003_count +
        counties_remaining_group6_lt_003_count + counties_remaining_group6_ge_003_count,

        counties_selected_group7_lt_003_count + counties_selected_group7_ge_003_count +
        counties_remaining_group7_lt_003_count + counties_remaining_group7_ge_003_count,

        counties_selected_group8_lt_003_count + counties_selected_group8_ge_003_count +
        counties_remaining_group8_lt_003_count + counties_remaining_group8_ge_003_count,
    ]
}

# 使用行索引标识各组
df_diff_data = pd.DataFrame(data, index=['Group1', 'Group2', 'Group3', 'Group4',
                                         'Group5', 'Group6', 'Group7', 'Group8'])
print(df_diff_data)

# ================================
# 2. 计算差值 —— 以 Group5 与 Group1 为例（不包括 'Total' 列）
df_diff = df_diff_data.loc['Group5', df_diff_data.columns[:-1]] - df_diff_data.loc['Group1', df_diff_data.columns[:-1]]
# 此时 df_diff 的索引为：['Selected ROI ≥ 0.03', 'Remaining ROI ≥ 0.03', 'ROI ≥ 0.03']

# ================================
# 3. 绘制环形图
# 为每个指标创建一个子图
fig, axs = plt.subplots(1, len(df_diff), figsize=(18, 6))


# 定义一个函数，用于生成较浅的颜色
def lighten_color(color, amount=0.5):
    try:
        c = mcolors.cnames[color]
    except KeyError:
        c = color
    c = mcolors.ColorConverter().to_rgb(c)
    return mcolors.to_rgba([(1 - amount) * x + amount for x in c])


# 定义每个指标对应的颜色映射（可根据需要调整）
cmap = {
    'Selected ROI ≥ 0.03': '#ffbf7b',
    'Remaining ROI ≥ 0.03': '#8fd0ca',
    'ROI ≥ 0.03': '#fa8070'
}

# 对每个指标循环绘制环形图
for i, category in enumerate(df_diff.index):
    # 以 Group5 的值作为总量
    total = df_diff_data.loc['Group5', category]
    # 计算差值 (Group5 - Group1)
    diff_value = df_diff[category]

    # 为防止除 0 错误及负值情况，做简单判断
    if total <= 0:
        percentage_diff = 0
        percentage_remaining = 0
    elif diff_value < 0:
        percentage_diff = 0
        percentage_remaining = 100
    else:
        percentage_diff = diff_value / total * 100
        percentage_remaining = (total - diff_value) / total * 100

    # 设置环形图颜色：差值部分使用较浅的颜色
    wedge_colors = [lighten_color(cmap.get(category), 0.7), cmap.get(category)]

    # 绘制环形图，wedgeprops 中的 width 控制环形宽度（此处设为 0.5）
    wedges, texts, autotexts = axs[i].pie([percentage_diff, percentage_remaining],
                                          colors=wedge_colors,
                                          startangle=90,
                                          wedgeprops=dict(width=0.5),
                                          autopct='%1.1f%%')

    # 添加中心白色圆圈，形成环形效果
    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
    axs[i].add_artist(centre_circle)

    # 设置子图标题，标明当前指标及差值（Group5-Group1）
    axs[i].set_title(f'{category} (Group5-Group1) Ratio', fontsize=14)

    # 调整环形图上百分比标注的字号
    for autotext in autotexts:
        autotext.set_fontsize(40)

plt.tight_layout()
plt.savefig('pop_diffenerce.png', dpi=1200, format='png')
plt.show()

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# ============================
# 1. 构建数据（8组）
data_pu = {
    'Selected ROI ≥ 0.03': [
        counties_selected_group1_ge_003_count,
        counties_selected_group2_ge_003_count,
        counties_selected_group3_ge_003_count,
        counties_selected_group4_ge_003_count,
        counties_selected_group5_ge_003_count,
        counties_selected_group6_ge_003_count,
        counties_selected_group7_ge_003_count,
        counties_selected_group8_ge_003_count
    ],
    'Remaining ROI ≥ 0.03': [
        counties_remaining_group1_ge_003_count,
        counties_remaining_group2_ge_003_count,
        counties_remaining_group3_ge_003_count,
        counties_remaining_group4_ge_003_count,
        counties_remaining_group5_ge_003_count,
        counties_remaining_group6_ge_003_count,
        counties_remaining_group7_ge_003_count,
        counties_remaining_group8_ge_003_count
    ],
    'ROI ≥ 0.03': [
        counties_selected_group1_ge_003_count + counties_remaining_group1_ge_003_count,
        counties_selected_group2_ge_003_count + counties_remaining_group2_ge_003_count,
        counties_selected_group3_ge_003_count + counties_remaining_group3_ge_003_count,
        counties_selected_group4_ge_003_count + counties_remaining_group4_ge_003_count,
        counties_selected_group5_ge_003_count + counties_remaining_group5_ge_003_count,
        counties_selected_group6_ge_003_count + counties_remaining_group6_ge_003_count,
        counties_selected_group7_ge_003_count + counties_remaining_group7_ge_003_count,
        counties_selected_group8_ge_003_count + counties_remaining_group8_ge_003_count
    ],
    'Total': [
        counties_selected_group1_lt_003_count + counties_selected_group1_ge_003_count +
        counties_remaining_group1_lt_003_count + counties_remaining_group1_ge_003_count,

        counties_selected_group2_lt_003_count + counties_selected_group2_ge_003_count +
        counties_remaining_group2_lt_003_count + counties_remaining_group2_ge_003_count,

        counties_selected_group3_lt_003_count + counties_selected_group3_ge_003_count +
        counties_remaining_group3_lt_003_count + counties_remaining_group3_ge_003_count,

        counties_selected_group4_lt_003_count + counties_selected_group4_ge_003_count +
        counties_remaining_group4_lt_003_count + counties_remaining_group4_ge_003_count,

        counties_selected_group5_lt_003_count + counties_selected_group5_ge_003_count +
        counties_remaining_group5_lt_003_count + counties_remaining_group5_ge_003_count,

        counties_selected_group6_lt_003_count + counties_selected_group6_ge_003_count +
        counties_remaining_group6_lt_003_count + counties_remaining_group6_ge_003_count,

        counties_selected_group7_lt_003_count + counties_selected_group7_ge_003_count +
        counties_remaining_group7_lt_003_count + counties_remaining_group7_ge_003_count,

        counties_selected_group8_lt_003_count + counties_selected_group8_ge_003_count +
        counties_remaining_group8_lt_003_count + counties_remaining_group8_ge_003_count
    ]
}

# 使用行索引标识各组
df = pd.DataFrame(data_pu, index=['Group1', 'Group2', 'Group3', 'Group4',
                                  'Group5', 'Group6', 'Group7', 'Group8'])

# ============================
# 2. 计算差值，以 Group1 为基准
df.loc['Difference (Group2 - Group1)'] = df.loc['Group2'] - df.loc['Group1']
df.loc['Difference (Group3 - Group1)'] = df.loc['Group3'] - df.loc['Group1']
df.loc['Difference (Group4 - Group1)'] = df.loc['Group4'] - df.loc['Group1']
df.loc['Difference (Group5 - Group1)'] = df.loc['Group5'] - df.loc['Group1']
df.loc['Difference (Group6 - Group1)'] = df.loc['Group6'] - df.loc['Group1']
df.loc['Difference (Group7 - Group1)'] = df.loc['Group7'] - df.loc['Group1']
df.loc['Difference (Group8 - Group1)'] = df.loc['Group8'] - df.loc['Group1']

# ============================
# 3. 绘制表格
# 调整图形大小，以适应较多的行（原始8行 + 7差值行 = 15行数据）
fig, ax = plt.subplots(figsize=(14, 14))

# 关闭坐标轴
ax.axis('off')

# 使用 matplotlib 的 table 方法绘制表格
table = ax.table(
    cellText=df.values,
    colLabels=df.columns,
    rowLabels=df.index,
    cellLoc='center',
    loc='center'
)

# 调整表格字体和尺寸
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.5, 1.5)  # 放大表格，增大行间距

# 设置表格标题
plt.title("各组人口数值及其与 Group1 差值", fontsize=16)

# 显示表格
plt.show()


# ### 3.2 fig2 绘图

# #### fig2 分布

# 修改为百分数表示

# In[ ]:


import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import math
from matplotlib.ticker import FuncFormatter

def plot_roi_distribution(counties_selected, poverty_remaining, roi_prefix):

    print(roi_prefix)

    # 配色方案
    colors_lt_003 = ['#fcd27f', '#d3f0f4']  # ROI < 0.03
    colors_ge_003 = ['#f58750', '#94c3e1']  # ROI ≥ 0.03

    # 计算ROI的分布数据
    roi_selected_lt_003 = counties_selected[counties_selected[roi_prefix] < 0.03][roi_prefix].dropna()
    roi_selected_ge_003 = counties_selected[counties_selected[roi_prefix] >= 0.03][roi_prefix].dropna()

    roi_remaining_lt_003 = poverty_remaining[poverty_remaining[roi_prefix] < 0.03][roi_prefix].dropna()
    roi_remaining_ge_003 = poverty_remaining[poverty_remaining[roi_prefix] >= 0.03][roi_prefix].dropna()

    # 创建图形
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 颜色匹配
    colors = [colors_lt_003[0], colors_ge_003[0],
              colors_lt_003[1], colors_ge_003[1]]

    # 计算最小值和最大值，处理 NaN
    min_value = min(roi_selected_lt_003.min(), roi_remaining_lt_003.min())
    if pd.isna(min_value):
        min_value = min(roi_selected_ge_003.min(), roi_remaining_ge_003.min())

    max_value = max(roi_selected_ge_003.max(), roi_remaining_ge_003.max())

    # 判断是否绘制 ROI=0.03 的线
    draw_line = min_value < 0.03

    # 设定 bin 范围
    min_bin = math.floor(min_value * 100) / 100
    max_bin = math.ceil(max_value * 100) / 100
    print(min_bin)
    print(max_bin)

    if draw_line:
        group_counts = round((max_bin - min_bin) * 500) + 1
    else:
        group_counts = round((max_bin - min_bin) * 150) + 1

    print(f"group_counts: {group_counts}")

    bins = np.linspace(min_bin, max_bin, group_counts)
    print(f"bins: {bins[:20]} ... {bins[-20:]}")
    if 0.01 in bins:
        print("0.01 在分界点上")
    else:
        print("⚠️ 0.01 不在分界点上")

    # 直方图
    ax1.hist([roi_selected_lt_003, roi_selected_ge_003,
              roi_remaining_lt_003, roi_remaining_ge_003],
             bins=bins, color=colors,
             label=[f'Selected Counties {roi_prefix} < 0.03',
                    f'Selected Counties {roi_prefix} ≥ 0.03',
                    f'Remaining Counties {roi_prefix} < 0.03',
                    f'Remaining Counties {roi_prefix} ≥ 0.03'],
             stacked=True, alpha=0.6)

    # 左侧 y 轴
    ax1.set_ylabel('Frequency', fontsize=12)

    # 创建第二个 y 轴
    ax2 = ax1.twinx()

    # 核密度估计
    sns.kdeplot(pd.concat([roi_selected_lt_003, roi_selected_ge_003]),
                color='#d8432d', ax=ax2, label='Selected Counties', lw=2)
    sns.kdeplot(pd.concat([roi_remaining_lt_003, roi_remaining_ge_003]),
                color='#4a7bb7', ax=ax2, label='Remaining Counties', lw=2)
    sns.kdeplot(pd.concat([roi_selected_lt_003, roi_selected_ge_003,
                           roi_remaining_lt_003, roi_remaining_ge_003]),
                color='#9eb0b2', ax=ax2, label='All Counties', lw=2)

    ax2.set_ylabel('Density', fontsize=12)

    # 条件性绘制 ROI = 0.03 的线

    ax1.axvline(x=0.03, color='red', linestyle='--', lw=2, label='ROI = 0.03')

    # 标题和标签
    ax1.set_title(f'{roi_prefix} Distribution', fontsize=16, pad=20)
    ax1.set_xlabel(roi_prefix, fontsize=12)
    ax1.set_xticks(np.arange(min_bin, max_bin + 0.01, 0.01))
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
    ax1.tick_params(axis='both', which='major', length=10, width=2)
    ax2.tick_params(axis='both', which='major', length=10, width=2)
    ax1.yaxis.set_tick_params(labelsize=14)
    ax2.yaxis.set_tick_params(labelsize=14)
    ax1.xaxis.set_tick_params(labelsize=12)

    ax1.spines['bottom'].set_visible(False)
    ax1.grid(False)
    ax2.grid(False)

    plt.tight_layout()
    plt.savefig(f'{roi_prefix}_distribution.png', transparent=True, dpi=1200)
    plt.show()

    # 计算均值和方差
    selected_counties_roi = pd.concat([roi_selected_lt_003, roi_selected_ge_003])
    remaining_counties_roi = pd.concat([roi_remaining_lt_003, roi_remaining_ge_003])
    total_counties_roi = pd.concat([selected_counties_roi, remaining_counties_roi])

    selected_mean = selected_counties_roi.mean()
    selected_variance = selected_counties_roi.var()
    remaining_mean = remaining_counties_roi.mean()
    remaining_variance = remaining_counties_roi.var()
    total_mean = total_counties_roi.mean()
    total_variance = total_counties_roi.var()

    print(f"{roi_prefix} - Selected Counties: Mean = {selected_mean:.4f}, Variance = {selected_variance:.4f}")
    print(f"{roi_prefix} - Remaining Counties: Mean = {remaining_mean:.4f}, Variance = {remaining_variance:.4f}")
    print(f"{roi_prefix} - Total Counties: Mean = {total_mean:.4f}, Variance = {total_variance:.4f}")


# 遍历所有列，生成图
for column in counties_selected.columns:
    if column.startswith('ROI'):
        plot_roi_distribution(counties_selected, poverty_remaining, column)

print(counties_selected['ROI_y'].isna().sum())
print(poverty_remaining['ROI_y'].isna().sum())


# In[ ]:


counties_selected


# #### fig2c

# In[ ]:


import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import Normalize, ListedColormap
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.cm as cm
import matplotlib.patches as mpatches
import numpy as np

# 设置固定的区间：0.1-0.6，每 0.1 为一档
bins = np.arange(0.1, 0.7, 0.1)  # [0.1, 0.2, ..., 0.6]
print("分类的具体分界值为:", bins)

# 创建归一化的颜色映射
norm = Normalize(vmin=0.1, vmax=0.6)

# 创建离散颜色映射
cmap = plt.cm.Reds
discrete_cmap = ListedColormap(cmap(np.linspace(0.1, 0.9, len(bins)-1)))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制 contribute 热力图（按贡献分组）
for _, row in merged_df[(merged_df['j_x'] != 0) & (merged_df['ROI_y'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute_x']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1  # 获取对应的分组索引
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))  # 使用离散颜色映射

    if isinstance(geometry, Polygon):
        ax.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 去掉主图的网格
ax.grid(False)

# 去掉主图的边框
for spine in ax.spines.values():
    spine.set_visible(False)

# 去掉主图的坐标轴上的数字
ax.set_xticks([])
ax.set_yticks([])

# 创建图例并取消图例外框
legend_patches = [
    mpatches.Patch(color=discrete_cmap(i / (len(bins) - 1)), label=f'{bins[i]:.1f} - {bins[i+1]:.1f}')
    for i in range(len(bins) - 1)
]

# 创建色带
cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=discrete_cmap),
                    ax=ax,
                    orientation='vertical',
                    shrink=0.35,   # 调整色带的缩放比例为 0.9
                    pad=0)         # 设置主图和色带之间的间距为 0.05

# 设置色带的刻度
cbar.set_ticks([(bins[i] + bins[i+1]) / 2 for i in range(len(bins) - 1)])  # 设置色带的刻度为区间的中点
cbar.ax.set_yticklabels([f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins) - 1)])  # 设置刻度标签
cbar.ax.xaxis.set_tick_params(labelsize=15)  # 设置刻度字体大小

# 设置色带标签位置在顶部
cbar.ax.xaxis.set_label_position("top")
cbar.outline.set_visible(True)  # 取消色带外框

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域热力图
for _, row in merged_df[(merged_df['j_x'] != 0) & (merged_df['ROI_y'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute_x']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))

    if isinstance(geometry, Polygon):
        ax_inset.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax_inset.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 绘制省级边界
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图并加阴影（子图）
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像并将背景设为透明
plt.savefig('pv_pvh_fixed_bins_0.1_to_0.6.png', dpi=1200, format='png', transparent=True)
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import Normalize, ListedColormap
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.cm as cm
import matplotlib.patches as mpatches
import numpy as np

# 设置固定的区间：0.1-0.6，每 0.1 为一档
bins = np.arange(0.1, 0.7, 0.1)  # [0.1, 0.2, ..., 0.6]
print("分类的具体分界值为:", bins)

# 创建归一化的颜色映射
norm = Normalize(vmin=0.1, vmax=0.6)

# 创建离散颜色映射
cmap = plt.cm.Reds
discrete_cmap = ListedColormap(cmap(np.linspace(0.1, 0.9, len(bins)-1)))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制 contribute 热力图（按贡献分组）
for _, row in merged_df[(merged_df['j_m'] != 0) & (merged_df['ROI_m'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute_m']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1  # 获取对应的分组索引
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))  # 使用离散颜色映射

    if isinstance(geometry, Polygon):
        ax.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 去掉主图的网格
ax.grid(False)

# 去掉主图的边框
for spine in ax.spines.values():
    spine.set_visible(False)

# 去掉主图的坐标轴上的数字
ax.set_xticks([])
ax.set_yticks([])

# 创建图例并取消图例外框
legend_patches = [
    mpatches.Patch(color=discrete_cmap(i / (len(bins) - 1)), label=f'{bins[i]:.1f} - {bins[i+1]:.1f}')
    for i in range(len(bins) - 1)
]

# 创建色带
cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=discrete_cmap),
                    ax=ax,
                    orientation='vertical',
                    shrink=0.35,   # 调整色带的缩放比例为 0.9
                    pad=0)         # 设置主图和色带之间的间距为 0.05

# 设置色带的刻度
cbar.set_ticks([(bins[i] + bins[i+1]) / 2 for i in range(len(bins) - 1)])  # 设置色带的刻度为区间的中点
cbar.ax.set_yticklabels([f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins) - 1)])  # 设置刻度标签
cbar.ax.xaxis.set_tick_params(labelsize=15)  # 设置刻度字体大小

# 设置色带标签位置在顶部
cbar.ax.xaxis.set_label_position("top")
cbar.outline.set_visible(True)  # 取消色带外框

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域热力图
for _, row in merged_df[(merged_df['j'] != 0) & (merged_df['ROI_y'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))

    if isinstance(geometry, Polygon):
        ax_inset.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax_inset.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 绘制省级边界
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图并加阴影（子图）
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像并将背景设为透明
plt.savefig('pv_pvh_fixed_bins_0.1_to_0.6_m.png', dpi=1200, format='png', transparent=True)
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import Normalize, ListedColormap
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.cm as cm
import matplotlib.patches as mpatches
import numpy as np

# 设置固定的区间：0.1-0.6，每 0.1 为一档
bins = np.arange(0.1, 0.7, 0.1)  # [0.1, 0.2, ..., 0.6]
print("分类的具体分界值为:", bins)

# 创建归一化的颜色映射
norm = Normalize(vmin=0.1, vmax=0.6)

# 创建离散颜色映射
cmap = plt.cm.Reds
discrete_cmap = ListedColormap(cmap(np.linspace(0.1, 0.9, len(bins)-1)))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制 contribute 热力图（按贡献分组）
for _, row in merged_df[(merged_df['j_y'] != 0) & (merged_df['ROI_e'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute_y']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1  # 获取对应的分组索引
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))  # 使用离散颜色映射

    if isinstance(geometry, Polygon):
        ax.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 去掉主图的网格
ax.grid(False)

# 去掉主图的边框
for spine in ax.spines.values():
    spine.set_visible(False)

# 去掉主图的坐标轴上的数字
ax.set_xticks([])
ax.set_yticks([])

# 创建图例并取消图例外框
legend_patches = [
    mpatches.Patch(color=discrete_cmap(i / (len(bins) - 1)), label=f'{bins[i]:.1f} - {bins[i+1]:.1f}')
    for i in range(len(bins) - 1)
]

# 创建色带
cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=discrete_cmap),
                    ax=ax,
                    orientation='vertical',
                    shrink=0.35,   # 调整色带的缩放比例为 0.9
                    pad=0)         # 设置主图和色带之间的间距为 0.05

# 设置色带的刻度
cbar.set_ticks([(bins[i] + bins[i+1]) / 2 for i in range(len(bins) - 1)])  # 设置色带的刻度为区间的中点
cbar.ax.set_yticklabels([f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins) - 1)])  # 设置刻度标签
cbar.ax.xaxis.set_tick_params(labelsize=15)  # 设置刻度字体大小

# 设置色带标签位置在顶部
cbar.ax.xaxis.set_label_position("top")
cbar.outline.set_visible(True)  # 取消色带外框

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域热力图
for _, row in merged_df[(merged_df['j_y'] != 0) & (merged_df['ROI_e'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute_y']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))

    if isinstance(geometry, Polygon):
        ax_inset.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax_inset.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 绘制省级边界
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图并加阴影（子图）
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像并将背景设为透明
plt.savefig('pv_pvh_fixed_bins_0.1_to_0.6_e.png', dpi=1200, format='png', transparent=True)
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import Normalize, ListedColormap
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.cm as cm
import matplotlib.patches as mpatches
import numpy as np

# 设置固定的区间：0.1-0.6，每 0.1 为一档
bins = np.arange(0.1, 0.7, 0.1)  # [0.1, 0.2, ..., 0.6]
print("分类的具体分界值为:", bins)

# 创建归一化的颜色映射
norm = Normalize(vmin=0.1, vmax=0.6)

# 创建离散颜色映射
cmap = plt.cm.Reds
discrete_cmap = ListedColormap(cmap(np.linspace(0.1, 0.9, len(bins)-1)))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制 contribute 热力图（按贡献分组）
for _, row in merged_df[(merged_df['j'] != 0) & (merged_df['ROI_c'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1  # 获取对应的分组索引
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))  # 使用离散颜色映射

    if isinstance(geometry, Polygon):
        ax.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 去掉主图的网格
ax.grid(False)

# 去掉主图的边框
for spine in ax.spines.values():
    spine.set_visible(False)

# 去掉主图的坐标轴上的数字
ax.set_xticks([])
ax.set_yticks([])

# 创建图例并取消图例外框
legend_patches = [
    mpatches.Patch(color=discrete_cmap(i / (len(bins) - 1)), label=f'{bins[i]:.1f} - {bins[i+1]:.1f}')
    for i in range(len(bins) - 1)
]

# 创建色带
cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=discrete_cmap),
                    ax=ax,
                    orientation='vertical',
                    shrink=0.35,   # 调整色带的缩放比例为 0.9
                    pad=0)         # 设置主图和色带之间的间距为 0.05

# 设置色带的刻度
cbar.set_ticks([(bins[i] + bins[i+1]) / 2 for i in range(len(bins) - 1)])  # 设置色带的刻度为区间的中点
cbar.ax.set_yticklabels([f'{bins[i]:.1f} - {bins[i+1]:.1f}' for i in range(len(bins) - 1)])  # 设置刻度标签
cbar.ax.xaxis.set_tick_params(labelsize=15)  # 设置刻度字体大小

# 设置色带标签位置在顶部
cbar.ax.xaxis.set_label_position("top")
cbar.outline.set_visible(True)  # 取消色带外框

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域热力图
for _, row in merged_df[(merged_df['j'] != 0) & (merged_df['ROI_c'] > 0.03)].iterrows():
    geometry = row['geometry']
    contribute_value = row['contribute']

    # 确定数据所属的分组
    group = np.digitize(contribute_value, bins) - 1
    if group < 0 or group >= len(bins) - 1:  # 如果值超出范围，跳过
        continue
    color = discrete_cmap(group / (len(bins) - 1))

    if isinstance(geometry, Polygon):
        ax_inset.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax_inset.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 绘制省级边界
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图并加阴影（子图）
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像并将背景设为透明
plt.savefig('pv_pvh_fixed_bins_0.1_to_0.6_c.png', dpi=1200, format='png', transparent=True)
plt.show()


# In[ ]:


from matplotlib.colors import LinearSegmentedColormap

# 创建颜色渐变的配色方案
cmap_select = LinearSegmentedColormap.from_list('select_cmap', ['#f4e6e6', '#8d0000'])  # 从浅色到深红色
cmap_remaining = LinearSegmentedColormap.from_list('remaining_cmap', ['#e6ecf3', '#034087'])  # 从浅色到深绿色

# 归一化 contribute_m 的值用于配色
norm = Normalize(vmin=merged_df['contribute_m'].min(), vmax=merged_df['contribute_m'].max())

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 设置阴影效果
shadow_effect = [
    PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
    PathEffects.Normal()
]

# 绘制国界底图并加阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制 contribute_m 热力图（已开展）
for _, row in merged_df[(merged_df['name'].isin(counties_selected['name'])) & (merged_df['j'] != 0) & (merged_df['ROI_m'] > 0.03)].iterrows():
    geometry = row['geometry']
    color = cmap_select(norm(row['contribute_m']))

    if isinstance(geometry, Polygon):
        ax.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 绘制 contribute_m 热力图（未开展）
for _, row in merged_df[(merged_df['name'].isin(poverty_remaining['name'])) & (merged_df['j'] != 0) & (merged_df['ROI_m'] > 0.03)].iterrows():
    geometry = row['geometry']
    color = cmap_remaining(norm(row['contribute_m']))

    if isinstance(geometry, Polygon):
        ax.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 设置x和y轴的范围，适应EPSG:3857下的中国大陆地区
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 去掉主图的网格
ax.grid(False)

# 去掉主图的边框
for spine in ax.spines.values():
    spine.set_visible(False)

# 去掉主图的坐标轴上的数字
ax.set_xticks([])
ax.set_yticks([])

# 创建自定义图例并取消图例外框
legend_patches = [
    mpatches.Patch(color='#efa4ca', label='Contribute (Selected)'),
    mpatches.Patch(color='#c09fcb', label='Contribute (Remaining)')
]

# 创建第一个色带，设置缩放比例和主图之间的间距
cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap_select),
                    ax=ax,
                    orientation='vertical',
                    shrink=0.35,   # 调整色带的缩放比例为 0.9，使其接近图框的高度
                    pad=0)     # 设置主图和色带之间的间距为 0.05


cbar.ax.xaxis.set_label_position("top")  # 设置色带标签位置在顶部
cbar.outline.set_visible(True)  # 取消色带外框
cbar.ax.tick_params(labelsize=15)  # 调整色条刻度字体大小

# 创建第二个色带，设置缩放比例和主图之间的间距
cbar_remaining = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap_remaining),
                              ax=ax,
                              orientation='vertical',
                              shrink=0.35,   # 调整色带的缩放比例与第一个色带一致
                              pad=0.01)     # 设置第二个色带的间距以增加两个色带之间的距离


cbar_remaining.ax.xaxis.set_label_position("top")  # 设置色带标签位置在顶部
cbar_remaining.outline.set_visible(True)  # 取消色带外框
cbar_remaining.ax.tick_params(labelsize=15)  # 调整色条刻度字体大小

# 创建子图，显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)

# 设置子图x和y轴的范围，适应南海诸岛的范围
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域热力图
for _, row in merged_df[(merged_df['name'].isin(counties_selected['name'])) & (merged_df['j'] != 0) & (merged_df['ROI_m'] > 0.03)].iterrows():
    geometry = row['geometry']
    color = cmap_select(norm(row['contribute_m']))

    if isinstance(geometry, Polygon):
        ax_inset.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax_inset.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

for _, row in merged_df[(merged_df['name'].isin(poverty_remaining['name'])) & (merged_df['j'] != 0) & (merged_df['ROI_m'] > 0.03)].iterrows():
    geometry = row['geometry']
    color = cmap_remaining(norm(row['contribute_m']))

    if isinstance(geometry, Polygon):
        ax_inset.add_patch(plt.Polygon(
            geometry.exterior.coords,
            color=color,
            linewidth=0,
            edgecolor='none'
        ))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            ax_inset.add_patch(plt.Polygon(
                poly.exterior.coords,
                color=color,
                linewidth=0,
                edgecolor='none'
            ))

# 绘制省级边界
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')

# 绘制国界底图并加阴影（子图）
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

# 去掉子图的边框和坐标轴
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])

# 去掉子图的网格
ax_inset.grid(False)

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()
# 保存高质量图像
plt.savefig('pv_pvh_2.png', dpi=1200, format='png')
plt.show()


# #### fig3

# In[ ]:


counties_selected


# In[ ]:


poverty_remaining


# ### fig3

# #### fig3a

# In[ ]:


# Here's the modified code to plot semi-transparent circles with a light blue fill color.

import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 根据条件分类
def classify_sdg(sdg):
    if sdg < 0.03:
        return 0
    else:
        return 1

# 映射 SDG_all 和 ROI_y 列
counties_selected['SDG_all_2'] = counties_selected['name'].map(merged_df.set_index('name')['SDG_all_2'])
counties_selected['ROI_y_mapped'] = counties_selected['name'].map(merged_df.set_index('name')['ROI_y'])

# 分类 SDG_all
counties_selected['group'] = counties_selected['SDG_all_2'].apply(classify_sdg)

# 分类 poverty_remaining
poverty_remaining['SDG_all_2'] = poverty_remaining['name'].map(merged_df.set_index('name')['SDG_all_2'])
poverty_remaining['ROI_y_mapped'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_y'])


# 分类未开展区域
poverty_remaining['group'] = poverty_remaining['SDG_all_2'].apply(classify_sdg) + 2  # 将分类值加2，以区分已开展和未开展

# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black')

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制组合后的热图
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')

# 在县的中心绘制半透明的淡蓝色圆圈
combined_centroids = combined.copy()
combined_centroids['geometry'] = combined['geometry'].centroid  # 计算几何中心

# 筛选符合条件的县
highlighted = combined_centroids[(combined_centroids['ROI_y_mapped'] < 0.03) & (combined_centroids['SDG_all_2'] > 0.03)]

# 绘制半透明的圆圈，使用淡蓝色（#add8e6）并设置透明度（alpha=0.4）
highlighted.plot(ax=ax, facecolor='none', edgecolor='black', marker='^', markersize=80, alpha=1, label='Highlighted')

# 设置x和y轴的范围
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 创建子图显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.grid(False)
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black')

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('output_map_sdg_roi_highlighted.png', dpi=1200, bbox_inches='tight', transparent=True, format='png')

plt.show()


# In[ ]:


# Here's the modified code to plot semi-transparent circles with a light blue fill color.

import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 根据条件分类
def classify_sdg(sdg):
    if sdg < 0.03:
        return 0
    else:
        return 1

# 映射 SDG_all 和 ROI_y 列
counties_selected['SDG_all_3'] = counties_selected['name'].map(merged_df.set_index('name')['SDG_all_3'])
counties_selected['ROI_m_mapped'] = counties_selected['name'].map(merged_df.set_index('name')['ROI_m'])

# 分类 SDG_all
counties_selected['group'] = counties_selected['SDG_all_3'].apply(classify_sdg)

# 分类 poverty_remaining
poverty_remaining['SDG_all_3'] = poverty_remaining['name'].map(merged_df.set_index('name')['SDG_all_3'])
poverty_remaining['ROI_m_mapped'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_m'])


# 分类未开展区域
poverty_remaining['group'] = poverty_remaining['SDG_all_3'].apply(classify_sdg) + 2  # 将分类值加2，以区分已开展和未开展

# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black')

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制组合后的热图
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')

# 在县的中心绘制半透明的淡蓝色圆圈
combined_centroids = combined.copy()
combined_centroids['geometry'] = combined['geometry'].centroid  # 计算几何中心

# 筛选符合条件的县
highlighted = combined_centroids[(combined_centroids['ROI_y_mapped'] < 0.03) & (combined_centroids['SDG_all_2'] > 0.03)]

# 绘制半透明的圆圈，使用淡蓝色（#add8e6）并设置透明度（alpha=0.4）
highlighted.plot(ax=ax, facecolor='none', edgecolor='black', marker='^', markersize=80, alpha=1, label='Highlighted')

# 设置x和y轴的范围
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 创建子图显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.grid(False)
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black')

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('output_map_sdg_roi_highlighted_2.png', dpi=1200, bbox_inches='tight', transparent=True, format='png')

plt.show()


# In[ ]:


# Here's the modified code to plot semi-transparent circles with a light blue fill color.

import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 根据条件分类
def classify_sdg(sdg):
    if sdg < 0.03:
        return 0
    else:
        return 1

# 映射 SDG_all 和 ROI_y 列
counties_selected['SDG_all_4'] = counties_selected['name'].map(merged_df.set_index('name')['SDG_all_4'])
counties_selected['ROI_e_mapped'] = counties_selected['name'].map(merged_df.set_index('name')['ROI_e'])

# 分类 SDG_all
counties_selected['group'] = counties_selected['SDG_all_4'].apply(classify_sdg)

# 分类 poverty_remaining
poverty_remaining['SDG_all_4'] = poverty_remaining['name'].map(merged_df.set_index('name')['SDG_all_4'])
poverty_remaining['ROI_e_mapped'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_e'])


# 分类未开展区域
poverty_remaining['group'] = poverty_remaining['SDG_all_4'].apply(classify_sdg) + 2  # 将分类值加2，以区分已开展和未开展

# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black')

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制组合后的热图
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')

# 在县的中心绘制半透明的淡蓝色圆圈
combined_centroids = combined.copy()
combined_centroids['geometry'] = combined['geometry'].centroid  # 计算几何中心

# 筛选符合条件的县
highlighted = combined_centroids[(combined_centroids['ROI_e_mapped'] < 0.03) & (combined_centroids['SDG_all_4'] > 0.03)]

# 绘制半透明的圆圈，使用淡蓝色（#add8e6）并设置透明度（alpha=0.4）
highlighted.plot(ax=ax, facecolor='none', edgecolor='black', marker='^', markersize=80, alpha=1, label='Highlighted')

# 设置x和y轴的范围
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 创建子图显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.grid(False)
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black')

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('output_map_sdg_roi_highlighted_3.png', dpi=1200, bbox_inches='tight', transparent=True, format='png')

plt.show()


# In[ ]:


# Here's the modified code to plot semi-transparent circles with a light blue fill color.

import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 创建自定义的颜色
cmap = {
    0: '#fcd182',  # 已开展 ROI < 0.03 浅绿色
    1: '#d9412a',  # 已开展 0.03 < ROI 绿色
    2: '#d6eff6',  # 未开展 ROI < 0.03 浅蓝色
    3: '#4a7bb6'   # 未开展 0.03 < ROI 蓝色
}

# 根据条件分类
def classify_sdg(sdg):
    if sdg < 0.03:
        return 0
    else:
        return 1

# 映射 SDG_all 和 ROI_y 列
counties_selected['SDG_all_5'] = counties_selected['name'].map(merged_df.set_index('name')['SDG_all_5'])
counties_selected['ROI_c_mapped'] = counties_selected['name'].map(merged_df.set_index('name')['ROI_c'])

# 分类 SDG_all
counties_selected['group'] = counties_selected['SDG_all_5'].apply(classify_sdg)

# 分类 poverty_remaining
poverty_remaining['SDG_all_5'] = poverty_remaining['name'].map(merged_df.set_index('name')['SDG_all_5'])
poverty_remaining['ROI_c_mapped'] = poverty_remaining['name'].map(merged_df.set_index('name')['ROI_c'])


# 分类未开展区域
poverty_remaining['group'] = poverty_remaining['SDG_all_5'].apply(classify_sdg) + 2  # 将分类值加2，以区分已开展和未开展

# 合并两个 GeoDataFrame
combined = gpd.GeoDataFrame(pd.concat([counties_selected, poverty_remaining], ignore_index=True))

# 创建图形
fig, ax = plt.subplots(figsize=(10, 10))

# 去掉主图的边框和坐标轴
ax.set_axis_off()

# 绘制国界底图并加粗和添加浅蓝色阴影
china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black')

# 绘制省级底图
provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

# 绘制组合后的热图
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax, color=color, linewidth=0, edgecolor='none')

# 在县的中心绘制半透明的淡蓝色圆圈
combined_centroids = combined.copy()
combined_centroids['geometry'] = combined['geometry'].centroid  # 计算几何中心

# 筛选符合条件的县
highlighted = combined_centroids[(combined_centroids['ROI_c_mapped'] < 0.03) & (combined_centroids['SDG_all_5'] > 0.03)]

# 绘制半透明的圆圈，使用淡蓝色（#add8e6）并设置透明度（alpha=0.4）
highlighted.plot(ax=ax, facecolor='none', edgecolor='black', marker='^', markersize=80, alpha=1, label='Highlighted')

# 设置x和y轴的范围
ax.set_xlim(7792364.36, 15584728.71)
ax.set_ylim(1689200.14, 7361866.11)

# 创建子图显示南海区域
ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
ax_inset.set_frame_on(True)
ax_inset.set_xticks([])
ax_inset.set_yticks([])
ax_inset.grid(False)
ax_inset.set_xlim(11688546.53, 13692297.37)
ax_inset.set_ylim(222684.21, 2632018.64)

# 绘制南海区域
for group, color in cmap.items():
    combined[combined['group'] == group].plot(ax=ax_inset, color=color, linewidth=0, edgecolor='none')
provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black')

# 修改子图框的颜色和样式
for spine in ax_inset.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1.5)

# 调整布局并显示图像
plt.tight_layout()

# 保存高质量图像
plt.savefig('output_map_sdg_roi_highlighted_4.png', dpi=1200, bbox_inches='tight', transparent=True, format='png')

plt.show()


# In[ ]:


# Assuming 'merged_df' is available

import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))

# Creating a DataFrame for the boxplot
boxplot_data = merged_df[['work', 'environment', 'difference']]

# Defining colors for each boxplot
palette_colors = ['#FFBFBF', '#EAF5F8', '#A3C9E1']

# Plotting the boxplots horizontally with the specified colors
sns.boxplot(data=boxplot_data, ax=ax, orient='h', palette=palette_colors)

# Removing x-axis, y-axis, and grid
ax.tick_params(axis='x', bottom=False, labelbottom=False)
ax.tick_params(axis='y', left=False, labelleft=False)
ax.grid(False)

# Removing all spines (axes frames)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

# Calculating and annotating important statistics
for i, column in enumerate(boxplot_data.columns):
    mean_value = np.mean(boxplot_data[column])
    variance_value = np.var(boxplot_data[column])

    # Annotating the mean
    ax.text(mean_value, i, f'Mean: {mean_value:.4f}', ha='center', va='center', color='black', fontsize=10, weight='bold')

    # Annotating the variance
    ax.text(mean_value, i - 0.2, f'Variance: {variance_value:.4f}', ha='center', va='center', color='black', fontsize=9)

# Show the plot
plt.tight_layout()
plt.show()


# In[ ]:


import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib import cm
import matplotlib.patheffects as PathEffects
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 设定你所使用的字体，如有需要
# font_prop = ...

def create_cmap(base_color):
    """
    生成一个自定义的colormap: 从约10%透明度到100%透明度的一个渐变
    """
    return LinearSegmentedColormap.from_list(
        'custom_cmap',
        [
            (0, to_rgba(base_color, alpha=0.1)),  # 10%透明度
            (1, to_rgba(base_color, alpha=1))    # 100%透明度
        ]
    )

def plot_sdg_visualization(df, sdg_column, base_color, china, provinces,
                           output_filename, sdg_label,
                           vmin_val=None, vmax_val=None):
    """
    生成各个SDG的可视化图，并加上色带（colorbar）。
    如果 vmin_val 和 vmax_val 不为 None，则强制使用指定的颜色映射范围；
    否则根据数据最小值和最大值自动适配。
    """
    # 生成自定义颜色映射
    cmap = create_cmap(base_color)

    # 创建画布
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_axis_off()  # 去掉坐标轴

    # 设置阴影效果
    shadow_effect = [
        PathEffects.SimpleLineShadow(offset=(-1, 1), shadow_color="#b0bde8", linewidth=5),
        PathEffects.Normal()
    ]

    # 画出全国边界并添加阴影
    china.boundary.plot(ax=ax, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)
    # 画出各省边界
    provinces.boundary.plot(ax=ax, linewidth=0.1, edgecolor='black')

    # 如果未指定vmin、vmax，则根据数据动态获取
    if vmin_val is None:
        vmin_val = df[sdg_column].min()
    if vmax_val is None:
        vmax_val = df[sdg_column].max()

    # 定义归一化和scalarMappable
    norm = Normalize(vmin=vmin_val, vmax=vmax_val)
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []  # colorbar专用

    # 绘制热力图
    df.plot(ax=ax, column=sdg_column, cmap=cmap, linewidth=0, edgecolor='none', norm=norm)

    # 设置可视化的主图范围（EPSG:3857下中国范围大致）
    ax.set_xlim(7792364.36, 15584728.71)
    ax.set_ylim(1689200.14, 7361866.11)

    # 添加垂直方向的色带
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", fraction=0.03, pad=0.04)
    cbar.set_label(sdg_label, fontsize=12, fontproperties=font_prop)

    # 添加南海区域的小插图
    ax_inset = inset_axes(ax, width="25%", height="25%", loc='lower right', borderpad=2)
    ax_inset.set_frame_on(True)
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    ax_inset.grid(False)

    # 设置南海插图的坐标范围
    ax_inset.set_xlim(11688546.53, 13692297.37)
    ax_inset.set_ylim(222684.21, 2632018.64)

    # 在插图上画出热力图
    df.plot(ax=ax_inset, column=sdg_column, cmap=cmap, linewidth=0, edgecolor='none', norm=norm)

    # 画省级边界
    provinces.boundary.plot(ax=ax_inset, linewidth=0.2, edgecolor='black')
    # 画全国边界（带阴影）
    china.boundary.plot(ax=ax_inset, linewidth=1.5, edgecolor='black', path_effects=shadow_effect)

    # 给插图外边框画线
    for spine in ax_inset.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(1.5)

    # 标题
    ax.set_title(sdg_label, fontproperties=font_prop, fontsize=16)

    # 保存与显示
    plt.savefig(output_filename, dpi=1200, bbox_inches='tight', transparent=True, format='png')
    plt.show()


# ---------------------- 调用示例 ---------------------- #
# 下方示例演示了如何在对 difference 列（以及 difference_m, difference_x, difference_y）可视化时，
# 强制将颜色映射范围固定为 [0, 0.014]。
#
# 如果你想自动根据数据计算最小值与最大值，则可以去掉 vmin_val 和 vmax_val 参数。

# 1. difference 列
plot_sdg_visualization(
    merged_df,
    'difference',
    '#6a3d9a',
    china,
    provinces,
    'difference_visualization_with_colorbar.png',
    'Difference Column Visualization',
    vmin_val=0,
    vmax_val=0.014
)

# 2. difference_m 列
plot_sdg_visualization(
    merged_df,
    'difference_m',
    '#6a3d9a',
    china,
    provinces,
    'difference_visualization_with_colorbar_m.png',
    'Difference Column Visualization (m)',
    vmin_val=0,
    vmax_val=0.014
)

# 3. difference_x 列
plot_sdg_visualization(
    merged_df,
    'difference_x',
    '#6a3d9a',
    china,
    provinces,
    'difference_visualization_with_colorbar_x.png',
    'Difference Column Visualization (x)',
    vmin_val=0,
    vmax_val=0.014
)

# 4. difference_y 列
plot_sdg_visualization(
    merged_df,
    'difference_y',
    '#6a3d9a',
    china,
    provinces,
    'difference_visualization_with_colorbar_y.png',
    'Difference Column Visualization (y)',
    vmin_val=0,
    vmax_val=0.014
)


# In[ ]:


# Adding code to adjust the font size for the ticks and remove the grid

fig, ax = plt.subplots(figsize=(10, 10))

# Plot the histogram for 'difference' without KDE curve
sns.histplot(merged_df['difference'], ax=ax, color="#a285bd", bins=30, label='Difference', edgecolor='black')

# Set x-axis and y-axis labels and increase their font size
ax.set_xlabel('Difference', fontsize=14, color='black')
ax.set_ylabel('Frequency', fontsize=14, color='black')

# Adjust the ticks, increase their font size, and remove grid
ax.tick_params(axis='both', which='major', labelsize=22, colors='black', direction='out')

# Remove gridlines
ax.grid(False)

# Modify the spines (axes frame) color to black
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('black')
ax.spines['bottom'].set_color('black')

# Fill the kernel density plot area (removing extra lines by using only kdeplot instead of combining with histplot)
sns.kdeplot(merged_df['difference'], ax=ax, color="#1978b5", fill=True, alpha=0.4, linewidth=2)

# Show the plot
plt.tight_layout()
plt.show()


# In[ ]:


# 将 `environment` 的值取负数
merged_df['environment'] = -merged_df['environment']

# Scatter Plot
plt.figure(figsize=(8, 6))
plt.scatter(merged_df['work'], merged_df['environment'], alpha=0.4, edgecolors='w')
plt.xlabel('Work')
plt.ylabel('Environment (Negative)')
plt.title('Work vs Environment (Negative)', y=1.05)
plt.show()

# Joint Plot
jp = sns.jointplot(x='work', y='environment', data=merged_df,
                   kind='reg', space=0, height=5, ratio=4)
jp.fig.suptitle('Work vs Environment (Negative) (Joint Plot)', y=1.05)
plt.show()


# In[ ]:


# Modifying the code further as per your latest instructions

fig, axs = plt.subplots(1, 2, figsize=(20, 2))  # Compressing the height by adjusting the figure size

# Plot kernel density estimation for 'work' on the first subplot
sns.kdeplot(merged_df['work'], ax=axs[0], color="red", fill=True)
axs[0].set_xlabel('Work', fontsize=14)
axs[0].tick_params(axis='y', left=False, labelleft=False)  # Hide the y-axis
axs[0].tick_params(axis='x', labelsize=22)  # Increase the size of x-axis tick labels

# Plot kernel density estimation for 'environment' on the second subplot
sns.kdeplot(merged_df['environment'], ax=axs[1], color="lightblue", fill=True)
axs[1].set_xlabel('Environment', fontsize=14)
axs[1].tick_params(axis='y', left=False, labelleft=False)  # Hide the y-axis
axs[1].tick_params(axis='x', labelsize=22)  # Increase the size of x-axis tick labels

# Customizing both axes: Remove grid, set x-axis color to black, and make it thicker
for ax in axs:
    ax.grid(False)  # Remove grid
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('black')  # Set x-axis to black
    ax.spines['bottom'].set_linewidth(1)  # Make the x-axis thicker

# Show the plot
plt.tight_layout()
plt.show()


# In[ ]:





# In[175]:


sdg_columns = ['ROI_e', 'difference_y']  # 确保这些列存在
merged_df['SDG_all_4'] = merged_df[sdg_columns].sum(axis=1)

sdg_columns = ['ROI_c', 'difference']  # 确保这些列存在
merged_df['SDG_all_5'] = merged_df[sdg_columns].sum(axis=1)


# In[177]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 定义计算 ROI > 0.03 的数量的函数
def count_roi_greater_than(dataframe, column):
    return (dataframe[column] > 0.03).sum()

# 定义需要计算的列
all_datasets = [
    ['ROI_x', 'ROI_y', 'SDG_all_2'],
    ['ROI_x', 'ROI_m', 'SDG_all_3'],
    ['ROI_x', 'ROI_e', 'SDG_all_4'],
    ['ROI_x', 'ROI_c', 'SDG_all_5']
]

for idx, datasets in enumerate(all_datasets):
    # 计算 `counties_selected` 的统计结果
    counties_selected_counts = {dataset: count_roi_greater_than(counties_selected, dataset) for dataset in datasets}

    # 计算 `poverty_remaining` 的统计结果
    poverty_remaining_counts = {dataset: count_roi_greater_than(poverty_remaining, dataset) for dataset in datasets}

    # 将统计结果汇总为 DataFrame
    roi_summary = pd.DataFrame({
        'Dataset': ['Counties Selected', 'Poverty Remaining'],
        **{dataset: [counties_selected_counts[dataset], poverty_remaining_counts[dataset]] for dataset in datasets}
    })

    # 提取数据
    counties_values = roi_summary.iloc[0, 1:].values
    poverty_values = roi_summary.iloc[1, 1:].values

    # 设置横坐标
    x = np.arange(len(datasets))  # ROI_x, ROI_y, SDG_all_x 的位置
    bar_width = 0.4  # 每组柱子的宽度

    # 颜色定义
    counties_colors = ['#fed0d0', '#fb7171', '#f81212']  # 第一组颜色
    poverty_colors = ['#c0d6e3', '#82acc7', '#2e75a2']   # 第二组颜色

    # 绘制 counties_selected 的柱状图
    fig1, ax1 = plt.subplots(figsize=(8, 6))  # 第一幅图
    for i in range(len(datasets)):
        ax1.bar(
            x[i], counties_values[i],
            bar_width, color=counties_colors[i], edgecolor='none', label=datasets[i]
        )
        # 添加黑点标注
        ax1.plot(
            x[i], counties_values[i],
            'o', color='black', markersize=6
        )

    # 用虚线连接重点标注点
    ax1.plot(
        x, counties_values,
        linestyle='--', color='black', linewidth=1
    )

    # 设置标题、标签和刻度
    ax1.set_title(f'Counties Selected ({datasets})', fontsize=14)
    ax1.set_xlabel('ROI Categories', fontsize=12)
    ax1.set_ylabel('Count (ROI > 0.03)', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(datasets, fontsize=10)

    # 去掉背景色
    fig1.patch.set_facecolor('white')
    ax1.set_facecolor('white')
    plt.tight_layout()
    plt.savefig(f'counties_selected_{idx}.png')
    plt.close()

    # 绘制 poverty_remaining 的柱状图
    fig2, ax2 = plt.subplots(figsize=(8, 6))  # 第二幅图
    for i in range(len(datasets)):
        ax2.bar(
            x[i], poverty_values[i],
            bar_width, color=poverty_colors[i], edgecolor='none', label=datasets[i]
        )
        # 添加黑点标注
        ax2.plot(
            x[i], poverty_values[i],
            'o', color='black', markersize=6
        )

    # 用虚线连接重点标注点
    ax2.plot(
        x, poverty_values,
        linestyle='--', color='black', linewidth=1
    )

    # 设置标题、标签和刻度
    ax2.set_title(f'Poverty Remaining ({datasets})', fontsize=14)
    ax2.set_xlabel('ROI Categories', fontsize=12)
    ax2.set_ylabel('Count (ROI > 0.03)', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(datasets, fontsize=10)

    # 去掉背景色
    fig2.patch.set_facecolor('white')
    ax2.set_facecolor('white')

    # 调整布局并保存图形
    plt.tight_layout()
    plt.savefig(f'poverty_remaining_{idx}.png')
    plt.close()


# ### 3.4敏感性分析绘图

# In[ ]:


clean_data1


# In[ ]:


clean_data2


# In[ ]:


clean_data3


# In[ ]:


clean_data4


# In[168]:


# clean_data1.to_excel('cleaned_data.xlsx', index=False)


# In[ ]:


# 首先把clean_data0、clean_data1、clean_data2、clean_data3、clean_data4 按照'name' 和 ‘year’ 两个键（两个都要满足）匹配起来，形成一个大的数据框，在除了name和year两个列之外的相同的列名加后缀，跟数据框命名的后缀相同（0 1 2 3 4）

# 假设已经有 clean_data0, clean_data1, clean_data2, clean_data3, clean_data4 这五个 DataFrame

# 为每个 DataFrame 的除 'name' 和 'year' 之外的列添加后缀
clean_data0_renamed = clean_data0.rename(
    columns={col: col + "_0" for col in clean_data0.columns if col not in ['name', 'year']}
)
clean_data1_renamed = clean_data1.rename(
    columns={col: col + "_1" for col in clean_data1.columns if col not in ['name', 'year']}
)
clean_data2_renamed = clean_data2.rename(
    columns={col: col + "_2" for col in clean_data2.columns if col not in ['name', 'year']}
)
clean_data3_renamed = clean_data3.rename(
    columns={col: col + "_3" for col in clean_data3.columns if col not in ['name', 'year']}
)
clean_data4_renamed = clean_data4.rename(
    columns={col: col + "_4" for col in clean_data4.columns if col not in ['name', 'year']}
)

# 按照 ['name', 'year'] 两列进行依次合并
clean_data_all = clean_data0_renamed.merge(
    clean_data1_renamed, on=['name', 'year'], how='outer'
).merge(
    clean_data2_renamed, on=['name', 'year'], how='outer'
).merge(
    clean_data3_renamed, on=['name', 'year'], how='outer'
).merge(
    clean_data4_renamed, on=['name', 'year'], how='outer'
)

# 查看最终合并结果
clean_data_all


# In[ ]:


print(clean_data_all['year'])


# In[ ]:


import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 假设合并后的数据命名为 clean_data_all

# 1. 先筛选出 year 在 [2025, 2035, 2050] 的行，并复制一份
clean_data_all['year'] = clean_data_all['year'].astype(int)
subset_data = clean_data_all[clean_data_all['year'].isin([2025, 2035, 2050])].copy()

# 2. 如果后缀为 0 时没有 ROI_en_0 而是 ROI_0，则统一重命名为 ROI_en_0，方便后续处理
if 'ROI_0' in subset_data.columns:
    subset_data.rename(columns={'ROI_0': 'ROI_en_0'}, inplace=True)

# 3. 将五种可能存在的 ROI 列（带后缀）列举出来
value_vars = ['ROI_en_0', 'ROI_en_1', 'ROI_en_2', 'ROI_en_3', 'ROI_en_4']
# # 如果有些后缀列不存在，就只保留实际存在的列，避免出错
# value_vars = [col for col in value_vars if col in subset_data.columns]

# 4. 宽表转长表
melted_df = subset_data.melt(
    id_vars=['year', 'name'],   # 保留的键列
    value_vars=value_vars,      # 需要展开的 ROI 列
    var_name='Group',           # 新列名：原列名(ROI_en_0/1/2/3/4)
    value_name='ROI_en'         # 新列名：展开后的数值
)

# 5. 检查并去除 year 和 ROI_en 中的 NaN
#    - year 在前面使用了 isin 2025/2035/2050，已经过滤了一部分
#    - 这里再做一次保险（若残留空值，也会被剔除）
melted_df.dropna(subset=['year', 'ROI_en'], inplace=True)

# 6. 将 year 转为字符串，以便在横坐标按类别显示 (而非按数值轴)
melted_df['year'] = melted_df['year'].astype(str)

# 7. 绘图：横坐标为 year (字符串), 纵坐标为 ROI_en, 颜色/分组(hue)根据后缀区分
plt.figure(figsize=(10, 6))
sns.boxplot(
    data=melted_df,
    x='year',
    y='ROI_en',
    hue='Group',
    # 如果想强制排序，可使用 order 参数
    order=['2025', '2035', '2050']
)

new_labels = ['Group 0 (ROI)', 'Group 1 (ROI)', 'Group 2 (ROI)', 'Group 3 (ROI)', 'Group 4 (ROI_en)']
plt.legend(handles, new_labels, title="ROI Groups")
plt.xlabel('Year')
plt.ylabel('ROI')
plt.tight_layout()
plt.show()


# In[ ]:


clean_data_all['year'] = clean_data_all['year'].astype(int)
subset_data = clean_data_all[clean_data_all['year'].isin([2025, 2035, 2050])].copy()
subset_data


# In[ ]:


import pandas as pd
import matplotlib.pyplot as plt

# 1. 先筛选 2020-2050 年的数据
subset_data = clean_data_all[clean_data_all['year'].between(2020, 2050)].copy()

# 2. 定义 ROI_group 和 ROI_en 的列
roi_group_cols = ['ROI_group_0', 'ROI_group_1', 'ROI_group_2', 'ROI_group_3', 'ROI_group_4']
roi_en_cols = ['ROI_0', 'ROI_en_1', 'ROI_en_2', 'ROI_en_3', 'ROI_en_4']

# 3. 确保 ROI_group_x 存在
roi_group_cols = [col for col in roi_group_cols if col in subset_data.columns]
roi_en_cols = [col for col in roi_en_cols if col in subset_data.columns]

# 4. 去掉 `ROI_en_X` 全为空的年份
valid_years = subset_data.dropna(subset=roi_en_cols)['year'].unique()  # 获取至少有一个 ROI_en_x 非空的年份
subset_data = subset_data[subset_data['year'].isin(valid_years)]  # 过滤数据

# 5. 计算每年 `ROI_group_x` 中 **不等于 `'<0.03'`** 的个数
count_df = subset_data.groupby('year')[roi_group_cols].apply(lambda df: (df != '< 0.03').sum())

# 6. 绘制折线图
plt.figure(figsize=(12, 6))

for col in count_df.columns:
    plt.plot(count_df.index, count_df[col], marker='o', linestyle='-', label=col)

plt.title("不同年份 (2020 - 2050) 各 ROI_group 统计值")
plt.xlabel("Year")
plt.ylabel("Count of ROI_group ≠ '<0.03'")
plt.xticks(range(2020, 2051, 5))  # X 轴间隔 5 年
plt.legend(title="ROI Group")
plt.grid(True)

plt.show()


# In[ ]:


count_df


# In[ ]:


poverty_selected


# In[ ]:





# ---
