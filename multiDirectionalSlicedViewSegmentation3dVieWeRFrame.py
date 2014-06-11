# multiDirectionalSlicedViewSegmentation3dVieWeRFrame by Ralf Nieuwenhuizen & Jan-Willem van Velzen
# Description //TODO
#
# Based on SkeletonAUIViewerFrame:
# Copyright (c) Charl P. Botha, TU Delft.
# Inspired by EmphysemaViewerFrame by Corine Slagboom & Noeska Smit
#
# All rights reserved.
# See COPYRIGHT for details.

import cStringIO
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import wx
import vtk

# one could have loaded a wxGlade created resource like this:
#from resources.python import DICOMBrowserPanels
#reload(DICOMBrowserPanels)
class multiDirectionalSlicedViewSegmentation3dVieWeRFrame(wx.Frame):
    """wx.Frame child class used by multiDirectionalSlicedViewSegmentation3dVieWeR for its
    interface.
    """

    def __init__(self, parent, id=-1, title="", name=""):
        """Populates the menu and adds all required panels
        """
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(1000,875), name=name)

        self.SetBackgroundColour("#888888")

        views_control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        views_sizer_left = wx.BoxSizer(wx.VERTICAL)
        views_sizer_right = wx.BoxSizer(wx.VERTICAL)

        views_sizer_left.Add(self._create_top_pane(), 1, wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND, 7)
        views_sizer_left.Add(self._create_front_pane(), 1, wx.LEFT|wx.BOTTOM|wx.EXPAND, 7)
        views_sizer_right.Add(self._create_side_pane(), 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 7)
        views_sizer_right.Add(self._create_3D_pane(), 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 7)

        views_control_sizer.Add(views_sizer_left, 1, wx.EXPAND)
        views_control_sizer.Add(views_sizer_right, 1, wx.EXPAND)

        views_control_sizer.Add(self._create_controls_pane(), 0, wx.EXPAND)

        self.SetSizer(views_control_sizer)
        self.Layout()
                
        # self.CreateStatusBar()
        # self.SetStatusText("multiDirectionalSlicedViewSegmentation3dVieWeR loaded")




    def close(self):
        """Selfdestruct :)
        """
        self.Destroy()

    def _create_controls_pane(self):
        """Create a pane for the controls (containing file, selection and displaying tools)
        """
        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('#AAAAAA') 
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(wx.Size(200,600))
        font_title = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        #FILE
        file_box = wx.BoxSizer(wx.VERTICAL)
        
        file_label = wx.StaticText(panel, -1, "VTI File" , wx.Point(0, 0))
        file_label.SetFont(font_title)
        self.filename_label = wx.Button(panel, -1, 'NO INPUT' , wx.Point(0, 0), wx.Size(150, 20))
        file_box.Add(file_label)
        file_box.Add(self.filename_label)

        #SELECTION
        selection_box = wx.BoxSizer(wx.VERTICAL)
        
        selection_label = wx.StaticText(panel, -1, "Selection:" , wx.Point(0, 0))
        selection_label.SetFont(font_title)
        selection_box.Add(selection_label)

        color_box = wx.BoxSizer(wx.HORIZONTAL)
        self.color_label = wx.StaticText(panel, -1, "Color" , wx.Point(0, 0))
        color_box.Add((5,0), 0)
        color_box.Add(self.color_label, 1, wx.ALIGN_CENTER_VERTICAL)
        color_box.Add((125,0), 0)
        self.color_picker = wx.ColourPickerCtrl(panel, -1)
        color_box.Add(self.color_picker, 1, wx.ALIGN_RIGHT)

        selection_box.Add(color_box)

        #tolerance
        tolerance_label = wx.StaticText(panel, -1, "Tolerance" , wx.Point(0, 0))
        tolerance_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        selection_box.Add(tolerance_label)

        lower_box = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_slider = wx.Slider(panel, -1, 0, -100, 0, (0, 0), (200, 50),wx.SL_HORIZONTAL)
        self.lower_value_label = wx.StaticText(panel, -1, str(self.lower_slider.GetValue()))
        self.lower_value_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        lower_label = wx.StaticText(panel, -1, "Lower" , wx.Point(0, 0))
        lower_box.Add((5,0), 0)
        lower_box.Add(lower_label)
        lower_box.Add((130,0), 0)
        lower_box.Add(self.lower_value_label, 0, wx.ALIGN_RIGHT)
        self.lower_slider.Bind(wx.EVT_SLIDER, self._update_lower_label)

        upper_box = wx.BoxSizer(wx.HORIZONTAL)
        self.upper_slider = wx.Slider(panel, -1, 0, 0, 100  , (0, 0), (200, 50),wx.SL_HORIZONTAL)
        self.upper_value_label = wx.StaticText(panel, -1, str(self.upper_slider.GetValue()))
        self.upper_value_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        upper_label = wx.StaticText(panel, -1, "Upper" , wx.Point(0, 0))        
        upper_box.Add((5,0), 0)
        upper_box.Add(upper_label)
        upper_box.Add((130,0), 0)
        upper_box.Add(self.upper_value_label, 0, wx.ALIGN_RIGHT)
        self.upper_slider.Bind(wx.EVT_SLIDER, self._update_upper_label)

        selection_box.Add(lower_box)
        selection_box.Add(self.lower_slider)
        selection_box.Add(upper_box)
        selection_box.Add(self.upper_slider)


        continuous_box = wx.BoxSizer(wx.HORIZONTAL)
        continuous_label = wx.StaticText(panel, -1, "Continuous" , wx.Point(0, 0))
        self.continuous_check = wx.CheckBox(panel, -1, "" , wx.Point(0, 0))
        continuous_box.Add((5,0), 0)
        continuous_box.Add(continuous_label, 1)
        continuous_box.Add((105,0), 0)
        continuous_box.Add(self.continuous_check, 0, wx.ALIGN_RIGHT)
        selection_box.Add(continuous_box)

        #UNSELECTED
        unselected_box = wx.BoxSizer(wx.VERTICAL)
        
        unselected_label = wx.StaticText(panel, -1, "Unselected:" , wx.Point(0, 0))
        unselected_label.SetFont(font_title)
        unselected_box.Add(unselected_label)

        transparency_box = wx.BoxSizer(wx.HORIZONTAL)
        self.transparency_slider = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (200, 50),wx.SL_HORIZONTAL)
        transparency_label = wx.StaticText(panel, -1, "Opacity" , wx.Point(0, 0))
        self.transparency_value_label = wx.StaticText(panel, -1, str(self.transparency_slider.GetValue()) + '%')
        self.transparency_value_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.transparency_slider.Bind(wx.EVT_SLIDER, self._update_transparency_label)

        transparency_box.Add((5,0), 0)
        transparency_box.Add(transparency_label)
        transparency_box.Add((75,0), 0)
        transparency_box.Add(self.transparency_value_label)

        unselected_box.Add(transparency_box)
        unselected_box.Add(self.transparency_slider)

        tbd_box = wx.BoxSizer(wx.HORIZONTAL)
        transparencybydistance_label = wx.StaticText(panel, -1, "Transparency by distance" , wx.Point(0, 0))
        self.transparencybydistance_check = wx.CheckBox(panel, -1, "" , wx.Point(0, 0))
        tbd_box.Add((5,0), 0)
        tbd_box.Add(transparencybydistance_label)
        tbd_box.Add((20,0), 0)
        tbd_box.Add(self.transparencybydistance_check)

        unselected_box.Add(tbd_box)

        #RESET        
        reset_box = wx.BoxSizer(wx.VERTICAL)
        self.reset_controls_button = wx.Button(panel, -1, "Reset Settings" , wx.Point(0, 0))
        reset_box.Add(self.reset_controls_button, 1, wx.EXPAND)
        self.reset_controls_button.Bind(wx.EVT_BUTTON, self._reset_controls)

        #Sizing
        sizer.Add(file_box, 1, wx.BOTTOM | wx.EXPAND, 7)
        sizer.Add(selection_box, 5, wx.BOTTOM|wx.EXPAND, 7)
        sizer.Add(unselected_box, 5, wx.BOTTOM|wx.EXPAND, 7)
        sizer.Add(reset_box, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        self._reset_controls()

        return panel

    def _create_top_pane(self):
        """Create a RenderWindowInteractor for the top-view data
        """
        panel = wx.Panel(self, -1)

        self.top = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.top_zoomer = wx.Slider(panel, -1, 0, 0, 0, (0, 0), (20, 400), wx.SL_VERTICAL)

        label = wx.StaticText(panel, -1, "Transverse (Top view)" , wx.Point(0, 0))
        self.reset_top = wx.Button(panel, -1, "Reset Camera")

        #Sizers
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(self.top, 1, wx.EXPAND)
        sizer_top.Add(self.top_zoomer, 0, wx.EXPAND)
        sizer.Add(sizer_top, 1, wx.EXPAND)

        sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)
        sizer_bottom.Add(label, 1, wx.ALIGN_CENTER)
        sizer_bottom.Add(self.reset_top, 1, wx.ALIGN_RIGHT)
        sizer.Add(sizer_bottom, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        return panel

    def _create_side_pane(self):
        """Create a RenderWindowInteractor for the side-view data
        """        
        panel = wx.Panel(self, -1)

        self.side = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.side_zoomer = wx.Slider(panel, -1, 0, 0, 0, (0, 0), (20, 400), wx.SL_VERTICAL)

        label = wx.StaticText(panel, -1, "Sagittal (Side view)" , wx.Point(0, 0))
        self.reset_side = wx.Button(panel, -1, "Reset Camera")

        #Sizers
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(self.side, 1, wx.EXPAND)
        sizer_top.Add(self.side_zoomer, 0, wx.EXPAND)
        sizer.Add(sizer_top, 1, wx.EXPAND)

        sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)
        sizer_bottom.Add(label, 1, wx.ALIGN_CENTER)
        sizer_bottom.Add(self.reset_side, 1, wx.ALIGN_RIGHT)
        sizer.Add(sizer_bottom, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        return panel

    def _create_front_pane(self):
        """Create a RenderWindowInteractor for the front-view data
        """
        panel = wx.Panel(self, -1)

        self.front = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.front_zoomer = wx.Slider(panel, -1, 0, 0, 0, (0, 0), (20, 400), wx.SL_VERTICAL)

        label = wx.StaticText(panel, -1, "Coronal (Front view)" , wx.Point(0, 0))
        self.reset_front = wx.Button(panel, -1, "Reset Camera")

        #Sizers
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(self.front, 1, wx.EXPAND)
        sizer_top.Add(self.front_zoomer, 0, wx.EXPAND)
        sizer.Add(sizer_top, 1, wx.EXPAND)

        sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)
        sizer_bottom.Add(label, 1, wx.ALIGN_CENTER)
        sizer_bottom.Add(self.reset_front, 1, wx.ALIGN_RIGHT)
        sizer.Add(sizer_bottom, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        return panel

    def _create_3D_pane(self):
        """Create a RenderWindowInteractor for the 3D data
        """
        panel = wx.Panel(self, -1)

        self.view3d = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.save_button = wx.Button(panel, -1, "Save Snapshot")
        self.reset_view3d = wx.Button(panel, -1, "Reset Camera")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.view3d, 1, wx.EXPAND)

        sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)
        sizer_bottom.Add(self.save_button, 1)
        sizer_bottom.Add(self.reset_view3d, 1, wx.ALIGN_RIGHT)
        sizer.Add(sizer_bottom, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        self._create_orientation_widget(self.view3d)

        return panel

    def _create_orientation_widget(self, view3d):
        """setup orientation widget stuff
        """
        view3d._orientation_widget = vtk.vtkOrientationMarkerWidget()
        
        view3d._annotated_cube_actor = aca = vtk.vtkAnnotatedCubeActor()

        aca.GetXMinusFaceProperty().SetColor(1,0,0)
        aca.GetXPlusFaceProperty().SetColor(1,0,0)
        aca.GetYMinusFaceProperty().SetColor(0,1,0)
        aca.GetYPlusFaceProperty().SetColor(0,1,0)
        aca.GetZMinusFaceProperty().SetColor(0,0,1)
        aca.GetZPlusFaceProperty().SetColor(0,0,1)
        
        view3d._axes_actor = vtk.vtkAxesActor()

        view3d._orientation_widget.SetInteractor(view3d)
        view3d._orientation_widget.SetOrientationMarker(view3d._axes_actor)
        view3d._orientation_widget.On()
       
        # make sure interaction is off; when on, interaction with
        # software raycasters is greatly slowed down!
        view3d._orientation_widget.InteractiveOff()

    def _reset_controls(self, event = None):
        self.color_picker.SetColour('#00FF00')
        self.lower_slider.SetValue(-20)
        self.upper_slider.SetValue(20)
        self.continuous_check.SetValue(1)
        self.transparency_slider.SetValue(20)
        self.transparencybydistance_check.SetValue(0)
        self._update_lower_label()
        self._update_upper_label()
        self._update_transparency_label()

    def _get_filename(self):
        if self.filename_label.GetLabel() == 'NO INPUT': 
            return None 
        else: 
            return self.filename_label.GetLabel()

    def _set_filename(self, filename = 'NO INPUT'):
        self.filename_label.SetLabel(filename)

    def _update_lower_label(self, event = None):
        self.lower_value_label.SetLabel(str(self.lower_slider.GetValue()))

    def _update_upper_label(self, event = None):
        self.upper_value_label.SetLabel(str(self.upper_slider.GetValue()))

    def _update_transparency_label(self, event = None):
        self.transparency_value_label.SetLabel(str(self.transparency_slider.GetValue()) + '%')

    def render(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.view3d.Render()
        self.front.Render()
        self.top.Render()
        self.side.Render()