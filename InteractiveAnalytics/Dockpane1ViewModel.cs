/*
   Licensed under the Apache License, Version 2.0 (the "License");

   you may not use this file except in compliance with the License.

   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software

   distributed under the License is distributed on an "AS IS" BASIS,

   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

   See the License for the specific language governing permissions and

   limitations under the License.​

*/
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using System.Windows.Input;
using ArcGIS.Desktop.Mapping;
using ArcGIS.Core.CIM;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core.Geoprocessing;

namespace InteractiveAnalytics
{

  internal class Dockpane1ViewModel : DockPane
  {

    private List<FeatureLayer> _layers = new List<FeatureLayer>();
    private FeatureLayer _selectedLayer = null;
    private string _minPoints = "2";
    private int _valueSlider = 0;
    private int _valueThreshold = 0;
    private const string _dockPaneID = "InteractiveAnalytics_Dockpane1";

    protected Dockpane1ViewModel() { }

    /// <summary>
    /// Show the DockPane.
    /// </summary>
    internal static void Show()
    {
      DockPane pane = FrameworkApplication.DockPaneManager.Find(_dockPaneID);
      if (pane == null)
        return;

      pane.Activate();
    }

    /// <summary>
    /// Text shown near the top of the DockPane.
    /// </summary>
    private string _heading = "Cluster Analytics";
    public string Heading
    {
      get { return _heading; }
      set
      {
        SetProperty(ref _heading, value, () => Heading);
      }
    }

    public List<FeatureLayer> Layers
    {
      get { return _layers; }
      set
      {
        SetProperty(ref _layers, value, () => Layers);
      }
    }
    public FeatureLayer SelectedLayer
    {
      get { return _selectedLayer; }
      set
      {
        SetProperty(ref _selectedLayer, value, () => SelectedLayer);
      }
    }


    internal async  void GetLayersInMap()
    {

      if (MapView.Active == null)
        return;

      var currentMap = MapView.Active.Map;
      var layers = currentMap.GetLayersAsFlattenedList();
      List<FeatureLayer> featureLayers = new List<FeatureLayer>();
      foreach (Layer lyr in layers)
      {
        if (lyr is FeatureLayer)
        {
          FeatureLayer flyr = lyr as FeatureLayer;
          bool check = true;
          check = (flyr.ShapeType == esriGeometryType.esriGeometryPoint);
          if (check)
          {
            /// Verify that point feature class contains Reachability Distance field
            int hasClusteredOpticLayer = await QueuedTask.Run<int>(() =>
            {
             return flyr.GetTable().GetDefinition().FindField("REACHDIST");
            });

            if (hasClusteredOpticLayer >= 0)
              featureLayers.Add(flyr);
          }
        }
      }
      _layers = featureLayers;
      NotifyPropertyChanged(() => Layers);

    }

    public string MinPoints
    {
      get { return _minPoints; }
      set
      {
        SetProperty(ref _minPoints, value, () => MinPoints);
      }
    }
    public int ValueSlider
    {
      get { return _valueSlider; }
      set
      {
        SetProperty(ref _valueSlider, value, () => ValueSlider);
      }
    }


    public int ValueThreshold
    {
      get { return _valueThreshold; }
      set
      {
        SetProperty(ref _valueThreshold, value, () => ValueThreshold);
      }
    }


