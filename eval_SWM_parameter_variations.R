#eval_SWM_parameter_variations.R
#calculates efficiency values for multiple SWM output for a given time period, and considering the init period
#HMS, IPG 2022

#loads libaray required for efficiency value calculation
library(hydroGOF)
#set working directory (where observed and simulated data are located)
setwd("C:/2021_HydroGIS/SWM_arcpy/Evaluation/")

#output file name
outname <- "Uebung11_evaluation"

#reads observed streamflow
obsdata <- read.csv("Eichelsachsen_Messwerte.csv",sep=";")

#defines dates for start of init run and the start/end of the evaluation time period
DateInit_day <- 11
DateInit_month <- 6
DateInit_year <- 2004
DateStart_day <- 30
DateStart_month <- 6
DateStart_year <- 2004
DateEnd_day <- 13
DateEnd_month <- 8
DateEnd_year <- 2004

#defines the RP, c and IDW parameter values that should be assessed 
#note that the corresponding output csv files has to be available
RP_par <- c(0.85,0.90,0.95,1.0)
c_par <- c(50,200,350,500,650)
IDW_par <- c(0.5,1,1.5,2.0)

#creating proper dates
DateInit <- as.Date(paste0(DateInit_year,"/",DateInit_month,"/",DateInit_day))
DateStart <- as.Date(paste0(DateStart_year,"/",DateStart_month,"/",DateStart_day))
DateEnd <- as.Date(paste0(DateEnd_year,"/",DateEnd_month,"/",DateEnd_day))

obsdata$Datum <- as.Date(obsdata$Datum, format="%d.%m.%Y")

#find the position of the observation time series where evaluation should be based on
pos.start <- head(which(obsdata$Datum > DateStart-1),1)
pos.end <- tail(which(obsdata$Datum < DateEnd+1),1)
obs_ts <- obsdata$Messwert[pos.start:pos.end] 

#define the init dates which should be not considered for the assessment
dropsim <- as.numeric(DateStart - DateInit)

#prepare a matrix where the output should be written to
outmat <- matrix(NA,nrow=length(obs_ts),ncol=2)
#add date to the first and the observed streamflow to second column
outmat[,1] <- obsdata$Datum[pos.start:pos.end]
outmat[,2] <- obs_ts
#and indicate the column number (for filling in the simulated values later)
n <- 2


for (r in RP_par) { #loop over RP parameter values
   for (c in c_par) { #loop over c parameter values
      for (i in IDW_par) { #loop over IDW exponent values
         n <- n + 1
         #in case the csv is not there, skip this combination
         if (!file.exists(paste0("Q_rp",r*100,"_c",c,"_idw",i*100,"_s",DateInit_year,sprintf("%02d", DateInit_month),sprintf("%02d", DateInit_day),"_e",DateEnd_year,sprintf("%02d", DateEnd_month),sprintf("%02d", DateEnd_day),".csv"))) {
            print(paste0("Q_rp",r*100,"_c",c,"_idw",i*100,"_s",DateInit_year,sprintf("%02d", DateInit_month),sprintf("%02d", DateInit_day),"_e",DateEnd_year,sprintf("%02d", DateEnd_month),sprintf("%02d", DateEnd_day),".csv"," does not exist, therefore skipping"))
            n <- n -1 #to set n back
            next
         } else {
            #read in the data of this combination and save it to the matrix in a column
            outmat <- cbind(outmat,read.csv(paste0("Q_rp",r*100,"_c",c,"_idw",i*100,"_s",DateInit_year,sprintf("%02d", DateInit_month),sprintf("%02d", DateInit_day),"_e",DateEnd_year,sprintf("%02d", DateEnd_month),sprintf("%02d", DateEnd_day),".csv"),sep=",",header=T,skip=as.numeric(dropsim))[,3])   
            if (n == 3) {
               cnamelist <- paste("r",r,"c",c,"i",i,sep="_")
            } else {
               cnamelist <- c(cnamelist,paste("r",r,"c",c,"i",i,sep="_"))
            } 
         }
         #create a name list for naming the columns later on
      }
   }
}


#create a matrix where the efficiency metrics should be written to
outmatm <- matrix(NA,nrow=5,ncol=length(cnamelist)+1)
#set row names
outmatm[,1] <- c("NSE","KGE","KGEr","KGEb","KGEg")

#calculate and write efficiency metrics
for (m in 1:length(cnamelist)) {
   outmatm[1,m+1] <- NSE(as.numeric(outmat[,m+2]),as.numeric(outmat[,2]))
   outmatm[2,m+1] <- KGE(as.numeric(outmat[,m+2]),as.numeric(outmat[,2]), method="2012", out.type="full")$KGE.value
   outmatm[3,m+1] <- KGE(as.numeric(outmat[,m+2]),as.numeric(outmat[,2]), method="2012", out.type="full")$KGE.elements[1]
   outmatm[4,m+1] <- KGE(as.numeric(outmat[,m+2]),as.numeric(outmat[,2]), method="2012", out.type="full")$KGE.elements[2]
   outmatm[5,m+1] <- KGE(as.numeric(outmat[,m+2]),as.numeric(outmat[,2]), method="2012", out.type="full")$KGE.elements[3]
}

#combine and add the column names
cnamelisto <- c("date","obs",cnamelist)
cnamelistm <- c("effparam",cnamelist)
colnames(outmat) <- cnamelisto
colnames(outmatm) <- cnamelistm

#write the output to disk
write.table(outmat,paste0(outname,".txt"),col.names = T,row.names = F)
write.table(outmatm,paste0(outname,"_efficiencies.txt"),col.names = T,row.names = F)

