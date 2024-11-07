#@ File[] (label = "Input files", style="File") files
#@ File (label="Select folder for ",style="directory") outputFolder
#@ Integer (label="target channel",min=1,max=10, value=1) targetchannel
#@ String (label = "Segmentation method", choices={"DoG spot detector", "Ilastik segmentation"}, style="listBox") spotDetector
#@ String (value="DoG spot detector options", visibility="MESSAGE",required=false) DoGMessage
#@ Double(label="Spot diameter",value=0.5) spotDiameter
#@ Double(label="Quality threshold (spot detection)",value=50.0) spotQuality
#@ String (value="Ilastik spot detector options", visibility="MESSAGE",required=false) IlastikMessage
#@ File (label="Select Ilastik model file",style="file",default="C:/") modelfolder
#@ Integer (label="Class index",min=1,max=10, value=1) classindex
#@ String (value="Tracking options", visibility="MESSAGE",required=false) TrackMessage
#@ Double(label="Linking Max Distance (um)",value=1.0) maxDistance
#@ Boolean (label = "Allow Gap Closing?", value=true) allowGap
#@ Integer(label="Maximum Gap (frames)",value=1) maxGap
#@ Double(label="Linking Max Distance (um)",value=1.0) maxGapDistance
#To be added parameters for track splitting an merging

import sys
import os
from ij import IJ
from ij import WindowManager
from java.io import File
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from fiji.plugin.trackmate.io import TmXmlWriter
from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.detection import DogDetectorFactory
from fiji.plugin.trackmate.tracking.jaqaman import LAPUtils
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.ilastik import IlastikDetectorFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettings
from fiji.plugin.trackmate.action.fit import SpotFitterController
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.action.IJRoiExporter as IJRoiExporter
import fiji.plugin.trackmate.action.ExportTracksToXML as ExportTracksToXML
#import fiji.plugin.trackmate.action.ExtractTrackStackAction as ExtractTrackStackAction
from java.util import Collections, ArrayList
import java.awt.Frame as Frame

def trackFoci(outputFolder,filename,imp,spotDetector):
	outFile = File(outputFolder, filename+"exportTracks.xml")
	# We have to do the following to avoid errors with UTF8 chars generated in 
	# TrackMate that will mess with our Fiji Jython.
	reload(sys)
	sys.setdefaultencoding('utf-8')
		
	#----------------------------
	# Create the model object now
	#----------------------------
	 
	# Some of the parameters we configure below need to have
	# a reference to the model at creation. So we create an
	# empty model now.
	 
	model = Model()
	 
	# Send all messages to ImageJ log window.
	model.setLogger(Logger.IJ_LOGGER)
	
	#------------------------
	# Prepare settings object
	#------------------------
	 
	settings = Settings(imp)
	if spotDetector=="DoG spot detector":
		detectFociDoG(settings)
	
	elif spotDetector=="Ilastik segmentation":
		detectFociIlastik(settings)
	
	# Configure detector - We use the Strings for the keys
	
	# Configure tracker - We want to allow merges and fusions
	settings.trackerFactory = SparseLAPTrackerFactory()
	settings.trackerSettings = settings.trackerFactory.getDefaultSettings() # almost good enough

	settings.trackerSettings['LINKING_MAX_DISTANCE']  = maxDistance
	settings.trackerSettings['ALLOW_GAP_CLOSING'] = allowGap
	settings.trackerSettings['MAX_FRAME_GAP'] = maxGap
	settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE']  = maxGapDistance
	settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = False
	settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = 1.0
	settings.trackerSettings['ALLOW_TRACK_MERGING'] = False
	settings.trackerSettings['MERGING_MAX_DISTANCE'] = 1.0
	
	# Add ALL the feature analyzers known to TrackMate. They will 
	# yield numerical features for the results, such as speed, mean intensity etc.
	settings.addAllAnalyzers()
	 
	#-------------------
	# Instantiate plugin
	#-------------------
	 
	trackmate = TrackMate(model, settings)
	 
	#--------
	# Process
	#--------
	 
	ok = trackmate.checkInput()
	if not ok:
	    sys.exit(str(trackmate.getErrorMessage()))
	 
	ok = trackmate.process()
	if not ok:
	    return
	
	 #----------------
	# Display results
	#----------------
	 
	# A selection.
	selectionModel = SelectionModel( model )
	 
	# Read the default display settings.
	ds = DisplaySettingsIO.readUserDefault()
	 
