# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
import resources
from Project import SovzondABTOMainWindow
from Project import SovzondCMRMainWindow
from Project import SovzondCMR2MainWindow
from Project import SovzondLandsatMainWindow
from qgis.core import *
from PyQt4 import QtGui
from PyQt4.QtSql import *
from PyQt4 import QtCore, QtGui
from osgeo import ogr
import sys
import cv2
import numpy as np
import pickle
import os
import os, math, time, sys
import osr, ogr, gdal
from gdalconst import GA_ReadOnly, GRA_Cubic, GDT_Byte, GDT_UInt16, GDT_Float32
import numpy as np
import cv2
import vector_lib
# initialize Qt resources from file resources.py
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)
class TestPlugin:
  def __init__(self, iface):
    # save reference to the QGIS interface
    self.iface = iface
  def initGui(self):
    try:
       self.toolbar = self.iface.addToolBar(u"Экологический мониторнг")
       # create action that will start plugin configuration
       #action 1
       icons = ["autovector.png","importdem.png","volume.png","watermask.png"]
       pathToIcons = ":/plugins/EcoMonitoringTools/icons/"
       icons = [pathToIcons + x for x in icons]
       methods = ["runABTO","runCMR","runCMR2","runLandsat"]
       names = [u"Выявление изменений",u"Импорт ЦМР",u"Вычисление изменений объемов",u"Создание маски воды"]
       methods = ["self." + x for x in methods]
       for i in range(len(methods)):
          self.action = QAction(QIcon(icons[i]), names[i], self.iface.mainWindow())
          QObject.connect(self.action,SIGNAL("triggered()"),eval(methods[i]))
          self.toolbar.addAction(self.action)
       QObject.connect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), self.renderTest)
    except Exception as inst:
       print inst.args
       x, y = inst.args
       QtGui.QMessageBox.critical(None,x,y)
  def unload(self):
    # remove the plugin menu item and icon
    self.iface.removePluginMenu("&Test plugins", self.action)
    self.iface.removeToolBarIcon(self.action)
    # disconnect form signal of the canvas
    QObject.disconnect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), self.renderTest)
  def justShowMeWindow(self,window):
      ui = window()
      ui.show()
      return ui
  ''' ABTO '''
  def runABTO(self):
      self.uiABTO = self.justShowMeWindow(SovzondABTOMainWindow)
      QObject.connect(self.uiABTO.pushButton_2,SIGNAL("clicked()"),self.uiABTO.deleteLater)
      map(self.uiABTO.comboBox.addItem,self.getRasterPaths())
      map(self.uiABTO.comboBox_2.addItem,self.getRasterPaths())
      pass
  ''' CMR '''
  def runCMR(self):
      self.uiCMR = self.justShowMeWindow(SovzondCMRMainWindow)
      QObject.connect(self.uiCMR.pushButton_2,SIGNAL("clicked()"),self.uiCMR.deleteLater)
      QObject.connect(self.uiCMR.toolButton,SIGNAL("clicked()"),self.toolButtonUiCmr)
  def toolButtonUiCmr(self):
      self.uiCMR.lineEdit.setText(self.openFileDialog(self.uiCMR,u"Открыть tif-файл","Image (*tif)"))
  ''' CMR2 '''
  def runCMR2(self):
      self.uiCMR2 = self.justShowMeWindow(SovzondCMR2MainWindow)
      # QObject.connect(self.uiCMR2.pushButton_2,SIGNAL("clicked()"),self.uiCMR2.deleteLater)
      self.createClickedSignal(self.uiCMR2.pushButton_2,self.uiCMR2.deleteLater)
      self.createClickedSignal(self.uiCMR2.pushButton,self.pushProcessButtonClickeduiCMR2)
      map(self.uiCMR2.comboBox.addItem,self.getRasterPaths())
      map(self.uiCMR2.comboBox_2.addItem,self.getRasterPaths())
      map(self.uiCMR2.comboBox_3.addItem,self.getShpFilePaths())
  def pushProcessButtonClickeduiCMR2(self):
      input1 = self.uiCMR2.comboBox.currentText()
      input2 = self.uiCMR2.comboBox_2.currentText()
      output = self.uiCMR2.comboBox_3.currentText()
      if input1 == "":
          self.errorMessage(u"Не задан первый tif-файл")
          return
      if input2 == "":
          self.errorMessage(u"Не задан второй tif-файл")
          return
      if output == "":
          self.errorMessage(u"Не задан shp-файл")
          return
      result = self.startDEMChanges(input1,input2,output)
      print result
      pass
  def startDEMChanges(self,input_dem_1,input_dem_2,input_shapefile):
      dem_1_ds=gdal.Open ( input_dem_1, GA_ReadOnly )
      dem_2_ds=gdal.Open ( input_dem_2, GA_ReadOnly )
      shp = ogr.Open(input_shapefile, 1)

      if dem_1_ds is not None:
          if dem_2_ds is not None:
              if shp is not None:
                  #DEM properties
                  if False not in [dem_1_ds.RasterXSize==dem_2_ds.RasterXSize,dem_1_ds.RasterYSize==dem_2_ds.RasterYSize,\
                                   int(dem_1_ds.GetGeoTransform()[0])==int(dem_2_ds.GetGeoTransform()[0]),\
                                   (dem_1_ds.GetGeoTransform()[1])==(dem_2_ds.GetGeoTransform()[1]),\
                                   int(dem_1_ds.GetGeoTransform()[3])==int(dem_2_ds.GetGeoTransform()[3]),\
                                   (dem_1_ds.GetGeoTransform()[4])==(dem_2_ds.GetGeoTransform()[4])]:
                      #raise Exception()
                      xOrigin = dem_1_ds.GetGeoTransform()[0]
                      yOrigin = dem_1_ds.GetGeoTransform()[3]
                      pixelWidth = dem_1_ds.GetGeoTransform()[1]
                      pixelHeight = dem_1_ds.GetGeoTransform()[5]
                      #add new fields to shape
                      source = ogr.Open(input_shapefile, 1)
                      layer = source.GetLayer()
                      layer_defn = layer.GetLayerDefn()
                      field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
                      if not 'DEM1' in field_names:
                          fld = ogr.FieldDefn('DEM1', ogr.OFTString)
                          fld.SetWidth(max(len(input_dem_1),len(input_dem_2)))
                          layer.CreateField(fld)
                      if not 'DEM2' in field_names:
                          fld = ogr.FieldDefn('DEM2', ogr.OFTString)
                          fld.SetWidth(max(len(input_dem_1),len(input_dem_2)))
                          layer.CreateField(fld)
                      if not 'VOLUME' in field_names:
                          fld = ogr.FieldDefn('VOLUME', ogr.OFTReal)
                          fld.SetWidth(12)
                          fld.SetPrecision(2)
                          fld.SetWidth(max(len(input_dem_1),len(input_dem_2)))
                          layer.CreateField(fld)
                      shp = None
                      shp = ogr.Open(input_shapefile, 1)
                      #create mask
                      mask_ds = gdal.GetDriverByName('MEM').Create('', dem_1_ds.RasterXSize, dem_1_ds.RasterYSize, 1, GDT_Byte)
                      mask_ds.SetGeoTransform(dem_1_ds.GetGeoTransform())
                      mask_ds.SetProjection(dem_1_ds.GetProjectionRef())
                      layer=shp.GetLayer()
                      gdal.RasterizeLayer(mask_ds, [1], layer, burn_values=[1])
                      feature = layer.GetNextFeature()
                      #featList = range(layer.GetFeatureCount())
                      while feature:
                          geom = feature.GetGeometryRef()
                          # Get extent of feature
                          if (geom.GetGeometryName() == 'MULTIPOLYGON'):
                              count = 0
                              pointsX = []; pointsY = []
                              for polygon in geom:
                                  geomInner = geom.GetGeometryRef(count)
                                  ring = geomInner.GetGeometryRef(0)
                                  numpoints = ring.GetPointCount()
                                  for p in range(numpoints):
                                      lon, lat, z = ring.GetPoint(p)
                                      pointsX.append(lon)
                                      pointsY.append(lat)
                                  count += 1
                          elif (geom.GetGeometryName() == 'POLYGON'):
                              ring = geom.GetGeometryRef(0)
                              numpoints = ring.GetPointCount()
                              pointsX = []; pointsY = []
                              for p in range(numpoints):
                                  lon, lat, z = ring.GetPoint(p)
                                  pointsX.append(lon)
                                  pointsY.append(lat)
                          else:sys.exit("ERROR: Geometry needs to be either Polygon or Multipolygon")
                          xmin = min(pointsX)
                          xmax = max(pointsX)
                          ymin = min(pointsY)
                          ymax = max(pointsY)
                          # Specify offset and rows and columns to read
                          xoff = int((xmin - xOrigin)/pixelWidth)
                          yoff = int((yOrigin - ymax)/pixelWidth)
                          xcount = int((xmax - xmin)/pixelWidth)+1
                          ycount = int((ymax - ymin)/pixelWidth)+1
                          data_dem1=dem_1_ds.GetRasterBand(1).ReadAsArray(xoff,yoff,xcount,ycount).astype(np.float32)
                          data_dem2=dem_2_ds.GetRasterBand(1).ReadAsArray(xoff,yoff,xcount,ycount).astype(np.float32)
                          data_mask=mask_ds.GetRasterBand(1).ReadAsArray(xoff,yoff,xcount,ycount).astype(np.byte)
                          change=data_dem2-data_dem1
                          zonechange = np.ma.masked_array(change,  np.logical_not(data_mask))
                          volume = np.sum(zonechange) * pixelWidth * pixelWidth
                          feature.SetField('DEM1', vector_lib.encode(input_dem_1))
                          feature.SetField('DEM2', vector_lib.encode(input_dem_2))
                          feature.SetField('VOLUME', volume)
                          layer.SetFeature(feature)
                          layer.SyncToDisk()
                          feature = layer.GetNextFeature()
                      shp = None
                      dem_1_ds=None
                      dem_2_ds=None
                      mask_ds=None
                      return 'ALL DONE'
                  else: sys.exit('DEMs have different properties')
              else: sys.exit('ERROR reading: %s'%(input_shapefile))
          else: sys.exit('ERROR reading: %s'%(input_dem_1))
      else: sys.exit('ERROR reading: %s'%(input_dem_1))
      pass
  ''' watermask '''
  def runLandsat(self):
      self.uiLandsat = self.justShowMeWindow(SovzondLandsatMainWindow)
      QObject.connect(self.uiLandsat.pushButton,SIGNAL("clicked()"),self.pushButtonProcessUiLandsat)
      QObject.connect(self.uiLandsat.toolButton,SIGNAL("clicked()"),self.toolButtonOpenFileUiLandsat)
      QObject.connect(self.uiLandsat.pushButton_2,SIGNAL("clicked()"),self.uiLandsat.deleteLater)
      map(self.uiLandsat.comboBox.addItem,self.getRasterPaths())
  def toolButtonOpenFileUiLandsat(self):
      dir = self.openDirectoryDialog(self.uiLandsat)
      self.uiLandsat.lineEdit.setText(dir + "output.shp")
  def pushButtonProcessUiLandsat(self):
      input_image= self.uiLandsat.comboBox.currentText() #'c:\\CHANGE\\20140724_30m_L8_6b.TIF'
      min_area = self.uiLandsat.spinBox.value() #hectare
      index_value= self.uiLandsat.doubleSpinBox.value()
      output = self.uiLandsat.lineEdit.text()
      if input_image == '':
          self.errorMessage(u"Снимок не задан")
          return
      if output == '':
          self.errorMessage(u"shp-файл не задан")
          return
      #self.informationMessage(input_image + str(min_area) + str(index_value) + output)
      self.waterMaskBuilder(input_image,min_area,index_value,output)
  def waterMaskBuilder(self,input_image,min_area,index_value,output_shapefile=''):
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
      pass
  # ''' Satelite '''
  def renderTest(self, painter):
    # use painter for drawing to map canvas
    pass
  ''' work with layers '''
  def getLayersObject(self):
      return self.iface.legendInterface().layers()

  def getRasterPaths(self):
      res = []
      layers = self.getLayersObject()
      for layer in layers:
        layerType = layer.type()
        if layerType == QgsMapLayer.RasterLayer:
            res.append(layer.source())
      return res

  def getVectorPaths(self):
      res = []
      layers = self.getLayersObject()
      for layer in layers:
        layerType = layer.type()
        if layerType == QgsMapLayer.VectorLayer:
            res.append(layer.source())
      return res
  def getShpFilePaths(self):
      paths = self.getVectorPaths()
      return [x for x in paths if x.endswith(".shp")]

  ''' messages '''
  def errorMessage(self,msg):
      QtGui.QMessageBox.critical(None,u"Ошибка",msg)
  def informationMessage(self,msg):
      QtGui.QMessageBox.information(None,u"Внимание",msg)
  def debugMessage(self,msg):
      debugFlag = True
      if debugFlag == True:
          QtGui.QMessageBox.information(None,u"Отладочная информация",msg)
  ''' interface features '''
  def addNewCheckBoxToScrollArea(self,name,ui,scrollArea,layout):
    ui.checkBox = QtGui.QCheckBox(scrollArea)
    ui.checkBox.setText(_translate("m", name, None))
    layout.addWidget(ui.checkBox) # first scroll area
    return ui.checkBox
  def openDirectoryDialog(self,ui):
    dir = QtGui.QFileDialog.getExistingDirectory(ui,u"Открыть директорию")
    dir += '/'
    return dir
  def openFileDialog(self,ui,msg,filter, folder = "/"):
      '''
      :param ui:
      :param msg:
      :param filter: "Video Files (*.avi *.mp4 *.mov)"
      :return:
      '''
      fileName = QtGui.QFileDialog.getOpenFileName(ui,msg,folder,filter)
      return fileName
  ''' signal '''
  def createClickedSignal(self,button,function):
      QObject.connect(button,SIGNAL("clicked()"),function)
