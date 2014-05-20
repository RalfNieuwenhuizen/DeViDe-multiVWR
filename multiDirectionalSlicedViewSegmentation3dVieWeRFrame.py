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

        # TODO remove?
        views_default_id = wx.NewId()
        views_max_image_id = wx.NewId()


        # tell FrameManager to manage this frame        
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        panel_width = 350
        panel_height = 400

        self._mgr.AddPane(self._create_top_pane(), wx.aui.AuiPaneInfo().
                          Name("top").Caption("Top").
                          Left().
                          BestSize(wx.Size(panel_width,panel_height)).
                          CloseButton(False).MaximizeButton(True).Resizable(False))

        self._mgr.AddPane(self._create_front_pane(), wx.aui.AuiPaneInfo().
                          Name("front").Caption("Front").
                          Left().
                          BestSize(wx.Size(panel_width,panel_height)).
                          CloseButton(False).MaximizeButton(True).Resizable(False))

        self._mgr.AddPane(self._create_side_pane(), wx.aui.AuiPaneInfo().
                          Name("side").Caption("Side").
                          Center().
                          BestSize(wx.Size(panel_width,panel_height)).
                          CloseButton(False).MaximizeButton(True).Resizable(False))

        self._mgr.AddPane(self._create_3D_pane(), wx.aui.AuiPaneInfo().
                          Name("view3d").Caption("3D").
                          Center().
                          BestSize(wx.Size(panel_width,panel_height)).
                          CloseButton(False).MaximizeButton(True).Resizable(False))

        self._mgr.AddPane(self._create_controls_pane(), wx.aui.AuiPaneInfo().
                          Name("controls").Caption("Controls").
                          Right().
                          BestSize(wx.Size(300,800)).
                          CloseButton(False).MaximizeButton(False).Resizable(False))

        self.SetMinSize(wx.Size(400, 300))

        # first we save this default perspective with all panes
        # visible
        self._perspectives = {} 
        self._perspectives['default'] = self._mgr.SavePerspective()

        # finally tell the AUI manager to do everything that we've
        # asked
        self._mgr.Update()

        # we bind the views events here, because the functionality is
        # completely encapsulated in the frame and does not need to
        # round-trip to the DICOMBrowser main module.
        self.Bind(wx.EVT_MENU, self._handler_default_view, 
                id=views_default_id)

        self.Bind(wx.EVT_MENU, self._handler_max_image_view, 
                id=views_max_image_id)
                
        self.CreateStatusBar()
        self.SetStatusText("multiDirectionalSlicedViewSegmentation3dVieWeR loaded")




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
        """Create a RenderWindowInteractor for the original data and added emphysema overlay
        """
        panel = wx.Panel(self, -1)

        self.top = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.button3 = wx.Button(panel, -1, "Reset Camera")
        self.button4 = wx.Button(panel, -1, "Reset All")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.button3)
        button_sizer.Add(self.button4)

        sizer1 = wx.BoxSizer(wx.VERTICAL)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_front_pane(self):
        """Create a RenderWindowInteractor for the original data and added emphysema overlay
        """
        panel = wx.Panel(self, -1)

        self.front = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.button3 = wx.Button(panel, -1, "Reset Camera")
        self.button4 = wx.Button(panel, -1, "Reset All")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.button3)
        button_sizer.Add(self.button4)

        sizer1 = wx.BoxSizer(wx.VERTICAL)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_side_pane(self):
        """Create a RenderWindowInteractor for the original data and added emphysema overlay
        """
        panel = wx.Panel(self, -1)

        self.side = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.button3 = wx.Button(panel, -1, "Reset Camera")
        self.button4 = wx.Button(panel, -1, "Reset All")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.button3)
        button_sizer.Add(self.button4)

        sizer1 = wx.BoxSizer(wx.VERTICAL)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

        panel.SetSizer(tl_sizer)
        tl_sizer.Fit(panel)

        return panel

    def _create_3D_pane(self):
        """Create a RenderWindowInteractor for the original data and added emphysema overlay
        """
        panel = wx.Panel(self, -1)

        self.view3d = wxVTKRenderWindowInteractor(panel, -1, (400,400))

        self.button3 = wx.Button(panel, -1, "Reset Camera")
        self.button4 = wx.Button(panel, -1, "Reset All")
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.button3)
        button_sizer.Add(self.button4)

        sizer1 = wx.BoxSizer(wx.VERTICAL)

        tl_sizer = wx.BoxSizer(wx.VERTICAL)
        tl_sizer.Add(sizer1, 1, wx.ALL|wx.EXPAND, 7)

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
      
    def _handler_default_view(self, event):
        """Event handler for when the user selects View | Default from
        the main menu.
        """
        self._mgr.LoadPerspective(
                self._perspectives['default'])

    def _handler_max_image_view(self, event):
        """Event handler for when the user selects View | Max Image
        from the main menu.
        """
        self._mgr.LoadPerspective(
            self._perspectives['max_image'])




