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

        #FILE
        file_box = wx.BoxSizer(wx.VERTICAL)

        self.filename = "<from network>"
        
        file_label = wx.StaticText(panel, -1, "VTI FILE" , wx.Point(0, 0))
        self.filename_label = wx.Button(panel, -1, self.filename , wx.Point(0, 0))
        file_box.Add(file_label)
        file_box.Add(self.filename_label)

        #SELECTION
        selection_box = wx.BoxSizer(wx.VERTICAL)
        
        selection_label = wx.StaticText(panel, -1, "Selection:" , wx.Point(0, 0))
        selection_box.Add(selection_label)

        color_label = wx.StaticText(panel, -1, "Color" , wx.Point(0, 0))
        selection_box.Add(color_label)

        #tolerance
        tolerance_label = wx.StaticText(panel, -1, "Tolerance" , wx.Point(0, 0))
        selection_box.Add(tolerance_label)

        self.lower_slider = wx.Slider(panel, -1, 0, -100, 0, (0, 0), (200, 50),wx.SL_HORIZONTAL | wx.SL_LABELS)
        lower_label = wx.StaticText(panel, -1, "Lower" , wx.Point(0, 0))
        self.upper_slider = wx.Slider(panel, -1, 0, 0, 100  , (0, 0), (200, 50),wx.SL_HORIZONTAL | wx.SL_LABELS)
        upper_label = wx.StaticText(panel, -1, "Upper" , wx.Point(0, 0))

        selection_box.Add(lower_label)
        selection_box.Add(self.lower_slider)
        selection_box.Add(upper_label)
        selection_box.Add(self.upper_slider)


        #continuous_label = wx.StaticText(panel, -1, "Continuous" , wx.Point(0, 0))
        continuous_check = wx.CheckBox(panel, -1, "Continuous" , wx.Point(0, 0))
        #selection_box.Add(continuous_label)
        selection_box.Add(continuous_check)

        #UNSELECTED
        unselected_box = wx.BoxSizer(wx.VERTICAL)
        
        unselected_label = wx.StaticText(panel, -1, "Unselected:" , wx.Point(0, 0))
        unselected_box.Add(unselected_label)

        self.transparency_slider = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (200, 50),wx.SL_HORIZONTAL | wx.SL_LABELS)
        transparency_label = wx.StaticText(panel, -1, "Transparency" , wx.Point(0, 0))

        unselected_box.Add(transparency_label)
        unselected_box.Add(self.transparency_slider)

        #transparencybydistance_label = wx.StaticText(panel, -1, "Transparency by distance" , wx.Point(0, 0))
        transparencybydistance_check = wx.CheckBox(panel, -1, "Transparency by distance" , wx.Point(0, 0))
        #unselected_box.Add(transparencybydistance_label)
        unselected_box.Add(transparencybydistance_check)
  
        sizer.Add(file_box, 1, wx.ALL|wx.EXPAND, 7)
        sizer.Add(selection_box, 3, wx.ALL|wx.EXPAND, 7)
        sizer.Add(unselected_box, 3, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        return panel

    def _create_top_pane(self):
        """Create a RenderWindowInteractor for the top-view data
        """
        panel = wx.Panel(self, -1)

        self.top = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.top_zoomer = wx.Slider(panel, -1, 0, 0, 100, (0, 0), (20, 400), wx.SL_VERTICAL)

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

    def _create_front_pane(self):
        """Create a RenderWindowInteractor for the front-view data
        """
        panel = wx.Panel(self, -1)

        self.front = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.front_zoomer = wx.Slider(panel, -1, 0, 0, 100, (0, 0), (20, 400), wx.SL_VERTICAL)

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

    def _create_side_pane(self):
        """Create a RenderWindowInteractor for the side-view data
        """        
        panel = wx.Panel(self, -1)

        self.side = wxVTKRenderWindowInteractor(panel, -1, (400,400))
        self.side_zoomer = wx.Slider(panel, -1, 0, 0, 100, (0, 0), (20, 400), wx.SL_VERTICAL)

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

    def _create_3D_pane(self):
        """Create a RenderWindowInteractor for the 3D data
        """
        panel = wx.Panel(self, -1)

        self.view3d = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.reset_view3d = wx.Button(panel, -1, "Reset Camera")

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(self.view3d, 1, wx.EXPAND)
        tl_sizer.Add(self.reset_view3d)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def render(self):
        """Update embedded RWI, i.e. update the image.
        """
        self.view3d.Render()
        self.front.Render()
        self.top.Render()
        self.side.Render()