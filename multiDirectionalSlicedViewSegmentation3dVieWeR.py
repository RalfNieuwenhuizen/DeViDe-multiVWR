# multiDirectionalSlicedViewSegmentation3dVieWeR by Ralf Nieuwenhuizen & Jan-Willem van Velzen
# Description //TODO
#
# Based on SkeletonAUIViewer:
# Copyright (c) Charl P. Botha, TU Delft.
# Inspired by EmphysemaViewer by Corine Slagboom & Noeska Smit
#
# All rights reserved.
# See COPYRIGHT for details.

# import the frame, i.e. the wx window containing everything
import multiDirectionalSlicedViewSegmentation3dVieWeRFrame
# and do a reload, so that the GUI is also updated at reloads of this
# module.
reload(multiDirectionalSlicedViewSegmentation3dVieWeRFrame)

from module_kits.misc_kit import misc_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
from comedi_utils import CMSliceViewer
import module_utils
import os
import sys
import traceback
import vtk
import wx

class multiDirectionalSlicedViewSegmentation3dVieWeR(IntrospectModuleMixin, ModuleBase):
    """Module to visualize lungemphysema in a CT scan. A lung mask is also needed. 

    EmphysemaViewer consists of a volume rendering and two linked slice-based views; one with the original data and one with an emphysema overlay. The volume rendering shows 3 
    contours: the lungedges and 2 different contours of emphysema; a normal one and a severe one. 

    There are two ways of setting the emphysema values. 
    - The first way is choosing the 'default' values, which are literature-based. They are set on -950 HU (emphysema) and -970 HU (severe). 
    - The other way is a computational way: The lowest 11% values, that are present in the data are marked as emphysema, the lowest 8,5% values are marked as severe emphysema.
    The theory behind this is the hypothesis that the histograms of emphysema patients differ from healthy people in a way that in emphysema patients there are relatively more  
    lower values present. In both ways you can finetune the values, or completely change them (if you want to). 

    After loading your image data and mask data, you can inspect the data and examine the severity of the emphysema of the patient. 

    Controls:
    LMB: The left mouse button can be used to rotate objects in the 3D scene, or to poll Houndsfield Units in areas of interest (click and hold to see the values)\n
    RMB: For the slice viewers, you can set the window and level values by clicking and holding the right mouse button in a slice and moving your mouse. You can see the current
    window and level values in the bottom of the viewer. Outside of the slice, this zooms the camera in and out\n
    MMB: The middle mouse button enables stepping through the slices if clicked and held in the center of the slice. When clicking on de edges of a slice, this re-orients the 
    entire slice. Outside of the slice, this pans the camera\n
    Scrollwheel: The scrollwheel can be used for zooming in and out of a scene, but also for sliceviewing if used with the CTRL- or SHIFT-key\n
    SHIFT: By holding the SHIFT-key, it is possible to use the mouse scrollwheel to scroll through the slices.\n
    CTRL: Holding the CTRL-key does the same, but enables stepping through the data in steps of 10 slices.\n
    """

    NUM_INPUTS = 1

    PARTS_TO_INPUTS = {0 : tuple(range(NUM_INPUTS))}
    # PARTS_TO_OUTPUTS = {0 : (3,4), 1 : (0,4), 2 : (1,4), 3 : (2,4)}

    def __init__(self, module_manager):
        """Standard constructor.  All DeVIDE modules have these, we do
        the required setup actions.
        """

        def _init_frame():
            # call base constructor
            ModuleBase.__init__(self, module_manager)        
            self._numDataInputs = self.NUM_INPUTS
            # use list comprehension to create list keeping track of inputs
            self._inputs = [{'Connected' : None, 'inputData' : None,
                             'vtkActor' : None, 'ipw' : None}
                           for i in range(self._numDataInputs)]

            # create the view frame
            self.frame = module_utils.instantiate_module_view_frame(
                self, self._module_manager, 
                multiDirectionalSlicedViewSegmentation3dVieWeRFrame.multiDirectionalSlicedViewSegmentation3dVieWeRFrame)
            
            #THE FRAME (reference)
            frame = self.frame

            # change the title to something more spectacular (or at least something non-default)
            frame.SetTitle('multiDirectionalSlicedViewSegmentation3dVieWeR')

            # predefine this
            self.selectedData = None

            # anything you stuff into self._config will be saved
            self._config.last_used_dir = ''

            #color definitions
            twoD_bg_color = (0.19,0.19,0.19)
            threeD_bg_color = (0.62,0.62,0.62)
            contour_color = (0.6,0.6,0.6)

            # create the necessary VTK objects

            # setup the Top Renderer (id: 1)
            self.renderer_top = vtk.vtkRenderer()
            self.renderer_top.SetBackground(twoD_bg_color)
            frame.top.GetRenderWindow().AddRenderer(self.renderer_top)
            self.slice_viewer_top = CMSliceViewer(frame.top, self.renderer_top)
            self.slice_viewer_top.set_parallel()
        
            # setup the Side Renderer (id: 2)
            self.renderer_side = vtk.vtkRenderer()
            self.renderer_side.SetBackground(twoD_bg_color)
            frame.side.GetRenderWindow().AddRenderer(self.renderer_side)
            self.slice_viewer_side = CMSliceViewer(frame.side, self.renderer_side)
            self.slice_viewer_side.set_parallel()

            # setup the Front Renderer (id: 3)
            self.renderer_front = vtk.vtkRenderer()
            self.renderer_front.SetBackground(twoD_bg_color)
            frame.front.GetRenderWindow().AddRenderer(self.renderer_front)
            self.slice_viewer_front = CMSliceViewer(frame.front, self.renderer_front)
            self.slice_viewer_front.set_parallel()

            # setup the 3D Renderer (id: 4)
            self.contour_actor = vtk.vtkActor()
            self.contour_selected_actor = vtk.vtkActor()

            self.contour_mapper = vtk.vtkPolyDataMapper()
            self.contour_mapper.ScalarVisibilityOff()
            self.contour_selected_mapper = vtk.vtkPolyDataMapper()
            self.contour_selected_mapper.ScalarVisibilityOff()

            self.contour_actor.SetMapper(self.contour_mapper)
            self.contour_actor.GetProperty().SetColor(contour_color)
            self._on_slide_transparency()

            self.contour_selected_actor.SetMapper(self.contour_selected_mapper)
            self._on_select_new_color()

            self.renderer_3d = vtk.vtkRenderer()
            self.renderer_3d.SetBackground(threeD_bg_color)
            self.renderer_3d.AddActor(self.contour_actor)
            self.renderer_3d.AddActor(self.contour_selected_actor)
            frame.view3d.GetRenderWindow().AddRenderer(self.renderer_3d)
            frame.view3d._outline_source = vtk.vtkOutlineSource()
            om = vtk.vtkPolyDataMapper()
            om.SetInput(frame.view3d._outline_source.GetOutput())
            frame.view3d._outline_actor = vtk.vtkActor()
            frame.view3d._outline_actor.SetMapper(om)
            frame.view3d._orientation_widget.On()  
            frame.view3d._cInteractorStyle = vtk.vtkInteractorStyleTrackballCamera()
            frame.view3d.SetInteractorStyle(frame.view3d._cInteractorStyle)

            # make our window appear (this is a viewer after all)
            self.view()
            # all modules should toggle this once they have shown their views. 
            self.view_initialised = True

            # apply config information to underlying logic
            self.sync_module_logic_with_config()
            # then bring it all the way up again to the view
            self.sync_module_view_with_logic()
            
        # END OF _INIT_FRAME

        _init_frame()
        self._reset_frame()
        self._bind_events()

    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """
        frame = self.frame
        
        # bind onClickedAViewer
        #frame.top.Unbind(wx.EVT_LEFT_DOWN)
        frame.top.Bind(wx.EVT_LEFT_DOWN, lambda evt: self._on_clicked_viewer(evt, 1))  
        frame.side.Bind(wx.EVT_BUTTON, lambda evt: self._on_clicked_viewer(evt, 2))  
        frame.front.Bind(wx.EVT_BUTTON, lambda evt: self._on_clicked_viewer(evt, 3))  
        frame.view3d.Bind(wx.EVT_BUTTON, lambda evt: self._on_clicked_viewer(evt, 4))  

        # bind onScrollViewer
        #frame.slice_viewer_top.Unbind(wx.EVT_MOUSEWHEEL)
        #frame.slice_viewer_side.Unbind(wx.EVT_MOUSEWHEEL)
        #frame.slice_viewer_front.Unbind(wx.EVT_MOUSEWHEEL)
        frame.view3d.Unbind(wx.EVT_MOUSEWHEEL)
        frame.view3d.Bind(wx.EVT_MOUSEWHEEL, lambda evt: self._on_scroll_viewer(evt, 4))  

        # bind onChangeSliderSlice
        frame.top_zoomer.Bind(wx.EVT_SLIDER, lambda evt: self._on_slide_slice(evt, 1))
        frame.side_zoomer.Bind(wx.EVT_SLIDER, lambda evt: self._on_slide_slice(evt, 2))
        frame.front_zoomer.Bind(wx.EVT_SLIDER, lambda evt: self._on_slide_slice(evt, 3))

        # bind onChangeSliderToleranceLow
        frame.lower_slider.Bind(wx.EVT_SCROLL_CHANGED, self._on_slide_tolerance_low)

        # bind onChangeSliderToleranceHigh
        frame.upper_slider.Bind(wx.EVT_SCROLL_CHANGED, self._on_slide_tolerance_high)

        # bind onChangeSliderTransparency
        frame.transparency_slider.Bind(wx.EVT_SCROLL_CHANGED, self._on_slide_transparency)

        # bind onChangeSelectionColor
        frame.color_picker.Bind(wx.EVT_COLOURPICKER_CHANGED, self._on_select_new_color)

        # bind onCheckContinuous
        frame.continuous_check.Bind(wx.EVT_CHECKBOX, self._on_check_continuous)

        # bind onCheckTransparencyDistance
        frame.transparencybydistance_check.Bind(wx.EVT_CHECKBOX, self._on_check_transparency_distance)

        # bind onClickresetViewer
        frame.reset_top.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(1))
        frame.reset_side.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(2))
        frame.reset_front.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(3))
        frame.reset_view3d.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(4))

        # bind onClickFileButton
        frame.filename_label.Bind(wx.EVT_BUTTON, self._on_clicked_btn_new_file)    

    def _on_clicked_viewer(self, event, viewer_id):
        # TODO
        print "clicked Viewer!"
        if viewer_id == 1: # Top Viewer
            print event
        elif viewer_id == 2: # Side Viewer
            print event
        elif viewer_id == 3: # Front Viewer
            print event
        elif  viewer_id == 4: # 3D Viewer
            print event

        if event.ControlDown():
            print "CONTROL WAS DOWN!!!"
        
        pass

    def _on_scroll_viewer(self, event, viewer_id):
        if viewer_id == 1: # Top Viewer
            return # TODO
        elif viewer_id == 2: # Side Viewer
            return # TODO
        elif viewer_id == 3: # Front Viewer
            return # TODO
        elif viewer_id == 4: # 3D Viewer
            # event.GetWheelRotation() is + or - 120 depending on
            # direction of turning.
            if event.ControlDown():
                delta = 10
            elif event.ShiftDown():
                delta = 1
            else:
                # if user is NOT doing shift / control, we pass on to the
                # default handling which will give control to the VTK
                # mousewheel handlers.
                self.frame.view3d.OnMouseWheel(event)
                return
                
            selected_sds  = self.sliceDirections.getSelectedSliceDirections()
            if len(selected_sds) == 0:
                if len(self.sliceDirections._sliceDirectionsDict) == 1:
                    # convenience: nothing selected, but there is only one SD, use that then!
                    sd = self.sliceDirections._sliceDirectionsDict.items()[0][1]
                else:
                    return
                
            else:
                sd = selected_sds[0]
                
            if event.GetWheelRotation() > 0:
                sd.delta_slice(+delta)

            else:
                sd.delta_slice(-delta)

        self.render()
        #self.ipws[0].InvokeEvent('InteractionEvent')

    def _on_slide_slice(self, event, viewer_id):
        sv = None
        slicer_max = 0
        if viewer_id == 1: # Top Viewer
            sv = self.slice_viewer_top
            slicer_max = self.top_zoomer_max
        elif viewer_id == 2: # Side Viewer
            sv = self.slice_viewer_side
            slicer_max = self.side_zoomer_max
        elif viewer_id == 3: # Front Viewer
            sv = self.slice_viewer_front
            slicer_max = self.front_zoomer_max

        if not(sv == None):
            value = slicer_max - event.GetEventObject().GetValue()
            sv.ipws[0].SetSliceIndex(value)
        self.render()

    def _on_slide_tolerance_low(self, event):
        """Handler for slider adjustment (Lower Threshold)
        """
        if self.selectedData == None:
            return
        else:
            self._calculate_selection()

    def _on_slide_tolerance_high(self, event):
        """Handler for slider adjustment (Upper Threshold)
        """        
        if self.selectedData == None:
            return
        else:  
            self._calculate_selection()   

    def _on_select_new_color(self, event = None):
        """Handler for color adjustment (Color of selection)
        """
        self.contour_selected_actor.GetProperty().SetColor(self.frame.color_picker.GetColour().Get())

    def _on_slide_transparency(self, event = None):
        """Handler for slider adjustment (Transparency of unselected Actors)
        """  
        self.contour_actor.GetProperty().SetOpacity(float(self.frame.transparency_slider.GetValue()) / 100)   

    def _on_check_continuous(self, event):
        """Handler for checkbox adjustment (Continous selection)
        """        
        if self.selectedData == None:
            return
        else:  
            self._calculate_selection()    

    def _on_check_transparency_distance(self, event):
        """Handler for checkbox adjustment (Unselected transparency by distance)
        """        
        if self.selectedData == None:
            return
        else:  
            return #TODO    

    def _on_clicked_btn_new_file(self, event):
        """Handler for file opening
        """
        filters = 'Volume files (*.vti)|*.vti;'
        dlg = wx.FileDialog(self.frame, "Please choose a VTI file", self._config.last_used_dir, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:            
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            full_file_path = "%s/%s" % (self._config.last_used_dir, filename)
            self._load_data_from_file(full_file_path)
        dlg.Destroy() 

    def _load_data_from_file(self, file_path):
        """Loads scanvolume data from file. Also sets the volume as input for the sliceviewers
        """
        #self.frame.SetStatusText("Opening file: %s..." % (file_path))        
        filename = os.path.split(file_path)[1]
        fileBaseName = os.path.splitext(filename)[0]

        self.frame._set_filename(filename)

        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(file_path)
        reader.Update()

        self.set_input(0, reader.GetOutput())

    def _reset_frame(self, event = None):
        """Handler for resetting the frame
        """
        self._reset_controls()
        self._reset_all_viewers()

    def _reset_controls(self, event = None):
        """Handler for resetting the controls
        """
        self.frame._reset_controls()
        #Update the contours
        self._reset_viewer(4)

    def _reset_all_viewers(self, event = None):
        """Handler for resetting all viewer
        """        
        self._reset_viewer(1)
        self._reset_viewer(2)
        self._reset_viewer(3)
        self._reset_viewer(4)

    def _reset_viewer(self, viewer_id, event = None):
        """Handler for resetting a specific viewer
        """
        if self._inputs[0]['inputData'] == None:
            return
        else:
            size = self._inputs[0]['inputData'].GetDimensions()
            if viewer_id == 1: # Top Viewer
                self.top_zoomer_max = size[2]-1
                self.frame.top_zoomer.SetMax(self.top_zoomer_max)
                self.frame.top_zoomer.SetValue(self.top_zoomer_max)
                self.slice_viewer_top.reset_to_default_view(2)
                for i, ipw in enumerate(self.slice_viewer_top.ipws):
                        ipw.SetSliceIndex(0)
                self.slice_viewer_top.ipws[0].SetPlaneOrientation(2)
                cam_top = self.slice_viewer_top.renderer.GetActiveCamera()
                cam_top.SetViewUp(0,1,0)            
                #cam_top.SetPosition(127, 127, 1000)
            elif viewer_id == 2: # Side Viewer
                self.side_zoomer_max = size[0]-1
                self.frame.side_zoomer.SetMax(self.side_zoomer_max)
                self.frame.side_zoomer.SetValue(self.side_zoomer_max)
                self.slice_viewer_side.reset_to_default_view(2)
                for i, ipw in enumerate(self.slice_viewer_side.ipws):
                        ipw.SetSliceIndex(0)
                self.slice_viewer_side.ipws[0].SetPlaneOrientation(0)
                cam_side = self.slice_viewer_side.renderer.GetActiveCamera()
                #cam_side.SetViewUp(-1,1,0)            
                #cam_side.SetPosition(1000, 127, 127)
            elif viewer_id == 3: # Front Viewer
                self.front_zoomer_max = size[1]-1
                self.frame.front_zoomer.SetMax(self.front_zoomer_max)
                self.frame.front_zoomer.SetValue(self.front_zoomer_max)
                self.slice_viewer_front.reset_to_default_view(2)
                for i, ipw in enumerate(self.slice_viewer_front.ipws):
                        ipw.SetSliceIndex(0)
                self.slice_viewer_front.ipws[0].SetPlaneOrientation(1)
                # cam_front = self.slice_viewer_front.renderer.GetActiveCamera()
                # cam_front.SetViewUp(0,0,-1)            
                # cam_front.SetPosition(127, 1000, 127)
            elif viewer_id == 4: # 3D Viewer
                self._update_3d_renderer(self._inputs[0]['inputData'])

            self._update_indicators()

            self.render()
            return #TODO

    def _reset_zoomers(self):
        """Handler for setting the camera zoomers to standard
        """
        return #TODO

    def _update_indicators(self):
        """Handler for updating all indicators
        """
        return #TODO

    def set_input(self, idx, input_stream):
        # this gets called right before you get executed.  take the
        # input_stream and store it so that it's available during execute_module()

        def add_primary_init(input_stream):
            """After a new primary has been added, a number of other
            actions have to be performed.
            """
            # add outline actor to renderer
            self.renderer_3d.AddActor(self.frame.view3d._outline_actor)
            self.frame.view3d._outline_actor.PickableOff()
            # end of method add_primary_init()

        def _handleNewImageDataInput():
            connecteds = [i['Connected'] for i in self._inputs]

            # if we already have a primary, make sure the new inputStream
            # is added at a higher port number than all existing
            # primaries and overlays
            if 'vtkImageDataPrimary' in connecteds:
                highestPortIndex = connecteds.index('vtkImageDataPrimary')
                for i in range(highestPortIndex, len(connecteds)):
                    if connecteds[i] == 'vtkImageDataOverlay':
                        highestPortIndex = i

                if idx <= highestPortIndex:
                    raise Exception, \
                          "Please add overlay data at higher input " \
                          "port numbers " \
                          "than existing primary data and overlays."

            # find out whether this is  primary or an overlay, record it
            if 'vtkImageDataPrimary' in connecteds:
                # there's no way there can be only overlays in the list,
                # the check above makes sure of that
                self._inputs[idx]['Connected'] = 'vtkImageDataOverlay'
            else:
                # there are no primaries or overlays, this must be
                # a primary then
                self._inputs[idx]['Connected'] = 'vtkImageDataPrimary'

            # also store binding to the data itself
            self._inputs[idx]['inputData'] = input_stream

            if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                # things to setup when primary data is added
                add_primary_init(input_stream)
                if self.frame._get_filename() == None:
                    self.frame._set_filename('FROM NETWORK')

                # reset everything, including ortho camera
                #self._resetAll()
            
            #set the input on the 2d slice viewers
            self._update_2d_renderers(input_stream)
            #update our 3d renderer
            self._update_3d_renderer(input_stream)

            self._reset_all_viewers()
            self._reset_zoomers()
            # end of function _handleImageDataInput()

        if not(input_stream == None):
            if input_stream.IsA('vtkImageData'):
                if self._inputs[idx]['Connected'] is None:
                    _handleNewImageDataInput()
                else:
                    # take necessary actions to refresh
                    prevData = self._inputs[idx]['inputData']
                    #set the input on the 2d slice viewers
                    self._update_2d_renderers(input_stream)
                    #update our 3d renderer
                    self._update_3d_renderer(input_stream)
                    # record it in our main structure
                    self._inputs[idx]['inputData'] = input_stream
                    if self.frame._get_filename() == None:
                        self.frame._set_filename('FROM NETWORK')
                    self._reset_all_viewers()
                    self._reset_zoomers()
            else:
                print "ERROR: input_stream isn't vtkImageData!"
        else:
            self.frame._set_filename()
            print "No input_stream"
    # end of set_input

    def _update_2d_renderers(self, input_stream):
        """Convenience method to pass the input stream to the 2d slice viewers
        """
        self.slice_viewer_top.set_input(input_stream)
        self.slice_viewer_side.set_input(input_stream)
        self.slice_viewer_front.set_input(input_stream)

    def _update_3d_renderer(self, input_stream):
        """Calculate the contour based on the input data
        """
        self._config.iso_value = 128
        contourFilter = vtk.vtkContourFilter()
        contourFilter.SetInput(input_stream)
        contourFilter.Update()
        self.contour_mapper.SetInput(contourFilter.GetOutput())
        self.contour_mapper.Update()
        self._calculate_selection()
        self.renderer_3d.ResetCamera()

        return contourFilter.GetOutput()

    def _calculate_selection(self, iso_value = 0):
        #TODO make dynamic
        iso_value = -110

        #TODO handle continuous (marching cubes?)

        contourFilter = vtk.vtkContourFilter()
        contourFilter.SetInput(self._inputs[0]['inputData'])
        contourFilter.GenerateValues(contourFilter.GetNumberOfContours(), iso_value - self.frame.lower_slider.GetValue(), iso_value + self.frame.upper_slider.GetValue())
        contourFilter.Update()

        self.selectedData = contourFilter.GetOutput()
        
        self.contour_selected_mapper.SetInput(self.selectedData)
        self.contour_selected_mapper.Update()

        return self.selectedData

    # def create_contour(self, contourValueModerate, contourValueSevere):
    #     """
    #     """
    #     mask = vtk.vtkImageMask()
    #     severeFraction = 0.10
    #     moderateFraction = 0.12
        
    #     # We only want to contour the lungs, so mask it
    #     mask.SetMaskInput(self.mask_data)
    #     mask.SetInput(self._inputs[0]['inputData'])
    #     mask.Update()
    #     self.selectedData = mask.GetOutput()
        
        
    #     if contourValueModerate == 0 and contourValueSevere == 0: # This means we get to calculate the percentual values ourselves!
    #         scalars = self.lungVolume.GetScalarRange()
    #         range = scalars[1]-scalars[0]

    #         contourValueSevere = scalars[0]+range*severeFraction
    #         contourValueModerate = scalars[0]+range*moderateFraction

    #         self.frame.upper_slider.SetValue(contourValueModerate)    
    #         self.frame.lower_slider.SetValue(contourValueSevere)
    #         self.create_overlay(contourValueModerate,contourValueSevere)

    #     # Create the contours
    #     self.adjust_contour(self.selectedData, contourValueSevere, self.severe_mapper)
    #     self.adjust_contour(self.selectedData, contourValueModerate, self.moderate_mapper)
    #     #self.adjust_contour(self.mask_data, 0.5, self.lung_mapper)
    #     contourData = vtk.vtkMarchingCubes()
    #     contourData.SetValue(0,1)
    #     contourData.SetInput(self.mask_data)

    #     smoother = vtk.vtkWindowedSincPolyDataFilter()
    #     smoother.SetInput(contourData.GetOutput())
    #     smoother.BoundarySmoothingOn()
    #     smoother.SetNumberOfIterations(40)
    #     smoother.Update()
    #     self.contour_mapper.SetInput(smoother.GetOutput())
    #     self.contour_mapper.Update()

    #     # Set the camera to a nice view
    #     cam = self.ren.GetActiveCamera()
    #     cam.SetPosition(0,-100,0)
    #     cam.SetFocalPoint(0,0,0)
    #     cam.SetViewUp(0,0,1)
    #     self.ren.ResetCamera()
    #     self.render()
        

    #     self._imageThreshold = vtk.vtkImageThreshold()
    #     self._contourFilter = vtk.vtkContourFilter()

    #     # now setup some defaults before our sync
    #     self._config.iso_value = 128
    #     # now setup some defaults before our sync
    #     self._config.lowerThreshold = 0
    #     self._config.upperThreshold = 2500
    #     #self._config.rtu = 1
    #     self._config.replaceIn = 1
    #     self._config.inValue = 1
    #     self._config.replaceOut = 1
    #     self._config.outValue = 0
    #     self._config.outputScalarType = self._imageThreshold.GetOutputScalarType()

    #     self.selectedData = self._imageThreshold.GetOutput()

    # def adjust_contour(self, volume, contourValue, mapper):
    #     """Adjust or create an isocontour using the Marching Cubes surface at the given 
    #     value using the given mapper
    #     """
    # 	self.frame.SetStatusText("Calculating new volumerender...")
    # 	contour = vtk.vtkMarchingCubes()
    # 	contour.SetValue(0,contourValue)
    # 	contour.SetInput(volume)
    # 	mapper.SetInput(contour.GetOutput())
    # 	mapper.Update()
    # 	self.render()
    # 	self.frame.SetStatusText("Calculated new volumerender")      

    ###################################################################################
    #   _____ _______ ____  _____    _____  ______          _____ _____ _   _  _____  #
    #  / ____|__   __/ __ \|  __ \  |  __ \|  ____|   /\   |  __ \_   _| \ | |/ ____| #
    # | (___    | | | |  | | |__) | | |__) | |__     /  \  | |  | || | |  \| | |  __  #
    #  \___ \   | | | |  | |  ___/  |  _  /|  __|   / /\ \ | |  | || | | . ` | | |_ | #
    #  ____) |  | | | |__| | |      | | \ \| |____ / ____ \| |__| || |_| |\  | |__| | #
    # |_____/   |_|  \____/|_|      |_|  \_\______/_/    \_\_____/_____|_| \_|\_____| #
    #                                                                                 #
    ###################################################################################

    def view(self):
        self.frame.Show()
        self.frame.Raise()

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self.render()

    def render(self):
        """Method that calls Render() on the embedded RenderWindow.
        Use this after having made changes to the scene.
        """
        self.frame.render()
        self.renderer_3d.Render()
        self.slice_viewer_top.render()
        self.slice_viewer_side.render()
        self.slice_viewer_front.render()

    def get_input_descriptions(self):
        # define this as a tuple of input descriptions if you want to
        # take input data e.g. return ('vtkPolyData', 'my kind of
        # data')

        # concatenate it num_inputs times (but these are shallow copies!)
        return self._numDataInputs * ('vtkImageData',)

    def get_output_descriptions(self):
        # define this as a tuple of output descriptions if you want to
        # generate output data.
        return ()

    def get_output(self, idx):
        # this can get called at any time when a consumer module wants
        # you output data.
        pass

    def execute_module(self):
        # when it's you turn to execute as part of a network
        # execution, this gets called.
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        pass

    def view_to_config(self):
        pass

    def close(self):
        """Clean-up method called on all DeVIDE modules when they are
        deleted.
        FIXME: Still get a nasty X error :(
        """        
        #THE FRAME (reference)
        frame = self.frame

        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self.renderer_top.RemoveAllViewProps()
        self.renderer_side.RemoveAllViewProps()
        self.renderer_front.RemoveAllViewProps()
        self.renderer_3d.RemoveAllViewProps()

        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self.slice_viewer_top.close()
        self.slice_viewer_side.close()
        self.slice_viewer_front.close()
        frame.top.GetRenderWindow().Finalize()
        frame.top.SetRenderWindow(None)
        frame.side.GetRenderWindow().Finalize()
        frame.side.SetRenderWindow(None)
        frame.front.GetRenderWindow().Finalize()
        frame.front.SetRenderWindow(None)
        frame.view3d.GetRenderWindow().Finalize()
        frame.view3d.SetRenderWindow(None)
        del frame.top
        del frame.side
        del frame.front
        del frame.view3d
        del self.slice_viewer_top
        del self.slice_viewer_side
        del self.slice_viewer_front
        # done with VTK de-init

        # now take care of the wx window
        frame.close()
        # then shutdown our introspection mixin
        IntrospectModuleMixin.close(self)