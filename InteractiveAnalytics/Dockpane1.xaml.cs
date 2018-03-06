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
