# -*- coding: utf-8 -*-

"""
***************************************************************************
    ExecuteSQL.py -- use virtual layers to execute SQL on any sources
    ---------------------
    Date                 : Jan 2016
    Copyright            : (C) 2016 by Hugo Mercier
    Email                : hugo dot mercier at oslandia dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Hugo Mercier'
__date__ = 'January 2016'
__copyright__ = '(C) 2016, Hugo Mercier'

# This will get replaced with a git SHA1 when you do a git archive323

__revision__ = '$Format:%H$'

from qgis.core import (QgsFeature,
                       QgsVirtualLayerDefinition,
                       QgsVectorLayer,
                       QgsCoordinateReferenceSystem,
                       QgsWkbTypes,
                       QgsApplication,
                       QgsProcessingUtils)

from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterString
from processing.core.parameters import ParameterMultipleInput
from processing.core.parameters import ParameterCrs
from processing.core.parameters import ParameterSelection
from processing.core.outputs import OutputVector


class ExecuteSQL(QgisAlgorithm):

    """ This algorithm allows executing an SQL query on a set of input
    vector layers thanks to the virtual layer provider
    """

    INPUT_DATASOURCES = 'INPUT_DATASOURCES'
    INPUT_QUERY = 'INPUT_QUERY'
    INPUT_UID_FIELD = 'INPUT_UID_FIELD'
    INPUT_GEOMETRY_FIELD = 'INPUT_GEOMETRY_FIELD'
    INPUT_GEOMETRY_TYPE = 'INPUT_GEOMETRY_TYPE'
    INPUT_GEOMETRY_CRS = 'INPUT_GEOMETRY_CRS'
    OUTPUT_LAYER = 'OUTPUT_LAYER'

    def group(self):
        return self.tr('Vector general tools')

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(ParameterMultipleInput(name=self.INPUT_DATASOURCES,
                                                 description=self.tr('Additional input datasources (called input1, .., inputN in the query)'),
                                                 optional=True))

        self.addParameter(ParameterString(name=self.INPUT_QUERY,
                                          description=self.tr('SQL query'),
                                          multiline=True))

        self.addParameter(ParameterString(name=self.INPUT_UID_FIELD,
                                          description=self.tr('Unique identifier field'), optional=True))

        self.addParameter(ParameterString(name=self.INPUT_GEOMETRY_FIELD,
                                          description=self.tr('Geometry field'), optional=True))

        self.geometryTypes = [
            self.tr('Autodetect'),
            self.tr('No geometry'),
            'Point',
            'LineString',
            'Polygon',
            'MultiPoint',
            'MultiLineString',
            'MultiPolygon']
        self.addParameter(ParameterSelection(self.INPUT_GEOMETRY_TYPE,
                                             self.tr('Geometry type'), self.geometryTypes, optional=True))

        self.addParameter(ParameterCrs(self.INPUT_GEOMETRY_CRS,
                                       self.tr('CRS'), optional=True))

        self.addOutput(OutputVector(self.OUTPUT_LAYER, self.tr('SQL Output')))

    def name(self):
        return 'executesql'

    def displayName(self):
        return self.tr('Execute SQL')

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.getParameterValue(self.INPUT_DATASOURCES)
        query = self.getParameterValue(self.INPUT_QUERY)
        uid_field = self.getParameterValue(self.INPUT_UID_FIELD)
        geometry_field = self.getParameterValue(self.INPUT_GEOMETRY_FIELD)
        geometry_type = self.getParameterValue(self.INPUT_GEOMETRY_TYPE)
        geometry_crs = self.getParameterValue(self.INPUT_GEOMETRY_CRS)

        df = QgsVirtualLayerDefinition()
        layerIdx = 1
        if layers:
            for layerSource in layers.split(';'):
                layer = QgsProcessingUtils.mapLayerFromString(layerSource, context)
                if layer:
                    df.addSource('input{}'.format(layerIdx), layer.id())
                layerIdx += 1

        if query == '':
            raise GeoAlgorithmExecutionException(
                self.tr('Empty SQL. Please enter valid SQL expression and try again.'))
        else:
            df.setQuery(query)

        if uid_field:
            df.setUid(uid_field)

        if geometry_type == 1:  # no geometry
            df.setGeometryWkbType(QgsWkbTypes.NullGeometry)
        else:
            if geometry_field:
                df.setGeometryField(geometry_field)
            if geometry_type > 1:
                df.setGeometryWkbType(geometry_type - 1)
            if geometry_crs:
                crs = QgsCoordinateReferenceSystem(geometry_crs)
                if crs.isValid():
                    df.setGeometrySrid(crs.postgisSrid())

        vLayer = QgsVectorLayer(df.toString(), "temp_vlayer", "virtual")
        if not vLayer.isValid():
            raise GeoAlgorithmExecutionException(vLayer.dataProvider().error().message())

        writer = self.getOutputFromName(self.OUTPUT_LAYER).getVectorWriter(vLayer.fields(),
                                                                           vLayer.wkbType() if geometry_type != 1 else 1,
                                                                           vLayer.crs(), context)

        features = QgsProcessingUtils.getFeatures(vLayer, context)
        total = 100.0 / vLayer.featureCount() if vLayer.featureCount() else 0
        outFeat = QgsFeature()
        for current, inFeat in enumerate(features):
            outFeat.setAttributes(inFeat.attributes())
            if geometry_type != 1:
                outFeat.setGeometry(inFeat.geometry())
            writer.addFeature(outFeat, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))
        del writer
