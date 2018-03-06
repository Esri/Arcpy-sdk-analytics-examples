# ExampleDotNetAndPythonForAnalytics
This repository shows how use a python script in a Add-in, using an example of Density-Based Clustering Analysis

# Requirements
1 ArcGIS PRO 2.1

2 Visual Studio 2017 C#

# How To Use
This repo contains the source code for an ArcGIS Pro Add-in.  The Add-in allows you to perform an interactive clustering of points using a popular machine learning clustering algorithm called OPTICS (Ankerst et al., 1999).  The repro contains a pyt file whose path must be explicitly referenced in the file Dockpanel1ViewModel.cs (167).  
The Add-in is designed to work with the output of the Density-based Clustering geoprocessing tool found in the Spatial Statistics toolbox.  This tool provides three clustering methods.  The Add-in requires that you run the tool using the Multi-scale (OPTICS) Clustering Method.   Density-based Clustering creates all the required output (Reachability distance/Reachability Order) for the Add-in. The Add-in will automatically detect clusters and allows you to dynamically and interactively explore alternative clustering solutions by adjusting tolerances and threshold distances. 
Mihael Ankerst, Markus M. Breunig, Hans-Peter Kriegel, Jörg Sander (1999). OPTICS: Ordering Points To Identify the Clustering Structure. ACM SIGMOD international conference on Management of data. ACM Press. pp. 49–60.

 ![alt text](https://github.com/ArcGIS/ExampleDotNetAndPythonForAnalytics/blob/master/addin.gif) 

# Licensing
Copyright 2018 Esri

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

A copy of the license is available in the repository's LICENSE.txt file.


