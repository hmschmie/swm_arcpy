# -*- coding: cp1252 -*-

"""Soil Water Model in Python für ArcGIS
Course "GIS für hydrologische Fragestellungen" of the Faculty 11 of the Institute of Physical Geography at the Johann
Wolfgang Goethe University of Frankfurt.

This simple Soil Water Model calculates the soilwater content for each rastercell of a basin. The output of the model
are tables of the daily runoff in m^3 of the basin for each combination of variables and if selected, the raster datasets
of different modelparameter like PET, AET, precipitation, runoff or soilwater storage.
The following datasets are neccessary for the model and has to exist together in a File Geodatabase:
basin(s) - vector (polygon)
TempFeuchte - table of climate data. The attribute table has to have the field names as followed: "TagesID", "Jahr",
            "Monat", "Tag", "RelFeu", and "Temp".
FK_von_L - raster (field capacity in the effective root zone, in mm)
L_in_metern - raster (effective root zone, in m)
WP_von_L - raster (wilting point, in mm)
Gewaesser - raster (mask of water areas with water areas = 1 and non water areas = 0)
N_Zeitreihen - table of precipitation data for each day and station. The attribute table has to have the field names as
            followed: "Stationsnummer", "Tagessumme_mm" and "TagesID".
N_Messstationen- vector (points); Stations for precipitation measuring. The attribute table has to have the field name
                as followed: "Stationsnummer"
Haude_[1-12] - one file per month, Haude parameter
"""
"""History
Version 2.3 (Hannes Müller Schmied) 01/2022
- final output is now in m3 s-1
- new option to store cumulated raster files (e.g. for calculating annual runoff coefficients)
Version 2.2 (Hannes Müller Schmied) 03/2021
- runoff for water bodies is not 0 but precipitation in the case P<=PET
- negative soil storage is avoided in any case (set to 0 if negative)
- improvements in text outputs
Version 2.1 (Hannes Müller Schmied) 02/2021
- time series output not written in geodatabase anymore but as csv in results folder
- correct writing of message in case RP < max(WP/FK) and thus this combination is skipped
- IDW exponent now as float data type
- resulting csv-file reflects also information about idw power
"""

__author__ = "Florian Herz"
__copyright__ = "Copyright 2019, FH"
__credits__ = ["Florian Herz", "Dr. Hannes Müller Schmied", "Dr. Irene Marzolff"]
__version__ = "2.3"
__maintainer__ = "Hannes Müller Schmied"
__email__ = "hannes.mueller.schmied@em.uni-frankfurt.de"
__status__ = "Production"

########################################################################################################################
#  import the modules and activate arc gis extensions
########################################################################################################################

import arcpy
from arcpy.sa import *
import time
arcpy.CheckOutExtension("Spatial")
arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Systemmodule geladen.")

########################################################################################################################
#  function definition
########################################################################################################################


