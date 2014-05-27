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

# wxPython 2.8.8.1 wx.aui bugs severely on GTK. See:
# http://trac.wxwidgets.org/ticket/9716
# Until this is fixed, use this PyAUI to which I've added a
# wx.aui compatibility layer.
if wx.Platform == "__WXGTK__":
    from external import PyAUI
    wx.aui = PyAUI
else:
    import wx.aui

# one could have loaded a wxGlade created resource like this:
#from resources.python import DICOMBrowserPanels
#reload(DICOMBrowserPanels)
class multiDirectionalSlicedViewSegmentation3dVieWeRFrame(wx.Frame):
    """wx.Frame child class used by multiDirectionalSlicedViewSegmentation3dVieWeR for its
    interface.

    This is an AUI-managed window, so we create the top-level frame,
    and then populate it with AUI panes.
    """

    def __init__(self, parent, id=-1, title="", name=""):
        """Populates the menu and adds all required panels
        """
        wx.Frame.__init__(self, parent, id=id, title=title, 
                pos=wx.DefaultPosition, size=(1000,875), name=name)

        # TODO remove?
        file_menu = wx.Menu()
        self.id_file_open = wx.NewId()
        self.id_mask_open = wx.NewId()
        self.id_mask_save = wx.NewId()

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
        """Create a pane for the controls (containing the threshold sliders and buttons for 
        setting default or calculated values)
        """
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(wx.Size(200,600))

        #FILE
        file_box = wx.BoxSizer(wx.VERTICAL)
        
        file_label = wx.StaticText(panel, -1, "DICOM FILE" , wx.Point(0, 0))
        file_box.Add(file_label)

        #SELECTION
        selection_box = wx.BoxSizer(wx.VERTICAL)
        
        selection_label = wx.StaticText(panel, -1, "Selection:" , wx.Point(0, 0))
        selection_box.Add(selection_label)

        color_label = wx.StaticText(panel, -1, "Color" , wx.Point(0, 0))
        selection_box.Add(color_label)

        #tolerance
        tolerance_label = wx.StaticText(panel, -1, "Tolerance" , wx.Point(0, 0))
        selection_box.Add(tolerance_label)

        self.lower_slider = wx.Slider(panel, -1, 30, 0, 100, (0, 0), (200, 50),wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        lower_label = wx.StaticText(panel, -1, "Lower" , wx.Point(0, 0))
        self.upper_slider = wx.Slider(panel, -1, 45, 0, 100  , (0, 0), (200, 50),wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
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

        self.transparency_slider = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (200, 50),wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        transparency_label = wx.StaticText(panel, -1, "Transparency" , wx.Point(0, 0))

        unselected_box.Add(transparency_label)
        unselected_box.Add(self.transparency_slider)

        #transparencybydistance_label = wx.StaticText(panel, -1, "Transparency by distance" , wx.Point(0, 0))
        transparencybydistance_check = wx.CheckBox(panel, -1, "Transparency by distance" , wx.Point(0, 0))
        #unselected_box.Add(transparencybydistance_label)
        unselected_box.Add(transparencybydistance_check)

  #      self.button5 = wx.Button(panel, -1, "-950 / -970 HU",pos=(8, 8), size=(175, 28))
  #      self.button6 = wx.Button(panel, -1, "12% / 10% Lowest HU",pos=(8, 8), size=(175, 28))
  
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
        self.top_zoomer = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (20, 400), wx.SL_VERTICAL)

        label = wx.StaticText(panel, -1, "Top" , wx.Point(0, 0))
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
        self.front_zoomer = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (20, 400), wx.SL_VERTICAL)

        label = wx.StaticText(panel, -1, "Front" , wx.Point(0, 0))
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
        self.side_zoomer = wx.Slider(panel, -1, 50, 0, 100, (0, 0), (20, 400), wx.SL_VERTICAL)

        label = wx.StaticText(panel, -1, "Side" , wx.Point(0, 0))
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



