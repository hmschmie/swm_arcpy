# swm_arcpy
ArcPy implementation of the soil water model for use in a lecture at Goethe University Frankfurt am Main

# creator
Initial creator is Florian Herz, who developed under the supervision of Hannes Müller Schmied this implementation. The implementation was funded by the Goethe University Frankfurt, Germany within an e-learning Förderfonds-activity. The initial developed model version was modified several times by Hannes Müller Schmied (see the .py document).

# note to the implementation
Using a python toolbar instead of a .tbx is a better solution but due to the lack of time, this python script and the (not in an IDE editable) tbx need to be stored at one place that it can be found in ArcGIS. 

# SWM in Arcpy Hinweise 

## Relative Pfadnamen 
Das Script-Tool wurde unter Verwendung relativer Pfadnamen erstellt. Die vorgegebenen Dateipfade 
(z.B. Default der Basisdatenbank) beziehen sich auf den Dateipfad des Pythonscriptes (.py). Somit müs-
sen folgende Dateien zum Abruf der relativen Pfadnamen im Arbeitsverzeichnis vorhanden sein: 
- Script.py 
- Basisdatenbank.gdb 
- Toolbox.tbx 

Liegt z.B. das Pythonscript (Script.py) in einem anderen Verzeichnis oder mit einem anderen Namen 
als vorgegeben vor, muss in Arc GIS in der Toolbox mit rechtsklick auf das Script unter _Properties_ im 
Reiter _Source_ der Dateipfad des Pythonscriptes unter _Script File_ ausgewählt werden. Eine andere Ba-
sisdstenbank kann beim ausführen des Script-Tools ausgewählt werden. 

## Tool-Validator 
Der Tool-Validator ist aufrufbar mit rechtsklick auf Properties des Pythonscripts in der Toolbox im Rei-
ter _Validation_. Hier werden die Werte der Toolparameter validiert und das Verhalten der Benutzer-
oberfläche kontrolliert. Die Zuordnung der Toolparameter zum Löschen der täglichen Rasterdaten-
sätze zur **Kategorie** „Speichern der täglichen Rasterdateien“ und der Toolparameter zur Variation des 
RP-Faktors und des c-Parameters sowie zur Wahl des IDW-Exponenten zur Kategorie „weitere Para-
metereinstellungen“ erfolgt beim Öffnen des Tools im Tool-Validator. 

Unter _update Parameters_ kann unter anderem ein **Default-Wert für Toolparameter** definiert werden. 
Hier wurden die Werte der von relativen Pfadnamen abhängigen Toolparameter „Geodatenbank der 
Basisdaten“, „Einzugsgebiet“, Initialer Bodenwasserspeicher und „Speicherpfad des Ausgabeordners“ 
initialisiert. So lange keiner dieser Parameter vom Benutzer geändert wurde, werden die relativen 
Pfade der Dateien für das EZG Schotten 2 verwendet. Zum Ändern dieser Voreinstellung muss der 
Name der Datei unter _Edit_ abgeändert werden (siehe Abbildung 1). 

