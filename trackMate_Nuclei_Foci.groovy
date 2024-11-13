#@ File[] (label="Select input file(s)", style="files") input_files
#@ File (label="Select output folder", style="directory") outputfolder
#@ Integer (label="Nuclei channel", value=1) nucleiChannel
#@ Integer (label="Foci channel", value=2) fociChannel
#@ Integer (label="Minimum nucleus area", value=100) minNucleusArea
#@ Integer (label="Maximum nucleus area", value=10000) maxNucleusArea
#@ Integer (label="Minimum nucleus track length (frames)", value=4) minTrackLength
#@ Double (label="Nuclei detection downscale", min=1.0, max=10.0, value=1.0) downscale
#@ Double (label="Saturate", min=0.0, max=100.0, value=0.0) saturate
#@ Boolean (label="Register nuclei in track stacks?", value=true) registerNucleus
#@ Boolean (label="Use label map instead of StarDist?", value=false) useLabelMap
#@ String (label="Label map suffix", value="_prediction.tif", required=false) labelMapSuffix
#@ String (value="Foci detection", visibility="MESSAGE",required=false) FociMessage
#@ Boolean (label="Track Foci in individual cells?", value=false) trackFoci
#@ String (label = "Segmentation method", choices={"DoG spot detector", "Ilastik segmentation"}, style="listBox") spotDetector
#@ Integer (label="Class index",min=0,max=10, value=1) classIndex
#@ String (value="Ilastik spot detector options", visibility="MESSAGE",required=false) IlastikMessage
#@ File (label="Select Ilastik model file",style="file",default="C:/") modelFolder
#@ Double (label="Foci spot diameter (μm)", value=0.5) spotDiameter
#@ Double (label="Foci quality threshold", value=50.0) spotQuality
#@ Double (label="Foci linking max distance (μm)", value=1.0) maxDistance
#@ Boolean (label="Allow foci gap closing", value=true) allowGap
#@ Integer (label="Maximum foci gap (frames)", value=1) maxGap
#@ Double (label="Maximum gap closing distance (μm)", value=1.0) maxGapDistance

import ij.IJ
import ij.ImagePlus
import ij.WindowManager
import ij.plugin.frame.RoiManager
import ij.measure.ResultsTable
import ij.plugin.Duplicator
import fiji.plugin.trackmate.Model
import fiji.plugin.trackmate.Settings
import fiji.plugin.trackmate.TrackMate
import fiji.plugin.trackmate.SelectionModel
import fiji.plugin.trackmate.Logger
import fiji.plugin.trackmate.io.TmXmlWriter
import fiji.plugin.trackmate.io.CSVExporter
import fiji.plugin.trackmate.detection.LabelImageDetectorFactory
import fiji.plugin.trackmate.detection.DogDetectorFactory
import fiji.plugin.trackmate.stardist.StarDistDetectorFactory
import fiji.plugin.trackmate.tracking.overlap.OverlapTrackerFactory
import fiji.plugin.trackmate.tracking.jaqaman.SparseLAPTrackerFactory
import fiji.plugin.trackmate.gui.displaysettings.DisplaySettingsIO
import fiji.plugin.trackmate.gui.displaysettings.DisplaySettings
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter
import fiji.plugin.trackmate.action.IJRoiExporter
import fiji.plugin.trackmate.action.LabelImgExporter
import fiji.plugin.trackmate.action.ExportTracksToXML
import fiji.plugin.trackmate.action.ExtractTrackStackAction
import plugin.trackmate.examples.action.ExtractTrackStackActionMP
import fiji.plugin.trackmate.io.TmXmlWriter
import java.awt.Frame
import java.io.File
import java.util.ArrayList
import java.io.FileReader
import ij.plugin.ChannelSplitter
import fiji.plugin.trackmate.visualization.table.TrackTableView