#	displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
#	displayer.render()
#	displayer.refresh()
	
	# Echo results with the logger we set at start:
	model.getLogger().log( str( model ) )
	
	fm = model.getFeatureModel()
	
	trackIDs = ArrayList(model.getTrackModel().trackIDs(True))
	
	#initiate new results table
	rt = ResultsTable()
	
	# Iterate over all the tracks that are visible.
	for id in model.getTrackModel().trackIDs(True):
	 
	    # Fetch the track feature from the feature model. 
		# Get all the spots of the current track.
		# write to resultsTable
	    track = model.getTrackModel().trackSpots(id)
	    for spot in track:
	        sid = spot.ID()
	        x=spot.getFeature('POSITION_X')
	        y=spot.getFeature('POSITION_Y')
	        t=spot.getFeature('FRAME')
	        q=spot.getFeature('QUALITY')
	        snr=spot.getFeature('SNR_CH1')
	        mean=spot.getFeature('MEAN_INTENSITY_CH1')
	        mean_ch3=spot.getFeature('MEAN_INTENSITY_CH3')
	        radius=spot.getFeature('RADIUS')
	        model.getLogger().log('\tspot ID = ' + str(sid) + ','+str(x)+','+str(y)+','+str(t)+','+str(q) + ','+str(snr) + ',' + str(mean)+","+str(id))
	        rt.addValue("sid",sid)
	        rt.addValue("x",x)
	        rt.addValue("y",y)
	        rt.addValue("t",t)
	        rt.addValue("q",snr)
	        rt.addValue("mean",mean)
	        rt.addValue("mean_ch3",mean_ch3)
	        rt.addValue("radius",radius)
	        rt.addValue("tid",id)
	        rt.addRow()
	
#	rt.show("ResultsTable")
	
	rt_file = File(outputFolder ,filename+"FociTracks.txt")
	rt.save(rt_file.getAbsolutePath())
	rt.reset()
	
	#outFile = File(outputFolder, filename+"exportFociTracks.xml")
	#ExportTracksToXML.export(model, settings, outFile)
	outFile_TMXML= File(outputFolder, filename+"exportFociXML.xml")
	
	writer = TmXmlWriter(outFile_TMXML) #a File path object
	writer.appendModel(trackmate.getModel()) #trackmate instantiate like this before trackmate = TrackMate(model, settings)
	writer.appendSettings(trackmate.getSettings())
	writer.writeToFile()
	
	rm = RoiManager.getInstance()
	if not rm:
	      rm = RoiManager()
	rm.reset()
	
	spots = trackmate.getModel().getSpots().iterable(True)
	exporter = IJRoiExporter(trackmate.getSettings().imp, model.getLogger())
	exporter.export(spots)
	rm = RoiManager.getInstance()
	rm.runCommand("Select All")
	roi_name = File(outputFolder,filename+"FociROI.zip")
	rm.runCommand("Save", roi_name.getAbsolutePath())

def detectFociIlastik(settings):
	# Configure detector - We use the Strings for the keys
	settings.detectorFactory = IlastikDetectorFactory()
	settings.detectorSettings = {
    'CLASSIFIER_FILEPATH' : modelfolder.getAbsolutePath(),
    'TARGET_CHANNEL' : targetchannel,
    'CLASS_INDEX' : classindex,
    'PROBA_THRESHOLD' : 0.5,  
	}  
	return settings
	
def detectFociDoG(settings):
	settings.detectorFactory = DogDetectorFactory()
	settings.detectorSettings = {
	    'DO_SUBPIXEL_LOCALIZATION' : True,
	    'RADIUS' : spotDiameter/2, #in TrackMate GUI diameter is used so for consistancy also use diameter instead of spot radius
	    'TARGET_CHANNEL' : targetchannel,
	    'THRESHOLD' : spotQuality,
	    'DO_MEDIAN_FILTERING' : False,  
	}  
	return settings
	 
imageN = 0	
totalN = len(files)
for file in files:
	imageN=imageN+1
	IJ.showStatus("Detecting foci in image "+str(imageN)+" of a total of "+ str(totalN)+"")
	IJ.showProgress(imageN,totalN)
	filename = file.getName()
	filename=filename.split(".")
	imp = IJ.openImage(file.getAbsolutePath())
	trackFoci(outputFolder,filename[0],imp,spotDetector)
	imp.changes = False
	imp.close()

