library(RImageJROI)
library(tidyverse)
library(spatstat)
#load ROIs with nuclei
nuclei <- read.ijzip(file = "D:/OneDrive/Data2/211025_timelapse_SPYDNA/MAX_dDBD007/nucleiROI.zip")
#convert to outlines to check if foci are inside
nuclei_spatstat <- ij2spatstat(nuclei)

#load nuclei IDs and track from trackmate
nuclei_data <- read_tsv(file = "D:/OneDrive/Data2/211025_timelapse_SPYDNA/MAX_dDBD007/NucleiTracks.txt")
#load foci IDs and track from trackmate
foci_data <- read_tsv(file = "D:/OneDrive/Data2/211025_timelapse_SPYDNA/MAX_dDBD007/FociTracks.txt" )
foci_data$Nucleus_name <- 0

#match foci to designated nucleus
length_movie <- max(nuclei_data$t)
for(i in 1:length_movie){
  subset_nuclei <- nuclei_data[nuclei_data$t==i,]
  subset_foci <- foci_data[foci_data$t==i,]
  if(nrow(subset_nuclei)>0&&nrow(subset_foci)>0){
    for (j in 1:nrow(subset_nuclei)){
      object <- nuclei_spatstat[[paste0("ID",subset_nuclei$sid[j])]]
      foci_inside <- inside.owin(subset_foci$x/0.1803752,subset_foci$y/0.1803752,object)
      for (k in 1:nrow(subset_foci)){
        if(foci_inside[k]){
          subset_foci$Nucleus_name[k] <- subset_nuclei$sid[j]
        }
      }
      }
  }
  foci_data[foci_data$t==i,] <- subset_foci
}

View(foci_data)

#summarize data showing number of foci per nucleus
foci_data %>%
  filter(Nucleus_name>0)%>%
  group_by(Nucleus_name)%>%
  dplyr::summarise(n=n())%>%
  filter(n<1000)%>%
  select(n) %>%
  .$n%>%
  hist()



foci_data%>%
  filter(Nucleus_name>0)%>%
  group_by(Nucleus_name)%>%
  dplyr::summarise(n=n())%>%
    left_join(nuclei_data,by=c("Nucleus_name"="sid"))%>%
ggplot(aes(x=t,y=n,color=tid)) +geom_line()+ theme(legend.position = "none")

foci_data%>%
  filter(Nucleus_name>0)%>%
  group_by(t,Nucleus_name)%>%
  dplyr::summarise(n=n())%>%
  left_join(nuclei_data,by=c("Nucleus_name"="sid"))%>%
  group_by(t.x)%>%
  summarise(mean_foci=mean(n),mean_foci=mean(n))%>%
  ggplot(aes(x=t.x,y=mean_foci)) +geom_line()+ theme(legend.position = "none")



#ROImanager file with nuclei
#take csv file which tells in which frame to look per ROI ID
#take ROI manager file with foci or trackmate txt file with coordinates
#loop over nuclei