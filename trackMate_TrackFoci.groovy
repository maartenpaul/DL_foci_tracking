//@ File[] (label = "Input files", style="File") files
//@ File (label="Select folder for output",style="directory") outputFolder
//@ Integer (label="target channel",min=1,max=10, value=1) targetchannel
//@ String (label = "Segmentation method", choices={"DoG spot detector", "Ilastik segmentation"}, style="listBox") spotDetector
//@ String (value="DoG spot detector options", visibility="MESSAGE",required=false) DoGMessage
//@ Double(label="Spot diameter",value=0.5) spotDiameter
//@ Double(label="Quality threshold (spot detection)",value=50.0) spotQuality
//@ String (value="Ilastik spot detector options", visibility="MESSAGE",required=false) IlastikMessage
//@ File (label="Select Ilastik model file",style="file",default="C:/") modelFile
//@ Integer (label="Class index",min=0,max=10, value=1) classindex
//@ String (value="Tracking options", visibility="MESSAGE",required=false) TrackMessage
//@ Double(label="Linking Max Distance (um)",value=1.0) maxDistance
//@ Boolean (label = "Allow Gap Closing?", value=true) allowGap
//@ Integer(label="Maximum Gap (frames)",value=1) maxGap
//@ Double(label="Linking Max Distance (um)",value=1.0) maxGapDistance
//To be added parameters for track splitting an merging

// ImageJ imports
import ij.IJ
import ij.WindowManager
import ij.measure.ResultsTable
import ij.plugin.frame.RoiManager

// Java imports
import java.awt.Frame
import java.io.File
import java.util.ArrayList
import java.util.Collections

// TrackMate imports
import fiji.plugin.trackmate.Model
import fiji.plugin.trackmate.Settings
import fiji.plugin.trackmate.TrackMate
import fiji.plugin.trackmate.SelectionModel
import fiji.plugin.trackmate.Logger
import fiji.plugin.trackmate.io.TmXmlWriter
import fiji.plugin.trackmate.detection.DogDetectorFactory
import fiji.plugin.trackmate.tracking.jaqaman.LAPUtils
import fiji.plugin.trackmate.tracking.jaqaman.SparseLAPTrackerFactory
import fiji.plugin.trackmate.ilastik.IlastikDetectorFactory
import fiji.plugin.trackmate.gui.displaysettings.DisplaySettingsIO
import fiji.plugin.trackmate.gui.displaysettings.DisplaySettings
import fiji.plugin.trackmate.action.fit.SpotFitterController
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter
import fiji.plugin.trackmate.action.IJRoiExporter
import fiji.plugin.trackmate.action.ExportTracksToXML
// import fiji.plugin.trackmate.action.ExtractTrackStackAction  // Commented out as in original

