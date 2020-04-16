import os, math, time, sys
import osr, ogr, gdal
from gdalconst import GA_ReadOnly, GRA_Cubic, GDT_Byte, GDT_UInt16, GDT_Float32
import numpy as np
import cv2
import vector_lib


input_image='c:\\CHANGE\\20140724_30m_L8_6b.TIF'
min_area=1 #hectare
index_value=0.0
output_shapefile=''

def ImageMetadata(filename):
    metadata={'date':'','year':'','month':'','day':'','ps':'','sensor':'','numbands':''}
    temp=filename.split('_')
    metadata['date']=temp[0]
    metadata['year']=metadata['date'][:4]
    metadata['month']=metadata['date'][4:6]
    metadata['day']=metadata['date'][6:]
    metadata['ps']=temp[1]
    metadata['sensor']=temp[2]
    metadata['numbands']=temp[3].replace('b','')
    return metadata

def WaterMask(input_image, index_value, min_area, output_shapefile=''):
    np.seterr(divide='ignore', invalid='ignore')
    image_ds=gdal.Open ( input_image, GA_ReadOnly )
    if image_ds is not None: 
        if image_ds.RasterCount<3:
            print 'Need image with more than 3 bands '
            print 'Need GREEN and NIR '
        else:
            dir_name=os.path.dirname(input_image)
            file_name=os.path.basename(input_image).split('.')[0]
            image_metadata=ImageMetadata(file_name)
            if output_shapefile=='':output_shapefile=os.path.join(dir_name, file_name+'_water_mask.SHP')
            fieldnames=["DATA", "SENSOR", "IMG_FILE", "AREA"]
            fields={"DATA":('string',8), "SENSOR":('string',5), "IMG_FILE":('string',64), "AREA":('float',6,2)}
            fields_value={"DATA":image_metadata['date'], "SENSOR":image_metadata['sensor'], "IMG_FILE":input_image, "AREA":None}
            #water_mask=np.zeros((image_ds.RasterYSize, image_ds.RasterXSize), dtype=np.int8)
            if image_metadata['sensor'] in ['L5','L7','L8','QB', 'GE', 'IK', 'WV2']:
                band_data_nir=image_ds.GetRasterBand(4).ReadAsArray().astype(np.float32)
                band_data_green=image_ds.GetRasterBand(2).ReadAsArray().astype(np.float32)
            elif image_metadata['sensor'] =='RE':
                band_data_nir=image_ds.GetRasterBand(5).ReadAsArray().astype(np.float32)
                band_data_green=image_ds.GetRasterBand(2).ReadAsArray().astype(np.float32)
            ndwi=(band_data_green-band_data_nir)/(band_data_green+band_data_nir)
            ndwi[ndwi>index_value]=255
            ndwi[ndwi<=index_value]=0
            ndwi = cv2.GaussianBlur(ndwi.astype(np.uint8),(5,5),0)
            ndwi[ndwi<60]=0
            ndwi[ndwi>=60]=255
            if min_area=='':min_area=6*image_ds.GetGeoTransform()[1]*image_ds.GetGeoTransform()[1]
            vector_lib.Raster2VectorP(image_ds, ndwi, output_shapefile, fieldnames, fields, fields_value, min_area)
            #vector_lib.Raster2VectorM(image_ds, ndwi, output_shapefile+'_m.shp', fieldnames, fields, fields_value, min_area)
            if os.path.exists(output_shapefile):
                return {'status':'OK', 'shp':output_shapefile} 
            else: return {'status':'ERROR', 'shp':''} 
    else:
        return {'status':'ERROR', 'shp':''}      
    
result = WaterMask(input_image, index_value, min_area, output_shapefile)
print result
