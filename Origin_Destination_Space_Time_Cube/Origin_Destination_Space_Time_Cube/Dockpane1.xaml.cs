using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;


namespace Origin_Destination_Space_Time_Cube
{
  /// <summary>
  /// Interaction logic for Dockpane1View.xaml
  /// </summary>
  public partial class Dockpane1View : UserControl
  {
    public Dockpane1View()
    {
      InitializeComponent();
    }

    private void originLayer_DropDownOpened(object sender, EventArgs e)
    {
          var m = (Dockpane1ViewModel)this.DataContext;
          m.GetLayersInMap();
    }

    private void destinationLayer_DropDownOpened(object sender, EventArgs e)
    {
          var m = (Dockpane1ViewModel)this.DataContext;
          m.GetLayersInMap();
    }
  }
}
