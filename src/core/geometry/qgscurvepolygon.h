/***************************************************************************
                         qgscurvepolygon.h
                         -------------------
    begin                : September 2014
    copyright            : (C) 2014 by Marco Hugentobler
    email                : marco at sourcepole dot ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifndef QGSCURVEPOLYGONV2_H
#define QGSCURVEPOLYGONV2_H

#include "qgis_core.h"
#include "qgis.h"
#include "qgssurface.h"

class QgsPolygonV2;

/** \ingroup core
 * \class QgsCurvePolygon
 * \brief Curve polygon geometry type
 * \since QGIS 2.10
 */
class CORE_EXPORT QgsCurvePolygon: public QgsSurface
{
  public:
    QgsCurvePolygon();
    QgsCurvePolygon( const QgsCurvePolygon &p );
    QgsCurvePolygon &operator=( const QgsCurvePolygon &p );
    ~QgsCurvePolygon();

    virtual QString geometryType() const override { return QStringLiteral( "CurvePolygon" ); }
    virtual int dimension() const override { return 2; }
    virtual QgsCurvePolygon *clone() const override SIP_FACTORY;
    void clear() override;

    virtual bool fromWkb( QgsConstWkbPtr &wkb ) override;
    virtual bool fromWkt( const QString &wkt ) override;

    QByteArray asWkb() const override;
    QString asWkt( int precision = 17 ) const override;
    QDomElement asGML2( QDomDocument &doc, int precision = 17, const QString &ns = "gml" ) const override;
    QDomElement asGML3( QDomDocument &doc, int precision = 17, const QString &ns = "gml" ) const override;
    QString asJSON( int precision = 17 ) const override;

    //surface interface
    virtual double area() const override;
    virtual double perimeter() const override;
    QgsPolygonV2 *surfaceToPolygon() const override SIP_FACTORY;
    virtual QgsAbstractGeometry *boundary() const override SIP_FACTORY;

    //curve polygon interface
    int numInteriorRings() const;
    const QgsCurve *exteriorRing() const;
    const QgsCurve *interiorRing( int i ) const;

    /** Returns a new polygon geometry corresponding to a segmentized approximation
     * of the curve.
     * \param tolerance segmentation tolerance
     * \param toleranceType maximum segmentation angle or maximum difference between approximation and curve*/
    virtual QgsPolygonV2 *toPolygon( double tolerance = M_PI_2 / 90, SegmentationToleranceType toleranceType = MaximumAngle ) const SIP_FACTORY;

    /** Sets the exterior ring of the polygon. The CurvePolygon type will be updated to match the dimensionality
     * of the exterior ring. For instance, setting a 2D exterior ring on a 3D CurvePolygon will drop the z dimension
     * from the CurvePolygon and all interior rings.
     * \param ring new exterior ring. Ownership is transferred to the CurvePolygon.
     * \see setInteriorRings()
     * \see exteriorRing()
     */
    virtual void setExteriorRing( QgsCurve *ring SIP_TRANSFER );

    //! Sets all interior rings (takes ownership)
    void setInteriorRings( const QList<QgsCurve *> &rings SIP_TRANSFER );
    //! Adds an interior ring to the geometry (takes ownership)
    virtual void addInteriorRing( QgsCurve *ring SIP_TRANSFER );

    /**
     * Removes an interior ring from the polygon. The first interior ring has index 0.
     * The corresponding ring is removed from the polygon and deleted. If a ring was successfully removed
     * the function will return true.  It is not possible to remove the exterior ring using this method.
     * \see removeInteriorRings()
     */
    bool removeInteriorRing( int ringIndex );

    /**
     * Removes the interior rings from the polygon. If the minimumAllowedArea
     * parameter is specified then only rings smaller than this minimum
     * area will be removed.
     * \since QGIS 3.0
     * \see removeInteriorRing()
     */
    void removeInteriorRings( double minimumAllowedArea = -1 );

    virtual void draw( QPainter &p ) const override;
    void transform( const QgsCoordinateTransform &ct, QgsCoordinateTransform::TransformDirection d = QgsCoordinateTransform::ForwardTransform,
                    bool transformZ = false ) override;
    void transform( const QTransform &t ) override;

    virtual bool insertVertex( QgsVertexId position, const QgsPoint &vertex ) override;
    virtual bool moveVertex( QgsVertexId position, const QgsPoint &newPos ) override;
    virtual bool deleteVertex( QgsVertexId position ) override;

    virtual QgsCoordinateSequence coordinateSequence() const override;
    virtual int nCoordinates() const override;
    bool isEmpty() const override;
    virtual double closestSegment( const QgsPoint &pt, QgsPoint &segmentPt SIP_OUT,
                                   QgsVertexId &vertexAfter SIP_OUT, bool *leftOf SIP_OUT,
                                   double epsilon ) const override;

    bool nextVertex( QgsVertexId &id, QgsPoint &vertex SIP_OUT ) const override;

    bool hasCurvedSegments() const override;

    /** Returns a geometry without curves. Caller takes ownership
     * \param tolerance segmentation tolerance
     * \param toleranceType maximum segmentation angle or maximum difference between approximation and curve*/
    QgsAbstractGeometry *segmentize( double tolerance = M_PI_2 / 90, SegmentationToleranceType toleranceType = MaximumAngle ) const override SIP_FACTORY;

    /** Returns approximate rotation angle for a vertex. Usually average angle between adjacent segments.
     *  \param vertex the vertex id
     *  \returns rotation in radians, clockwise from north
     */
    double vertexAngle( QgsVertexId vertex ) const override;

    virtual int vertexCount( int /*part*/ = 0, int ring = 0 ) const override;
    virtual int ringCount( int /*part*/ = 0 ) const override { return ( nullptr != mExteriorRing ) + mInteriorRings.size(); }
    virtual int partCount() const override { return ringCount() > 0 ? 1 : 0; }
    virtual QgsPoint vertexAt( QgsVertexId id ) const override;

    virtual bool addZValue( double zValue = 0 ) override;
    virtual bool addMValue( double mValue = 0 ) override;
    virtual bool dropZValue() override;
    virtual bool dropMValue() override;

  protected:

    QgsCurve *mExteriorRing = nullptr;
    QList<QgsCurve *> mInteriorRings;

    virtual QgsRectangle calculateBoundingBox() const override;
};

#endif // QGSCURVEPOLYGONV2_H
