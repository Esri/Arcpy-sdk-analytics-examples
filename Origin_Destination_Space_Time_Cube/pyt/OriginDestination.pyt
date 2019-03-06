# coding: utf-8
"""
   Licensed under the Apache License, Version 2.0 (the "License");

   you may not use this file except in compliance with the License.

   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software

   distributed under the License is distributed on an "AS IS" BASIS,

   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

   See the License for the specific language governing permissions and

   limitations under the License.​

"""

   
import arcpy as ARCPY


def loadInfo(inputFCOrigin, dateFieldOrigin, uniqueIDOrigin,
             inputFCDestination, dateFieldDestination, uniqueIDDestination,
             timeInterval = "1 Hours",     distInterval = "500 Meters",
             outputCubeOrigin = None,   outputCubeDestination = None,
             studyAreaFC = None, srf = None ):
             
    """ Create Origin - Destination Space-Time Cubes
    INPUT:
        inputFCOrigin {str}: Origin Feature class
        dateFieldOrigin {str}: Date-Time Field
        uniqueIDOrigin {str}: Unique ID Field
        inputFCDestination {str}: Origin Feature class
        dateFieldDestination {str}: Date-Time Field
        uniqueIDDestination {str}: Unique ID Field
        timeInterval {str}: Value - Unit e.g. 1 Hours
        distInterval {str}: Value = Unit e.g. 500 Meters
        outputCubeOrigin {str}: Output NC Origin
        outputCubeDestination {str}: Output NC Destination
        studyAreaFc {str}: Feature Class Polygon
        srf {spatial Reference}: Explicit Spatial Reference
   
    """
    import SSDataObject as SSDO
    import SSUtilities as UTILS
    import numpy as NUM
    import SSCubeObject as SSCO
    import SSCube as CUBE
    import arcgisscripting as ARC
    import scipy.spatial as SCPSP

    import Stats as STATS
    import collections as COLL

    def withinData(XY, timeBins,  idSource, extent):
        """ Is is XY inside of Extent"""

        X = XY.T[0]
        Y = XY.T[1]
        info =(X >=extent.XMin ) * (X <=extent.XMax) *  (Y >=extent.YMin ) * (Y <=extent.YMax)
        ids = NUM.where(info)[0]
        if len(ids) == len(X):
            return XY, timeBins, idSource, ids
        else:
            return XY[ids], timeBins[ids], idSource[ids], ids

    def locData(XY, timeBins, idSource,  extent, cellSize, numCols, numRows):
        """ Return Extent """
        
        XY, timeBins, idSource, ids = withinData(XY, timeBins, idSource, extent)

        sizeSlice = numCols * numRows
        XMin = extent.XMin
        YMax = extent.YMax
        X = XY.T[0]
        Y = XY.T[1]
        
        cols = (X - XMin) // cellSize
        rows = (YMax - Y) // cellSize
       
        locations = rows*numCols + cols + timeBins*sizeSlice
        return locations, idSource, ids

    class DerivedCubeObject():
        """ Derived Class of Cube Object to avoid Init """
        
        def __init__(self, ssdo, templateFC = None, explicitSpatialRef = None,
                     referenceCube = None, silentWarnings = False):
            self.obj = SSCO.SSCubeObject.__new__(SSCO.SSCubeObject)
            if referenceCube is not None:
                self.obj.refCube = CUBE.SSCube(referenceCube, 'r')
                explicitSpatialRef =  self.obj.refCube.spatialReference
                self.obj.useRefCube = True
            else:
                self.obj.refCube = None
                self.obj.useRefCube = False
            #### Create Composition and Accounting Structure ####
            self.obj.fields = {}
            self.obj.ssdo = ssdo
            #### Obtain a Full List of Field Names/Type ####
            self.obj.allFields = ssdo.allFields  
            
    class Data():
        """ Container """
        def __init__(self, name, data):
            self.name = name
            self.data = data

    class DataInfo():
        """Pseudo SSDataObject """
        
        def __init__(self, indices, xy, timeField, timeData, srf):
            """ Attributes required in the cube """
            self.useChordal = False
            self.spatialRef = srf
            self.xyCoords = xy
            timeData = Data(timeField,timeData)
            self.fields = {timeField: timeData }
            self.master2Order = {v:id for id, v in enumerate(indices)}
            self.order2Master = {id:v for id, v in enumerate(indices)}
            self.oidName = "OID"
            self.distanceInfo = UTILS.DistanceInfo(srf, 
                                             useChordalDistances = False)
            self.allFields = {timeField: timeData }
            minv = self.xyCoords.min(0)
            maxv = self.xyCoords.max(0)
            self.extent = ARCPY.Extent(XMax = maxv[0], YMax = maxv[1],
                                       XMin = minv[0], YMin = minv[1])
            self.numObs = len(self.xyCoords)
            self.getSurfaceAreaInfo()
            
        def obtainData(self, oidName , fields = [],
                                 types = None, minNumObs = None, 
                                 warnNumObs = False, 
                                 explicitBadRecordID = False,
                                 requireSearch = False):
            """This Method is required in the API """
            pass
            
        def getSurfaceAreaInfo(self):
            """Returns the total area of the extent of the feature centroids
               as well as the percentage that area makes up of the total 
               surface of the planet.
            """

            #### Get Extent Info ####

            try:   
                self.area = self.extent.polygon.getArea('PRESERVE_SHAPE')
                if self.useChordal:
                    maxExtent = self.sliceInfo.maxExtent
                    boundary2Use = self.sliceInfo
                else:

                    envelope = UTILS.Envelope(self.extent)
                    maxExtent = envelope.maxExtent
                    boundary2Use = envelope
                    self.envelope = envelope
            except:
                    envelope = UTILS.Envelope(self.extent)
                    maxExtent = envelope.maxExtent
                    boundary2Use = envelope
                    self.envelope = envelope
                    self.area = maxExtent * envelope.minExtent

            if not self.numObs:
                self.defaultCellSize = None
                self.uniqueXY = self.xyCoords
                self.numUnique = 0
                self.allUnique = True
            else:
                self.defaultNumCells = UTILS.maximumNumberOfCells
                self.defaultCellSize = UTILS.roof(maxExtent / (self.defaultNumCells * 1.0))

                #### Get Unique XY and Coincident Counts ####
                self.uniqueXY, self.counts = STATS.uniqueRows(self.xyCoords)
                self.numUnique = len(self.uniqueXY)
                self.isPanelData = self.counts.std() == 0.0
                self.allUnique = self.numUnique == self.numObs

            try:
                self.convexHull = UTILS.getConvexHull(self.uniqueXY, self.spatialRef)
                self.convexArea = self.convexHull.getArea('PRESERVE_SHAPE')
            except:
                self.convexArea = 0

            if self.convexArea > 0.0:
                self.skipNearestNeighbor = STATS.isDense(self.defaultCellSize, 
                                                         self.convexArea,
                                                         self.numUnique)
            else:
                self.skipNearestNeighbor = False        
            
    def isContained(fc, xy):
        ssdo = SSDO.SSDataObject(fc)
        ssdo.obtainData(requireGeometry = True)
        value = NUM.zeros(len(xy), dtype= bool)
        point = ARCPY.Point()
        for shape in ssdo.shapes:
            for i in NUM.arange(len(xy)):
                point.X = xy[i][0]
                point.Y = xy[i][1]
                cont = shape.contains(point)
                if not value[i] and cont:
                    value[i] = cont
        return NUM.where(value)[0]

    def isContainedBySSDO(ssdo, xy):
        """ Identify  locations inside of a zone """
        value = NUM.zeros(len(xy), dtype= bool)
        point = ARCPY.Point()
        for shape in ssdo.shapes:
            for i in NUM.arange(len(xy)):
                point.X = xy[i][0]
                point.Y = xy[i][1]
                cont = shape.contains(point)
                if not value[i] and cont:
                    value[i] = cont
        return NUM.where(value)[0]


    ssdoS = None
    #### Apply Spatial Reference ####
    ARCPY.env.outputCoordinateSystem = srf

    if studyAreaFC is not None:
        #### Get information 
        ssdoS = SSDO.SSDataObject(studyAreaFC)
        ssdoS.obtainData(requireGeometry = True)
        #### Use Study area spatial reference to re-project datasets ####
        ARCPY.env.outputCoordinateSystem = ssdoS.spatialRef
        srf = ssdoS.spatialRef
   
    
    #### Origin -> pickup / Destination Drop Off ####
    timePickup = dateFieldOrigin.upper()
    timeDropOff = dateFieldDestination.upper()

    #### Read Source Origin Data ####
    ssdo = SSDO.SSDataObject(inputFCOrigin)
    ssdo.obtainData(masterField = uniqueIDOrigin, fields= [timePickup])
    
    #### Read Source Destination Data ####
    ssdoOff = SSDO.SSDataObject(inputFCDestination)
    ssdoOff.obtainData(masterField = uniqueIDDestination, fields= [timeDropOff])
    
    #### Arrays of ID (OD) ####
    idsP = NUM.array(list(ssdo.master2Order.keys()))
    idsD = NUM.array(list(ssdoOff.master2Order.keys()))
    intersect = NUM.intersect1d(idsP, idsD)
    
    #### Number of valid ids ####
    n = len(intersect)
    indexPickup = NUM.zeros(n, dtype = NUM.int32)
    indexDropOff = NUM.zeros(n, dtype = NUM.int32)

    #### Use data that exist in both datasets ####
    for i, id in enumerate(intersect):
        indexPickup[i] = ssdo.master2Order[id]
        indexDropOff[i] = ssdoOff.master2Order[id]

    
    #### Get Coordinates of Origin  filtering invalid locations ####
    xyCoords = ssdo.xyCoords[indexPickup,:]
    #### Valid Ids ####
    ids = idsP[indexPickup]
    #### Time data ####
    timePickupData = ssdo.fields[timePickup].data[indexPickup]

    xyCoordsOff = ssdoOff.xyCoords[indexDropOff,:]
    idsOff = idsD[indexDropOff]
    timeDropOffData = ssdoOff.fields[timeDropOff].data[indexDropOff]
    
    ssdoO = None
    ssdoD = None
    
    
    if studyAreaFC is not None:
        #### Check Points are in the same Polygon Area ####
        indexOrig = isContainedBySSDO(ssdoS, xyCoords)
        indexDest = isContainedBySSDO(ssdoS, xyCoordsOff)
        intersectA = NUM.intersect1d(indexOrig, indexDest)
        ssdoO = DataInfo(ids[intersectA], xyCoords[intersectA,:],timePickup, timePickupData[intersectA], srf)
        ssdoD = DataInfo(idsOff[intersectA], xyCoordsOff[intersectA,:],timeDropOff, timeDropOffData[intersectA], srf)
    else:
        indices = NUM.arange(n)
        ssdoO = DataInfo(ids, xyCoords, timePickup, tOrigin, srf)
        ssdoD = DataInfo(idsOff, xyDestination, timeDropOff, xyDestination, srf)  
    

    #### Default Parameters #####
    timeAlignment  = "END_TIME"
    aggShapeType = "FISHNET_GRID"
    refTime = None
    aggFields = aggTypes = predTypes = []  
    
    
    ARCPY.AddMessage("Creating Origin Cube")
    
    #### Create Cube Object of Origin Data ####
    cubeData = DerivedCubeObject(ssdoO)
    cubeData.obj.obtainData(timePickup, timeInterval, timeAlignment, refTime,
                    distInterval, aggShapeType = aggShapeType,
                    fields = aggFields, aggregateTypes = aggTypes,
                    predictionTypes = predTypes)
                    
    #### Create Cube Origin ####
    cube = CUBE.SSCube(outputCubeOrigin, cubeObj = cubeData.obj)
    
    
    ARCPY.AddMessage("Creating Destination Cube")
    #### Create Cube Object of Destination Data ####
    cubeDataD = DerivedCubeObject(ssdoD, referenceCube = outputCubeOrigin)
    cubeDataD.obj.obtainData(timeDropOff, timeInterval, timeAlignment, refTime,
                    distInterval, aggShapeType = aggShapeType,
                    fields = aggFields, aggregateTypes = aggTypes,
                    predictionTypes = predTypes)    

    ARCPY.AddMessage("Getting Bins")
    
    #### Calculate Bin of Origin ####
    locOrigin, idSourceO, idsO = locData(ssdoO.xyCoords, cubeData.obj.timeBins, NUM.array(list(ssdoO.master2Order.keys()), dtype = NUM.int32), 
    cube.extent, cube.cellSize, cube.numCols, cube.numRows)
    hashO = { id:locOrigin[i] for i, id in enumerate(idSourceO)}    
    
    #### Calculate Bin of Destination ####
    locDest, idSourceD , idsD = locData(ssdoD.xyCoords, cubeDataD.obj.timeBins, NUM.array(list(ssdoD.master2Order.keys()), dtype = NUM.int32),
    cube.extent, cube.cellSize, cube.numCols, cube.numRows)   
    hashD = { id:locDest[i] for i, id in enumerate(idSourceD)}
    
    #### Use Ids that exist in Origin and Destination #####
    infSource = NUM.intersect1d(idSourceO, idSourceO)

    #### Create XY Hash Counter ####
    pointCounts = COLL.defaultdict(NUM.int32)
    for i in infSource:
        if i in hashO and i in hashD:
            loc = (hashO[i], hashD[i])
            pointCounts[loc] += 1
    
    binOriginDest = NUM.zeros((len(pointCounts),2), dtype = NUM.int32)
    cont = 0
    for pnt, count in UTILS.iteritems(pointCounts):
            #### Create Output Point ####
            binOriginDest[cont,0] = pnt[0]
            binOriginDest[cont,1] = pnt[1]
            cont += 1
            
    binOriginDest = binOriginDest[binOriginDest[:,0].argsort()]
    idOrigin, counts = NUM.unique(binOriginDest.T[0], return_counts=True)
    count = 0
    listCount = []
    for i in counts:
        count += i
        listCount.append(count)
        
    indexBins = NUM.zeros((len(idOrigin),2), dtype = NUM.int32)
    indexBins.T[0] = counts    
    indexBins.T[1] = listCount
    

    #### Slow Version to get bins
    if False:
        locations = NUM.arange(cube.sizeSlice, dtype = NUM.int32)
        centroids = cubeData.obj.agg.return_centroids()
        tree = SCPSP.cKDTree(centroids)
        nOrigin = len(ssdoO.xyCoords)
        
        for ind in NUM.arange(nOrigin):
            distO, neighO = tree.query(ssdoO.xyCoords[ind], k = 1)
            distD, neighD = tree.query(ssdoD.xyCoords[ind], k = 1)
            indexTimeO = cubeData.obj.timeBins[neighO] * cube.sizeSlice + locations[neighO]
            indexTimeD = cubeDataD.obj.timeBins[neighD] * cube.sizeSlice + locations[neighD]
            binOriginDest[ind,0] = indexTimeO
            binOriginDest[ind,1] = indexTimeD
    
    

    ### Store OD in Cube ####
    f = cube.dataset    
    f.createDimension('destination_array', len(binOriginDest))
    odVar = f.createVariable('destination_array', 'i4', ('destination_array'))
    odVar[:] = binOriginDest.T[1].copy()
    
    f.number_origin_bins = len(idOrigin)
    f.createDimension('valid_origin', len(idOrigin))
    odVar = f.createVariable('valid_origin', 'i4', ('valid_origin'))
    odVar[:] = idOrigin.copy() 

    f.createDimension('count_aggregation_od', 2)
    indVard = f.createVariable('index_dest_count', 'i4', ('valid_origin','count_aggregation_od' ))
    indVard[:] = indexBins
    
    #### Calculate Trends  Origin NC ####
    for varName in cubeData.obj.fieldNames:
        cube.mannKendall(varName)

    #### Create Destination Cube ####
    cubeD = CUBE.SSCube(outputCubeDestination, cubeObj = cubeDataD.obj)
    
    
    #### Change Order D-O Cube ####
    binOriginDest.T[0],binOriginDest.T[1] = binOriginDest.T[1], binOriginDest.T[0].copy()
    
    binOriginDest = binOriginDest[binOriginDest[:,0].argsort()]
    idOrigin, counts = NUM.unique(binOriginDest.T[0], return_counts=True)

    count = 0
    listCount = []
    for i in counts:
        count += i
        listCount.append(count)
        
    indexBins = NUM.zeros((len(idOrigin),2), dtype = NUM.int32)
    indexBins.T[0] = counts    
    indexBins.T[1] = listCount

    fd = cubeD.dataset    
    fd.createDimension('destination_array', len(binOriginDest))
    odVard = fd.createVariable('destination_array', 'i4', ('destination_array'))
    odVard[:] = binOriginDest.T[1].copy()
    
    fd.number_origin_bins = len(idOrigin)
    fd.createDimension('valid_origin', len(idOrigin))
    odVard = fd.createVariable('valid_origin', 'i4', ('valid_origin'))
    odVard[:] = idOrigin.copy() 

    fd.createDimension('count_aggregation_od', 2)
    indVard = fd.createVariable('index_dest_count', 'i4', ('valid_origin','count_aggregation_od' ))
    indVard[:] = indexBins
    
    #### Calculate Trends Destination Cube ####    
    for varName in cubeDataD.obj.fieldNames:
        cubeD.mannKendall(varName)   
    
    #### Close Cubes ####
    cube.close()
    cubeD.close()


        
