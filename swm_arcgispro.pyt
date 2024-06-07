# -*- coding: utf-8 -*-

import arcpy
from arcpy.sa import *
import time
import os
import shutil
import numpy as np


arcpy.env.parallelProcessingFactor = "100%"

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "SWM ArcGIS Pro"
        self.description = "This tool has parameters with default values."
        self.alias = "swmarcgispro"
        # List of tool classes associated with this toolbox
        self.tools = [Tool]

class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "SWM ArcPy"
        self.description = "Dieses einfache Bodenwasser-Modell berechnet für jede Rasterzelle eines Einzugsgebietes die Boden-Wasser-Bilanz. Ausgabe des Modells ist eine Tabelle mit täglichen Abflussvolumen in m3 s-1 für das Einzugsgebiet, sowie auf Wunsch die berechneten Rasterdatensätze (auch über einen Wunschzeitraum aufsummiert) verschiedener Modellparameter."
        self.canRunInBackground = False
        # Define default values
        self.workspace_default = r'C:/HydroGIS/Vogelsberg_GIS/Vogelsberg_GIS.gdb'
        self.basin_default = r'C:/HydroGIS/Vogelsberg_GIS/Vogelsberg_GIS.gdb/Hydrologie/EZG_Eichelsachsen_Vektor'
        self.s_init_default = r'C:/HydroGIS/Vogelsberg_GIS/Vogelsberg_GIS.gdb/FK'
        self.start_default = 20210526
        self.end_default = 20210526
        self.rp_factor_default = 0.85
        self.rp_factor_max_default = 0.85
        self.rp_factor_step_default = 0.05
        self.c_min_default = 150
        self.c_max_default = 150
        self.c_step_default = 50
        self.idw_exponent_default = 1.0
        self.folder_default = r'C:\HydroGIS\swmout'
        self.name_default = "SWM_Eichelsachsen_Ergebnisdaten_20210526"

    def getParameterInfo(self):
        """Define parameter definitions"""
        workspace_param = arcpy.Parameter(
            displayName="Geodatenbank der Basisdaten",
            name="workspace_name",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        basin_param = arcpy.Parameter(
            displayName="Einzugsgebiet",
            name="basin_name",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )
        s_init_param = arcpy.Parameter(
            displayName="Initialer Bodenwasserspeicher",
            name="s_init_name",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input"
        )
        start_param = arcpy.Parameter(
            displayName="Startdatum (JJJJMMTT)",
            name="start_name",
            datatype="Long",
            parameterType="Required",
            direction="Input"
        )
        end_param = arcpy.Parameter(
            displayName="Enddatum (JJJJMMTT)",
            name="end_name",
            datatype="Long",
            parameterType="Required",
            direction="Input"
        )
        rp_factor_param = arcpy.Parameter(
            displayName="RP",
            name="rp_factor_min_name",
            datatype="Double",
            parameterType="Required",
            direction="Input"
        )
        c_param = arcpy.Parameter(
            displayName="c-Parameter",
            name="c_min_name",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        idw_exponent_param = arcpy.Parameter(
            displayName="Exponent der IDW-Methode zur Niederschlagsinterpolation",
            name="idw_exponent_name",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )
        folder_param = arcpy.Parameter(
            displayName="Speicherpfad des Ausgabeordners",
            name="folder_name",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        name_param = arcpy.Parameter(
            displayName="Name des Ausgabeordners",
            name="name_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        c_max_param = arcpy.Parameter(
            displayName="c-Parameter (Max)",
            name="c_max_name",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
            category="Variation c-Parameter"
        )
        c_step_param = arcpy.Parameter(
            displayName="c-Parameter (Schrittweite)",
            name="c_step_name",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
            category="Variation c-Parameter"
        )
        rp_factor_max_param = arcpy.Parameter(
            displayName="RP (Max)",
            name="rp_factor_max_name",
            datatype="Double",
            parameterType="Optional",
            direction="Input",
            category="Variation RP"
        )
        rp_factor_step_param = arcpy.Parameter(
            displayName="RP (Schrittweite)",
            name="rp_factor_step_name",
            datatype="Double",
            parameterType="Optional",
            direction="Input",
            category="Variation RP"
        )
        raster_sum_param = arcpy.Parameter(
            displayName="Aufsummieren der Rasterdateien",
            name="check_raster_sum_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Aufsummieren der Rasterdateien"
        )
        sum_start_param = arcpy.Parameter(
            displayName="Startdatum Aufsummieren (JJJJMMTT)",
            name="sum_start_name",
            datatype="Long",
            parameterType="Optional",
            direction="Input",
            category="Aufsummieren der Rasterdateien"
        )
        sum_end_param = arcpy.Parameter(
            displayName="Enddatum Aufsummieren (JJJJMMTT)",
            name="sum_end_name",
            datatype="Long",
            parameterType="Optional",
            direction="Input",
            category="Aufsummieren der Rasterdateien"
        )
        check_pet_param = arcpy.Parameter(
            displayName="PET",
            name="check_pet_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )
        check_aet_param = arcpy.Parameter(
            displayName="AET",
            name="check_aet_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )
        check_p_param = arcpy.Parameter(
            displayName="Niederschlag",
            name="check_p_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )
        check_r_param = arcpy.Parameter(
            displayName="Gesamtabfluss",
            name="check_r_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )
        check_ro_param = arcpy.Parameter(
            displayName="Überlauf-Abfluss",
            name="check_ro_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )
        check_rs_param = arcpy.Parameter(
            displayName="Glugla-Abfluss",
            name="check_rs_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )
        check_s_param = arcpy.Parameter(
            displayName="Bodenwasserspeicher",
            name="check_s_name",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
            category="Speichern der täglichen Rasterdaten"
        )

        # Set default values for parameters
        workspace_param.value = self.workspace_default
        basin_param.value = self.basin_default
        s_init_param.value = self.s_init_default
        start_param.value = self.start_default
        end_param.value = self.end_default
        rp_factor_param.value = self.rp_factor_default
        rp_factor_max_param.value = self.rp_factor_max_default
        rp_factor_step_param.value = self.rp_factor_step_default
        c_param.value = self.c_min_default
        c_max_param.value = self.c_max_default
        c_step_param.value = self.c_step_default
        idw_exponent_param.value = self.idw_exponent_default
        folder_param.value = self.folder_default
        name_param.value = self.name_default
        raster_sum_param.value = False
        sum_start_param.value = 20210101
        sum_end_param.value = 20211231
        check_pet_param.value = False
        check_aet_param.value = False
        check_p_param.value = False
        check_r_param.value = False
        check_ro_param.value = False
        check_rs_param.value = False
        check_s_param.value = False

        # Define the parameter list
        parameters = [workspace_param, basin_param, s_init_param, start_param, end_param, rp_factor_param,
                      c_param, idw_exponent_param, folder_param, name_param, rp_factor_max_param, rp_factor_step_param,
                      c_max_param, c_step_param, raster_sum_param, sum_start_param, sum_end_param, check_pet_param,
                      check_aet_param, check_p_param, check_r_param, check_ro_param, check_rs_param, check_s_param]
        return parameters

    def validate(self, parameters, messages):
        """Modify the messages created by internal validation for each tool parameter. This method is called after internal validation."""
        return

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal validation is performed. This method is called whenever a parameter has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.CheckOutExtension("Spatial")
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Systemmodule geladen.")

        # Define the functions used in the model

        def get_pet(haude_factor, temperature, humidity, date, parameter_safe):
            """
            Calculates the potential evapotranspiration (PET) by Haude.
            :param haude_factor: Haude-factor of the current month (type: raster)
            :param temperature: temperature of the day in degrees Celsius (type: float)
            :param humidity: relative humidity (type: float)
            :param date: daily ID (type: integer)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: PET (type: raster)
            """
            # PET calculation using Haude method
            pet_raster = haude_factor * (6.1 * 10 ** ((7.5 * temperature) / (temperature + 237.2))) * (1.0 - humidity / 100.0)
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "PET berechnet.")  # Log message
            return pet_raster

        def get_aet(pet_raster, water_raster, s_pre_raster, rp_raster, rpwp_dif_raster, wp_raster, date, parameter_safe):
            """
            Calculates the actual evapotranspiration (AET). The AET equals the value of the PET in water cells and in cells with
            a soilwater content above the reduction point. The AET equals zero if the reduction point equals the wilting point.
            In other cases, the AET is calculated by the soilwater content, wilting point, difference between wilting point
            and reduction point, and PET.
            :param pet_raster: output of the function "get_pet" (type: raster)
            :param water_raster: mask of water cells (type: raster)
            :param s_pre_raster: soilwater content of the previous day (type: raster)
            :param rp_raster: reduction point (rp) (type: raster)
            :param rpwp_dif_raster: difference between reduction point (rp) and wilting point (wp) (type: raster)
            :param wp_raster: wilting point (wp) (type: raster)
            :param date: daily ID (type: integer)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: AET (type: raster)
            """
            # AET calculation using conditional logic based on water presence and soil water content
            aet_raster = Con(water_raster == 1, pet_raster,
                             Con(s_pre_raster >= rp_raster, pet_raster,
                                 Con(rpwp_dif_raster == 0, 0,
                                     ((s_pre_raster - wp_raster) / rpwp_dif_raster) * pet_raster)))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "AET berechnet.")  # Log message
            return aet_raster

        def get_precipitation(dataspace, date, idw_pow, rastercellsize, parameter_safe):
            """
            Interpolates the precipitation by Inverse Distance Weighting (IDW). The calculation is done by the "IDW" tool of the
            "Spatial Analyst" extension of ArcGIS. The precipitation data is selected by a query table from the timeseries
            table ("N_Zeitreihen") and the attribute table from the precipitation stations ("N_Messstationen").
            :param dataspace: directory of the base data (type: string)
            :param date: daily ID (type: integer)
            :param idw_pow: IDW power (type: float)
            :param rastercellsize: raster cellsize (type: float)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: precipitation interpolation (type: raster)
            """
            # Create a query table to get the precipitation data for the given date
            arcpy.management.MakeQueryTable(
                r'{}\N_Messstationen;'.format(dataspace) + r'{}\N_Zeitreihen'.format(dataspace), "p_temp",
                "USE_KEY_FIELDS", "N_Messstationen.Stationsnummer;N_Zeitreihen.TagesID",
                "N_Messstationen.Stationsnummer;N_Messstationen.Stationsname; N_Messstationen.Shape\
                                            ;N_Zeitreihen.Tagessumme_mm;N_Zeitreihen.TagesID", "N_Zeitreihen.Stationsnummer =\
                                                   N_Messstationen.Stationsnummer AND N_Zeitreihen.TagesID = {}".format(date))
            # Perform IDW interpolation on the precipitation data
            idw = Idw("p_temp", "N_Zeitreihen.Tagessumme_mm", rastercellsize, idw_pow, RadiusFixed(20000.00000, 5), "")
            arcpy.Delete_management("p_temp")  # Clean up temporary table
            return idw

        def get_runoff(water_raster, lambda_param, wp_raster, p_raster, s_pre_raster, fc_raster, pet_raster, date, parameter_safe):
            """
            Calculates a raster dataset of the total runoff. The total runoff is the sum of the land runoff and the water
            runoff. The first condition determines the amount of land runoff, the second condition determines the overflow, and
            the third condition determines the water runoff.
            :param water_raster: mask of water cells (type: raster)
            :param lambda_param: Lambda value (type: raster)
            :param wp_raster: wilting point (wp) (type: raster)
            :param p_raster: output of the function "get_precipitation" (type: raster)
            :param s_pre_raster: soilwater content of the previous day (type: raster)
            :param fc_raster: field capacity (fc) (type: raster)
            :param pet_raster: output of the function "get_pet" (type: raster)
            :param date: daily ID (type: integer)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: total runoff (type: raster)
            """
            # Calculate total runoff using conditional logic based on water presence, precipitation, and soil water content
            r = Con(water_raster == 1, Con(p_raster > pet_raster, p_raster - pet_raster, p_raster), (
                    lambda_param * ((s_pre_raster - wp_raster) ** 2) + Con(p_raster + s_pre_raster > fc_raster,
                                                                           p_raster + s_pre_raster - fc_raster, 0)))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Gesamtabfluss je Rasterzelle berechnet.")  # Log message
            return r

        def get_rsoil(water_raster, lambda_param, wp_raster, s_pre_raster, date, parameter_safe):
            """
            Calculates a raster dataset of the land runoff from soil (0 for water cells).
            :param water_raster: mask of water cells (type: raster)
            :param lambda_param: Lambda value (type: raster)
            :param wp_raster: wilting point (wp) (type: raster)
            :param s_pre_raster: soilwater content of the previous day (type: raster)
            :param date: daily ID (type: integer)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: runoff from soil according to Glugla (1969) (type: raster)
            """
            # Calculate land runoff from soil based on soil water content and wilting point
            r = Con(water_raster == 1, 0, (lambda_param * ((s_pre_raster - wp_raster) ** 2)))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Soil runoff (Glugla 1969) je Rasterzelle berechnet.")  # Log message
            return r

        def get_roverflow(water_raster, p_raster, s_pre_raster, fc_raster, date, parameter_safe):
            """
            Calculates a raster dataset of the overflow runoff. The overflow runoff is defined only for land areas, whereas in water cells overflow is set to 0.
            :param water_raster: mask of water cells (type: raster)
            :param p_raster: output of the function "get_precipitation" (type: raster)
            :param s_pre_raster: soilwater content of the previous day (type: raster)
            :param fc_raster: field capacity (fc) (type: raster)
            :param date: daily ID (type: integer)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: overflow runoff (type: raster)
            """
            # Calculate overflow runoff based on soil water content and field capacity
            r = Con(water_raster == 1, 0, Con(p_raster + s_pre_raster > fc_raster, p_raster + s_pre_raster - fc_raster, 0))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "R overflow je Rasterzelle berechnet.")  # Log message
            return r

        def get_soilwater(water_raster, s_pre_raster, p_raster, aet_raster, runoff_raster, date, parameter_safe):
            """
            Calculates a raster of the soilwater content based on the common equation of the water balance.
            :param water_raster: mask of water cells (type: raster)
            :param s_pre_raster: soilwater content of the previous day (type: raster)
            :param p_raster: output of the function "get_precipitation" (type: raster)
            :param aet_raster: output of the function "get_aet" (type: raster)
            :param runoff_raster: output of the function "get_runoff" (type: raster)
            :param date: daily ID (type: integer)
            :param parameter_safe: values of the variable combination (type: tuple)
            :return: soilwater content (type: raster)
            """
            # Calculate soil water content using the water balance equation
            soilwater = Con(water_raster == 0, s_pre_raster + p_raster - aet_raster - runoff_raster)
            soilwater = Con(soilwater < 0, 0, soilwater)  # Ensure soil water content is not negative
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Bodenwasserspeicher berechnet.")  # Log message
            return soilwater

        def get_q_m3(runoff_raster, rastercellsize):
            """
            Calculates the streamflow of the basin in m^3 s^{-1} by converting the runoff-raster into an array.
            :param runoff_raster: output of the function "get_runoff" (type: raster)
            :param rastercellsize: raster cellsize (type: float)
            :return: streamflow by basin in m^3 s^{-1} (type: float)
            """
            # Convert runoff raster to a numpy array and calculate total streamflow
            array = arcpy.RasterToNumPyArray(runoff_raster, nodata_to_value=0)
            r_sum = array.sum()  # Sum all the values in the runoff array
            r_m3 = (r_sum * 0.001 * rastercellsize ** 2 / 24 / 60 / 60)  # Convert to streamflow in m^3/s
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Q in m3 s-1 berechnet.")  # Log message
            return r_m3

        def save_rasters_to_disk(rasters, parameter_safe, date, workpath, save_flags):
            """
            Saves the rasters to disk if the corresponding flags are set to True.
            :param rasters: dictionary of raster datasets to save (type: dict)
            :param parameter_safe: values of the variable combination (type: tuple)
            :param date: daily ID (type: integer)
            :param workpath: path to the working directory (type: string)
            :param save_flags: list of booleans indicating which rasters to save (type: list)
            """
            # Iterate over rasters and save those with the corresponding flag set to True
            for (name, raster), save_flag in zip(rasters.items(), save_flags):
                if save_flag:
                    raster.save(os.path.join(workpath, f"{name}_rp{parameter_safe[0]}_c{parameter_safe[1]}_{date}.tif"))

        def delete_raster(save_flags, parameter_safe, date, workpath):
            """
            Deletes the rasters from the previous day if the corresponding flags are set to False.
            :param save_flags: list of booleans indicating which rasters to delete (type: list)
            :param parameter_safe: values of the variable combination (type: tuple)
            :param date: daily ID (type: integer)
            :param workpath: path to the working directory (type: string)
            """
            # Iterate over raster names and delete those with the corresponding flag set to False
            for name, save_flag in zip(["PET", "AET", "IDW", "R", "S", "Rsoil", "Roverflow"], save_flags):
                if not save_flag:
                    raster_path = os.path.join(workpath, f"{name}_rp{parameter_safe[0]}_c{parameter_safe[1]}_{date}.tif")
                    if arcpy.Exists(raster_path):
                        arcpy.Delete_management(raster_path)

        def delete_sum_raster(parameter_safe, date, workpath):
            """
            Deletes the sum rasters.
            :param parameter_safe: values of the variable combination (type: tuple)
            :param date: daily ID (type: integer)
            :param workpath: path to the working directory (type: string)
            """
            # Iterate over sum raster names and delete them
            for name in ["PET_sum", "AET_sum", "IDW_sum", "R_sum", "S_mean", "Roverflow_sum", "Rsoil_sum"]:
                raster_path = os.path.join(workpath, f"{name}_rp{parameter_safe[0]}_c{parameter_safe[1]}_{date}.tif")
                if arcpy.Exists(raster_path):
                    arcpy.Delete_management(raster_path)

        def write_to_table(resultspace, tablename, result, date):
            """
            Writes the result value and the date into the current result table.
            :param resultspace: working directory (type: string)
            :param tablename: name of the result table (type: string)
            :param result: total streamflow by basin in m^3 s^-1 (type: float)
            :param date: daily ID (type: integer)
            """
            # Create an insert cursor and write the result to the table
            q_cursor = arcpy.da.InsertCursor(r'{0}\{1}'.format(resultspace, tablename), ["Datum", "Q"])
            output_row = ["{0}.{1}.{2}".format(date[-2:], date[-4:-2], date[:4]), result]
            q_cursor.insertRow(output_row)
            del q_cursor

        def rasterquotient_array(dividend, divisor):
            """
            Calculates the quotient of two rasters in a numpy array.
            :param dividend: first raster object (type: raster)
            :param divisor: second raster object (type: raster)
            :return: numpy array of the quotient (type: array)
            """
            # Convert rasters to numpy arrays and calculate the quotient array
            array_dividend = arcpy.RasterToNumPyArray(dividend, nodata_to_value=0)
            array_divisor = arcpy.RasterToNumPyArray(divisor, nodata_to_value=0)
            quotient_array = np.divide(array_dividend, array_divisor, out=np.zeros_like(array_dividend), where=array_divisor != 0)
            return quotient_array


        # Access the parameter values, simplified without catching errors to avoid setting to default values in case something gets wrong
        data = parameters[0].valueAsText
        basin = parameters[1].valueAsText
        s_init = arcpy.sa.ExtractByMask(parameters[2].valueAsText, basin)
        id_yesterday = start = parameters[3].valueAsText
        end = parameters[4].valueAsText
        rp_factor_min = float(parameters[5].valueAsText.replace(",", "."))
        c_min = int(parameters[6].valueAsText)
        idw_exponent = float(parameters[7].valueAsText.replace(",", "."))
        folder = parameters[8].valueAsText
        name = parameters[9].valueAsText
        rp_factor_max = float(parameters[10].valueAsText.replace(",", "."))
        rp_factor_step = float(parameters[11].valueAsText.replace(",", "."))
        c_max = int(parameters[12].valueAsText)
        c_step = int(parameters[13].valueAsText)
        check_raster_sum = parameters[14].value
        sum_start = parameters[15].valueAsText
        sum_end = parameters[16].valueAsText
        save_pet = parameters[17].value
        save_aet = parameters[18].value
        save_p = parameters[19].value
        save_r = parameters[20].value
        save_ro = parameters[21].value
        save_rs = parameters[22].value
        save_s = parameters[23].value

        save_flags = [save_pet, save_aet, save_p, save_r, save_s, save_rs, save_ro]

        """Set main settings and create the working and scratch directories"""
        arcpy.env.overwriteOutput = True  # Allow overwriting of outputs
        arcpy.env.extent = s_init  # Set the working extent to the initial soil water storage raster

        # Define paths for the main working directory and scratch directory
        workpath = os.path.join(folder, name)
        scratch = "Scratch"
        scratchpath = os.path.join(folder, scratch)

        # Check if the working directory exists; if not, create it
        if not os.path.exists(workpath):
            os.makedirs(workpath)  # Create the main working directory
            arcpy.AddMessage(f"Ausgabeordner erstellt: {workpath}")
        else:
            # If the directory exists, delete it and create a new one
            shutil.rmtree(workpath)
            os.makedirs(workpath)
            arcpy.AddMessage("Ausgabeordner existiert bereits und wird neu aufgesetzt.")

        # Check if the scratch directory exists; if not, create it
        if not os.path.exists(scratchpath):
            os.makedirs(scratchpath)  # Create the scratch directory
            arcpy.AddMessage(f"Scratchordner erstellt: {scratchpath}")
        else:
            # If the directory exists, delete it and create a new one
            shutil.rmtree(scratchpath)
            os.makedirs(scratchpath)
            arcpy.AddMessage("Scratchordner existiert bereits und wird neu aufgesetzt.")

        arcpy.env.scratchWorkspace = scratchpath  # Set the scratch workspace

        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + f"Die Ergebnisdatenbank wurde im Verzeichnis {workpath} erstellt.")

        # Read data and create raster datasets from base data
        haude_path_template = r'{}\Haude_'.format(data)  # Template path for Haude-factor rasters
        haude_dic = {i: ExtractByMask(Raster(haude_path_template + month), basin) for i, month in enumerate(
            ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'], start=1)}  # Dictionary of Haude-factor rasters

        climatedata = r'{}\TempFeuchte_'.format(data)  # Path for climate data
        fc = ExtractByMask(Raster(r'{}\FK'.format(data)), basin)  # Extract field capacity raster
        wp = ExtractByMask(Raster(r'{}\WP'.format(data)), basin)  # Extract wilting point raster
        wpfc_qarray = rasterquotient_array(wp, fc)  # Calculate the quotient of wp and fc rasters
        rp_control = wpfc_qarray.max()  # Maximum value of the wp/fc quotient
        water = ExtractByMask(Raster(r'{}\Gewaessermaske'.format(data)), basin)  # Extract water mask raster
        s_pre = s_init  # Initial soil water storage raster

        cellsize = s_init.meanCellHeight  # Calculate the cell size of the rasters
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "cellsize={}".format(cellsize))
        l_m = ExtractByMask(Raster(r'{}\L_in_metern'.format(data)), basin)  # Extract length raster

        # Create lists of RP and c parameters based on the provided range and step values
        rp_factor = [round(rp_factor_min + i * rp_factor_step, 2) for i in range(int((rp_factor_max - rp_factor_min) / rp_factor_step) + 1)]
        c = [round(c_min + i * c_step, 2) for i in range(int((c_max - c_min) / c_step) + 1)]
        parameter_yesterday = (int(rp_factor[0] * 100), int(c[0]))  # Initial parameter combination for tracking

        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Berechnung der Rasterdatensaetze war erfolgreich.")
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Anzahl RP-Parameter={}".format(len(rp_factor)))
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Anzahl c-Parameter={}".format(len(c)))

        # Iterate over each RP factor
        for z in range(len(rp_factor)):
            arcpy.AddMessage("z={}".format(z))
            arcpy.AddMessage("Maximalwert von WP/FK={}".format(rp_control))
            arcpy.AddMessage("gewaehlter RP={}".format(rp_factor[z]))
            # Skip RP factors smaller than the wp/fc quotient
            if rp_control >= rp_factor[z]:
                arcpy.AddMessage("RP-Parameter ist kleiner als der Maximalwert von WP/FK. RP-Parameter = {} wird uebersprungen.".format(rp_factor[z]))
                continue
            rp = fc * rp_factor[z]  # Calculate RP raster
            rpwp_dif = rp - wp  # Difference between RP and WP rasters
            # Iterate over each c parameter
            for y in range(len(c)):
                arcpy.AddMessage("y={}".format(y))
                lambda_parameter = (c[y] / (l_m * 1000) ** 2)  # Calculate lambda parameter
                parameter_day = (int(rp_factor[z] * 100), int(c[y]))  # Current parameter combination
                arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "parameter_day={}".format(parameter_day))
                outname1 = "Q_rp{}_c{}_idw{}".format(int(rp_factor[z] * 100), int(c[y]), int(idw_exponent * 100))
                outname2 = "_s{}_e{}".format(int(start), int(end))
                result_path = arcpy.CreateTable_management(workpath, outname1)  # Create result table
                arcpy.AddField_management(result_path, "Datum", "DATE")
                arcpy.AddField_management(result_path, "Q", "DOUBLE")
                arcpy.DeleteField_management(result_path, ["OBJECTID", "FIELD1"])

                # Iterate over each day in the specified date range
                with arcpy.da.SearchCursor(climatedata, ['TagesID', 'Jahr', 'Monat', 'Tag', 'RelFeu', 'Temp_'],
                                           "TagesID >= {0} AND TagesID <= {1}".format(start, end)) as cursor:
                    for row in cursor:
                        id_day = int(row[0])
                        year = int(row[1])
                        month = int(row[2])
                        day = int(row[3])
                        humid = float(row[4])
                        temp = float(row[5])
                        pet = get_pet(haude_dic[month], temp, humid, id_day, parameter_day)  # Calculate PET
                        if id_day == start:
                            s_pre = s_init  # Initialize soil water storage

                        # Calculate various model parameters
                        aet = get_aet(pet, water, s_pre, rp, rpwp_dif, wp, id_day, parameter_day)
                        precipitation = get_precipitation(data, id_day, idw_exponent, cellsize, parameter_day)
                        runoff = get_runoff(water, lambda_parameter, wp, precipitation, s_pre, fc, pet, id_day, parameter_day)
                        runoff_m3 = get_q_m3(runoff, cellsize)
                        roverflow = get_roverflow(water, precipitation, s_pre, fc, id_day, parameter_day)
                        rsoil = get_rsoil(water, lambda_parameter, wp, s_pre, id_day, parameter_day)
                        s = get_soilwater(water, s_pre, precipitation, aet, runoff, id_day, parameter_day)

                        s_pre = s  # Update soil water storage for the next day
                        write_to_table(workpath, outname1, runoff_m3, str(id_day))  # Write daily runoff to the result table

                        rasters = {
                            "PET": pet,
                            "AET": aet,
                            "IDW": precipitation,
                            "R": runoff,
                            "S": s,
                            "Rsoil": rsoil,
                            "Roverflow": roverflow
                        }
                        save_rasters_to_disk(rasters, parameter_day, id_day, workpath, save_flags)  # Save rasters if required

                        # Check if raster sum is enabled
                        if check_raster_sum:
                            if int(sum_start) <= id_day <= int(sum_end):
                                if int(sum_start) == id_day:
                                    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Aufsummierung der Raster beginnt.")
                                    ndays = 1
                                    sum_pet = pet
                                    sum_aet = aet
                                    sum_precipitation = precipitation
                                    sum_runoff = runoff
                                    sum_s = s
                                    sum_roverflow = roverflow
                                    sum_rsoil = rsoil
                                elif int(sum_end) == id_day:
                                    sum_s = sum_s / ndays  # Average soil water storage over the period
                                    sum_aet += aet
                                    sum_pet += pet
                                    sum_precipitation += precipitation
                                    sum_runoff += runoff
                                    sum_s += s
                                    sum_roverflow += roverflow
                                    sum_rsoil += rsoil

                                    rasters_sum = {
                                        "PET_sum": sum_pet,
                                        "AET_sum": sum_aet,
                                        "IDW_sum": sum_precipitation,
                                        "R_sum": sum_runoff,
                                        "S_mean": sum_s,
                                        "Roverflow_sum": sum_roverflow,
                                        "Rsoil_sum": sum_rsoil
                                    }
                                    save_rasters_to_disk(rasters_sum, parameter_day, f"{sum_start}_{sum_end}", workpath, [True]*7)
                                    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Aufsummierte Raster geschrieben.")
                                else:
                                    ndays += 1
                                    sum_pet += pet
                                    sum_aet += aet
                                    sum_precipitation += precipitation
                                    sum_runoff += runoff
                                    sum_s += s
                                    sum_roverflow += roverflow
                                    sum_rsoil += rsoil

                        # Delete rasters from the previous day if necessary
                        if id_yesterday != start:
                            delete_raster(save_flags, parameter_day, id_yesterday, workpath)
                        id_yesterday = id_day  # Update the previous day ID

                        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit der Berechnung des {0}.{1}.{2}".format(day, month, year))
                del cursor  # Clean up cursor
                arcpy.TableToTable_conversion(result_path, workpath, outname1 + outname2 + ".csv")  # Convert result table to CSV
                delete_raster(save_flags, parameter_day, start, workpath)  # Delete initial day rasters if necessary
                if check_raster_sum:
                    delete_sum_raster(parameter_day, sum_start, workpath)  # Delete initial sum rasters if necessary
                if parameter_yesterday != parameter_day:
                    delete_raster(save_flags, parameter_yesterday, end, workpath)  # Delete final day rasters from previous parameter combination
                    if check_raster_sum:
                       delete_sum_raster(parameter_yesterday, sum_end - 1, workpath)  # Delete final sum rasters from previous parameter combination
                parameter_yesterday = parameter_day  # Update parameter combination
                arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit c={}".format(c[y]))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit rp={}".format(rp_factor[z]))

        delete_raster(save_flags, parameter_day, end, workpath)  # Delete final day rasters
        if check_raster_sum:
            delete_sum_raster(parameter_day, int(sum_end) - 1, workpath)  # Delete final sum rasters
        arcpy.Delete_management(result_path)  # Delete result table
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Modellierung abgeschlossen.")

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and added to the display."""
        return
