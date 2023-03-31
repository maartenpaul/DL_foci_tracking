#@ File[] (label="Select files for analysis",style="files") list

//parameters
nuclei_channel = 2;
downscale = 2.0;
//parameters to enhance contrast of nuclei
//ask for segmentation method foci


root_folder = File.getParent(list[0]);

print(root_folder);

for (i=0; i<list.length; i++) {
	
        if (endsWith(list[i], "tif")){

        	open(list[i]);
        	directory = getDir("image");
			filename = File.getNameWithoutExtension(getInfo("image.filename"));
			File.makeDirectory(directory+filename);
			write_folder = directory;
			
			
			write_folder= root_folder+File.separator+filename;

			//nuclei tracking
			//run("Duplicate...", "duplicate channels="+nuclei_channel+"");
			//enhance contrast to improve segmentation by Stardist
			//run("Enhance Contrast...", "saturated=10 process_all");
			run("MP_TrackNuclei_TrackmateStardist","outputfolder="+ write_folder+" downscale="+downscale+" targetchannel="+nuclei_channel+"");
			close();
			
			open(list[i]);
			//foci tracking
			//run("Duplicate...", "duplicate channels=1");
			//save(write_folder+File.separator+filename+"_RAD51.tif");
			run("TrackFoci ilastik batch ","outputfolder="+ write_folder+" modelfolder=/media/DATA/Maarten/OneDrive/Documents/Scripts/Ilastik/mClR51.ilp targetchannel=1");
			
			//track BRCA2 foci
			//run("Duplicate...", "duplicate channels=3");
			//save(write_folder+File.separator+filename+"_BRCA2.tif");
			run("TrackFoci ilastik batch BRCA2 ","outputfolder="+ write_folder+" targetchannel=2");
			
			//close original stack
			close();

        }
	

}


