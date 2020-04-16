# -*- coding: utf-8 -*-
"""
/***************************************************************************
                                 A QGIS plugin
 Baikal15
                             -------------------
        begin                : 2015-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2015 by SOVZOND
        email                : gtest@sovzond.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from PyQt4 import QtGui, uic
FORM_CLASS_ABTO, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'autovector.ui'))
class SovzondABTOMainWindow(QtGui.QMainWindow, FORM_CLASS_ABTO):
    def __init__(self, parent=None):
        """Constructor."""
        super(SovzondABTOMainWindow, self).__init__(parent)
        self.setupUi(self)
FORM_CLASS_CMR, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'importdem.ui'))
class SovzondCMRMainWindow(QtGui.QMainWindow, FORM_CLASS_CMR):
    def __init__(self, parent=None):
        """Constructor."""
        super(SovzondCMRMainWindow, self).__init__(parent)
        self.setupUi(self)
FORM_CLASS_CMR2, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'volume.ui'))
class SovzondCMR2MainWindow(QtGui.QMainWindow, FORM_CLASS_CMR2):
    def __init__(self, parent=None):
        """Constructor."""
        super(SovzondCMR2MainWindow, self).__init__(parent)
        self.setupUi(self)
#
FORM_CLASS_LANDSAT, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'watermask.ui'))
class SovzondLandsatMainWindow(QtGui.QMainWindow, FORM_CLASS_LANDSAT):
    def __init__(self, parent=None):
        """Constructor."""
        super(SovzondLandsatMainWindow, self).__init__(parent)
        self.setupUi(self)
#
# FORM_CLASS_MOTION2, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'video2.ui'))
# class SovzondMotion2MainWindow(QtGui.QMainWindow, FORM_CLASS_MOTION2):
#     def __init__(self, parent=None):
#         """Constructor."""
#         super(SovzondMotion2MainWindow, self).__init__(parent)
#         self.setupUi(self)
