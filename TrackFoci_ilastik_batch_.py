#@ File (label="Select folder for output",style="directory") outputfolder
#@ File (label="Select folder with model",style="file") modelfolder
#@ Integer (label="target channel",min=1,max=10, value=1) targetchannel
#@ Integer (label="Class index",min=1,max=10, value=1) classindex

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
from fiji.plugin.trackmate.tracking import LAPUtils
from fiji.plugin.trackmate.ilastik import IlastikDetectorFactory
from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
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


ch_name = "ch"+str(targetchannel)
outFile = File(outputfolder, ch_name+"exportTracks.xml")
print(outFile)
# We have to do the following to avoid errors with UTF8 chars generated in 
# TrackMate that will mess with our Fiji Jython.
reload(sys)
sys.setdefaultencoding('utf-8')
# Get currently selected image
imp = WindowManager.getCurrentImage()
logger = Logger.IJ_LOGGER
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
 
# Configure detector - We use the Strings for the keys
settings.detectorFactory = IlastikDetectorFactory()
settings.detectorSettings = {
    'CLASSIFIER_FILEPATH' : modelfolder.getAbsolutePath(),
    'TARGET_CHANNEL' : targetchannel,
    'CLASS_INDEX' : classindex,
    'PROBA_THRESHOLD' : 0.5,  
}  

# Configure spot filters - Classical filter on quality
#filter1 = FeatureFilter('AREA', 100, True)
#settings.addSpotFilter(filter1)
 
# Configure tracker - We want to allow merges and fusions
settings.trackerFactory = SparseLAPTrackerFactory()
settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap() # almost good enough

settings.trackerSettings['LINKING_MAX_DISTANCE']  = 3.0
settings.trackerSettings['ALLOW_GAP_CLOSING'] = True
settings.trackerSettings['MAX_FRAME_GAP'] = 1
settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE']  = 2.0
settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = 1.0
settings.trackerSettings['ALLOW_TRACK_MERGING'] = True
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
    sys.exit(str(trackmate.getErrorMessage()))

 #----------------
# Display results
#----------------
 
# A selection.
selectionModel = SelectionModel( model )
 
# Read the default display settings.
ds = DisplaySettingsIO.readUserDefault()
 
displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
displayer.render()
displayer.refresh()

# Echo results with the logger we set at start:
model.getLogger().log( str( model ) )

fm = model.getFeatureModel()

trackIDs = ArrayList(model.getTrackModel().trackIDs(True))

#controller = SpotFitterController(trackmate,selectionModel,model.getLogger().log( str( model ) ))
#controller.show()

#initiate new results table for spots
rt = ResultsTable()

spots = trackmate.getModel().getSpots().iterable(True)

for spot in spots:
	sid = spot.ID()
	x=spot.getFeature('POSITION_X')
	y=spot.getFeature('POSITION_Y')
	t=spot.getFeature('FRAME')
	q=spot.getFeature('QUALITY')
	snr=spot.getFeature('SNR_CH1')
	total_ch1=spot.getFeature('TOTAL_INTENSITY_CH1')
	total_ch2=spot.getFeature('TOTAL_INTENSITY_CH2')
	total_ch3=spot.getFeature('TOTAL_INTENSITY_CH3')
	mean_ch1=spot.getFeature('MEAN_INTENSITY_CH1')
	mean_ch2=spot.getFeature('MEAN_INTENSITY_CH2')
	mean_ch3=spot.getFeature('MEAN_INTENSITY_CH3')
	area=spot.getFeature('AREA')
	radius=spot.getFeature('RADIUS')
	model.getLogger().log('\tspot ID = ' + str(sid) + ','+str(x)+','+str(y)+','+str(t)+','+str(q) + ','+str(snr) + ',' + str(mean_ch1)+","+str(id))
	rt.addValue("sid",sid)
	rt.addValue("x",x)
	rt.addValue("y",y)
	rt.addValue("t",t)
	rt.addValue("q",snr)
	rt.addValue("total_ch1",total_ch1)
	rt.addValue("total_ch2",total_ch2)
	rt.addValue("total_ch3",total_ch3)
	rt.addValue("mean_ch1",mean_ch1)
	rt.addValue("mean_ch2",mean_ch2)
	rt.addValue("mean_ch3",mean_ch3)
	rt.addValue("area",area)
	rt.addValue("radius",radius)
	rt.addRow()



