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
using System.Windows.Controls.Primitives;


namespace InteractiveAnalytics
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

    private void ComboBox_DropDownOpened(object sender, EventArgs e)
    {
      var m = (Dockpane1ViewModel)this.DataContext;
      m.GetLayersInMap();
    }

    public bool sliderValueChanged { get; set; }
    private void Slider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
      if (!sliderValueChanged)
      {
        sliderValueChanged = true;
      }
      else
      {
        //var m = (Dockpane1ViewModel)this.DataContext;
        //m.UpdateCluster();
        //sliderValueChanged = false;
      }

    }

    private void TextBox_TextChanged(object sender, TextChangedEventArgs e)
    {
      //var m = (Dockpane1ViewModel)this.DataContext;
      //if (m != null)
      //  m.UpdateCluster();
    }

    private void Tolerance_DragCompleted(object sender, DragCompletedEventArgs e)
    {

      var m = (Dockpane1ViewModel)this.DataContext;
      if (m != null)
        m.UpdateCluster(true);
    }


    private void Threshold_DragCompleted(object sender, DragCompletedEventArgs e)
    {

      var m = (Dockpane1ViewModel)this.DataContext;
      if (m != null)
        m.UpdateCluster(false);
    }


  }
}
