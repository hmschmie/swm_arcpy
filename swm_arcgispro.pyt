# -*- coding: utf-8 -*-

# import packages
import arcpy
from arcpy.sa import *
import time
import os
import shutil

arcpy.env.parallelProcessingFactor = "100%"

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
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
        # self.workspace_default = r'C:/2023_HydroGIS/HYDROGIS_FUER_HANNES/Vogelsberg_GIS/Vogelsberg_GIS.gdb'
        # self.basin_default = r'C:/2023_HydroGIS/HYDROGIS_FUER_HANNES/Vogelsberg_GIS/Vogelsberg_GIS.gdb/Hydrologie/EZG_Eichelsachsen_Vektor'
        # self.s_init_default = r'C:/2023_HydroGIS/HYDROGIS_FUER_HANNES/Vogelsberg_GIS/Vogelsberg_GIS.gdb/FK_von_L'
        # self.start_default = 20210526
        # self.end_default = 20210526
        # self.rp_factor_default = 0.85
        # self.rp_factor_max_default = 0.85
        # self.rp_factor_step_default = 0.05
        # self.c_min_default = 150
        # self.c_max_default = 150
        # self.c_step_default = 50
        # self.idw_exponent_default = 1.0
        # self.folder_default = r'C:\2023_HydroGIS\HYDROGIS_FUER_HANNES\swmouttest'
        # self.name_default = "Ergebnis"

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

        #define standard values
        workspace_param.value = r'C:/HydroGIS/Vogelsberg_GIS/Vogelsberg_GIS.gdb'
        basin_param.value = workspace_param.valueAsText + "/Hydrologie/EZG_Eichelsachsen_Vektor"
        s_init_param.value = workspace_param.valueAsText + "/FK"
        start_param.value = 20210526
        end_param.value = 20210526
        rp_factor_param.value = 0.85
        rp_factor_max_param.value = 0.85
        rp_factor_step_param.value = 0.05
        c_param.value = 150
        c_max_param.value = 150
        c_step_param.value = 50
        idw_exponent_param.value = 1.0
        folder_param.value = r'C:\HydroGIS\swmout'
        name_param.value = "SWM_Eichelsachsen_Ergebnisdaten_20210526"
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


       #do not modify the order as this is numbered and numbers are hard coded in the following.
        parameters = [workspace_param, basin_param, s_init_param, start_param, end_param, rp_factor_param,
                c_param, idw_exponent_param, folder_param, name_param, rp_factor_max_param, rp_factor_step_param,
                c_max_param, c_step_param, raster_sum_param, sum_start_param, sum_end_param, check_pet_param,
                      check_aet_param, check_p_param, check_r_param, check_ro_param, check_rs_param, check_s_param]
        return parameters

    def validate(self, parameters, messages):
        return

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):

        #workspace_name = parameters[0].valueAsText
        #basin_name = parameters[1].valueAsText

        """The source code of the tool."""
        arcpy.CheckOutExtension("Spatial")
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Systemmodule geladen.")

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
            pet_raster = haude_factor * (6.1 * 10 ** ((7.5 * temperature) / (temperature + 237.2))) * (
                    1.0 - humidity / 100.0)
            pet_raster.save(f"PET_rp{parameter_safe[0]}_c{parameter_safe[1]}_{date}.tif")
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "PET berechnet.")

            return pet_raster

        def get_aet(pet_raster, water_raster, s_pre_raster, rp_raster, rpwp_dif_raster, wp_raster, date,
                    parameter_safe):
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
                                 Con(rpwp_dif_raster == 0, 0,
                                     ((s_pre_raster - wp_raster) / rpwp_dif_raster) * pet_raster)))
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
            #arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Niederschlag start.")
            arcpy.management.MakeQueryTable(
                r'{}\N_Messstationen;'.format(dataspace) + r'{}\N_Zeitreihen'.format(dataspace), "p_temp",
                "USE_KEY_FIELDS", "N_Messstationen.Stationsnummer;N_Zeitreihen.TagesID",
                "N_Messstationen.Stationsnummer;N_Messstationen.Stationsname; N_Messstationen.Shape\
                                            ;N_Zeitreihen.Tagessumme_mm;N_Zeitreihen.TagesID", "N_Zeitreihen.Stationsnummer =\
                                                   N_Messstationen.Stationsnummer AND N_Zeitreihen.TagesID = {}".format(
                    date))
            #arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Niederschlag query end.")
            idw = Idw("p_temp", "N_Zeitreihen.Tagessumme_mm", rastercellsize, idw_pow, RadiusFixed(20000.00000, 5), "")
            #arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Niederschlag idw end.")
            idw.save("IDW_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
            #arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Niederschlag save end.")
            arcpy.Delete_management("p_temp")
           #arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Niederschlag interpoliert.")

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
            r = Con(water_raster == 1, Con(p_raster > pet_raster, p_raster - pet_raster, p_raster), (
                    lambda_param * ((s_pre_raster - wp_raster) ** 2) + Con(p_raster + s_pre_raster > fc_raster,
                                                                           p_raster + s_pre_raster - fc_raster, 0)))
            r.save("R_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Gesamtabfluss je Rasterzelle berechnet.")

            return r

        def get_rsoil(water_raster, lambda_param, wp_raster, s_pre_raster, date, parameter_safe):
            """
            Calculates a raster dataset of the land runoff from soil (0 for water cells).
            :param water_raster: mask of water cells (:type: raster)
            :param lambda_param: Lambda value (:type: raster)
            :param wp_raster: wilting point (wp) (:type: raster)
            :param s_pre_raster: soilwater content of the previous day (:type: raster)
            :param date: daily ID (:type: integer)
            :param parameter_safe: values of the variable combination (:type: tuple)
            :return: runoff from soil according to Glugla (1969) (:type: raster)
            """
            r = Con(water_raster == 1, 0, (lambda_param * ((s_pre_raster - wp_raster) ** 2)))
            r.save("Rsoil_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Soil runoff (Glugla 1969) je Rasterzelle berechnet.")

            return r

        def get_roverflow(water_raster, p_raster, s_pre_raster, fc_raster, date, parameter_safe):
            """
            Calculates a raster dataset of the overflow runoff, defined only for land areas whereas in water cells overflow of 0 is given.
            :param water_raster: mask of water cells (:type: raster)
            :param p_raster: output of the function "get_precipitation" (:type: raster)
            :param s_pre_raster: soilwater content of the previous day (:type: raster)
            :param fc_raster: field capacity (fc) (:type: raster)
            :param date: daily ID (:type: integer)
            :param parameter_safe: values of the variable combination (:type: tuple)
            :return: overflow runoff (:type: raster)
            """
            r = Con(water_raster == 1, 0,
                    Con(p_raster + s_pre_raster > fc_raster, p_raster + s_pre_raster - fc_raster, 0))
            r.save("Roverflow_rp{}_c{}_{}.tif".format(parameter_safe[0], parameter_safe[1], date))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "R overflow je Rasterzelle berechnet.")

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
            soilwater = Con(water_raster == 0, s_pre_raster + p_raster - aet_raster - runoff_raster, )
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

        def delete_raster(bool_pet, bool_aet, bool_p, bool_r, bool_s, bool_rs, bool_ro, parameter_safe, yesterday):
            """
            Deletes the raster datasets created by the functions above if selected from the previous day.
            :param bool_pet: boolean to delete the PET-raster (::type: boolean)
            :param bool_aet: boolean to delete the AET-raster (::type: boolean)
            :param bool_p: boolean to delete the precipitation-raster (::type: boolean)
            :param bool_r: boolean to delete the runoff-raster (::type: boolean)
            :param bool_s: boolean to delete the soilwater-raster (::type: boolean)
            :param bool_rs: boolean to delete the runoff from soil -raster (::type: boolean)
            :param bool_ro: boolean to delete the overflow runoff-raster (::type: boolean)
            :param parameter_safe: values of the variable combination (::type: tuple)
            :param yesterday: previous daily ID (::type: integer)
            :return:
            """
            for i in [("PET", bool_pet), ("AET", bool_aet), ("IDW", bool_p), ("R", bool_r), ("S", bool_s),
                      ("Rsoil", bool_rs), ("Roverflow", bool_ro)]:
                if not i[1]:
                    arcpy.Delete_management(
                        "{}_rp{}_c{}_{}.tif".format(i[0], parameter_safe[0], parameter_safe[1], yesterday))

        def delete_sum_raster(parameter_safe, yesterday):
            """
            Deletes the sum raster datasets created by the functions above if selected from the previous day.
            :param parameter_safe: values of the variable combination (::type: tuple)
            :param yesterday: previous daily ID (::type: integer)
            :return:
            """
            for i in [("PET"), ("AET"), ("IDW"), ("R"), ("S"), ("Rsoil"), ("Roverflow")]:
                arcpy.Delete_management(
                    "{}_sum_rp{}_c{}_{}_sumday.tif".format(i, parameter_safe[0], parameter_safe[1], yesterday))

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
            quotient_array = arcpy.RasterToNumPyArray(dividend / divisor, nodata_to_value=0)
            return quotient_array


        # Access the parameter values, simplified without catching errors to avoid setting to default values in case something gets wrong
        data = parameters[0].valueAsText
        basin = parameters[1].valueAsText
        s_init = arcpy.sa.ExtractByMask(parameters[2].valueAsText, basin)
        id_yesterday = start = parameters[3].valueAsText
        end = parameters[4].valueAsText
        rp_factor_min = float(parameters[5].valueAsText.replace(",","."))
        c_min = int(parameters[6].valueAsText)
        idw_exponent = float(parameters[7].valueAsText.replace(",","."))
        folder = parameters[8].valueAsText
        name = parameters[9].valueAsText
        rp_factor_max = float(parameters[10].valueAsText.replace(",","."))
        rp_factor_step = float(parameters[11].valueAsText.replace(",","."))
        c_max = int(parameters[12].valueAsText)
        c_step = int(parameters[13].valueAsText)
        check_raster_sum = parameters[14].value
        sum_start = parameters[15].valueAsText
        sum_end = parameters[16].valueAsText
        check_pet = parameters[17].value
        check_aet = parameters[18].value
        check_p = parameters[19].value
        check_r = parameters[20].value
        check_ro = parameters[21].value
        check_rs = parameters[22].value
        check_s = parameters[23].value

        """ set main settings and creating the working and scratch directory """
        arcpy.env.overwriteOutput = True  # to overwrite results
        arcpy.env.extent = s_init  # set the working extent
        workpath = arcpy.env.workspace = os.path.join(folder, name)
        scratch = "Scratch"
        scratchpath = os.path.join(folder,scratch)

        arcpy.AddMessage(f"workpath: {workpath}")
        if not os.path.exists(workpath):  # if the working directory exists, it will be overwritten
            try:
                os.makedirs(workpath)
                arcpy.AddMessage(f"Ausgabeordner erstellt: {workpath}")
            except Exeption as e:
                arcpyAddError(f"Ausgabeordner nicht erstellt: {str(e)}")
        else:
            arcpy.AddMessage("Ausgabeordner existiert bereits und wird neu aufgesetzt.")
            shutil.rmtree(workpath)
            os.makedirs(workpath)

        if not os.path.exists(scratchpath):  # if the Scratch directory exists, it will be overwritten
            try:
                os.makedirs(scratchpath)
                arcpy.AddMessage(f"Scratchordner erstellt: {scratchpath}")
            except Exeption as e:
                arcpyAddError(f"Scratchordner nicht erstellt: {str(e)}")
        else:
            arcpy.AddMessage("Scratchordner existiert bereits und wird neu aufgesetzt.")
            shutil.rmtree(scratchpath)
            os.makedirs(scratchpath)

        arcpy.env.scratchWorkspace = scratchpath

        arcpy.AddMessage(
            time.strftime("%H:%M:%S: ") + f"Die Ergebnisdatenbank wurde im Verzeichnis {workpath} erstellt.")

        """link and extract the base datasets (The datasets has to be saved with the same name as below in the base directory.)"""
        # dictionary to link the month and its specific haudefactor
        haude_dic = {1: ExtractByMask(Raster(r'{}\Haude_Jan'.format(data)), basin),
                     2: ExtractByMask(Raster(r'{}\Haude_Feb'.format(data)), basin),
                     3: ExtractByMask(Raster(r'{}\Haude_Mar'.format(data)), basin),
                     4: ExtractByMask(Raster(r'{}\Haude_Apr'.format(data)), basin),
                     5: ExtractByMask(Raster(r'{}\Haude_Mai'.format(data)), basin),
                     6: ExtractByMask(Raster(r'{}\Haude_Jun'.format(data)), basin),
                     7: ExtractByMask(Raster(r'{}\Haude_Jul'.format(data)), basin),
                     8: ExtractByMask(Raster(r'{}\Haude_Aug'.format(data)), basin),
                     9: ExtractByMask(Raster(r'{}\Haude_Sep'.format(data)), basin),
                     10: ExtractByMask(Raster(r'{}\Haude_Okt'.format(data)), basin),
                     11: ExtractByMask(Raster(r'{}\Haude_Nov'.format(data)), basin),
                     12: ExtractByMask(Raster(r'{}\Haude_Dez'.format(data)), basin)}
        climatedata = r'{}\TempFeuchte_'.format(data)  # table
        fc = ExtractByMask(Raster(r'{}\FK'.format(data)), basin)  # raster
        wp = ExtractByMask(Raster(r'{}\WP'.format(data)), basin)  # raster
        wpfc_qarray = rasterquotient_array(wp, fc)  # calculates an array of the quotient of two rasters #  array
        rp_control = wpfc_qarray.max()  # extract the biggest vaule of the quotient of wp:fc to compare with the rp-factor
        water = ExtractByMask(Raster(r'{}\Gewaessermaske'.format(data)), basin)  # raster
        s_pre = s_init

        # p_data = r'{}\N_Zeitreihen'.format(data)  # table

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

        """main part - iterating through the climate data of the period"""
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Anzahl RP-Parameter={}".format(len(rp_factor)))
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Anzahl c-Parameter={}".format(len(c)))

        for z in range(len(rp_factor)):
            arcpy.AddMessage("z={}".format(z))
            arcpy.AddMessage("Maximalwert von WP/FK={}".format(rp_control))
            arcpy.AddMessage("gewaehlter RP={}".format(rp_factor[z]))
            if rp_control >= rp_factor[z]:  # the AET is negative, if the rp-factor is smaller than the quotient of wp:fc
                arcpy.AddMessage(
                    "RP-Parameter ist kleiner als der Maximalwert von WP/FK. RP-Parameter = {} wird uebersprungen.".format(
                        rp_factor[z]))
                continue  # skips all rp-factors smaller than the quotient of wp:fc
            rp = fc * rp_factor[z]
            rpwp_dif = rp - wp
            for y in range(len(c)):
                arcpy.AddMessage("y={}".format(y))
                lambda_parameter = (c[y] / (l_m * 1000) ** 2)
                # value memory for the current combination of variables to add it in the filenames and the result table
                parameter_day = (int(rp_factor[z] * 100), int(c[y]))
                arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "parameter_day={}".format(parameter_day))
                # creating a result table for each combination of variables
                outname1 = "Q_rp{}_c{}_idw{}".format(int(rp_factor[z] * 100), int(c[y]), int(idw_exponent * 100))
                #arcpy.AddMessage("outname1={}".format(outname1))
                outname2 = "_s{}_e{}".format(int(start), int(end))
                #arcpy.AddMessage("outname2={}".format(outname2))
                result_path = arcpy.CreateTable_management(workpath, outname1)
                arcpy.AddField_management(result_path, "Datum", "DATE")
                arcpy.AddField_management(result_path, "Q", "DOUBLE")
                arcpy.DeleteField_management(result_path, ["OBJECTID", "FIELD1"])

                # iterating through the climate data of the period
                with arcpy.da.SearchCursor(climatedata, ['TagesID', 'Jahr', 'Monat', 'Tag', 'RelFeu', 'Temp_'],
                                           "TagesID >= {0} AND TagesID <= {1}".format(start, end)) as cursor:
                    for row in cursor:

                        id_day = int(row[0])  # YYYYMMDD
                        year = int(row[1])  # YYYY
                        month = int(row[2])  # MM
                        day = int(row[3])  # DD
                        humid = float(row[4])  # in %
                        temp = float(row[5])  # in ?C
                        # calculating and saving a raster dataset for each parameter
                        pet = get_pet(haude_dic[month], temp, humid, id_day, parameter_day)
                        if id_day == start:
                            s_pre = s_init

                        aet = get_aet(pet, water, s_pre, rp, rpwp_dif, wp, id_day, parameter_day)
                        precipitation = get_precipitation(data, id_day, idw_exponent, cellsize, parameter_day)
                        runoff = get_runoff(water, lambda_parameter, wp, precipitation, s_pre, fc, pet, id_day, parameter_day)
                        runoff_m3 = get_q_m3(runoff, cellsize)  # floating point number
                        roverflow = get_roverflow(water, precipitation, s_pre, fc, id_day, parameter_day)
                        rsoil = get_rsoil(water, lambda_parameter, wp, s_pre, id_day, parameter_day)
                        s = get_soilwater(water, s_pre, precipitation, aet, runoff, id_day, parameter_day)

                        s_pre = s  # memory for soilwater from the previous day
                        write_to_table(workpath, outname1, runoff_m3, str(id_day))  # writing the runoff into the result table
                        if check_raster_sum == True:
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
                                    sum_s = sum_s / ndays  # storage as mean value
                                    sum_aet = sum_aet + aet
                                    sum_aet.save(
                                        "AET_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                            sum_end))
                                    sum_pet = sum_pet + pet
                                    sum_pet.save(
                                        "PET_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                            sum_end))
                                    sum_precipitation = sum_precipitation + precipitation
                                    sum_precipitation.save(
                                        "IDW_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                            sum_end))
                                    sum_runoff = sum_runoff + runoff
                                    sum_runoff.save(
                                        "R_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                          sum_end))
                                    sum_s = sum_s + s
                                    sum_s.save("S_mean_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                                  sum_end))
                                    sum_roverflow = sum_roverflow + roverflow
                                    sum_roverflow.save(
                                        "Roverflow_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                                  sum_end))
                                    sum_rsoil = sum_rsoil + rsoil
                                    sum_rsoil.save(
                                        "Rsoil_sum_rp{}_c{}_{}_{}.tif".format(parameter_day[0], parameter_day[1], sum_start,
                                                                              sum_end))
                                    arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Aufsummierte Raster geschrieben.")
                                else:
                                    ndays = ndays + 1
                                    sum_pet = sum_pet + pet
                                    sum_pet.save(
                                        "PET_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                                    sum_aet = sum_aet + aet
                                    sum_aet.save(
                                        "AET_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                                    sum_precipitation = sum_precipitation + precipitation
                                    sum_precipitation.save(
                                        "IDW_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                                    sum_runoff = sum_runoff + runoff
                                    sum_runoff.save(
                                        "R_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                                    sum_s = sum_s + s
                                    sum_s.save(
                                        "S_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                                    sum_roverflow = sum_roverflow + roverflow
                                    sum_roverflow.save(
                                        "Roverflow_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1],
                                                                                      id_day))
                                    sum_rsoil = sum_rsoil + rsoil
                                    sum_rsoil.save(
                                        "Rsoil_sum_rp{}_c{}_{}_sumday.tif".format(parameter_day[0], parameter_day[1], id_day))
                                    if ndays > 2:
                                        delete_sum_raster(parameter_day, id_yesterday)

                        # deletes the calculated rasters above if selected
                        if not id_yesterday == start:
                            delete_raster(check_pet, check_aet, check_p, check_r, check_s, check_rs, check_ro, parameter_day,
                                          id_yesterday)
                        id_yesterday = id_day  # memory for the id form the previous day; necessary to delete the rasterdatasets

                        arcpy.AddMessage(time.strftime("%H:%M:%S: ") +
                                         "Fertig mit der Berechnung des {0}.{1}.{2}".format(day, month, year))
                del cursor
                # convert resulting table to .csv
                arcpy.TableToTable_conversion(result_path, workpath, outname1 + outname2 + ".csv")
                # deleting the rasters of the first day of the current variable combination
                delete_raster(check_pet, check_aet, check_p, check_r, check_s, check_rs, check_ro, parameter_day, start)
                if check_raster_sum == True:
                    delete_sum_raster(parameter_day, sum_start)
                # deleting the rasters of the last day of the previous variable combination
                if not parameter_yesterday == parameter_day:
                    delete_raster(check_pet, check_aet, check_p, check_r, check_s, check_rs, check_ro, parameter_yesterday, end)
                    if check_raster_sum == True:
                       delete_sum_raster(parameter_yesterday, sum_end - 1)
                parameter_yesterday = parameter_day  # memory for the value of the last combination of variables
                arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit c={}".format(c[y]))
            arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Fertig mit rp={}".format(rp_factor[z]))

        # deleting the rasters of the last day of the last variable combination
        delete_raster(check_pet, check_aet, check_p, check_r, check_s, check_rs, check_ro, parameter_day, end)
        if check_raster_sum == True:
            delete_sum_raster(parameter_day, int(sum_end) - 1)
        arcpy.Delete_management(result_path)
        #shutil.rmtree(result_path)
        #arcpy.RefreshCatalog(workpath) #does not work with ArcGIS Pro
        arcpy.AddMessage(time.strftime("%H:%M:%S: ") + "Modellierung abgeschlossen.")

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
