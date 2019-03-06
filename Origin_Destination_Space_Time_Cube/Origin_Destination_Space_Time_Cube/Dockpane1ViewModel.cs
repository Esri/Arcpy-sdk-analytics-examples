using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Core.CIM;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Extensions;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Framework.Dialogs;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using ArcGIS.Desktop.Core.Geoprocessing;
using System.Windows.Input;

namespace Origin_Destination_Space_Time_Cube
{
  internal class Dockpane1ViewModel : DockPane
  {
    private const string _dockPaneID = "Origin_Destination_Space_Time_Cube_Dockpane1";

    private List<FeatureLayer> _layersOrigin = new List<FeatureLayer>();
    private FeatureLayer _selectedLayerOrigin = null;
    private List<FeatureLayer> _layersDestination = new List<FeatureLayer>();
    private FeatureLayer _selectedLayerDestination = null;
    private string _ncOrigin="";
    private string _ncDestination="";
    private ICommand _search = null;

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
    private string _heading = "Origin Destination";
    public string Heading
    {
      get { return _heading; }
      set
      {
        SetProperty(ref _heading, value, () => Heading);
      }
    }

    public List<FeatureLayer> LayersOrigin
    {
      get { return _layersOrigin; }
      set
      {
        SetProperty(ref _layersOrigin, value, () => LayersOrigin);
      }
    }
    public FeatureLayer SelectedLayerOrigin
    {
      get { return _selectedLayerOrigin; }
      set
      {
        SetProperty(ref _selectedLayerOrigin, value, () => SelectedLayerOrigin);
      }
    }

    public List<FeatureLayer> LayersDestination
    {
      get { return _layersDestination; }
      set
      {
        SetProperty(ref _layersDestination, value, () => LayersDestination);
      }
    }
    public FeatureLayer SelectedLayerDestination
    {
      get { return _selectedLayerDestination; }
      set
      {
        SetProperty(ref _selectedLayerDestination, value, () => SelectedLayerDestination);
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
            int hasElementField = await QueuedTask.Run<int>(() =>
            {
             return flyr.GetTable().GetDefinition().FindField("Element");
            });

            if (hasElementField >= 0)
              featureLayers.Add(flyr);
          }
        }
      }
      _layersOrigin = featureLayers;
      NotifyPropertyChanged(() => LayersOrigin);
      _layersDestination= featureLayers;
      NotifyPropertyChanged(() => LayersDestination);
    }

    public string NCOrigin
    {
      get { return _ncOrigin; }
      set
      {
        SetProperty(ref _ncOrigin, value, () => NCOrigin);
      }
    }

    public string NCDestination
    {
      get { return _ncDestination; }
      set
      {
        SetProperty(ref _ncDestination, value, () => NCDestination);
      }
    }
    

        //Create Cube button click
    public ICommand SearchCommand
    {
        get
        {
            if (_search == null)
            {
                _search = new RelayCommand(SeachDestination, () =>
                {
                  return _search != null;
                });
            }
            return _search;
        }
    }



    private async void SeachDestination(object obj)
    {
      if (MapView.Active == null)
        return;
      // Get Layer Name
      string inputOrigin = SelectedLayerOrigin.Name;
      string ncOrigin = NCOrigin;
      string inputDestination = SelectedLayerDestination.Name;
      string ncDestination = NCDestination;


      /// Set PYT path -This could be inserted as a resource file //
      string tool_path = "E:\\Dev_summit\\2019\\Origin_Destination_Space_Time_Cube\\pyt\\OriginDestination.pyt\\SelectDestination";

      IReadOnlyList<string> args= null;

      /// Arguments for executing process using Tolerance
      args = Geoprocessing.MakeValueArray(inputOrigin, ncOrigin, inputDestination,ncDestination);

      //Task<IGPResult> task;
      /// Execute the Tool in the python toolbox
      await Geoprocessing.ExecuteToolAsync(tool_path, args, flags: GPExecuteToolFlags.AddToHistory);

      IReadOnlyList<string> args2 = null;
      args2 = Geoprocessing.MakeValueArray(inputOrigin, "Shape.Z", "E:\\projects\\STCE24\\STCE24.gdb\\mzone","CONVEX_HULL", "ALL", "", "NO_MBV_FIELDS" );

      string tool_path_ddd = "ddd.MinimumBoundingVolume";
      // cancellation token variable is declared as a class member
      System.Threading.CancellationTokenSource _cts = new System.Threading.CancellationTokenSource();

      await Geoprocessing.ExecuteToolAsync(tool_path_ddd, args2, flags: GPExecuteToolFlags.AddOutputsToMap);
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