    internal async void UpdateCluster(bool isTolerance)
    {
      if (MapView.Active == null)
        return;
      // Get Layer Name
      string inputFC = SelectedLayer.Name;

      int minPoints = 2;
      bool parsed = Int32.TryParse(MinPoints, out minPoints);

      /// Set PYT path -This could be inserted as a resource file //
      string tool_path = "C:\\Dev_summit\\2018\\InteractiveAnalytics\\pyt\\UpdateCluster.pyt\\UpdateClusterTool";

      IReadOnlyList<string> args= null;
      if (isTolerance)
      {
        /// Arguments for executing process using Tolerance
        args = Geoprocessing.MakeValueArray(inputFC, minPoints, ValueSlider, -1);
      }
      else
      {
        /// Arguments for executing process using Threshold
        args = Geoprocessing.MakeValueArray(inputFC, minPoints, -1, ValueThreshold);
      }
      
      Task<IGPResult> task;
      /// Execute the Tool in the python toolbox
      task = Geoprocessing.ExecuteToolAsync(tool_path, args, flags: GPExecuteToolFlags.AddToHistory);


      StyleProjectItem style;
      CIMPointSymbol pointSymbol = null;

      /// Get Pro Styles
      style = await QueuedTask.Run<StyleProjectItem>(() => Project.Current.GetItems<StyleProjectItem>().First(s => s.Name == "ArcGIS 2D"));


      await QueuedTask.Run( () =>
      {
        /// Search for a specific Symbol
        /// Other styles Arcgis/Resouces/Styles/Styles.stylx SQLite DB
        SymbolStyleItem symbolStyleItem = (SymbolStyleItem)style.LookupItem(StyleItemType.PointSymbol, "Circle 1_Shapes_3");
        pointSymbol = (CIMPointSymbol)symbolStyleItem.Symbol;

        /// Cluster Ids based in Color Schema
        int[] ids = new int[] { -1, 1, 2, 3, 4, 5, 6, 7, 8 };

        /// Set Colors
        string[] colors = new string[]{ "156,156,156", "166,206,227", "31,120,180", "178,223,138",
                                        "51,160,44", "251,154,153", "227,26,28", "253,191,111",
                                       "255,127,0" };
        /// Color Field
        String[] fields = new string[] { "COLOR_ID" };

        /// Make a reference of the point symbol
        CIMSymbolReference symbolPointTemplate = pointSymbol.MakeSymbolReference();

        /// Get definition of type symbology unique values
        UniqueValueRendererDefinition uniqueValueRendererDef = new UniqueValueRendererDefinition(fields, symbolPointTemplate, null, symbolPointTemplate, false);

        /// Get Current renderer of the Selected Layer 
        CIMUniqueValueRenderer renderer = (CIMUniqueValueRenderer)SelectedLayer.CreateRenderer(uniqueValueRendererDef);
        CIMUniqueValueClass[] newClasses = new CIMUniqueValueClass[colors.Count()];

        /// Get Point Symbol as string for creating other point colors 
        string point = pointSymbol.ToXml();

        /// Create Each Color 
        for (int i = 0; i < ids.Length; i++)
        {
          CIMPointSymbol npoint = CIMPointSymbol.FromXml(point);
          if (ids[i] == -1)
          {
            npoint.SetSize(4);
          }
          else
          {
            npoint.SetSize(6);
          }
          CIMSymbolReference symbolPointTemplatei = npoint.MakeSymbolReference();
          newClasses[i] = new CIMUniqueValueClass();
          newClasses[i].Values = new CIMUniqueValue[1];
          newClasses[i].Values[0] = new CIMUniqueValue();
          newClasses[i].Values[0].FieldValues = new string[1];
          newClasses[i].Values[0].FieldValues[0] = ids[i].ToString();
          newClasses[i].Label = ids[i].ToString();
          newClasses[i].Symbol = symbolPointTemplatei;
          var color = colors[i].Split(',');
          double r = Convert.ToDouble(color[0]);
          double g = Convert.ToDouble(color[1]);
          double b = Convert.ToDouble(color[2]);
          newClasses[i].Symbol.Symbol.SetColor(CIMColor.CreateRGBColor(r, g, b));
        }
        /// Add Colors into the renderer
        renderer.Groups[0].Classes = newClasses;

        /// Apply new renderer in the layer
        SelectedLayer.SetRenderer(renderer);
        
        //SelectedLayer.RecalculateRenderer();
      });

    }
  }


  /// <summary>
  /// Button implementation to show the DockPane.
  /// </summary>
  internal class Dockpane1_ShowButton : Button
  {
    protected override void OnClick()
    {
      Dockpane1ViewModel.Show();
    }
  }




}
