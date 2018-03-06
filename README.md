# ExampleDotNetAndPythonForAnalytics
This repository shows how use a python script in a Add-in, using an example of Density-Based Clustering Analysis

# Requirements
1 ArcGIS PRO 2.1

2 Visual Studio 2017 C#

# How To Use
This repo contains the source code of an Add-in for interactive analysis of the clustering-base algorithm OPTICS.
It contains a pyt file that must be referenced manually in the file Dockpanel1ViewModel.cs according with git repo location.

Use the tool Density-Based Clustering from the toolbox Spatial Statistical for creating cluster using the method OPTICS,
The output will contain the information (Reachability distance/Reachability Order) That is required in the addin. The Add-in will 
automatically detect the cluster.
The Tool will find interactevely new clusters using the tolerance and threshold distance
 ![alt text](https://github.com/ArcGIS/ExampleDotNetAndPythonForAnalytics/blob/master/addin.gif) 

# Licensing
Copyright 2018 Esri

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

A copy of the license is available in the repository's LICENSE.txt file.


