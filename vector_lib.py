import os
import gdal
import ogr
import osr
import gdalconst
import cv2
import numpy as np

#EXAMPLE
#CREATE NEW OBJECT
#new_shape = ShapeFileWriter(shapefile='c:\\projects\\test7.shp',\
#                             fieldnames=["Name","DateTime","Image","Area"],\
#                             fields={"Name":('string',25),"DateTime":('string',20),"Image":('string',20),"Area":('float',6,2)},\
#                             srs_wkt=None,update=False)
#geom=GeomFromExtent([67,55,68,54])
#ADD NEW POLYGON AND METADATA TO SHAPEFILE
#new_shape.WriteRecord(geom.ExportToWkt(),attributes={"Name":'Test',"DateTime":'20141015',"Image":'Landsat',"Area":2.666})
#CLOSE OBJECT
#new_shape=None
#geom=None

def Raster2VectorP(gdal_dataset, input_binary_image, output_shape, fieldnames, fields,fields_value, min_area):
    if cv2.__version__[0]<'3': contours, hierarchy = cv2.findContours(input_binary_image.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    else: image, contours, hierarchy = cv2.findContours(input_binary_image.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    newshp = ShapeFileWriter(shapefile=output_shape,fieldnames=fieldnames, fields=fields, srs_wkt=gdal_dataset.GetProjection())
    for contour in contours:
        if len(contour)>3:
            wkt=[]
            for point in contour:
                wkt.append('%s %s' % (gdal_dataset.GetGeoTransform()[0]+point[0][0]*gdal_dataset.GetGeoTransform()[1]+float(gdal_dataset.GetGeoTransform()[1])/2,\
                                      gdal_dataset.GetGeoTransform()[3]+point[0][1]*gdal_dataset.GetGeoTransform()[5]+float(gdal_dataset.GetGeoTransform()[5])/2))
            wkt.append(wkt[0])
            wkt='POLYGON ((%s))' % ','.join(wkt)
            src_srs = osr.SpatialReference()
            src_srs.ImportFromWkt(gdal_dataset.GetProjection())
            geom=ogr.CreateGeometryFromWkt(wkt, src_srs)
            if geom.GetArea() > min_area:
                fields_value["AREA"]=geom.GetArea()/10000
                newshp.WriteRecord(geom.ExportToWkt(),attributes=fields_value)
    newshp=None
    geom=None
       
def Raster2VectorM(gdal_dataset, input_binary_image, output_shape, fieldnames, fields, fields_value, min_area):
    if cv2.__version__[0]<'3': contours, hierarchy = cv2.findContours(input_binary_image.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    else: image, contours, hierarchy = cv2.findContours(input_binary_image.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    newshp = ShapeFileWriter(shapefile=output_shape,fieldnames=fieldnames, fields=fields, srs_wkt=gdal_dataset.GetProjection())
    multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
    for contour in contours:
        if len(contour)>3:
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for point in contour:
                ring.AddPoint(gdal_dataset.GetGeoTransform()[0]+point[0][0]*gdal_dataset.GetGeoTransform()[1]+float(gdal_dataset.GetGeoTransform()[1])/2,\
                              gdal_dataset.GetGeoTransform()[3]+point[0][1]*gdal_dataset.GetGeoTransform()[5]+float(gdal_dataset.GetGeoTransform()[5])/2)
            if contour[0][0][0]!=contour[len(contour)-1][0][0] or contour[0][0][1]!=contour[len(contour)-1][0][1]:
                ring.AddPoint(gdal_dataset.GetGeoTransform()[0]+contour[0][0][0]*gdal_dataset.GetGeoTransform()[1]+float(gdal_dataset.GetGeoTransform()[1])/2,\
                              gdal_dataset.GetGeoTransform()[3]+contour[0][0][1]*gdal_dataset.GetGeoTransform()[5]+float(gdal_dataset.GetGeoTransform()[5])/2)
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)
            if poly.GetArea() > min_area:
                multipolygon.AddGeometry(poly)
    fields_value["AREA"]=multipolygon.GetArea()/10000       
    newshp.WriteRecord(multipolygon.ExportToWkt(),attributes=fields_value)
    newshp=None
    geom=None
    
# vector_lib.Raster2VectorP(image_ds, forest_mask, output_shapefile, fieldnames, fields, min_area)
#             fieldnames=["DATA", "SENSOR", "IMG_FILE", "AREA"]
#             fields={"DATA":('string',8), "SENSOR":('string',5), "DATA":('IMG_FILE',64), "AREA":('float',6,2)}
def encode(string):
    ''' Encode a unicode string
        @type     string:  C{unicode}
        @param    string:  Unicode string
        @rtype:   C{str}
        @return:  Encoded string
    '''
    if type(string) is unicode:return string.encode('utf-8')
    else:return string

def GeomFromExtent(ext,srs=None,srs_wkt=None):
    ''' Get and OGR geometry object from a extent list
        @type ext:  C{tuple/list}
        @param ext: extent coordinates
        @type srs:  C{str}
        @param srs: SRS WKT string
        @rtype:     C{ogr.Geometry}
        @return:    Geometry object
    '''
    if type(ext[0]) in [list, tuple]: #is it a list of xy pairs
        if ext[0] != ext[-1]:ext.append(ext[0])
        wkt = 'POLYGON ((%s))' % ','.join(map(' '.join, [map(str, i) for i in ext]))
    else: #it's a list of xy values
        xmin,ymin,xmax,ymax=ext
        template = 'POLYGON ((%(minx)f %(miny)f, %(minx)f %(maxy)f, %(maxx)f %(maxy)f, %(maxx)f %(miny)f, %(minx)f %(miny)f))'
        r1 = {'minx': xmin, 'miny': ymin, 'maxx':xmax, 'maxy':ymax}
        wkt = template % r1    
    if srs_wkt is not None:srs=osr.SpatialReference(wkt=srs_wkt)
    geom = ogr.CreateGeometryFromWkt(wkt,srs)
    return geom

def GeomFromImageFile(ifilename, outputEPSG):
    ''' Get OGR geometry object from a file
        @type ifilename:  C{str}
        @param ifilename: Input raster image
        @type outputEPSG:  C{int}
        @param outputEPSG: EPSG code
        @rtype:     C{ogr.Geometry}
        @return:    Geometry object
    '''
    ds = gdal.Open(ifilename)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5] 
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3]
    template = 'POLYGON ((%(minx)f %(miny)f, %(minx)f %(maxy)f, %(maxx)f %(maxy)f, %(maxx)f %(miny)f, %(minx)f %(miny)f))'
    r1 = {'minx': minx, 'miny': miny, 'maxx':maxx, 'maxy':maxy}
    wkt = template % r1
    src_srs = osr.SpatialReference()
    src_srs.ImportFromWkt(ds.GetProjectionRef())
    tgt_srs = osr.SpatialReference()
    tgt_srs.ImportFromEPSG(outputEPSG)
    geom = ogr.CreateGeometryFromWkt(wkt,src_srs)#geom.AssignSpatialReference(src_srs)
    geom.TransformTo(tgt_srs)
    ds=width=height=gt=minx=miny=maxx=maxy=src_srs=tgt_srs=None
    return geom

def ExtentFromWKTpolygon(WKTpolygon, bbox=False):
    ''' Get a extent list (Full or Bbox) from a WKT polygon
        @type WKTpolygon:  C{str}
        @param WKTpolygon: SRS WKT string
        @type bbox:  C{boolean}
        @param bbox: SRS WKT string
        @rtype:     Full coordinates list or bbox only
        @return:    Extent coordinates list 
    '''
    geomtype, points = WKTpolygon.split(None, 1)
    xlist=[]
    ylist=[]
    extent=[]
    if geomtype == 'POLYGON':
        for point in points.strip('()').split(','):
            if bbox:
                xlist.append(float(point.split()[0]))
                ylist.append(float(point.split()[1]))
                extent=[min(xlist),min(ylist),max(xlist),max(ylist)]
            else:
                extent.append([float(point.split()[0]),float(point.split()[1])])          
        xlist=ylist=None
        return extent  
    
#========================================================================================================
#{Shapefile Writer (Metageta + My Edition)
#========================================================================================================
class ShapeFileWriter:
    '''A class for writing geometry and fields to ESRI shapefile format'''
    def __init__(self,shapefile,fieldnames=[], fields={},srs_wkt=None,update=False):
        ''' Open the shapefile for writing or appending.
            @type shapefile:  C{gdal.Dataset}
            @param shapefile: Dataset object
            @type fields:     C{list}
            @param fields:    L{Fields order list}
            @type fields:     C{dict}
            @param fields:    L{Fields dict<formats.fields>}
            @type srs_wkt:    C{str}
            @param srs_wkt:   Spatial reference system WKT
            @type update:     C{boolean}
            @param update:    Update or overwrite existing shapefile
            @note: Field names can only be <= 10 characters long. Longer names will be silently truncated. This may result in non-unique column names, which will definitely cause problems later.
                   Field names can not contain spaces or special characters, except underscores.
                   Starting with version 1.7, the OGR Shapefile driver tries to generate unique field names. Successive duplicate field names, including those created by truncation to 10 characters, will be truncated to 8 characters and appended with a serial number from 1 to 99.
            @see: U{http://www.gdal.org/ogr/drv_shapefile.html}
        '''
        gdal.ErrorReset()
        ogr.UseExceptions()
        self.driver = ogr.GetDriverByName('ESRI Shapefile')
        self.srs=osr.SpatialReference()
        self.filename=shapefile
        self.srs_wkt=srs_wkt
        self.fieldsnames=[]#Truncated fields names
        self.shpfieldsnames=[]
        self.fields={}
        self.shpfields={}
        if fieldnames == None:fieldnames=sorted(self.fields.keys())
        for fieldname in fieldnames:
            if fieldname[0:10] not in self.fieldsnames:
                self.fieldsnames.append(fieldname[0:10])
                self.fields[fieldname[0:10]]=fields[fieldname]
                #print fieldname[0:10],':',self.fields[fieldname[0:10]]
        try:
            if update and os.path.exists(shapefile):
                print 'EDIT shape mode'
                self.shape=self.__openshapefile__()
            else:
                print 'CREATE shape mode'
                self.shape=self.__createshapefile__()
        except Exception, err:
            self.__error__(err)
        ogr.DontUseExceptions()

    def __del__(self):
        '''Shutdown and release the lock on the shapefile'''
        try:
            gdal.ErrorReset()
            self.shape.Release()
        except:pass

    def __error__(self, err):
        gdalerr=gdal.GetLastErrorMsg();gdal.ErrorReset()
        self.__del__()
        errmsg = str(err)
        if gdalerr:errmsg += '\n%s' % gdalerr
        raise err.__class__, errmsg

    def __createshapefile__(self):
        '''Open the shapefile for writing'''
        if self.srs_wkt:self.srs.ImportFromWkt(self.srs_wkt)
        else:self.srs.ImportFromEPSG(4326)
        if os.path.exists(self.filename):self.driver.DeleteDataSource(self.filename)
        shp = self.driver.CreateDataSource(self.filename)
        lyr=os.path.splitext(os.path.split(self.filename)[1])[0]
        lyr = shp.CreateLayer(lyr.encode('utf-8'),geom_type=ogr.wkbPolygon,srs=self.srs)
        for f in self.fieldsnames:
            if self.fields[f]:
                #Get field types
                if type(self.fields[f]) in [list,tuple]:
                    ftype=self.fields[f][0]
                    try:
                        fwidth=self.fields[f][1]
                    except:
                        fwidth=6
                    try:
                        fprecision=self.fields[f][2]
                    except:
                        fprecision=2
                if ftype.upper()=='STRING':#4
                    fld = ogr.FieldDefn(f, ogr.OFTString)
                    fld.SetWidth(fwidth)
                elif ftype.upper()=='INT':#0
                    fld = ogr.FieldDefn(f, ogr.OFTInteger)
                elif ftype.upper()=='FLOAT':#2
                    fld = ogr.FieldDefn(f, ogr.OFTReal)
                    fld.SetWidth(fwidth)
                    fld.SetPrecision(fprecision)       
                else:continue
                lyr.CreateField(fld)
        return shp

    def __openshapefile__(self,):
        '''Open the shapefile for updating/appending'''
        shp=self.driver.Open(self.filename,update=1)
        lyr=shp.GetLayer(0)
        lyrdef=lyr.GetLayerDefn()
        if lyrdef.GetFieldCount()==0:
            del lyrdef
            del lyr
            del shp
            return self.__createshapefile__()
        else:
            for field_index in range(lyrdef.GetFieldCount()):
                self.shpfieldsnames.append(lyrdef.GetFieldDefn(field_index).GetName())
                if lyrdef.GetFieldDefn(field_index).GetType() == 0:
                    self.shpfields[lyrdef.GetFieldDefn(field_index).GetName()]='int'
                if lyrdef.GetFieldDefn(field_index).GetType() == 2:
                    self.shpfields[lyrdef.GetFieldDefn(field_index).GetName()]=('float',lyrdef.GetFieldDefn(field_index).GetWidth(),lyrdef.GetFieldDefn(field_index).GetPrecision())
                if lyrdef.GetFieldDefn(field_index).GetType() == 4:               
                    self.shpfields[lyrdef.GetFieldDefn(field_index).GetName()]=('string',lyrdef.GetFieldDefn(field_index).GetWidth())
            print self.shpfieldsnames
            print self.shpfields
        self.srs=lyr.GetSpatialRef()
        return shp

    def WriteRecord(self,wkt,attributes):
        '''Write record
            @type wkt:      C{str}
            @param wkt:     POLYGON ((x1 y1, x.. y.., xn yn, x1 y1))
            @type attributes:  C{dict}
            @param attributes: Must match field names passed to __init__()
        '''
        for keys,values in attributes.items():
            if len(keys)>10:
                attributes[keys[0:10]]=values
                del attributes[keys]
        try:
            geom=ogr.CreateGeometryFromWkt(wkt,self.srs)
            if self.srs.IsGeographic(): #basic coordinate bounds test. Can't do for projected though
                srs=osr.SpatialReference()
                srs.ImportFromEPSG(4326)
                valid = GeomFromExtent([-180,-90,180,90], srs=srs)
                valid.TransformTo(self.srs)
                if not valid.Contains(geom): print 'Invalid extent coordinates'
            lyr=self.shape.GetLayer(0) 
            feat = ogr.Feature(lyr.GetLayerDefn())
            for f in self.fieldsnames:
                if attributes.has_key(f) and attributes[f] is not None:feat.SetField(f, encode(attributes[f]))
                else: 
                    feat.SetField(f, -9999)
            feat.SetGeometryDirectly(geom)
            lyr.CreateFeature(feat)
            lyr.SyncToDisk()
        except Exception, err:
            self.__error__(err)

    def UpdateRecord(self,wkt,attributes,where_clause):
        '''Update record/s
            @type where_clause:  C{str}
            @param where_clause: Shapefile supported SQL where clause
            @type attributes:    C{dict}
            @param attributes:   Must match field names passed to __init__()
        '''
        for keys,values in attributes.items():
            if len(keys)>10:
                attributes[keys[0:10]]=values
                del attributes[keys]
        try:
            geom=ogr.CreateGeometryFromWkt(wkt,self.srs)
            if self.srs.IsGeographic(): #basic coordinate bounds test. Can't do for projected though
                srs=osr.SpatialReference()
                srs.ImportFromEPSG(4326)
                valid = GeomFromExtent([-180,-90,180,90], srs=srs)
                valid.TransformTo(self.srs)
                if not valid.Contains(geom): print 'Invalid extent coordinates'           
            lyr=self.shape.GetLayer()
            lyr.SetAttributeFilter(where_clause)
            feat=lyr.GetNextFeature()
            try:feat.SetGeometryDirectly(geom)
            except:return self.WriteRecord(wkt,attributes)
            while feat:
                for f in self.fieldsnames:
                    if attributes.has_key(f):feat.SetField(f, encode(attributes[f]))
                    else: feat.SetField(f, -9999)
                lyr.SetFeature(feat)
                feat=lyr.GetNextFeature()
            lyr.SyncToDisk()
        except Exception, err:
            self.__error__(err)

    def DeleteRecord(self,where_clause):
        '''Delete record/s
            @type where_clause:  C{str}
            @param where_clause: Shapefile supported SQL where clause
        '''
        try:
            lyr=self.shape.GetLayer()
            lyr.SetAttributeFilter(where_clause)
            feat=lyr.GetNextFeature()
            while feat:
                fid=feat.GetFID()
                lyr.DeleteFeature(fid)
                feat=lyr.GetNextFeature()
            lyr.SyncToDisk()
        except Exception, err:
            self.__error__(err)
