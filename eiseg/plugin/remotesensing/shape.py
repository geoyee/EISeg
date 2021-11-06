import os.path as osp
from collections import defaultdict
import numpy as np
from .rstools import check_gdal


IPT_GDAL = check_gdal()
if IPT_GDAL:
    try:
        import gdal
        import osr
        import ogr
    except:
        from osgeo import gdal, osr, ogr


def convert_coord(point, g):
    tform = np.zeros((3, 3))
    tform[0, :] = np.array([g[1], g[2], g[0]])
    tform[1, :] = np.array([g[4], g[5], g[3]])
    tform[2, :] = np.array([0, 0, 1])
    olp = np.ones((1, 3))
    olp[0, :2] = np.array(point)
    nwp = np.dot(tform, olp.T)
    return nwp.T[0, :2]


def bound2wkt(bounds, tform):
    geo_list = []
    for bd in bounds:
        gl = defaultdict()
        gl["clas"] = bd["name"]
        gl["polygon"] = "Polygon (("
        p = bd["points"]
        for i in range(len(p)):
            x, y = convert_coord(p[i], tform)
            gl["polygon"] += (str(x) + " " + str(y)) + ","
        gl["polygon"] = gl["polygon"][:-1] + "))"
        geo_list.append(gl)
    return geo_list


def save_shp(shp_path, geocode_list, geo_info):
    if IPT_GDAL == True:
        # 支持中文路径
        gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
        # 属性表字段支持中文
        gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
        # 注册驱动
        ogr.RegisterAll()
        # 创建shp数据
        strDriverName = "ESRI Shapefile"
        oDriver = ogr.GetDriverByName(strDriverName)
        if oDriver == None:
            return "驱动不可用：" + strDriverName
        # 创建数据源
        oDS = oDriver.CreateDataSource(shp_path)
        if oDS == None:
            return "创建文件失败：" + shp_path
        # 创建一个多边形图层
        geosrs = osr.SpatialReference()
        # TODO：geo_info格式不统一，怎么解析，需要多看一点数据，目前默认使用WGS84
        geosrs.SetWellKnownGeogCS("WGS84")  # (geo_info)
        ogr_type = ogr.wkbPolygon
        shpe_name = osp.splitext(osp.split(shp_path)[-1])[0]
        oLayer = oDS.CreateLayer(shpe_name, geosrs, ogr_type)
        if oLayer == None:
            return "图层创建失败！"
        # 创建属性表
        # 创建id字段
        oId = ogr.FieldDefn("id", ogr.OFTInteger)
        oLayer.CreateField(oId, 1)
        # 创建字段
        oAddress = ogr.FieldDefn("clas", ogr.OFTString)
        oLayer.CreateField(oAddress, 1)
        oDefn = oLayer.GetLayerDefn()
        # 创建要素
        # 数据集
        for index, f in enumerate(geocode_list):
            oFeaturePolygon = ogr.Feature(oDefn)
            oFeaturePolygon.SetField("id", index)
            oFeaturePolygon.SetField("clas", f["clas"])
            geomPolygon = ogr.CreateGeometryFromWkt(f["polygon"])
            oFeaturePolygon.SetGeometry(geomPolygon)
            oLayer.CreateFeature(oFeaturePolygon)
        # 创建完成后，关闭进程
        oDS.Destroy()
        return "数据集创建完成！"
    else:
        raise ImportError('can\'t import gdal, osr, ogr!')


# test
if __name__ == "__main__":
    from rstools import open_tif

    tif_path = r"C:\Users\Geoyee\Desktop\jpg1.tif"
    img, geo_info = open_tif(tif_path)
    print("proj:", geo_info["proj"])
    # shp_path = r"E:\PdCVSIG\github\images\test.shp"
    # geocode_list = [
    #     {"clas": "build1", "polygon": "Polygon ((1 1,5 1,5 5,1 5,1 1))"},
    #     {"clas": "build2", "polygon": "Polygon ((6 3,9 2,9 4,6 3))"},
    #     ]
    # save_shp(shp_path, geocode_list, geo_info["proj"])
