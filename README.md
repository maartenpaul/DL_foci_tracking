# DL foci tracking
Scripts to track cell nuclei and foci within the nuclei from timelapse data

The scripts described below can be placed in the Fiji.app/plugin folder or can be run from the Script editor from Fiji (File->New..->Script.. then File-> Open.. to open the script)

### MP_TrackNuclei_TrackmateStardist.py
Jython script to segment and track nuclei in a time lapse movie using Stardist and Trackmate and export tracked nuclei to separate image Stacks. Apart from using a DNA stain it is also possible to use the signal from a nuclear localized protein. Adjusting the scaling of the image before Stardist segmentation and adjusting the saturation of the image can improve the segmentation.
 To run the script you need to activate the following Fiji update sites:
 - TrackMate
 - TrackMate-StarDist
 - StarDist
 - CSBdeep
 
In addition it requires:
 - Installation of  HyperStackReg_.class in the Fiji.app/plugin folder https://github.com/ved-sharma/HyperStackReg
 - copy the plugin "TrackMate_examples-ExtractStackWithoutDialog.jar" from this Github repository in the Fiji.app/plugin folder
 
The script will return the following files in the selected output folder:
 - labelmap.tif - labelmap of the tracked nuclei
 - ####stack.tif - cropped images of the tracked nuclei
 - ####stack_masked.tif - cropped images of the tracked nuclei with the signal outside the nucleus removed
 - ####stack_masked_registered.tif - cropped images of the tracked nuclei with the signal outside the nucleus removed and registered with HyperstackReg
 - ####stack.zip - ROIs of the segmented nucleus track
 - NucleiTracks.txt - a list of all the segmented nuclei with their image features, more info can be found of these features at the TrackMate website https://imagej.net/plugins/trackmate/
 - exportXML.xml - XML file that allows to load the results in TrackMate for visualization or adjustment of the tracking results
 
 ### MP_TrackNucleiFoci.py
 Jython script for tracking foci for example by selection the masked and registered nuclei in the nuclei tracking script. 
 To run the script you need to activate the following Fiji update sites:
 - TrackMate
 - TrackMate-Ilastik - only required when Ilastik is used for foci segmentation

In addition if Ilastik is used Ilastik need to installed,possibly you need to define the path to the Ilastik executable as is described here: https://imagej.net/plugins/trackmate/detectors/trackmate-ilastik

The script will return the following files for every processed image stack in the selected output folder:
 - ####stackFociROI.zip - ROIs of the segmented foci in the stack
 - ###stackFociTracks.txt - a list of all the detected and tracked foci with their image features, more info can be found of these features at the TrackMate website https://imagej.net/plugins/trackmate/
 - exportFociXML.xml - XML file that allows to load the results in TrackMate for visualization or adjustment of the tracking results
 
Contact: Maarten Paul, Erasmus MC, Rotterdam (m.w.paul@erasmusmc.nl)