supportDist = ["Feet", "Meters", "Kilometers", "Miles"]
supportTime = ["Seconds", "Minutes", "Hours", "Days", "Weeks",
               "Months", "Years"]
class Toolbox(object):
    def __init__(self):
        self.label = "Toolbox"
        self.alias = ""
        self.tools = [SelectDestination, CreateODCubes]
 


class CreateODCubes(object):
    def __init__(self):
        self.label = "Create Origin-Destination Cubes"
        self.description = ""
        self.canRunInBackground = False
    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Origin Features",name="in_features",datatype="GPFeatureLayer", parameterType="Required", direction="Input")
        param1 = ARCPY.Parameter(displayName="Origin Time Field",name="in_time_field",datatype="Field", parameterType="Required", direction="Input")
        param1.parameterDependencies = [param0.name]
        param2 = ARCPY.Parameter(displayName="Unique Field",name="unique_field",datatype="Field", parameterType="Required", direction="Input") 
        param2.parameterDependencies = [param0.name]
        
        param3 = ARCPY.Parameter(displayName="Destination Features",name="ind_features",datatype="GPFeatureLayer", parameterType="Required", direction="Input")
        param4 = ARCPY.Parameter(displayName="Destination Time Field",name="ind_time_field",datatype="Field", parameterType="Required", direction="Input")
        param4.parameterDependencies = [param3.name]
        param5 = ARCPY.Parameter(displayName="Unique Field",name="uniqued_field",datatype="Field", parameterType="Required", direction="Input")
        param5.parameterDependencies = [param3.name]        

        param6 = ARCPY.Parameter(displayName="Time Step Interval", name="time_step_interval", datatype="GPTimeUnit", parameterType="Required", direction="Input")
        param6.filter.list = supportTime
        param7 = ARCPY.Parameter(displayName="Distance Interval", name="distance_interval", datatype="GPLinearUnit", parameterType="Required", direction="Input")
        param7.filter.list = supportDist
 
        param8 = ARCPY.Parameter(displayName="Origin Space Time Cube", name="origin_cube",datatype="DEFile",   parameterType="Required", direction="Output")
        param8.filter.list = ['nc']
 
        param9 = ARCPY.Parameter(displayName="Destination Space Time Cube", name="cube_dest",datatype="DEFile", parameterType="Required", direction="Output")
        param9.filter.list = ['nc']        
        
        param10 = ARCPY.Parameter(displayName="Zone Features",name="in_featuresz",datatype="GPFeatureLayer", parameterType="Optional", direction="Input")        
        
        param11 = ARCPY.Parameter(displayName="Spatial Reference", name="srf_cube",datatype="GPSpatialReference",   parameterType="Optional", direction="Input")
       
        return [param0, param1, param2, param3,
                param4, param5, param6, param7,
                param8, param9, param10, param11]
    def isLicensed(self):
        return True
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
    
        loadInfo(inputFCOrigin = parameters[0].valueAsText,
                 dateFieldOrigin = parameters[1].valueAsText,
                 uniqueIDOrigin = parameters[2].valueAsText,
                 inputFCDestination = parameters[3].valueAsText,
                 dateFieldDestination = parameters[4].valueAsText,
                 uniqueIDDestination = parameters[5].valueAsText,
                 timeInterval = parameters[6].valueAsText,
                 distInterval = parameters[7].valueAsText,                 
                 outputCubeOrigin = parameters[8].valueAsText,                
                 outputCubeDestination = parameters[9].valueAsText,
                 studyAreaFC = parameters[10].valueAsText,
                 srf = parameters[11].value)

   
