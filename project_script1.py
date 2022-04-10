
import os
import xmltojson
import json
import requests
import csv
import pandas
from scipy.interpolate import interp2d,NearestNDInterpolator

os.chdir('/Users/asdfasd/Downloads/grmd3106 project')



r = requests.get('https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml')
ds = r.text
json_data = xmltojson.parse(ds)
info = json.loads(json.dumps(json_data))

traffic_raw = eval(info)['raw_speed_volume_list']['periods']['period'][0]['detectors']['detector']
with open('names.csv', 'w', newline='') as csvfile:
    fieldnames = ['detector_id', 'speed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for i in traffic_raw:
    	#print(i)
    	speeds = i['lanes']['lane']
    	speed = 0 
    	if type(speeds) != list:
    		speed += int(speeds['speed'])/len(speeds)
    	else:
    		for r in speeds:
    			speed += int(r['speed'])/len(speeds)
    	writer.writerow({'detector_id': i['detector_id'], 'speed': speed})
speed1 = pandas.read_csv('/Users/asdfasd/Downloads/grmd3106 project/traffic_speed_volume_occ_info.csv')
speed2 = pandas.read_csv('names.csv')
speed1 = speed1.set_index('AID_ID_Number').join(speed2.set_index('detector_id'))

speed1 = speed1.dropna(axis = 0, how = 'any')

x = speed1['Longitude']
y = speed1['Latitude']
z = speed1['speed']
coord = list(zip(x,y))
f1 = NearestNDInterpolator(coord, z)







r2 = requests.get('https://www.aqhi.gov.hk/epd/ddata/html/out/24aqhi_Eng.xml')
ds2 = r2.text
json_data2 = xmltojson.parse(ds2)
info2 = json.loads(json.dumps(json_data2))
air_raw = eval(info2)['AQHI24HrReport']['item']
with open('airpollution.csv','w',newline='') as csvfile:
	fieldnames = ['Facility','aqhi']
	writer = csv.DictWriter(csvfile,fieldnames = fieldnames)
	writer.writeheader()
	for i in range(0,len(air_raw),24):
		#print(air_raw[i])
		writer.writerow({'Facility': air_raw[i]['StationName'], 'aqhi': air_raw[i]['aqhi']})
df1 = pandas.read_csv('airpollution.csv')
df2 = pandas.read_csv('ahqi_monitor.csv')
df1 = df1.set_index('Facility').join(df2.set_index('Facility'))
df1 = df1.dropna(axis = 0, how = 'any')
x = df1['Longitude']
y = df1['Latitude']
z = df1['aqhi']
z = (z-z.mean())/z.std()
f2 = interp2d(x,y,z,kind = 'cubic')



r3 = requests.get('https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_1min_temperature.csv')
with open('latest_min_temperature.csv','w') as file:
	file.write(r3.text)
df1 = pandas.read_csv('weather-station-info.csv')
df2 = pandas.read_csv('latest_min_temperature.csv')
df1 = df1.set_index('station_name_en').join(df2.set_index('Automatic Weather Station'))
df1 = df1.dropna(axis=0, how = 'any')
x = df1['longitude']
y = df1['latitude']
z = df1['Air Temperature(degree Celsius)']
z = (z-z.mean())/z.std()
f3 = interp2d(x,y,z,kind = 'cubic')

# download average road speed from each monitor 






# download average road speed from each monitor 
from qgis.core import QgsProcessing
from qgis.core import QgsVectorLayer
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsCoordinateReferenceSystem,QgsProcessingParameterNumber
from qgis.core import QgsExpression
from qgis.core import (
  QgsPointXY,
  QgsProject,
  QgsApplication,
  QgsDataSourceUri,
  QgsCategorizedSymbolRenderer,
  QgsClassificationRange,
  QgsPointXY,
  QgsProject,
  QgsExpression,
  QgsField,
  QgsFields,
  QgsFeature,
  QgsFeatureRequest,
  QgsFeatureRenderer,
  QgsGeometry,
  QgsGraduatedSymbolRenderer,
  QgsMarkerSymbol,
  QgsMessageLog,
  QgsRectangle,
  QgsRendererCategory,
  QgsRendererRange,
  QgsSymbol,
  QgsVectorDataProvider,
  QgsVectorLayer,
  QgsVectorFileWriter,
  QgsWkbTypes,
  
  QgsSpatialIndex,
  QgsVectorLayerUtils
)
import qgis.processing as processing


class Model(QgsProcessingAlgorithm):
    
#remember: it just like a java class has a constructor once we inherit qgsprocessingalgorithm we can operate algorithm 
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterPoint('asdf', 'asdf', defaultValue='114.196359,22.43567'))
        self.addParameter(QgsProcessingParameterVectorLayer('destpoints', 'dest_points', types=[QgsProcessing.TypeVectorPoint], defaultValue='/Users/asdfasd/Downloads/grmd3106 project/test_points.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('Shortest_path', 'shortest_path', type=QgsProcessing.TypeVectorLine, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterBoolean('whether show step','show steps or not',defaultValue = 1))
        self.addParameter(QgsProcessingParameterString( 'PRINTER_type','drive',defaultValue = 'drive'))
        self.addParameter(QgsProcessingParameterString( 'assign Sequence', 'field to assign sequence',defaultValue = 'sequence'))
        self.addParameter(QgsProcessingParameterNumber( 'VAL', 'weights of air pollution', type=QgsProcessingParameterNumber.Double))
        self.addParameter(QgsProcessingParameterNumber( 'VAL2', 'weights of temperature', type=QgsProcessingParameterNumber.Double))
        self.addParameter(QgsProcessingParameterNumber( 'VAL3', 'weights of security', type=QgsProcessingParameterNumber.Double))
        
        #self.addParameter(QgsProcessingParameterLimitedDataTypes(types = [1,2]))
        # only show two decimal places in parameter's widgets, not 6:
        #param.setMetadata( {'widget_wrapper':{ 'decimals': 2 }})
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}
        mode = 1
        drive_path = '/Users/asdfasd/Downloads/grmd3106 project/simplify_road.kml'
        ped_path = '/Users/asdfasd/Downloads/grmd3106 project/ped-bike.geojson'
        if parameters['PRINTER_type'] != 'drive':
            path = ped_path
            mode = 0
        else:
            path = drive_path
        print('input',parameters['destpoints'])
        
        layer = QgsVectorLayer(path,'','ogr')
        features = layer.getFeatures()
        weight1 = parameters['VAL']
        weight2 = parameters['VAL2']
        for feature in features:
            geom = feature.geometry()
            weight3 = parameters['VAL3']
            z4 = feature['n']
            try:
                (30*weight3 - z4*weight3)/30
            except:
                z4 = weight3
            
            x1,y1 = geom.centroid().asPoint().x(),geom.centroid().asPoint().y()
            z1 = f1([x1],[y1])[0]
            z2 = f2([x1],[y1])[0]
            z3 = f3([x1],[y1])[0]
            
            feature['speed'] = z1/(1+z2*weight1+z3*weight2)
      
        #start to interpolate value for networks
        
        # end interpolation
        
        
        layer = QgsVectorLayer(parameters['destpoints'],'','ogr')
        features = layer.getFeatures()
        destinations = {}
        order = []
        
        
        
        
        
        for feature in features:
            print(1)
            geom = feature.geometry()
            z = (feature[parameters['assign Sequence']])

            if geom.type() == QgsWkbTypes.PointGeometry:
                destinations[z] = (geom.asPoint().x(),geom.asPoint().y())
        order= sorted(destinations)
        temporal_layers = []
        print('list of points:',destinations)
        
        
        
        
        
        for i in range(len(order)):
            path_shortest = '/Users/asdfasd/Downloads/grmd3106 project/'+'shortest_path'+str(i)+'.geojson'
            temporal_layers.append(path_shortest)
            if i == 0:
                alg_params = {
            'DEFAULT_DIRECTION': 2,
            'DEFAULT_SPEED': 50,
            'DIRECTION_FIELD': '',
            'END_POINT': str(destinations[order[i]][0])+','+str(destinations[order[i]][1])+' [EPSG:4326]',
            'INPUT': path,
            'SPEED_FIELD': 'speed',
            'START_POINT': parameters['asdf'],
            'STRATEGY': 0,
            'TOLERANCE': 0,
            'VALUE_BACKWARD': '',
            'VALUE_BOTH': '',
            'VALUE_FORWARD': '',
            'OUTPUT': path_shortest}
            else:
                alg_params = {
            'DEFAULT_DIRECTION': 2,
            'DEFAULT_SPEED': 50,
            'DIRECTION_FIELD': '',
            'END_POINT': str(destinations[order[i]][0])+','+str(destinations[order[i]][1])+' [EPSG:4326]',
            'INPUT': path,
            'SPEED_FIELD': 'speed',
            'START_POINT': str(destinations[order[i-1]][0])+','+str(destinations[order[i-1]][1])+' [EPSG:4326]',
            'STRATEGY': 0,
            'TOLERANCE': 0,
            'VALUE_BACKWARD': '',
            'VALUE_BOTH': '',
            'VALUE_FORWARD': '',
            'OUTPUT': path_shortest}
            processing.run('native:shortestpathpointtopoint', alg_params)
        alg_params = {
            'DEFAULT_DIRECTION': 2,
            'DEFAULT_SPEED': 50,
            'DIRECTION_FIELD': '',
            'END_POINT': parameters['asdf'],
            'INPUT': path,
            'SPEED_FIELD': 'speed',
            'START_POINT': str(destinations[order[-1]][0])+','+str(destinations[order[-1]][1])+' [EPSG:4326]',
            'STRATEGY': 0,
            'TOLERANCE': 0,
            'VALUE_BACKWARD': '',
            'VALUE_BOTH': '',
            'VALUE_FORWARD': '',
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/last_shortestpath.geojson'}
        processing.run('native:shortestpathpointtopoint', alg_params)
        temporal_layers.append('/Users/asdfasd/Downloads/grmd3106 project/last_shortestpath.geojson')
        alg_params = {
            'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'LAYERS': temporal_layers,
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/'+'shortest_path.geojson'
        }
        processing.run('native:mergevectorlayers', alg_params)
        if not parameters['whether show step']:
            for i in temporal_layers:
                os.remove(i)
        vlayer = QgsVectorLayer('/Users/asdfasd/Downloads/grmd3106 project/'+'shortest_path.geojson', "", "ogr")
        QgsProject.instance().addMapLayer(vlayer)
        
            
        
            
                
                


        
   
            
        
        
        '''if mode:
            # Join attributes by field value
            alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'AID_ID_Number',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'detector_id',
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/traffic_speed_volume_occ_info.csv',
            'INPUT_2': '/Users/asdfasd/Downloads/grmd3106 project/names.csv',
            'METHOD': 1,
            'NON_MATCHING': QgsExpression('Null').evaluate(),
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/joined_table.csv',
            'PREFIX': ''}
            outputs['JoinAttributesByFieldValue'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}
        else:
            alg_params = {
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/latest_min_temperature.csv',
            'MFIELD': '',
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/joined_layer.geojson',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'XFIELD': 'Longitude',
            'YFIELD': 'Latitude',
            'ZFIELD': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
            outputs['CreatePointsLayerFromTable'] = processing.run('native:createpointslayerfromtable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}
            
        # Create points layer from table
        if mode:
            alg_params = {
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/joined_table.csv',
            'MFIELD': '',
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/joined_layer.geojson',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'XFIELD': 'Longitude',
            'YFIELD': 'Latitude',
            'ZFIELD': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
            outputs['CreatePointsLayerFromTable'] = processing.run('native:createpointslayerfromtable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}
        else:
            alg_params = {
            'FAIL_OUTPUT': None,
            'FIELD': 'above_mean_sea_level',
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/joined_layer.geojson',
            'OPERATOR': 2,
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/extracted_layer1.geojson',
            'VALUE': '1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
            outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}
            
        
        # Extract by attribute
        alg_params = {
            'FAIL_OUTPUT': None,
            'FIELD': 'speed',
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/joined_layer.geojson',
            'OPERATOR': 2,
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/extracted_layer1.geojson',
            'VALUE': '1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Join attributes by nearest
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELDS_TO_COPY': ['speed'],
            'INPUT': path,
            'INPUT_2': '/Users/asdfasd/Downloads/grmd3106 project/extracted_layer1.geojson',
            'MAX_DISTANCE': None,
            'NEIGHBORS': 1,
            'NON_MATCHING': 'TEMPORARY_OUTPUT',
            'OUTPUT': '/Users/asdfasd/Downloads/grmd3106 project/road_assigned_speed.geojson',
            'PREFIX': ''
        }
        outputs['JoinAttributesByNearest'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Shortest path (point to layer)
        alg_params = {
            'DEFAULT_DIRECTION': 2,
            'DEFAULT_SPEED': 51,
            'DIRECTION_FIELD': '',
            'END_POINTS': parameters['destpoints'],
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/road_assigned_speed.geojson',
            'SPEED_FIELD': 'speed',
            'START_POINT': parameters['asdf'],
            'STRATEGY': 1,
            'TOLERANCE': 0,
            'VALUE_BACKWARD': '',
            'VALUE_BOTH': '',
            'VALUE_FORWARD': '',
            'OUTPUT': parameters['Shortest_path']
        }
        outputs['ShortestPathPointToLayer'] = processing.run('native:shortestpathpointtolayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Shortest_path'] = outputs['ShortestPathPointToLayer']['OUTPUT']
        return results'''
        return {}

    def name(self):
        return 'model'

    def displayName(self):
        return 'model'

    def group(self):
        return '1'

    def groupId(self):
        return '1'
# once we run we create an instance of Model()
    def createInstance(self):
        return Model()
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
      #  
        
        
        
        
''' alg_params = {
            'DEFAULT_DIRECTION': 2,
            'DEFAULT_SPEED': 50,
            'DIRECTION_FIELD': '',
            'END_POINT': parameters['endpoint'],
            'INPUT': '/Users/asdfasd/Downloads/grmd3106 project/simplifiedped.geojson',
            'SPEED_FIELD': '',
            'START_POINT': parameters['startpoint'],
            'STRATEGY': 0,
            'TOLERANCE': 0,
            'VALUE_BACKWARD': '',
            'VALUE_BOTH': '',
            'VALUE_FORWARD': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ShortestPathPointToPoint'] = processing.run('native:shortestpathpointtopoint', alg_params, context=context, feedback=feedback, is_child_algorithm=True)'''