![grafik](https://user-images.githubusercontent.com/57669828/147912666-d4cae953-8649-47cc-a054-38b61da3c8dd.png)
Abbildung 1: Beispiel Default Wert des ersten Toolparameters

Des Weiteren ist unter _update Parameters_ definiert, dass die Felder zur Variation des RP-Faktors und 
des c-Parameters erst freigeschaltet werden, wenn die jeweilige Checkbox aktiviert wurde. Bei Deak-
tivierung der Checkbox werden die Werte für die Toolparameter „RP-Faktor (Max)“ und „c-Parameter 
(Max)“ von den Toolparametern „RP-Faktor“ und „c-Parameter“ übernommen. Dies ist notwendig, da 
die Werte dieser Felder auch wenn diese nicht freigeschaltet sind, an das Pythonscript übergeben wer-
den und der entsprechende Parameter ungewünscht variiert werden würde. 

Unter _update Messages_ werden **Warnungen und Fehlermeldungen** für die einzelnen Toolparameter 
definiert. Dazu gehören folgende Fehlermeldungen: 
- Enddatum liegt vor dem Startdatum 
- Der Ausgabeordner existiert bereits 
- Ein eingegebener RP-Faktor liegt nicht zwischen 0 und 1 
- Der maximale RP-Faktor/c-Parameter ist kleiner als der minimale

## Python-Script 
Die Übergabe der in der Benutzeroberfläche in Arc GIS eigegebenen Toolparameter erfolgt ausschließ-
lich im Textformat als Strings. (GetParameterAsText() – im Pythonscript). Dies ist besonders für Dezi-
malzahlen problematisch. Das Dezimaltrennzeichen in Arc GIS ist abhängig von der Einstellung im Be-
triebssystem, während es sich bei Python ausschließlich um einen Punkt handelt. Kommas werden 
somit nach der Übergabe an das Script durch einen Punkt ersetzt. Auch die Werte der boolschen Para-
meter zum Löschen der täglichen Rasterdateien werden nach der Übergabe vom Typ „String“ in den 
Typ „Boolean“ überführt. 

Für das Scratch-Workspace des Scriptes wird ein Ordner „Scratch“ im Arbeitsverzeichnis angelegt. Die-
ser bleibt nach Ausführen des Tools bestehen, da er aufgrund einer Lock-File nicht nach Abschluss der 
Modellierung automatisch gelöscht werden kann. 

Die verwendeten Rasterdatensätze (wie Haudefaktor, FK, WP oder Durchwurzelungstiefe) werden auf 
das ausgewählte EZG beschnitten. Somit werden auch alle weiteren erstellten Rasterdatensätze nur 
für das EZG berechnet. Lediglich die Niederschlagsinterpolation wird für das kleinste umgebene Recht-
eck berechnet. Die Begrenzung auf das EZG ist Notwendig, da zur Bestimmung des Durchflusses in m³ 
das Gesamtabfluss-Raster in ein Array überführt wird und alle Zellenwerte aufsummiert werden. Ein 
nützlicher Nebeneffekt ist die Reduzierung von Speicherplatz, bei Speicherung der täglichen Rasterda-
teien. 

Der RP-Faktor kann nur mit zwei Nachkommastellen eingegeben werden, da die Nachkommastellen 
mit in den Namen der Ergebnistabelle aufgenommen wird. Dies erfolgt über die Multiplikation des RP-
Faktors mit 100. Dies wäre abänderbar wenn dieser Faktor sowohl in der Variable _parameter_day_ als 
auch in der Variable _parameter_yesterday_ geändert würde. Zusätzlich wird bei der Erstellung der Liste 
aller RP-Faktoren diese auf zwei Nachkommastellen gerundet. Auch hier müsste dann die Anzahl an-
gepasst werden. 

Das Modell vermeidet das Auftreten einer negativen AET, da es vor Beginn der Modellierung eines 
Durchlaufs den RP-Faktor prüft, ob dieser kleiner oder gleich dem größten Quotienten aus WP:FK in 
einer Rasterzelle ist. Ist dies der Fall, wird der gesamte Durchlauf übersprungen und mit dem nächsten 
RP-Faktor fortgefahren.  

Das Löschen der täglichen Rasterdateien erfolgt am Ende der nächsten Iteration. Das direkte Löschen 
der Rasterdatensätze ruft einen Fehler hervor, dessen genaue Ursache unbekannt ist. Wurde jedoch 
ein weiterer Rasterdatensatz erstellt, kann der vorherige Problemlos gelöscht werden. Die Reihenfolge 
des Löschens der Rasterdatensätze erfolgt folgender maßen: 
1. Löschen der Raster der ersten Parameterkombination vom zweiten bis zum vorletzten Tag des 
Zeitraums am jeweils darauffolgenden Tag. 
2. Nach Abschluss der Modellierung der ersten Parameterkombination löschen der Raster des 
ersten Tages der ersten Parameterkombination. 
3. Löschen der Raster der zweiten Parameterkombination vom zweiten bis zum vorletzten Tag 
des Zeitraums am jeweils darauffolgenden Tag. 
4. Nach Abschluss der Modellierung der zweiten Parameterkombination löschen der Raster des 
letzten Tages der ersten Parameterkombination und des ersten Tages der zweiten Parameter-
kombination. 
5. Wiederholung der Schritte 3 und 4 bis zur letzten Parameterkombination. 
6. Nach Abschluss der Iteration löschen der Raster des letzten Tages der letzten Parameterkom-
bination. 

Zum Ende des Scriptes wird der Arc GIS Catalog refreshed, um die ggf. erstellten Raster anzuzeigen. 
