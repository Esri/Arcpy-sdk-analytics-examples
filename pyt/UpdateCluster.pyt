import arcpy
import arcpy as ARCPY
class Toolbox(object):
    def __init__(self):
        self.label = "Toolbox"
        self.alias = ""
        self.tools = [UpdateClusterTool]
class UpdateClusterTool(object):
    def __init__(self):
        self.label = "Updated Cluster"
        self.description = ""
        self.canRunInBackground = False
    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Input Features",name="in_features",datatype="GPFeatureLayer", parameterType="Required", direction="Input")
        param1 = ARCPY.Parameter(displayName="Min Points",    name="min_points", datatype="GPLong",         parameterType="Required", direction="Input")
        param2 = ARCPY.Parameter(displayName="Tolerance",     name="tolerance",  datatype="GPLong",         parameterType="Optional", direction="Input")
        param3 = ARCPY.Parameter(displayName="Threshold",     name="threshold",  datatype="GPLong",         parameterType="Optional", direction="Input")
        
        return [param0, param1, param2, param3]
    def isLicensed(self):
        return True
    def updateParameters(self, parameters):
        #parameters[3].value = parameters[0].value
        return
    def updateMessages(self, parameters):
        return
    def execute(self, parameters, messages):
        import SSCluster as SSC
        import SSDataObject as SSDO
        import numpy as NUM
        
        #### Get Parameters ####
        inputFC = parameters[0].valueAsText       
        minPoints = int(parameters[1].valueAsText)
        tolerance = int(parameters[2].valueAsText)
        threshold = int(parameters[3].valueAsText)
        
        #### Allow overwrite Output ###
        ARCPY.env.overwriteOutput = True
        
        #### Load Data ####
        ssdo = SSDO.SSDataObject(inputFC)
        ssdo.obtainData(fields = ["REACHORDER","REACHDIST"])
        
        #### Sort Reachability Order ###
        ord = ssdo.fields["REACHORDER"].data
        
        #### Get Reachability Distances ####
        reachValues = ssdo.fields["REACHDIST"].data
        
        #### Load Data For Sorting by Index ####
        data = NUM.zeros((len(reachValues), 2), dtype= float)
        data[:, 0] = reachValues 
        data[:, 1] = ord
        odata = data[data[:,1].argsort()]
        
        #### Get New Index ####
        reachValues = odata[:,0]
        
        #### Get Maximum/Minimum  Reachability Distance ####
        maxDist = reachValues.max()
        minDist = reachValues.min()
        orderValues = ord.astype(NUM.intp)
        
        
        idClusters = None
        fields = ['CLUSTER_ID', 'COLOR_ID']      
        
        #### Apply Tolerance ###
        if tolerance != -1:
            #### Initialize Detect Zone Class ####
            zones = SSC.DetectZones()
            
            #### Get Cluster By Threshold ###
            idClusters, iv =  zones.getClusters(reachValues,
                                                    orderValues,
                                                    minPoints, 
                                                    tolerance,
                                                    showReachInMapPlotLib = False)


        #### Apply Threshold ####  
        if threshold != -1:
            
            proportion = (maxDist - minDist)*(100-threshold)/100.0
            threshold = minDist + proportion
            
            #### Function to get DBSCAN Clusters ####
            def getDBSCAN(distances, threshold, minPoints, orderValues):
                clusterArr = NUM.ones(len(distances), dtype = int)*-1
                indices = distances <= threshold
                ini = end = 0
                clusterIndex = 1
                c = 1
                for i in NUM.arange(len(indices)-1):
                    if indices[i] and indices[i] == indices[i+1]:
                        if c == 1:
                            ini = i
                        c += 1
                        end = i + 1
                    else:
                        if (end-ini) >= minPoints-1:
                            clusterArr[ini:end+1] = clusterIndex
                            clusterIndex += 1
                            ini = end = 0
                            c = 1
                return clusterArr[orderValues]
                
            idClusters = getDBSCAN(reachValues, threshold, minPoints, orderValues)

        #### Update Index Cluster ####
        labels = SSC.checkLabels(NUM.asarray(idClusters, dtype = NUM.long))
        
        #### Apply Color Scheme ###
        color = SSC.Colors(ssdo.xyCoords, labels)
        data = color.getColors()
        labelColor, idsLabels, countLabels = data
     
        ##### Update Cluster Id and Color Id #####
        with ARCPY.da.UpdateCursor(inputFC, fields) as cursor:
            id = 0;
            for row in cursor:
                row[0] = idClusters[id]
                row[1] = labelColor[id]
                cursor.updateRow(row)
                id += 1

        