def trackFoci(outputFolder, filename, imp, spotDetector) {
    def outFile = new File(new File(outputFolder, filename), filename + "exportTracks.xml")
	// We have to do the following to avoid errors with UTF8 chars generated in 
	 //TrackMate that will mess with our Fiji Jython.
//	reload(sys)
//	sys.setdefaultencoding('utf-8')
		
	//----------------------------
	// Create the model object now
	//----------------------------
	 
	// Some of the parameters we configure below need to have
	// a reference to the model at creation. So we create an
	// empty model now.
	 
	model = new Model()
	 
	//Send all messages to ImageJ log window.
	model.setLogger(Logger.IJ_LOGGER)
	
	//------------------------
	// Prepare settings object
	//------------------------
		// Configure detector - We use the Strings for the keys 
	settings = new Settings(imp)
	if (spotDetector=="DoG spot detector"){
		detectFociDoG(settings)
	} else if (spotDetector=="Ilastik segmentation"){
		detectFociIlastik(settings)
	}

    print("tracker is set")
	// Configure tracker - We want to allow merges and fusions
	settings.trackerFactory = new SparseLAPTrackerFactory()
	settings.trackerSettings = settings.trackerFactory.getDefaultSettings() // almost good enough

    settings.trackerSettings['LINKING_MAX_DISTANCE'] = maxDistance
    settings.trackerSettings['ALLOW_GAP_CLOSING'] = allowGap
    settings.trackerSettings['MAX_FRAME_GAP'] = maxGap
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = maxGapDistance
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = false
    settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = 1.0d
    settings.trackerSettings['ALLOW_TRACK_MERGING'] = false
    settings.trackerSettings['MERGING_MAX_DISTANCE'] = 1.0d
	// Add ALL the feature analyzers known to TrackMate. They will 
	// yield numerical features for the results, such as speed, mean intensity etc.
	settings.addAllAnalyzers()

	//-------------------
	// Instantiate plugin
	//-------------------

	def trackmate = new TrackMate(model, settings)

	//--------
	// Process
	//--------
	print("now trackis is set")
	def ok = trackmate.checkInput()
	if (!ok) {
	    System.exit(trackmate.getErrorMessage())
	}

	ok = trackmate.process()
	if (!ok) {
	    return
	}

	//----------------
	// Display results
	//----------------

	// A selection.
	def selectionModel = new SelectionModel(model)

	// Read the default display settings.
	def ds = DisplaySettingsIO.readUserDefault()

	// displayer = new HyperStackDisplayer(model, selectionModel, imp, ds)
	// displayer.render()
	// displayer.refresh()

	// Echo results with the logger we set at start:
	model.getLogger().log(model.toString())

	def fm = model.getFeatureModel()

	def trackIDs = new ArrayList(model.getTrackModel().trackIDs(true))

	// Initiate new results table
	def rt = new ResultsTable()

	// Iterate over all the tracks that are visible.
    for (def id : model.getTrackModel().trackIDs(true)) {
        // Fetch the track feature from the feature model. 
        // Get all the spots of the current track.
        // write to resultsTable
        def track = model.getTrackModel().trackSpots(id)
        
        track.each { spot ->
            def sid = spot.ID()
            def x = spot.getFeature('POSITION_X')
            def y = spot.getFeature('POSITION_Y')
            def t = spot.getFeature('FRAME')
            def q = spot.getFeature('QUALITY')
            def snr = spot.getFeature('SNR_CH1')
            def mean = spot.getFeature('MEAN_INTENSITY_CH1')
            def mean_ch3 = spot.getFeature('MEAN_INTENSITY_CH3')
            def radius = spot.getFeature('RADIUS')
            
            model.getLogger().log("\tspot ID = ${sid}, ${x}, ${y}, ${t}, ${q}, ${snr}, ${mean}, ${id}")
            
            rt.addValue("sid", sid)
            rt.addValue("x", x)
            rt.addValue("y", y)
            rt.addValue("t", t)
            rt.addValue("q", snr)
            rt.addValue("mean", mean)
            rt.addValue("mean_ch3", mean_ch3)
            rt.addValue("radius", radius)
            rt.addValue("tid", id)
            rt.addRow()
        }
    }
//	rt.show("ResultsTable")
    def rt_file = new File(new File(outputFolder, filename), filename + "FociTracks.txt")
    rt.save(rt_file.absolutePath)
    rt.reset()
    
    //outFile = new File(outputFolder, filename + "exportFociTracks.xml")
    //ExportTracksToXML.export(model, settings, outFile)
    def outFile_TMXML = new File(new File(outputFolder, filename), filename + "exportFociXML.xml")
    
    def writer = new TmXmlWriter(outFile_TMXML) //a File path object
    writer.appendModel(trackmate.model) //trackmate instantiate like this before trackmate = TrackMate(model, settings)
    writer.appendSettings(trackmate.settings)
    writer.writeToFile()
    
    def rm = RoiManager.getInstance()
    if (!rm) {
        rm = new RoiManager()
    }
    rm.reset()
    
    def spots = trackmate.model.spots.iterable(true)
    def exporter = new IJRoiExporter(trackmate.settings.imp, model.logger)
    exporter.export(spots)
    rm = RoiManager.getInstance()
    rm.runCommand("Select All")
    def roi_name = new File(new File(outputFolder, filename), filename + "FociROI.zip")
    rm.runCommand("Save", roi_name.absolutePath)
}  
def detectFociIlastik(settings) {
    // Configure detector - We use the Strings for the keys
    settings.detectorFactory = new IlastikDetectorFactory()
    settings.detectorSettings = [
        'CLASSIFIER_FILEPATH': modelFile.absolutePath,
        'TARGET_CHANNEL': targetchannel,
        'CLASS_INDEX': classindex,
        'PROBA_THRESHOLD': 0.5
    ]
    return settings
}
def detectFociDoG(settings) {
    settings.detectorFactory = new DogDetectorFactory()
    settings.detectorSettings = [
        'DO_SUBPIXEL_LOCALIZATION': true,
        'RADIUS': spotDiameter/2,  // in TrackMate GUI diameter is used for consistency
        'TARGET_CHANNEL': targetchannel,
        'THRESHOLD': spotQuality,
        'DO_MEDIAN_FILTERING': false
    ]
    return settings
}

def imageN = 0
def totalN = files.size()

files.each { file ->
    IJ.showStatus("Detecting foci in image ${imageN} of a total of ${totalN}")
    IJ.showProgress(imageN, totalN)
    
    def filename = file.getName()
    def filenameParts = filename.split("\\.")
    
    def imp = IJ.openImage(file.absolutePath)
    imp.show()
    trackFoci(outputFolder, filenameParts[0], imp, spotDetector)
    
    imp.changes = false
    imp.close()
    
    imageN++
}