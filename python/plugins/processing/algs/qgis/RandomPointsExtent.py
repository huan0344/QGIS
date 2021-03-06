# -*- coding: utf-8 -*-

"""
***************************************************************************
    RandomPointsExtent.py
    ---------------------
    Date                 : April 2014
    Copyright            : (C) 2014 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from builtins import str

__author__ = 'Alexander Bruy'
__date__ = 'April 2014'
__copyright__ = '(C) 2014, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import random

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsGeometry, QgsFeatureSink, QgsRectangle, QgsFeature, QgsFields, QgsWkbTypes,
                       QgsField, QgsSpatialIndex, QgsPointXY,
                       QgsCoordinateReferenceSystem,
                       QgsMessageLog,
                       QgsProcessingUtils)

from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from processing.core.parameters import ParameterExtent
from processing.core.parameters import ParameterNumber
from processing.core.parameters import ParameterCrs
from processing.core.outputs import OutputVector
from processing.tools import vector, dataobjects

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class RandomPointsExtent(QgisAlgorithm):

    EXTENT = 'EXTENT'
    POINT_NUMBER = 'POINT_NUMBER'
    MIN_DISTANCE = 'MIN_DISTANCE'
    OUTPUT = 'OUTPUT'
    CRS = 'CRS'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'images', 'ftools', 'random_points.png'))

    def group(self):
        return self.tr('Vector creation tools')

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(ParameterExtent(self.EXTENT,
                                          self.tr('Input extent'), optional=False))
        self.addParameter(ParameterNumber(self.POINT_NUMBER,
                                          self.tr('Points number'), 1, None, 1))
        self.addParameter(ParameterNumber(self.MIN_DISTANCE,
                                          self.tr('Minimum distance'), 0.0, None, 0.0))
        self.addParameter(ParameterCrs(self.CRS,
                                       self.tr('Output layer CRS'), 'ProjectCrs'))
        self.addOutput(OutputVector(self.OUTPUT, self.tr('Random points'), datatype=[dataobjects.TYPE_VECTOR_POINT]))

    def name(self):
        return 'randompointsinextent'

    def displayName(self):
        return self.tr('Random points in extent')

    def processAlgorithm(self, parameters, context, feedback):
        pointCount = int(self.getParameterValue(self.POINT_NUMBER))
        minDistance = float(self.getParameterValue(self.MIN_DISTANCE))
        extent = str(self.getParameterValue(self.EXTENT)).split(',')

        crsId = self.getParameterValue(self.CRS)
        crs = QgsCoordinateReferenceSystem()
        crs.createFromUserInput(crsId)

        xMin = float(extent[0])
        xMax = float(extent[1])
        yMin = float(extent[2])
        yMax = float(extent[3])
        extent = QgsGeometry().fromRect(
            QgsRectangle(xMin, yMin, xMax, yMax))

        fields = QgsFields()
        fields.append(QgsField('id', QVariant.Int, '', 10, 0))
        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(fields, QgsWkbTypes.Point, crs, context)

        nPoints = 0
        nIterations = 0
        maxIterations = pointCount * 200
        total = 100.0 / pointCount if pointCount else 1

        index = QgsSpatialIndex()
        points = dict()

        random.seed()

        while nIterations < maxIterations and nPoints < pointCount:
            rx = xMin + (xMax - xMin) * random.random()
            ry = yMin + (yMax - yMin) * random.random()

            pnt = QgsPointXY(rx, ry)
            geom = QgsGeometry.fromPoint(pnt)
            if geom.within(extent) and \
                    vector.checkMinDistance(pnt, index, minDistance, points):
                f = QgsFeature(nPoints)
                f.initAttributes(1)
                f.setFields(fields)
                f.setAttribute('id', nPoints)
                f.setGeometry(geom)
                writer.addFeature(f, QgsFeatureSink.FastInsert)
                index.insertFeature(f)
                points[nPoints] = pnt
                nPoints += 1
                feedback.setProgress(int(nPoints * total))
            nIterations += 1

        if nPoints < pointCount:
            QgsMessageLog.logMessage(self.tr('Can not generate requested number of random points. '
                                             'Maximum number of attempts exceeded.'), self.tr('Processing'), QgsMessageLog.INFO)

        del writer