rt.show("ResultsTable")
rt_file = File(outputfolder ,ch_name+"_FociSpots.txt")
rt.save(rt_file.getAbsolutePath())
rt.reset()

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
       	total_ch1=spot.getFeature('TOTAL_INTENSITY_CH1')
        total_ch2=spot.getFeature('TOTAL_INTENSITY_CH2')
        total_ch3=spot.getFeature('TOTAL_INTENSITY_CH3')
        mean_ch1=spot.getFeature('MEAN_INTENSITY_CH1')
        mean_ch2=spot.getFeature('MEAN_INTENSITY_CH2')
        mean_ch3=spot.getFeature('MEAN_INTENSITY_CH3')
        area=spot.getFeature('AREA')
        radius=spot.getFeature('RADIUS')
        model.getLogger().log('\tspot ID = ' + str(sid) + ','+str(x)+','+str(y)+','+str(t)+','+str(q) + ','+str(snr) + ',' + str(mean_ch1)+","+str(id))
        rt.addValue("sid",sid)
        rt.addValue("x",x)
        rt.addValue("y",y)
        rt.addValue("t",t)
        rt.addValue("q",snr)
        rt.addValue("total_ch1",total_ch1)
        rt.addValue("total_ch2",total_ch2)
        rt.addValue("total_ch3",total_ch3)
        rt.addValue("mean_ch1",mean_ch1)
        rt.addValue("mean_ch2",mean_ch2)
        rt.addValue("mean_ch3",mean_ch3)
        rt.addValue("area",area)
        rt.addValue("radius",radius)
        rt.addValue("tid",id)
        rt.addRow()
logger.log(str(rt.size()))

rt.show("ResultsTable")

rt_file = File(outputfolder ,ch_name+"_FociTracks.txt")
rt.save(rt_file.getAbsolutePath())
rt.reset()

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
       	total_ch1=spot.getFeature('TOTAL_INTENSITY_CH1')
        total_ch2=spot.getFeature('TOTAL_INTENSITY_CH2')
        total_ch3=spot.getFeature('TOTAL_INTENSITY_CH3')
        mean_ch1=spot.getFeature('MEAN_INTENSITY_CH1')
        mean_ch2=spot.getFeature('MEAN_INTENSITY_CH2')
        mean_ch3=spot.getFeature('MEAN_INTENSITY_CH3')
        area=spot.getFeature('AREA')
        radius=spot.getFeature('RADIUS')
        model.getLogger().log('\tspot ID = ' + str(sid) + ','+str(x)+','+str(y)+','+str(t)+','+str(q) + ','+str(snr) + ',' + str(mean_ch1)+","+str(id))
        rt.addValue("sid",sid)
        rt.addValue("x",x)
        rt.addValue("y",y)
        rt.addValue("t",t)
        rt.addValue("q",snr)
        rt.addValue("total_ch1",total_ch1)
        rt.addValue("total_ch2",total_ch2)
        rt.addValue("total_ch3",total_ch3)
        rt.addValue("mean_ch1",mean_ch1)
        rt.addValue("mean_ch2",mean_ch2)
        rt.addValue("mean_ch3",mean_ch3)
        rt.addValue("area",area)
        rt.addValue("radius",radius)
        rt.addValue("tid",id)
        rt.addRow()

rt.show("ResultsTable")

rt_file = File(outputfolder ,ch_name+"_FociTracks.txt")
rt.save(rt_file.getAbsolutePath())
rt.reset()

outFile = File(outputfolder, ch_name+"_exportFociTracks.xml")
ExportTracksToXML.export(model, settings, outFile)
outFile_TMXML= File(outputfolder, ch_name+"_exportFociXML.xml")

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
roi_name = File(outputfolder,ch_name+"_fociROI.zip")
rm.runCommand("Save", roi_name.getAbsolutePath())
