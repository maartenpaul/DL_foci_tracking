#@ File (label="Select folder for ",style="directory") outputfolder
#@ Integer (label = "Segmentation channel", value = 1) segmentationChannel
#@ Integer (label = "Minimum nucleus area", value = 100) minNucleusArea
#@ Integer (label = "Maximum nucleus area", value = 10000) maxNucleusArea
#@ Integer (label = "Minimum nucleus track length (frames)", value = 4) minTrackLength
#@ Double (label="Downscale",min=1.0,max=10.0, value=1.0) downscale
#@ Double (label="Saturate",min=0.0,max=100.0, value=0.0) saturate
#@ Boolean (label = "Register nuclei in track stacks?", value=true) registerNucleus

# Script to segment and track nuclei in a time lapse movie using Stardist and Trackmate and export tracked nuclei to separate image Stacks
# To run the script you need to activate the following Fiji update sites:
# - TrackMate
# - TrackMate-StarDist
# - StarDist
# - CSBdeep
# The script will return the following files:
# - exportTracks.xml
# Author: Maarten Paul, Erasmus MC, Rotterdam (m.w.paul@erasmusmc.nl)

import sys
import os
from ij import IJ
from ij import WindowManager
from java.io import File
from ij.plugin.frame import RoiManager
import ij.plugin.Duplicator as Duplicator
from ij.measure import ResultsTable
from fiji.plugin.trackmate.io import TmXmlWriter
from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.stardist import StarDistDetectorFactory
from fiji.plugin.trackmate.tracking.jaqaman import LAPUtils
from fiji.plugin.trackmate.tracking.overlap import OverlapTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettings
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.action.IJRoiExporter as IJRoiExporter
import fiji.plugin.trackmate.action.ExportTracksToXML as ExportTracksToXML
import fiji.plugin.trackmate.action.ExtractTrackStackAction as ExtractTrackStackAction
import fiji.plugin.trackmate.action.LabelImgExporter as LabelImgExporter
import plugin.trackmate.examples.action.ExtractTrackStackActionMP as ExtractTrackStackActionMP
from java.util import Collections, ArrayList
import java.awt.Frame as Frame
 
def center_roi(imp):
	roiImp = imp.getRoi()
	impDimensions = imp.getDimensions()
	bounds = roiImp.getBounds()
	offset_x = (impDimensions[0]/2)-(bounds.getWidth()/2)
	offset_y = (impDimensions[1]/2)-(bounds.getHeight()/2)
	roiImp.setLocation(offset_x,offset_y)
	imp.setRoi(roiImp)
	return imp

# Get currently selected image
imp= IJ.getImage()
imp_dimensions=imp.getDimensions() #width, height, nChannels, nSlices, nFrames
imp_temp = Duplicator().run(imp,segmentationChannel,segmentationChannel,1,imp_dimensions[3],1,imp_dimensions[4])
imp_temp.show()
#imp_temp.show()
if saturate>0.0:
	IJ.run(imp_temp,"Enhance Contrast...", "saturated="+str(saturate)+" process_all")

reload(sys)

sys.setdefaultencoding('utf-8')

# when downscaling for StarDist include an additional routine to use a label image 
if downscale != 1.0:

	x = imp_temp.getDimensions()[0]
	y = imp_temp.getDimensions()[1]
	IJ.run(imp_temp,"Size...", "width=" + str(x/downscale) + " height="+ str(y/downscale) +" constrain interpolation=None")
		
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
	 
settings = Settings(imp_temp)
	 
# Configure detector - We use the Strings for the keys
settings.detectorFactory = StarDistDetectorFactory()
settings.detectorSettings = {
    'TARGET_CHANNEL' : segmentationChannel,
}  
# Configure spot filters - Classical filter on quality
filter1 = FeatureFilter('AREA', minNucleusArea, True)
settings.addSpotFilter(filter1)
filter2 = FeatureFilter('AREA', maxNucleusArea, False)
settings.addSpotFilter(filter2)

# Configure tracker - We want to allow merges and fusions
settings.trackerFactory = OverlapTrackerFactory()
settings.trackerSettings['IOU_CALCULATION'] = "PRECISE"
settings.trackerSettings['MIN_IOU'] = 0.5
settings.trackerSettings['SCALE_FACTOR'] = 1.0
 
# Add ALL the feature analyzers known to TrackMate. They will 
# yield numerical features for the results, such as speed, mean intensity etc.
settings.addAllAnalyzers()

# Filter on track length
filter3 = FeatureFilter('NUMBER_SPOTS', minTrackLength, True)
settings.addTrackFilter(filter3)

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