class SelectDestination(object):
    def __init__(self):
        self.label = "Select Origin-Destination Features"
        self.description = ""
        self.canRunInBackground = False
    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Origin Features",name="in_features",datatype="GPFeatureLayer", parameterType="Required", direction="Input")
        param1 = ARCPY.Parameter(displayName="input Space Time Cube", name="input_cube",datatype="DEFile",   parameterType="Required", direction="Input")
        param1.filter.list = ['nc']
        param2 = ARCPY.Parameter(displayName="Destination Features",name="in_features_dest",datatype="GPFeatureLayer", parameterType="Optional", direction="Input")
        param3 = ARCPY.Parameter(displayName="input Space Time Cube", name="input_cube_dest",datatype="DEFile",       parameterType="Optional", direction="Input")
        param3.filter.list = ['nc']
        
        return [param0, param1, param2, param3]
    def isLicensed(self):
        return True
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        import SSDataObject as SSDO
        import numpy as NUM
        import netCDF4 as NET
        import arcpy.management as DM
        DM.SelectLayerByAttribute
        #### Get Parameters ####
        inputOrigin = parameters[0].valueAsText       
        inputNCO = parameters[1].valueAsText
        inputDestination = parameters[0].valueAsText       
        inputNCDestination = parameters[1].valueAsText        
        
        #### Allow overwrite Output ###
        ARCPY.env.overwriteOutput = True
        
        #### Load Data ####
        ssdo = SSDO.SSDataObject(inputOrigin)
        ssdo.obtainData(fields = ["ELEMENT", "VALUE"])
        cube = NET.Dataset(inputNCO, 'r')
        dataset = cube
        
        n = dataset.number_origin_bins
        valid = dataset.variables["valid_origin"][:]
        elements = ssdo.fields["ELEMENT"].data
        counts = ssdo.fields["VALUE"].data
        indicesValues = NUM.where(counts>0)[0]
        elements = elements[indicesValues]
        if len(elements) > 0:
            indices = NUM.flatnonzero(NUM.isin(valid, elements))
            indexDest = dataset.variables["index_dest_count"][:]
            destination = dataset.variables["destination_array"][:]
            destIndex = NUM.array([], dtype = NUM.int32)
            for i in indices:
                info = indexDest[i]
                endV = info[1]
                count = info[0]
                startV = endV-count
                infoSlice = slice(startV, endV)
                destIndex = NUM.append(destIndex, destination[infoSlice])
                
            uniqueIndex = NUM.unique(destIndex)
            sql = "ELEMENT in ({0})".format(",".join([str(i) for i in uniqueIndex]))
            
            if inputDestination is None:
                DM.SelectLayerByAttribute(inputOrigin, "NEW_SELECTION", sql)
            else:
                DM.SelectLayerByAttribute(inputDestination, "NEW_SELECTION", sql)            
        
        cube.close()        