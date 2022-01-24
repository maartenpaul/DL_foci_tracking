dir = getDir("Choose a Directory");
parent = File.getParent(dir);
foldername = File.getName(dir);
Dialog.create("Title");
Dialog.addNumber("Date:", 210101);
Dialog.addString("Positions:", "1,2,3,4,5,6,7,8,9",15);
Dialog.addString("Channels:", "0,1",5);
Dialog.addNumber("Number of z-slices:", 10);
Dialog.show();
date = Dialog.getNumber();
n_pos = Dialog.getString();
n_pos = split(n_pos, ",");
n_ch = Dialog.getString();
n_ch = split(n_ch, ",");
n_slice = Dialog.getNumber();
for (j=0; j < n_ch.length; j++) {
	n_ch_string=toString(n_ch[j]);
	for (i = 0; i < n_pos.length; i++) {
		n_pos_string=toString(n_pos[i]);
		
		run("Image Sequence...", "open=["+dir+"TileScan_001--Stage"+IJ.pad(n_pos_string, 2)+"--t00--Z00--C"+IJ.pad(n_ch_string, 2)+".tif] file=(Stage"+IJ.pad(n_pos_string, 2)+".*C"+IJ.pad(n_ch_string, 2)+") sort");
		getDimensions(width, height, channels, slices, frames);
		if (slices%n_slice!=0){
			 exit("Number of frames: "+slices+" not dividable by number of Z-slices: "+n_slice); 	
		}
		n_frames=slices/n_slice;
		
		run("Stack to Hyperstack...", "order=xyczt(default) channels=1 slices="+n_slice+" frames="+n_frames+" display=Color");
		saveAs("Tiff", parent+File.separator +date+"_"+foldername +"_ch"+IJ.pad(n_ch_string, 2)+"_p"+IJ.pad(n_pos_string, 3)+".tif");
		run("Z Project...", "projection=[Max Intensity] all");
	
		saveAs("Tiff", parent+File.separator +"MAX"+date+"_"+foldername +"_ch"+IJ.pad(n_ch_string, 2)+"_p"+IJ.pad(n_pos_string, 3)+".tif");
		close();
		close();
	}
}