// New method to read CSV once and return frame counts map
def getFociCountsMap(File csvFile, int startFrame) {
    def frameCounts = [:]
    def lines = []
    
    try {
        def allLines = csvFile.readLines()
        def header = allLines[0]
        
        // Debug: Print total lines
        logInfo("Total lines in CSV: ${allLines.size()}")
        
        // Add new column to header
        def newHeader = header + "\tt_original"
        lines.add(newHeader)
        
        // Initialize frame counts to 0
        def maxFrame = -1
        allLines.tail().each { line ->
            if (!line.trim().isEmpty()) {
                def parts = line.split("\t")
                if (parts.length >= 4) {
                    try {
                        def frameNum = Integer.parseInt(parts[3].trim())
                        maxFrame = Math.max(maxFrame, frameNum)
                    } catch (NumberFormatException e) {}
                }
            }
        }
        
        // Initialize all frames to 0
        (0..maxFrame).each { frame ->
            frameCounts[frame] = 0
        }
        
        // Count spots per frame
        allLines.tail().each { line ->
            if (!line.trim().isEmpty()) {
                def parts = line.split("\t")
                if (parts.length >= 4) {
                    try {
                        def frameNum = Integer.parseInt(parts[3].trim())
                        frameCounts[frameNum]++
                        
                        // Add original timeframe
                        def t_original = frameNum + startFrame
                        lines.add(line + "\t" + t_original)
                        
                        // Debug: Print frame counts
                        logInfo("Frame ${frameNum}: count = ${frameCounts[frameNum]}")
                    } catch (NumberFormatException e) {
                        logError("Invalid frame number in line: ${line}")
                        lines.add(line + "\t")
                    }
                }
            }
        }
        
        // Write back to file with new column
        csvFile.text = lines.join("\n")
        
    } catch (Exception e) {
        logError("Error processing foci CSV: ${e.message}")
    }
    return frameCounts
}

def runFociTracking(trackStackPath, fociOutputFolder, spotID) {
    def scriptPath = "script:C:\\Fiji.app\\scripts\\My Plugins\\Ubuntu\\MP_TrackFoci_batch_Trackmate.py"
    // def modelFolder = new File("C:\\")  // Default model folder path
    // def classIndex = 1  // Default class index for spot detection
    def command = String.format(Locale.US,
        "files=[%s] " +
        "outputfolder=[%s] " +
        "targetchannel=%d " +
        "spotdetector=[%s] " +
        "spotdiameter=%.1f " +
        "spotquality=%.1f " +
        "modelfolder=[%s] " +  // Changed to use format specifier
        "classindex=%d " +
        "maxdistance=%.1f " +
        "allowgap=%b " +
        "maxgap=%d " +
        "maxgapdistance=%.1f ",
        trackStackPath,
        fociOutputFolder.absolutePath,
        fociChannel,
        spotDetector,
        spotDiameter,
        spotQuality,
        modelFolder.absolutePath,
        classIndex,  // classindex as integer
        maxDistance,
        allowGap,
        maxGap,
        maxGapDistance
    )
    
	logInfo(command)
    IJ.run("MP TrackFoci batch Trackmate", command)
    
    // Wait a bit to ensure file is written
    Thread.sleep(1000)
}


// Logging functions
def logInfo(message) {
    IJ.log("INFO: $message")
}

def logError(message) {
    IJ.log("ERROR: $message")
}

// Input validation
def validateInputs() {
    if (nucleiChannel < 1) {
        logError("Nuclei channel must be >= 1")
        return false
    }
    if (minNucleusArea >= maxNucleusArea) {
        logError("Minimum nucleus area must be less than maximum nucleus area")
        return false
    }
    if (minTrackLength < 1) {
        logError("Minimum track length must be >= 1")
        return false
    }
    if (downscale < 1.0 || downscale > 10.0) {
        logError("Downscale must be between 1.0 and 10.0")
        return false
    }
    if (saturate < 0.0 || saturate > 100.0) {
        logError("Saturate must be between 0.0 and 100.0")
        return false
    }
    return true
}

// Cleanup function
def cleanup() {
    WindowManager.getIDList().each { id ->
        def imp = WindowManager.getImage(id)
        if (imp) {
            imp.changes = false
            imp.close()
        }
    }
}