def get_pet(haude_factor, temperature, humidity, date, parameter_safe):
    """
    Calculates the potential evapotranspiration (PET) by Haude.
    :param haude_factor: Haude-factor of the current month (:type: raster)
    :param temperature: temperature of the day in degrees Celsius (:type: float)
    :param humidity: relative humidity (:type: float)
    :param date: daily ID (:type: integer)
    :param parameter_safe: values of the variable combination (:type: tuple)
    :return: PET (:type: raster)
    """
    pet_raster = haude_factor * (6.1 * 10 ** ((7.5 * temperature) / (temperature + 237.2))) * (1.0 - humidity / 100.0)
    pet_raster.save("PET_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "PET berechnet.")

    return pet_raster


def get_aet(pet_raster, water_raster, s_pre_raster, rp_raster, rpwp_dif_raster, wp_raster, date, parameter_safe):
    """
    Calculates the actual evapotranspiration (AET). The AET equals the value of the PET in water cells and in cells with
    a soilwater content above the reduction point. The AET equals zero if the reduction point equals the wilting point. 
    In the other cases the AET is calculated by the soilwater content, wilting point, difference between wilting point 
    and reduction point and PET.
    :param pet_raster: output of the function "get_pet" (:type: raster)
    :param water_raster: mask of water cells (:type: raster)
    :param s_pre_raster: soilwater content of the previous day (:type: raster)
    :param rp_raster: reduction point (rp) (:type: raster)
    :param rpwp_dif_raster: difference between reduction point (rp) and wilting point (wp) (:type: raster)
    :param wp_raster: wilting point (wp) (:type: raster)
    :param date: daily ID (Typ: integer)
    :param parameter_safe: values of the variable combination (:type: tuple)
    :return: AET (:type: raster)
    """
    aet_raster = Con(water_raster == 1, pet_raster,
                     Con(s_pre_raster >= rp_raster, pet_raster,
                         Con(rpwp_dif_raster == 0, 0, ((s_pre_raster - wp_raster) / rpwp_dif_raster) * pet_raster)))
    aet_raster.save("AET_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "AET berechnet.")

    return aet_raster


def get_precipitation(dataspace, date, idw_pow, rastercellsize, parameter_safe):
    """
    Interpolates the precipitation by Inverse Distance Weighting (IDW). The calculation is done by the "IDW" tool of the
    "Spatial Analyst" extension of Arc GIS. The precipitation data is selected by a query table from the timeseries 
    table ("N_Zeitreihen") and the attribute table from the precipitation stations ("N_Messstationen").
    :param dataspace: directory of the base data (:type: string)
    :param date: daily ID (:type: integer)
    :param idw_pow: IDW power (:type: float)
    :param rastercellsize: raster cellsize (:type: float)
    :param parameter_safe: values of the variable combination (:type: tuple)
    :return: precipitation interpolation (:type: raster)
    """
    arcpy.MakeQueryTable_management(r'{}\N_Messstationen;'.format(dataspace) +
                                    r'{}\N_Zeitreihen'.format(dataspace), "p_temp",
                                    "USE_KEY_FIELDS", "N_Messstationen.Stationsnummer;N_Zeitreihen.TagesID",
                                    "N_Messstationen.Stationsnummer;N_Messstationen.Stationsname; N_Messstationen.Shape\
                                    ;N_Zeitreihen.Tagessumme_mm;N_Zeitreihen.TagesID", "N_Zeitreihen.Stationsnummer =\
                                    N_Messstationen.Stationsnummer AND N_Zeitreihen.TagesID = {}".format(date))
    idw = Idw("p_temp", "N_Zeitreihen.Tagessumme_mm", rastercellsize, idw_pow, RadiusFixed(20000.00000, 5), "")
    idw.save("IDW_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
    arcpy.Delete_management("p_temp")
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Niederschlag interpoliert.")

    return idw


def get_runoff(water_raster, lambda_param, wp_raster, p_raster, s_pre_raster, fc_raster, pet_raster, date,
               parameter_safe):
    """
    Calculates a raster dataset of the total runoff. The total runoff is the sum of the land runoff and the water 
    runoff. The first condition determines the amount of land runoff, the second condition determines the overflow and 
    the third condition determines the water runoff.
    :param water_raster: mask of water cells (:type: raster)
    :param lambda_param: Lambda value (:type: raster)
    :param wp_raster: wilting point (wp) (:type: raster)
    :param p_raster: output of the function "get_precipitation" (:type: raster)
    :param s_pre_raster: soilwater content of the previous day (:type: raster)
    :param fc_raster: field capacity (fc) (:type: raster)
    :param pet_raster: output of the function "get_pet" (:type: raster)
    :param date: daily ID (:type: integer)
    :param parameter_safe: values of the variable combination (:type: tuple)
    :return: total runoff (:type: raster)
    """
    r = Con(water_raster == 1, Con(p_raster > pet_raster, p_raster - pet_raster, p_raster), (lambda_param * ((s_pre_raster - wp_raster) ** 2) + Con(p_raster + s_pre_raster > fc_raster, p_raster + s_pre_raster - fc_raster, 0)))
    r.save("R_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Gesamtabfluss je Rasterzelle berechnet.")

    return r


def get_soilwater(water_raster, s_pre_raster, p_raster, aet_raster, runoff_raster, date, parameter_safe):
    """
    Calculates a raster of the soilwater content based of the common equation of the water balance. 
    :param water_raster: mask of water cells (:type: raster)
    :param s_pre_raster: soilwater content of the previous day (::type: raster)
    :param p_raster: output of the function "get_precipitation" (::type: raster)
    :param aet_raster: output of the function "get_aet" (::type: raster)
    :param runoff_raster: output of the function "get_runoff" (::type: raster)
    :param date: daily ID (::type: integer)
    :param parameter_safe: values of the variable combination (::type: tuple)
    :return: soilwater content (::type: raster)
    """
    soilwater = Con(water_raster == 0, s_pre_raster + p_raster - aet_raster - runoff_raster,)
    soilwater = Con(soilwater < 0, 0, soilwater)
    soilwater.save("S_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Bodenwasserspeicher berechnet.")

    return soilwater


def get_q_m3(runoff_raster, rastercellsize):
    """
    Calculates the streamflow of the basin in m^3 s^{-1} by converting the runoff-raster into an array.
    :param runoff_raster: output of the function "get_runoff" (::type: raster)
    :param rastercellsize: raster cellsize (::type: float)
    :return: streamflow by basin in m^3 s^{-1} (::type: float)
    """
    array = arcpy.RasterToNumPyArray(runoff_raster, nodata_to_value=0)
    r_sum = array.sum()
    r_m3 = (r_sum * 0.001 * rastercellsize ** 2 / 24 / 60 / 60)
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Q in m3 s-1 berechnet.")

    return r_m3


def delete_raster(bool_pet, bool_aet, bool_p, bool_r, bool_s, parameter_safe, yesterday):
    """
    Deletes the raster datasets created by the functions above if selected from the previous day.
    :param bool_pet: boolean to delete the PET-raster (::type: boolean)
    :param bool_aet: boolean to delete the AET-raster (::type: boolean)
    :param bool_p: boolean to delete the precipitation-raster (::type: boolean)
    :param bool_r: boolean to delete the runoff-raster (::type: boolean)
    :param bool_s: boolean to delete the soilwater-raster (::type: boolean)
    :param parameter_safe: values of the variable combination (::type: tuple)
    :param yesterday: previous daily ID (::type: integer)
    :return: 
    """
    for i in [("PET", bool_pet), ("AET", bool_aet), ("IDW", bool_p), ("R", bool_r), ("S", bool_s)]:
        if not i[1]:
            arcpy.Delete_management("{}_rp{}_c{}_{}.tif".format(i[0], parameter_safe[0], parameter_safe[1], yesterday))

def delete_sum_raster(parameter_safe, yesterday):
    """
    Deletes the sum raster datasets created by the functions above if selected from the previous day.
    :param parameter_safe: values of the variable combination (::type: tuple)
    :param yesterday: previous daily ID (::type: integer)
    :return:
    """
    for i in [("PET"), ("AET"), ("IDW"), ("R"), ("S")]:
        arcpy.Delete_management("{}_sum_rp{}_c{}_{}_sumday.tif".format(i, parameter_safe[0], parameter_safe[1], yesterday))

def write_to_table(resultspace, tablename, result, date):
    """
    Writes the result value and the date into the current result table.
    :param resultspace: working directory (::type: sting)
    :param tablename: name of the result table (::type: string)
    :param result: total streamflow by basin in m^3 s-1 (::type: float)
    :param date: daily ID (::type: integer)
    :return:
    """
    q_cursor = arcpy.da.InsertCursor(r'{0}\{1}'.format(resultspace, tablename), ["Datum", "Q"])
    output_row = ["{0}.{1}.{2}".format(date[-2:], date[-4:-2], date[:4]), result]
    q_cursor.insertRow(output_row)
    del q_cursor


def rasterquotient_array(dividend, divisor):
    """
    Calculates the quotient of two rasters in a numpy array.
    :param dividend: first raster object (:type: raster)
    :param divisor: second raster object (:type: raster)
    :return: numpy array of the quotient (:type: array)
    """
    quotient_array = arcpy.RasterToNumPyArray(dividend/divisor, nodata_to_value=0)
    return quotient_array


########################################################################################################################
#  User input in ArcMap
########################################################################################################################

data = arcpy.GetParameterAsText(0)  # datatype: workspace #  default: C:\HiWi_Hydro-GIS\MTP_HydroGIS_Basisdaten.gdb
basin = arcpy.GetParameterAsText(1)  # datatype: featurelayer
#  default: C:\HiWi_Hydro-GIS\MTP_HydroGIS_Basisdaten.gdb\EZG_Schotten2_Vektor
basin_id = arcpy.GetParameterAsText(2)  # field #  default: Id
name = arcpy.GetParameterAsText(9)  # datatype: string #  default: SWM_Schotten2_2003-2004
folder = arcpy.GetParameterAsText(8)  # datatype: folder #  default: C:\HiWi_Hydro-GIS
id_yesterday = start = int(arcpy.GetParameterAsText(4))  # datatype: long #  default: 20030101
end = int(arcpy.GetParameterAsText(5))  # datatype: long #  default: 20041231
s_init = ExtractByMask(Raster(arcpy.GetParameterAsText(3)), basin)  # datatype: geodataset
#  default: C:\HiWi_Hydro-GIS\MTP_HydroGIS_Basisdaten.gdb\FK_von_L
sum_start = int(arcpy.GetParameterAsText(23))  # datatype: long #  default: 20040101
sum_end = int(arcpy.GetParameterAsText(24))  # datatype: long #  default: 20041201
rp_factor_min = float(arcpy.GetParameterAsText(6).replace(",", "."))  # datatype: double #  default: 0.85
rp_factor_max = float(arcpy.GetParameterAsText(16).replace(",", "."))  # datatype: double #  default: 0.85
rp_factor_step = float(arcpy.GetParameterAsText(17).replace(",", "."))  # datatype: double #  default: 0.05
c_min = int(arcpy.GetParameterAsText(7))   # datatype: long #  default: 150
c_max = int(arcpy.GetParameterAsText(19))  # datatype: long #  default: 150
c_step = int(arcpy.GetParameterAsText(20))  # datatype: long #  default: 50
idw_exponent = float(arcpy.GetParameterAsText(21).replace(",", "."))  # datatype: double #  default: 1
check_raster_sum = arcpy.GetParameterAsText(22)  # datatype: boolean #  default: false
if check_raster_sum == 'false':
    check_raster_sum = False
else:
    check_raster_sum = True
check_pet = arcpy.GetParameterAsText(10)  # datatype: boolean #  default: true
if check_pet == 'false':
    check_pet = False
else:
    check_pet = True
check_aet = arcpy.GetParameterAsText(11)  # datatype: boolean #  default: true
if check_aet == 'false':
    check_aet = False
else:
    check_aet = True
check_p = arcpy.GetParameterAsText(12)  # datatype: boolean #  default: true
if check_p == 'false':
    check_p = False
else:
    check_p = True
check_r = arcpy.GetParameterAsText(13)  # datatype: boolean #  default: true
if check_r == 'false':
    check_r = False
else:
    check_r = True
check_s = arcpy.GetParameterAsText(14)  # datatype: boolean #  default: true
if check_s == 'false':
    check_s = False
else:
    check_s = True

########################################################################################################################
#  set main settings and creating the working and scratch directory
########################################################################################################################

arcpy.env.overwriteOutput = True  # it´s possible to overwrite the results
arcpy.env.extent = s_init  # set the working extent
if arcpy.Exists(r'{}\{}'.format(folder, name)):  # if the working directory exists, it will be overwritten
    arcpy.Delete_management(r'{}\{}'.format(folder, name))
arcpy.CreateFolder_management(folder, name)
workspace = arcpy.env.workspace = r'{}\{}'.format(folder, name)  # set the working directory
#arcpy.CreateFileGDB_management(workspace, "Ergebnistabellen.gdb")  # creates a geodatabase for the result tables

arcpy.CreateFolder_management(folder, "Scratch")  # creates the scratch workspace for temporary dataset
arcpy.env.scratchWorkspace = r'{}\Scratch'.format(folder)

arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Die Ergebnisdatenbank wurde im Verzeichnis {} erstellt.".format(folder))

########################################################################################################################
#  link and extract the base datasets
#  (The datasets has to be saved with the same name as below in the base directory.)
########################################################################################################################

# dictionary to link the month and its specific haudefactor
haude_dic = {1: ExtractByMask(Raster(r'{}\Haude_1'.format(data)), basin),
             2: ExtractByMask(Raster(r'{}\Haude_2'.format(data)), basin),
             3: ExtractByMask(Raster(r'{}\Haude_3'.format(data)), basin),
             4: ExtractByMask(Raster(r'{}\Haude_4'.format(data)), basin),
             5: ExtractByMask(Raster(r'{}\Haude_5'.format(data)), basin),
             6: ExtractByMask(Raster(r'{}\Haude_6'.format(data)), basin),
             7: ExtractByMask(Raster(r'{}\Haude_7'.format(data)), basin),
             8: ExtractByMask(Raster(r'{}\Haude_8'.format(data)), basin),
             9: ExtractByMask(Raster(r'{}\Haude_9'.format(data)), basin),
             10: ExtractByMask(Raster(r'{}\Haude_10'.format(data)), basin),
             11: ExtractByMask(Raster(r'{}\Haude_11'.format(data)), basin),
             12: ExtractByMask(Raster(r'{}\Haude_12'.format(data)), basin)}
climatedata = r'{}\TempFeuchte'.format(data)  # table
fc = ExtractByMask(Raster(r'{}\FK_von_L'.format(data)), basin)  # raster
wp = ExtractByMask(Raster(r'{}\WP_von_L'.format(data)), basin)  # raster
wpfc_qarray = rasterquotient_array(wp, fc)  # calculates an array of the quotient of two rasters #  array
rp_control = wpfc_qarray.max()  # extract the biggest vaule of the quotient of wp:fc to compare with the rp-factor
water = ExtractByMask(Raster(r'{}\Gewaesser'.format(data)), basin)  # raster
s_pre = s_init
p_data = r'{}\N_Zeitreihen'.format(data)  # table
cellsize = s_init.meanCellHeight
arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "cellsize={}".format(cellsize))
l_m = ExtractByMask(Raster(r'{}\L_in_metern'.format(data)), basin)  # raster

rp_factor = []  # list of all rp-factor from minimum to maximum raised by step
while rp_factor_min <= rp_factor_max:
    rp_factor.append(rp_factor_min)
    rp_factor_min = round(rp_factor_min + rp_factor_step, 2)
c = []  # list of all c-parameter from minimum to maximum raised by step
while c_min <= c_max:
    c.append(c_min)
    c_min = round(c_min + c_step, 2)
# necessary to delete the raster datasets after starting to calculate a new combination of variables
parameter_yesterday = (int(rp_factor[0]*100), int(c[0]))  # memory for the value of the last combination of variables

arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Berechnung der Rasterdatensaetze war erfolgreich.")

########################################################################################################################
#  main part
#  iterating through the climate data of the period
########################################################################################################################
arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Anzahl RP-Parameter={}".format(len(rp_factor)))
arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Anzahl c-Parameter={}".format(len(c)))

for z in range(len(rp_factor)):
    arcpy.AddMessage("z={}".format(z))
    arcpy.AddMessage("maximalwert von WP/FK={}".format(rp_control))
    arcpy.AddMessage("gewählter RP-Parameter={}".format(rp_factor[z]))
    if rp_control >= rp_factor[z]:  # the AET is negative, if the rp-factor is smaller than the quotient of wp:fc
        arcpy.AddMessage("RP-Parameter ist kleiner als der Maximalwert von WP/FK. RP-Parameter = {} wird übersprungen.".format(rp_factor[z]))
        continue  # skips all rp-factors smaller than the quotient of wp:fc
    rp = fc * rp_factor[z]
    rpwp_dif = rp - wp
    for y in range(len(c)):
        arcpy.AddMessage("y={}".format(y))
        lambda_parameter = (c[y] / (l_m * 1000) ** 2)
        # value memory for the current combination of variables to add it in the filenames and the result table
        parameter_day = (int(rp_factor[z]*100), int(c[y]))
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "parameter_day={}".format(parameter_day))
        # creating a result table for each combination of variables
        outname1 = "Q_rp{}_c{}_idw{}".format(int(rp_factor[z]*100), int(c[y]), int(idw_exponent*100))
        arcpy.AddMessage("outname1={}".format(outname1))
        outname2 = "_s{}_e{}".format(int(start), int(end))
        arcpy.AddMessage("outname2={}".format(outname2))
        result_path = arcpy.CreateTable_management(workspace, outname1)
        arcpy.AddField_management(result_path, "Datum", "DATE")
        arcpy.AddField_management(result_path, "Q", "DOUBLE")
        arcpy.DeleteField_management(result_path, ["OBJECTID","FIELD1"])

        # iterating through the climate data of the period
        with arcpy.da.SearchCursor(climatedata, ['TagesID', 'Jahr', 'Monat', 'Tag', 'RelFeu', 'Temp'],
                                   "TagesID >= {0} AND TagesID <= {1}".format(start, end)) as cursor:
            for row in cursor:

                id_day = int(row[0]) #YYYYMMDD
                year = int(row[1]) #YYYY
                month = int(row[2]) #MM
                day = int(row[3]) #DD
                humid = float(row[4]) #in %
                temp = float(row[5]) #in °C
                # calculating and saving a raster dataset for each parameter
                pet = get_pet(haude_dic[month], temp, humid, id_day, parameter_day)
                if id_day == start:
                    s_pre = s_init

                aet = get_aet(pet, water, s_pre, rp, rpwp_dif, wp, id_day, parameter_day)
                precipitation = get_precipitation(data, id_day, idw_exponent, cellsize, parameter_day)
                runoff = get_runoff(water, lambda_parameter, wp, precipitation, s_pre, fc, pet, id_day, parameter_day)
                runoff_m3 = get_q_m3(runoff, cellsize)  # floating point number
                s = get_soilwater(water, s_pre, precipitation, aet, runoff, id_day, parameter_day)

                s_pre = s  # memory for soilwater from the previous day
                write_to_table(workspace, outname1, runoff_m3, str(id_day))  # writing the runoff into the result table
                if check_raster_sum == True:
                    if sum_start <= id_day <= sum_end:
                        if sum_start == id_day:
                            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Aufsummierung der Raster beginnt.")
                            ndays = 1
                            sum_pet = pet
                            sum_aet = aet
                            sum_precipitation = precipitation
                            sum_runoff = runoff
                            sum_s = s
                        elif sum_end == id_day:
                            sum_s = sum_s / ndays  # storage as mean value
                            sum_aet = sum_aet + aet
                            sum_aet.save("AET_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start, sum_end))
                            sum_pet = sum_pet + pet
                            sum_pet.save("PET_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start, sum_end))
                            sum_precipitation = sum_precipitation + precipitation
                            sum_precipitation.save("IDW_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start, sum_end))
                            sum_runoff = sum_runoff + runoff
                            sum_runoff.save("R_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start, sum_end))
                            sum_s = sum_s + s
                            sum_s.save("S_mean_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start, sum_end))
                            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Aufsummierte Raster geschrieben.")
                        else:
                            ndays = ndays + 1
                            sum_pet = sum_pet + pet
                            sum_pet.save("PET_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                            sum_aet = sum_aet + aet
                            sum_aet.save("AET_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                            sum_precipitation = sum_precipitation + precipitation
                            sum_precipitation.save("IDW_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                            sum_runoff = sum_runoff + runoff
                            sum_runoff.save("R_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                            sum_s = sum_s + s
                            sum_s.save("S_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                            if ndays > 2:
                                delete_sum_raster(parameter_day, id_yesterday)

                # deletes the calculated rasters above if selected
                if not id_yesterday == start:
                    delete_raster(check_pet, check_aet, check_p, check_r, check_s, parameter_day, id_yesterday)
                id_yesterday = id_day  # memory for the id form the previous day; necessary to delete the rasterdatasets

                arcpy.AddMessage(time.strftime("%H:%M:%S: ") +
                                 "Fertig mit der Berechnung des {0}.{1}.{2}".format(day, month, year))
        del cursor
        # convert resulting table to .csv
        arcpy.TableToTable_conversion(result_path, workspace, outname1+outname2+".csv")
        # deleting the rasters of the first day of the current variable combination
        delete_raster(check_pet, check_aet, check_p, check_r, check_s, parameter_day, start)
        if check_raster_sum == True:
            delete_sum_raster(parameter_day, sum_start)
        # deleting the rasters of the last day of the previous variable combination
        if not parameter_yesterday == parameter_day:
            delete_raster(check_pet, check_aet, check_p, check_r, check_s, parameter_yesterday, end)
            if check_raster_sum == True:
                delete_sum_raster(parameter_yesterday, sum_end-1)
        parameter_yesterday = parameter_day  # memory for the value of the last combination of variables
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit c={}".format(c[y]))
    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit rp={}".format(rp_factor[z]))
    

# deleting the rasters of the last day of the last variable combination
delete_raster(check_pet, check_aet, check_p, check_r, check_s, parameter_day, end)
if check_raster_sum == True:
    delete_sum_raster(parameter_day, sum_end-1)
arcpy.Delete_management(result_path)
arcpy.RefreshCatalog(workspace)
arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Modellierung abgeschlossen.")

