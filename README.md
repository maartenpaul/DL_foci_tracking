# DL_foci_tracking
Scripts to track cell nuclei and foci within the nuclei from timelapse data

## MP_TrackNuclei_TrackmateStardist.py
Script to segment and track nuclei in a time lapse movie using Stardist and Trackmate and export tracked nuclei to separate image Stacks
 To run the script you need to activate the following Fiji update sites:
 - TrackMate
 - TrackMate-StarDist
 - StarDist
 - CSBdeep
In addition it requires 
 - Installation of  HyperStackReg_.class in the Fiji.app/plugin folder https://github.com/ved-sharma/HyperStackReg
 - copy the plugin "TrackMate_examples-ExtractStackWithoutDialog.jar" from this Github repository in the Fiji.app/plugin folder
 
The script will return the following files in the selected output folder:
 - labelmap.tif - labelmap of the tracked nuclei
 - ####stack.tif - cropped images of the tracked nuclei
 - ####stack_masked.tif - cropped images of the tracked nuclei with the signal outside the nucleus removed
 - ####stack_masked_registered.tif - cropped images of the tracked nuclei with the signal outside the nucleus removed and registered with HyperstackReg
 - ####stack.zip - ROIs of the segmented nucleus track
 - NucleiTracks.txt - a list of all the segmented nuclei with their image features, more info can be found of these features at the TrackMate website https://imagej.net/plugins/trackmate/
 - exportTracks.xml - XML file that allows to load the results in TrackMate for 
Contact: Maarten Paul, Erasmus MC, Rotterdam (m.w.paul@erasmusmc.nl)


Contact: Maarten Paul, m.w.paul@erasmusmc.nl
