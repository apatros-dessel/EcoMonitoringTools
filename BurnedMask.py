import os, math, time, sys
import osr, ogr, gdal
from gdalconst import GA_ReadOnly, GRA_Cubic, GDT_Byte, GDT_UInt16, GDT_Float32
import numpy as np
import cv2
import vector_lib


input_image='c:\\CHANGE\\20140724_30m_L8_6b.TIF'
min_area=10 #hectare
index_value=0.1
output_shapefile=''
output_imagefile=''

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

def BurnedMask(input_image, index_value, min_area, output_shapefile='', output_imagefile=''):
    np.seterr(divide='ignore', invalid='ignore')
    image_ds=gdal.Open ( input_image, GA_ReadOnly )
    if image_ds is not None: 
        if image_ds.RasterCount<6:
            print 'Need image with more than 5 bands '
            print 'Need GREEN, NIR, SWIR1 and  SWIR2'
        else:
            dir_name=os.path.dirname(input_image)
            file_name=os.path.basename(input_image).split('.')[0]
            image_metadata=ImageMetadata(file_name)
            if image_metadata['sensor'] in ['L5','L7','L8']:
                if output_shapefile=='':output_shapefile=os.path.join(dir_name, file_name+'_burned_mask.SHP')
                if output_imagefile=='':output_imagefile=os.path.join(dir_name, file_name+'_%s.TIF')   
                fieldnames=["DATA", "SENSOR", "IMG_FILE", "AREA"]
                fields={"DATA":('string',8), "SENSOR":('string',5), "IMG_FILE":('string',64), "AREA":('float',6,2)}
                fields_value={"DATA":image_metadata['date'], "SENSOR":image_metadata['sensor'], "IMG_FILE":input_image, "AREA":None}
                band_data_green=image_ds.GetRasterBand(2).ReadAsArray().astype(np.int16)
                band_data_red=image_ds.GetRasterBand(3).ReadAsArray().astype(np.int16)
                band_data_swir1=image_ds.GetRasterBand(5).ReadAsArray().astype(np.int16)
                band_data_nir=image_ds.GetRasterBand(4).ReadAsArray().astype(np.float32)
                band_data_swir2=image_ds.GetRasterBand(6).ReadAsArray().astype(np.float32)
                nbr1=band_data_nir-band_data_swir2
                nbr2=band_data_nir+band_data_swir2
                indxZeros=np.where(nbr2==0)
                indxNonZeros=np.where(nbr2!=0)
                nbr=np.empty(nbr2.shape)
                nbr[indxZeros]=0
                nbr[indxNonZeros]=nbr1[indxNonZeros]/nbr2[indxNonZeros]
                indxZeros=np.where(nbr>=index_value)
                indxNonZeros=np.where(nbr<index_value)
                nbr[indxZeros]=0
                nbr[indxNonZeros]=255
                indxZeros=np.where(nbr2==0)
                nbr = cv2.GaussianBlur(nbr.astype(np.uint8),(5,5),0)
                nbr[nbr<60]=0
                nbr[nbr>=60]=255
                indxZeros=np.where(band_data_green==0)
                nbr[indxZeros]=0
                indxZeros=np.where(band_data_red==0)
                nbr[indxZeros]=0
                if min_area=='':min_area=60*image_ds.GetGeoTransform()[1]*image_ds.GetGeoTransform()[1]
                image753_ds = gdal.GetDriverByName("GTiff").Create( output_imagefile % ('753') , image_ds.RasterXSize, image_ds.RasterYSize,  3, GDT_UInt16)
                image542_ds = gdal.GetDriverByName("GTiff").Create( output_imagefile % ('542') , image_ds.RasterXSize, image_ds.RasterYSize,  3, GDT_UInt16)
                image753_ds.SetGeoTransform( image_ds.GetGeoTransform() )
                image753_ds.SetProjection( image_ds.GetProjection() )
                image753_ds.GetRasterBand(1).WriteArray(band_data_swir2.astype(np.int16))
                image753_ds.GetRasterBand(2).WriteArray(band_data_swir1.astype(np.int16))
                image753_ds.GetRasterBand(3).WriteArray(band_data_red.astype(np.int16))
                image753_ds=None
                image542_ds.SetGeoTransform( image_ds.GetGeoTransform() )
                image542_ds.SetProjection( image_ds.GetProjection() )
                image542_ds.GetRasterBand(1).WriteArray(band_data_swir1.astype(np.int16))
                image542_ds.GetRasterBand(2).WriteArray(band_data_nir.astype(np.int16))
                image542_ds.GetRasterBand(3).WriteArray(band_data_green.astype(np.int16))
                image542_ds=None
                vector_lib.Raster2VectorP(image_ds, nbr, output_shapefile+'_p.shp', fieldnames, fields, fields_value, min_area)
                vector_lib.Raster2VectorM(image_ds, nbr, output_shapefile+'_m.shp', fieldnames, fields, fields_value, min_area)
                if os.path.exists(output_shapefile):
                    return {'status':'OK', 'shp':output_shapefile} 
                else: return {'status':'ERROR', 'shp':''} 
    else:
        return {'status':'ERROR', 'shp':''}      
    
result = BurnedMask(input_image, index_value, min_area, output_shapefile, output_imagefile)
print result