// Center ROI function
def centerRoi(imp) {
    def roi = imp.getRoi()
    def bounds = roi.getBounds()
    def width = imp.getWidth()
    def height = imp.getHeight()
    def offsetX = (width / 2) - (bounds.width / 2)
    def offsetY = (height / 2) - (bounds.height / 2)
    roi.setLocation(offsetX as int, offsetY as int)
    imp.setRoi(roi)
    return imp
}

// Class to handle foci data collection
class FociDataCollector {
    private File outputFile
    private List buffer
    private int bufferSize
    private BufferedWriter writer
    
    FociDataCollector(String outputPath) {
        outputFile = new File(outputPath)
        buffer = []
        bufferSize = 1000
        initializeFile()
    }
    
    private void initializeFile() {
        writer = outputFile.newWriter(false)
        writer.writeLine("Movie,Frame,Nucleus_Track_ID,Nucleus_ID,Focus_Track_ID,Focus_ID," +
                        "Focus_X,Focus_Y,Focus_Intensity,Focus_Area,Focus_Quality,Original_Frame")
        writer.flush()
    }
    
    void addFocus(Map data) {
        buffer << data
        if (buffer.size() >= bufferSize) {
            writeBuffer()
        }
    }
    
    private void writeBuffer() {
        if (!buffer.isEmpty()) {
            buffer.each { data ->
                writer.writeLine("${data.movie},${data.frame},${data.nucleus_track_id}," +
                               "${data.nucleus_id},${data.focus_track_id},${data.focus_id}," +
                               "${data.x},${data.y},${data.intensity},${data.area}," +
                               "${data.quality},${data.original_frame}")
            }
            writer.flush()
            buffer.clear()
        }
    }
    
    void finalize() {
        writeBuffer()
        writer.close()
    }
}

// Process image function
def processImage(imp) {
    def impTemp
    if (useLabelMap) {
        def impPath = imp.originalFileInfo.directory
        def impName = imp.title.tokenize('.')[0]
        def labelMapPath = new File(impPath, "${impName}_prediction.tif")
        impTemp = IJ.openImage(labelMapPath.absolutePath)
        if (!impTemp) {
            logError("Label map not found at ${labelMapPath.absolutePath}")
            return null
        }
        impTemp.setCalibration(imp.getCalibration())
        // Convert Z-stack to time series if needed
        def dims = impTemp.getDimensions()
        if (dims[3] > 1 && dims[4] == 1) {  // If Z > 1 and T == 1
            IJ.run(impTemp, "Stack to Hyperstack...", 
                  "order=xyczt(default) channels=1 slices=1 frames=${dims[3]} display=Grayscale")
        }
    } else {
        impTemp = imp.duplicate()
        impTemp.setC(nucleiChannel)
        if (saturate > 0.0) {
            IJ.run(impTemp, "Enhance Contrast...", "saturated=$saturate process_all")
        }
        if (downscale != 1.0) {
            def width = (impTemp.width / downscale) as int
            def height = (impTemp.height / downscale) as int
            IJ.run(impTemp, "Size...", "width=$width height=$height constrain interpolation=None")
        }
    }
    return impTemp
}

