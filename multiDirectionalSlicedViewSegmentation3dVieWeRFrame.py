# multiDirectionalSlicedViewSegmentation3dVieWeRFrame by Ralf Nieuwenhuizen & Jan-Willem van Velzen
# Description 
#   Class that defines the frame used by the multiDirectionalSlicedViewSegmentation3dVieWeR.
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
        """Populates the screen and adds the controls
        """
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(1000,875), name=name)

        self.SetBackgroundColour("#888888")

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        views_sizer_left = wx.BoxSizer(wx.VERTICAL) #The leftmost viewers
        views_sizer_right = wx.BoxSizer(wx.VERTICAL) #The rightmost viewers

        views_sizer_left.Add(self._create_top_pane(), 1, wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND, 7)
        views_sizer_left.Add(self._create_front_pane(), 1, wx.LEFT|wx.BOTTOM|wx.EXPAND, 7)
        views_sizer_right.Add(self._create_side_pane(), 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 7)
        views_sizer_right.Add(self._create_3D_pane(), 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 7)

        sizer.Add(views_sizer_left, 1, wx.EXPAND)
        sizer.Add(views_sizer_right, 1, wx.EXPAND)

        sizer.Add(self._create_controls_pane(), 0, wx.EXPAND)

        self.SetSizer(sizer)
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
        self.file_button = wx.Button(panel, -1, 'NO INPUT' , wx.Point(0, 0), wx.Size(150, 30))
        file_box.Add((0,10), 0)
        file_box.Add(file_label)
        file_box.Add((0,10), 0)
        file_box.Add(self.file_button)

        #SELECTION
        selection_box = wx.BoxSizer(wx.VERTICAL)
        
        selection_label = wx.StaticText(panel, -1, "Selection" , wx.Point(0, 0))
        selection_label.SetFont(font_title)
        selection_box.Add(selection_label)
        selection_box.Add((0,3), 0)

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
        continuous_label = wx.StaticText(panel, -1, "Only connected" , wx.Point(0, 0))
        self.continuous_check = wx.CheckBox(panel, -1, "" , wx.Point(0, 0))
        continuous_box.Add((5,0), 0)
        continuous_box.Add(continuous_label, 1)
        continuous_box.Add((85,0), 0)
        continuous_box.Add(self.continuous_check, 0, wx.ALIGN_RIGHT)
        selection_box.Add(continuous_box)

        #seedpoints
        seedpoint_label = wx.StaticText(panel, -1, "Seedpoints" , wx.Point(0, 0))
        seedpoint_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.seedpoint_list = wx.ListCtrl(panel, size=(195,200), style=wx.LC_REPORT)
        self.seedpoint_list.SetBackgroundColour("#888888")
        self.seedpoint_list.SetTextColour("white")
        self.seedpoint_list.InsertColumn(1, 'X', width=44, format=wx.LIST_FORMAT_RIGHT)
        self.seedpoint_list.InsertColumn(2, 'Y', width=44, format=wx.LIST_FORMAT_RIGHT)
        self.seedpoint_list.InsertColumn(3, 'Z', width=44, format=wx.LIST_FORMAT_RIGHT)
        self.seedpoint_list.InsertColumn(4, 'ISO', width=50, format=wx.LIST_FORMAT_RIGHT)
        self.seedpoint_button = wx.Button(panel, label="Delete selected seedpoints")
        
        selection_box.Add((0,5), 0)
        selection_box.Add(seedpoint_label)
        selection_box.Add(self.seedpoint_list, 1, wx.ALIGN_CENTER)
        selection_box.Add((0,5), 0)
        selection_box.Add(self.seedpoint_button, 0, wx.ALIGN_CENTER)

        #UNSELECTED
        unselected_box = wx.BoxSizer(wx.VERTICAL)
        
        unselected_label = wx.StaticText(panel, -1, "Unselected" , wx.Point(0, 0))
        unselected_label.SetFont(font_title)
        unselected_box.Add(unselected_label)
        unselected_box.Add((0,10), 0)

        transparency_box = wx.BoxSizer(wx.HORIZONTAL)
        self.transparency_slider = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (200, 50),wx.SL_HORIZONTAL)
        transparency_label = wx.StaticText(panel, -1, "Opacity" , wx.Point(0, 0))
        self.transparency_value_label = wx.StaticText(panel, -1, str(self.transparency_slider.GetValue()) + '%')
        self.transparency_value_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.transparency_slider.Bind(wx.EVT_SLIDER, self._update_transparency_label)

        transparency_box.Add((5,0), 0)
        transparency_box.Add(transparency_label)
        transparency_box.Add((110,0), 0)
        transparency_box.Add(self.transparency_value_label)

        unselected_box.Add(transparency_box)
        unselected_box.Add(self.transparency_slider)

        #RESET        
        reset_box = wx.BoxSizer(wx.VERTICAL)
        self.reset_controls_button = wx.Button(panel, -1, "Reset Settings" , wx.Point(0, 0))
        reset_box.Add(self.reset_controls_button, 1, wx.ALIGN_CENTER)
        self.reset_controls_button.Bind(wx.EVT_BUTTON, self._reset_controls)

        #Sizing
        sizer.Add(file_box, 0, wx.BOTTOM | wx.EXPAND | wx.LEFT, 5)
        sizer.Add((0,30), 0)
        sizer.Add(selection_box, 0, wx.BOTTOM|wx.EXPAND | wx.LEFT, 5)
        sizer.Add((0,40), 0)
        sizer.Add(unselected_box, 0, wx.BOTTOM|wx.EXPAND | wx.LEFT, 5)
        sizer.Add((0,30), 0)
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
        """setup orientation widget stuff, the axes in the bottom
        """
        view3d._orientation_widget = vtk.vtkOrientationMarkerWidget()
                
        view3d._axes_actor = vtk.vtkAxesActor()

        view3d._orientation_widget.SetOrientationMarker(view3d._axes_actor)
        view3d._orientation_widget.SetInteractor(view3d)

    def _reset_controls(self, event = None):
        """Method to set the standard values on the controls.
        """
        self.color_picker.SetColour('#00FF00')
        self.continuous_check.SetValue(0)
        self.transparency_slider.SetValue(20)
        self._update_transparency_label()
        self._reset_thresholds()

    def _reset_thresholds(self):
        """Method to set the standard values on the threshold sliders.
        """
        continuous = self.continuous_check.GetValue()
        if continuous:
            self.lower_slider.SetMin(-500)
            self.lower_slider.SetValue(-250)
            self.upper_slider.SetMax(500)
            self.upper_slider.SetValue(250)
        else:
            self.lower_slider.SetMin(-500)
            self.lower_slider.SetValue(-250)
            self.upper_slider.SetMax(500)
            self.upper_slider.SetValue(250)

        self._update_lower_label()
        self._update_upper_label()


    def _get_filename(self):
        """Return the filename currently displayed on the file button, or None.
        """
        if self.file_button.GetLabel() == 'NO INPUT': 
            return None 
        else: 
            return self.file_button.GetLabel()

    def _set_filename(self, filename = 'NO INPUT'):        
        """Set the filename on the file button, or reset.
        """
        self.file_button.SetLabel(filename)

    def _update_lower_label(self, event = None):
        """Method to keep the slider labels up-to-date
        """
        self.lower_value_label.SetLabel(str(self.lower_slider.GetValue()))

    def _update_upper_label(self, event = None):
        """Method to keep the slider labels up-to-date
        """
        self.upper_value_label.SetLabel(str(self.upper_slider.GetValue()))

    def _update_transparency_label(self, event = None):
        """Method to keep the slider labels up-to-date
        """
        self.transparency_value_label.SetLabel(str(self.transparency_slider.GetValue()) + '%')

    def render(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.view3d.Render()
        self.front.Render()
        self.top.Render()
        self.side.Render()