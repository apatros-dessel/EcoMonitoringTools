import os, math, time, subprocess, sys
import osr, ogr, gdal
from gdalconst import GA_ReadOnly, GRA_Cubic, GDT_Byte, GDT_UInt16, GDT_Float32
import numpy as np
from PIL import Image
import cv2
import vector_lib


input_image='c:\\CHANGE\\20140724_30m_L8_6b.TIF'
min_countur_area=6
red=[100, 500]
nir=[1000, 3100]
output_shapefile=''
output_cirfile=''

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

def ForestMask(input_image, red=[100, 500], nir=[1000, 3100], output_shapefile='', output_cirfile=''):
    image_ds=gdal.Open ( input_image, GA_ReadOnly )
    if image_ds is not None: 
        if image_ds.RasterCount<3:
            print 'Need image with more than 3 bands '
            print 'Need RED and NIR '
        else:
            dir_name=os.path.dirname(input_image)
            file_name=os.path.basename(input_image).split('.')[0]
            image_metadata=ImageMetadata(file_name)
            if output_shapefile=='':output_shapefile=os.path.join(dir_name, file_name+'_forest_mask.SHP')
            if output_cirfile=='':output_cirfile=os.path.join(dir_name, file_name+'_CIR.TIF')
            fieldnames=["DATA", "SENSOR", "IMG_FILE", "AREA"]
            fields={"DATA":('string',8), "SENSOR":('string',5), "IMG_FILE":('string',64), "AREA":('float',6,2)}
            fields_value={"DATA":image_metadata['date'], "SENSOR":image_metadata['sensor'], "IMG_FILE":input_image, "AREA":None}
            forest_mask=np.ones((image_ds.RasterYSize, image_ds.RasterXSize), dtype=np.int8)
            if image_metadata['sensor'] in ['L5','L7','L8','QB', 'GE', 'IK', 'WV2']:
                band_data_nir=image_ds.GetRasterBand(4).ReadAsArray().astype(np.int16)
                band_data_red=image_ds.GetRasterBand(3).ReadAsArray().astype(np.int16)
            elif image_metadata['sensor'] =='RE':
                band_data_nir=image_ds.GetRasterBand(5).ReadAsArray().astype(np.int16)
                band_data_red=image_ds.GetRasterBand(3).ReadAsArray().astype(np.int16)
            forest_mask[band_data_nir<nir[0]]=0
            forest_mask[band_data_nir>nir[1]]=0
            forest_mask[band_data_red<red[0]]=0
            forest_mask[band_data_red>red[1]]=0
            forest_mask[forest_mask==1]=255
            forest_mask = cv2.GaussianBlur(forest_mask.astype(np.uint8),(5,5),0)
            forest_mask[forest_mask<60]=0
            forest_mask[forest_mask>=60]=255
            print image_metadata
            cir_image_ds = gdal.GetDriverByName("GTiff").Create( output_cirfile , image_ds.RasterXSize, image_ds.RasterYSize,  3, GDT_UInt16)
            cir_image_ds.SetGeoTransform( image_ds.GetGeoTransform() ) 
            cir_image_ds.SetProjection( image_ds.GetProjection() ) 
            cir_image_ds.GetRasterBand(1).WriteArray(band_data_nir.astype(np.int16))
            cir_image_ds.GetRasterBand(2).WriteArray(band_data_red.astype(np.int16))
            cir_image_ds.GetRasterBand(3).WriteArray(image_ds.GetRasterBand(2).ReadAsArray().astype(np.int16))
            cir_image_ds=None
            min_area=min_countur_area*image_ds.GetGeoTransform()[1]*image_ds.GetGeoTransform()[1]
            vector_lib.Raster2VectorP(image_ds, forest_mask, output_shapefile+'_p.shp', fieldnames, fields, fields_value, min_area)
            vector_lib.Raster2VectorM(image_ds, forest_mask, output_shapefile+'_m.shp', fieldnames, fields, fields_value, min_area)
            if os.path.exists(output_cirfile) and os.path.exists(output_shapefile):
                return {'status':'OK', 'shp':output_shapefile, 'cir_img':output_cirfile} 
            else: return {'status':'ERROR', 'shp':'', 'cir_img':''} 
    else:
        return {'status':'ERROR', 'shp':'', 'cir_img':''}      
    
result = ForestMask(input_image, red, nir, output_shapefile, output_cirfile)
print result