// Process file
def processFile(file,trackFoci) {
    // Initialize ResultsTable
    def rt = new ResultsTable()
    logInfo("Processing file: ${file.absolutePath}")
    
    def imp = IJ.openImage(file.absolutePath)
    if (!imp) {
        logError("Failed to open image: ${file.absolutePath}")
        return
    }
    
    imp.show()
    
    // Create output folders
    def fileName = file.name.tokenize('.')[0]
    def fileOutputFolder = new File(outputfolder, fileName)
    fileOutputFolder.mkdirs()
    
    // Process input image for TrackMate
    def impTemp = processImage(imp)
    if (!impTemp) {
        logError("Failed to process image: ${file.absolutePath}")
        return
    }
       
    def fociCollector = new FociDataCollector(
        new File(fileOutputFolder, "detailed_foci.csv").absolutePath
    )
    
    def model = new Model()
    model.setLogger(Logger.IJ_LOGGER)
    def settings = new Settings(impTemp)
    
    // Configure nucleus detector
    if (useLabelMap) {
        settings.detectorFactory = new LabelImageDetectorFactory()
        settings.detectorSettings = [
            TARGET_CHANNEL: 1,
            SIMPLIFY_CONTOURS: false
        ]
    } else {
        settings.detectorFactory = new StarDistDetectorFactory()
        settings.detectorSettings = [
            TARGET_CHANNEL: nucleiChannel
        ]
    }
    
    // Add filters and configure tracker
    settings.addSpotFilter(new FeatureFilter('AREA', minNucleusArea as Double, true))
    settings.addSpotFilter(new FeatureFilter('AREA', maxNucleusArea as Double, false))
    
    settings.trackerFactory = new OverlapTrackerFactory()
    settings.trackerSettings = [
        IOU_CALCULATION: "PRECISE",
        MIN_IOU: 0.2 as Double,
        SCALE_FACTOR: 1.0 as Double
    ]
    
    settings.addAllAnalyzers()
    settings.addTrackFilter(new FeatureFilter('NUMBER_SPOTS', minTrackLength, true))
    
    // Initialize and run TrackMate

    def trackmate = new TrackMate(model, settings)
    if (!trackmate.checkInput() || !trackmate.process()) {
        logError("Error in TrackMate: ${trackmate.getErrorMessage()}")
        return
    }
    
    // Setup display
    def selectionModel = new SelectionModel(model)
    def ds = DisplaySettingsIO.readUserDefault()
    
    // Save label image
   // def labelImp = LabelImgExporter.createLabelImagePlus(trackmate, false, true, 
   //                LabelImgExporter.LabelIdPainting.LABEL_IS_TRACK_ID)
   // labelImp.show()
   // IJ.run(labelImp, "Size...", "width=${imp.width} height=${imp.height} constrain interpolation=None")
   // IJ.saveAsTiff(labelImp, new File(fileOutputFolder, "labelmap.tif").absolutePath)
   // labelImp.close()
    
    // Project tracks on original image
    imp.show()
    
    // Create track visualization
    settings = settings.copyOn(imp)
    trackmate = new TrackMate(model, settings)
    def displayer = new HyperStackDisplayer(model, selectionModel, imp, ds)
    displayer.render()
    displayer.refresh()
    
    // Initialize RoiManager once at the start
    def rm = RoiManager.getInstance()
    if (rm == null) {
        rm = new RoiManager()
    }
    rm.reset()
    
    // Define frame property
    def frame = new Frame()
    
    // Process individual tracks
    model.getTrackModel().trackIDs(true).each { trackID ->
        selectionModel.clearSelection()
        def track = new ArrayList(model.getTrackModel().trackSpots(trackID))
        
        // Validate track
        if (track.isEmpty()) {
            logError("Empty track found for trackID: ${trackID}")
            return
        }
        
        def spot = track[0]
        def spotID = spot.ID()
        
        try {
            // Clear any existing windows
            
            selectionModel.addSpotToSelection(spot)
            
            // Extract track stack with validation
            def ETSA = new ExtractTrackStackActionMP()
            def disp = new DisplaySettings()
            
            // Ensure stack index is within valid range
            def stackTrack = ETSA.execute(trackmate, selectionModel, disp, frame)
            def impStack = WindowManager.getCurrentImage()
            
            if (impStack == null || impStack.getStackSize() < 1) {
                logError("Invalid stack created for track ${trackID}")
                return
            }
            
            // Log stack info
            logInfo("Track ${trackID}: Stack size = ${impStack.getStackSize()}")
            
            // Save track stack
            def trackStackPath = new File(fileOutputFolder, "${spotID}stack.tif").absolutePath
            IJ.saveAsTiff(impStack, trackStackPath)
            
            // Process foci if needed
            if (trackFoci) {
                runFociTracking(trackStackPath, fociOutputFolder, spotID)
                
                // Get first frame and read foci counts once
                def startFrame = track[0].getFeature('FRAME') as int
                def fociCSV = new File(fociOutputFolder, "${spotID}stackFociTracks.txt")
                def frameCounts = getFociCountsMap(fociCSV, startFrame)
            } else {
                def fociCount = 0
            }
            
            // Process each nucleus using cached counts
            track.each { nucleus ->
                def frameSpot = nucleus.getFeature('FRAME') as int
                def nucleusId = nucleus.ID()
                
                try {

                    
                    rt.incrementCounter()
                    rt.addValue("Track ID", trackID)
                    rt.addValue("Spot ID", nucleusId)
                    rt.addValue("Frame", frameSpot)
                    rt.addValue("X", nucleus.getFeature('POSITION_X'))
                    rt.addValue("Y", nucleus.getFeature('POSITION_Y'))
                    rt.addValue("Area", nucleus.getFeature('AREA'))
                    if (trackFoci) {
                    	def fociCount = frameCounts[frameSpot - startFrame] ?: 0
                    	rt.addValue("Foci Count", fociCount)
                    }
                } catch (Exception e) {
                    logError("Error processing nucleus ${nucleusId} in frame ${frameSpot}: ${e.message}")
                }
            }
            
            impStack.close()
        } catch (Exception e) {
            logError("Error processing track ${trackID}: ${e.message}")
        }
    }

    // After track processing but before final cleanup:
    try {
        // Clear existing ROIs
        rm.reset()

        // Export all spots to ROIs
        def spots = model.getSpots().iterable(true)
        def exporter = new IJRoiExporter(imp, model.getLogger())
        exporter.export(spots)

        // Save all ROIs
        if (rm.getCount() > 0) {
            rm.runCommand("Select All")
            def movieName = file.getName().take(file.getName().lastIndexOf('.'))
            def roiZipPath = new File(fileOutputFolder, "${movieName}_AllROIs.zip")
            rm.runCommand("Save", roiZipPath.absolutePath)
        }
        rm.reset()
    } catch (Exception e) {
        logError("Error saving ROIs: ${e.message}")
    }

    // Continue with table exports
    def spotTable = TrackTableView.createSpotTable(model, ds)
    spotTable.exportToCsv(new File(fileOutputFolder, "all_track_spots.csv"))
    
	def only_visible = false
	// If you set this flag to False, it will include all the spots,
	// the ones not in tracks, and the ones not visible.
	CSVExporter.exportSpots( new File(fileOutputFolder, "all_nuclei_spots.csv").absolutePath, model, only_visible )

    def trackTable = TrackTableView.createTrackTable(model, ds)
    trackTable.exportToCsv(new File(fileOutputFolder, "all_nuclei_tracks.csv"))
	if (trackFoci) {
    // Save results
    	rt.save(new File(fileOutputFolder, "combined_results.csv").absolutePath)
    	fociCollector.finalize()
	}
    
    // After all tracks are processed, save combined ROIs
    // Add this before final cleanup:
    try {
        if (rm != null && rm.getCount() > 0) {
            rm.runCommand("Select All")
            def movieName = file.getName().take(file.getName().lastIndexOf('.'))
            def roiPath = new File(fileOutputFolder, "${movieName}_AllROIs.zip")
            rm.runCommand("Save", roiPath.absolutePath)
        }
        rm.reset()
    } catch (Exception e) {
        logError("Error saving combined ROIs: ${e.message}")
    }
    def outFile_TMXML = new File(fileOutputFolder, "nuclei_XML.xml")
	def writer = new TmXmlWriter(outFile_TMXML) //a File path object
	writer.appendModel(trackmate.getModel()) //trackmate instantiate like this before trackmate = TrackMate(model, settings)
	writer.appendSettings(trackmate.getSettings())
	writer.writeToFile()
    // Cleanup
    imp.close()
    impTemp.close()
    cleanup()
    
    logInfo("Processing complete for file: ${file.absolutePath}")
}

// Main execution
if (validateInputs()) {
    input_files.each { file ->
        processFile(file,trackFoci)
    }
    logInfo("All files processed. Results saved in ${outputfolder.absolutePath}")
} else {
    IJ.error("Invalid inputs")
}