label_imp=LabelImgExporter.createLabelImagePlus(trackmate,False,True,False)
label_imp.show()
IJ.run(label_imp,"Size...", "width=" + str(x) + " height="+ str(y) +" constrain interpolation=None")
file_name = File(outputfolder,"labelmap.tif")
IJ.saveAsTiff(label_imp,file_name.getAbsolutePath())
label_imp.close()

#project tracks on original image
imp.show()
settings=settings.copyOn(imp)
trackmate = TrackMate(model, settings)
imp_temp.changes = False
imp_temp.close()

displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
displayer.render()
displayer.refresh()

# Echo results with the logger we set at start:
model.getLogger().log( str( model ) )

fm = model.getFeatureModel()

#prepare the stacks with nuclei
trackIDs = ArrayList(model.getTrackModel().trackIDs(True))
Frame = Frame()
####create cropped and aligned nuclei movies
for trackID in trackIDs: 
	selectionModel.clearSelection()
	disp = DisplaySettings()
	track = ArrayList(model.getTrackModel().trackSpots(trackID))
	spot = track[0]
	spotID = spot.ID()
	selectionModel.addSpotToSelection(spot)
	ETSA = ExtractTrackStackActionMP()
	
	stackTrack = ETSA.execute(trackmate,selectionModel,disp,Frame)
	
#save trackstack with trackID
	stackname=str(spotID)+"stack.tif"
	file_name = File(outputfolder,stackname)
	imp= IJ.getImage()
	IJ.saveAsTiff(imp,file_name.getAbsolutePath())

#obtain ROIs from track
	rm = RoiManager.getInstance()
	if not rm:
	      rm = RoiManager()
	rm.reset()
	selectionModel.clearSelection()
	selectionModel.addSpotToSelection(track)
	spots = ArrayList(model.getTrackModel().trackSpots(trackID))
	exporter = IJRoiExporter(trackmate.getSettings().imp, model.getLogger())
	exporter.export(spots)
	rm = RoiManager.getInstance()
	rm.runCommand("Select All")
	roi_name = File(outputfolder,str(spotID)+"stack.zip")
	rm.runCommand("Save", roi_name.getAbsolutePath())
	#clean up signal outside the ROIs in all frames of the stack
	number_roi = rm.getCount()
	number_of_ch = imp.getDimensions()[2]
	rm.runCommand("Sort")
	for i in range(number_roi):
		rm.select(i)
		slice = imp.getSlice()
		for j in range(number_of_ch):
			imp.setC(j+1)
			imp.setT(i+1)
			imp=center_roi(imp)
			IJ.run("Clear Outside", "slice")
	IJ.run("Select None")
	stackname=str(spotID)+"stack_masked.tif"
	file_name = File(outputfolder,stackname)
	IJ.saveAsTiff(imp,file_name.getAbsolutePath())
	if registerNucleus:
		channelsToReg = "channel"
		nChannels = imp_dimensions=imp.getDimensions()[2] #width, height, nChannels, nSlices, nFrames
		print(nChannels)
		for i in range(1,nChannels):
			channelsToReg = channelsToReg+" channel_"+str(i-1)
		print(channelsToReg)	
		IJ.run(imp,"HyperStackReg ", "transformation=[Rigid Body] "+channelsToReg+"")
		
		stackname=str(spotID)+"stack_masked_registered.tif"
		file_name = File(outputfolder,stackname)
		imp_reg= IJ.getImage()
		IJ.saveAsTiff(imp_reg,file_name.getAbsolutePath())
		imp_reg.close()
	imp.close()
		
####

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
        model.getLogger().log('\tspot ID = ' + str(sid) + ','+str(x)+','+str(y)+','+str(t)+','+str(q) + ','+str(snr) + ',' + str(mean)+","+str(id))
        rt.addValue("sid",sid)
        rt.addValue("x",x)
        rt.addValue("y",y)
        rt.addValue("t",t)
        rt.addValue("q",snr)
        rt.addValue("mean",mean)
        rt.addValue("tid",id)
        rt.addRow()

rt.show("ResultsTable")

rt_file = File(outputfolder ,"NucleiTracks.txt")
rt.save(rt_file.getAbsolutePath())
rt.reset()

#outFile = File(outputfolder, "exportTracks.xml")
#ExportTracksToXML.export(model, settings, outFile)
outFile_TMXML= File(outputfolder, "exportXML.xml")

writer = TmXmlWriter(outFile_TMXML) #a File path object
writer.appendModel(trackmate.getModel()) #trackmate instantiate like this before trackmate = TrackMate(model, settings)
writer.appendSettings(trackmate.getSettings())
writer.writeToFile()

