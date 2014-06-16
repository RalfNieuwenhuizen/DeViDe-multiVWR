# multiDirectionalSlicedViewSegmentation3dVieWeR by Ralf Nieuwenhuizen & Jan-Willem van Velzen
# Description see below
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
    """Module to visualize VTI images, easily combining axial, coronal and sagittal data in one screen,
     and giving the possibility to select seedpoints that will grow into contours on the 3D screen. 

    The multiDirectionalSlicedViewSegmentation3dVieWeR consists of three sliceviewers, and a 3D viewer. 

    There are two ways of setting the input. 
    - The first way is using a vtiRDR, to load the data via the network. 
    - The other way is just using the file browser to collect a VTI file from your file system. 

    After loading your image data , you can inspect the data and examine the patient, by highlighting one or multiple areas by your choice. 

    Controls:
    LMB: The left mouse button can be used to select a seedpoint from the different 2D views\n
    CTRL + LMB: Holding the CTRL-key does the same, but adds a seedpoint to your selection, LMB then returns your selection to a single point\n
    RMB: For the slice viewers, you can set the window and level values by clicking and holding the right mouse button in a slice and moving your mouse. You can see the current
    window and level values in the bottom of the viewer. Outside of the slice, this zooms the camera in and out\n
    MMB: The middle mouse button enables stepping through the slices if clicked and held in the center of the slice. When clicking on de edges of a slice, this re-orients the 
    entire slice. Outside of the slice, this pans the camera\n
    Scrollwheel: The scrollwheel can be used for zooming in and out of a scene\n
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
            self.selectedData = []

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
            self.contour_mapper = vtk.vtkPolyDataMapper()
            self.contour_mapper.ScalarVisibilityOff()

            self.contour_selected_actors = []

            self.contour_actor.SetMapper(self.contour_mapper)
            self.contour_actor.GetProperty().SetColor(contour_color)
            self._on_slide_transparency()

            self.renderer_3d = vtk.vtkRenderer()
            self.renderer_3d.SetBackground(threeD_bg_color)
            self.renderer_3d.AddActor(self.contour_actor)

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

            self.seedPoints = []
            
        # END OF _INIT_FRAME

        _init_frame()
        self._reset_frame()
        self._bind_events()

    def _bind_events(self):
        """Bind wx events to Python callable object event handlers.
        """
        frame = self.frame

        #CONTROL check
        frame.top.Bind(wx.EVT_LEFT_UP, self.onLeftUp)

        # bind onClickedAViewer
        self.slice_viewer_top.ipws[0].AddObserver('StartInteractionEvent', lambda e, o: self._ipwStartInteractionCallback(1))
        self.slice_viewer_top.ipws[0].AddObserver('InteractionEvent', lambda e, o: self._ipwInteractionCallback(1))
        self.slice_viewer_top.ipws[0].AddObserver('EndInteractionEvent', lambda e, o: self._ipwEndInteractionCallback(1, e))

        self.slice_viewer_side.ipws[0].AddObserver('StartInteractionEvent', lambda e, o: self._ipwStartInteractionCallback(2))
        self.slice_viewer_side.ipws[0].AddObserver('InteractionEvent', lambda e, o: self._ipwInteractionCallback(2))
        self.slice_viewer_side.ipws[0].AddObserver('EndInteractionEvent', lambda e, o: self._ipwEndInteractionCallback(2, e))

        self.slice_viewer_front.ipws[0].AddObserver('StartInteractionEvent', lambda e, o: self._ipwStartInteractionCallback(3))
        self.slice_viewer_front.ipws[0].AddObserver('InteractionEvent', lambda e, o: self._ipwInteractionCallback(3))
        self.slice_viewer_front.ipws[0].AddObserver('EndInteractionEvent', lambda e, o: self._ipwEndInteractionCallback(3, e))

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

        # bind onClickresetViewer
        frame.reset_top.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(1))
        frame.reset_side.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(2))
        frame.reset_front.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(3))
        frame.reset_view3d.Bind(wx.EVT_BUTTON, lambda x: self._reset_viewer(4))

        # bind onClickFileButton
        frame.file_button.Bind(wx.EVT_BUTTON, self._on_clicked_btn_new_file) 

        # bind onClickSaveSnapshotButton
        frame.save_button.Bind(wx.EVT_BUTTON, self._save_snapshot)    

    def _ipwStartInteractionCallback(self, viewer_id):
        # print "_ipwStartInteractionCallback " + str(viewer_id)
        self.tempCursorData = None
        self._ipwInteractionCallback(viewer_id)

    def _ipwInteractionCallback(self, viewer_id):
        cd = 4 * [0.0]
        if viewer_id == 1 and self.slice_viewer_top.ipws[0].GetCursorData(cd):
            self.tempCursorData = cd
        elif viewer_id == 2 and self.slice_viewer_side.ipws[0].GetCursorData(cd):
            self.tempCursorData = cd
        elif viewer_id == 3 and self.slice_viewer_front.ipws[0].GetCursorData(cd):
            self.tempCursorData = cd

    def onLeftUp(self, evt):
        # print "leftUP!!" + str(evt.ControlDown())
        self.controlIsCurrentlyDown = evt.ControlDown()
        evt.Skip()

    def _ipwEndInteractionCallback(self, viewer_id, event):
        print "_ipwEndInteractionCallback "
        if not (self.controlIsCurrentlyDown):
            self.seedPoints = []
        self.seedPoints.append(self.tempCursorData)

        self._calculate_selection()

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
        if len(self.seedPoints) == 0:
            return
        else:
            self._calculate_selection()

    def _on_slide_tolerance_high(self, event):
        """Handler for slider adjustment (Upper Threshold)
        """        
        if len(self.seedPoints) == 0:
            return
        else:  
            self._calculate_selection()   

    def _on_select_new_color(self, event = None):
        """Handler for color adjustment (Color of selection)
        """
        for actor in self.contour_selected_actors:
            actor.GetProperty().SetColor(self.frame.color_picker.GetColour().Get())

    def _on_slide_transparency(self, event = None):
        """Handler for slider adjustment (Transparency of unselected Actors)
        """  
        self.contour_actor.GetProperty().SetOpacity(float(self.frame.transparency_slider.GetValue()) / 100)   

    def _on_check_continuous(self, event):
        """Handler for checkbox adjustment (Continous selection)
        """        
        self.frame._reset_thresholds()
        if len(self.seedPoints) == 0:
            return
        else:  
            self._calculate_selection()    

    def _on_check_transparency_distance(self, event):
        """Handler for checkbox adjustment (Unselected transparency by distance)
        """        
        if len(self.seedPoints) == 0:
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

    def _save_snapshot(self, event):
        """Handler for filesaving
        """
        filters = 'png file (*.png)|*.png'
        dlg = wx.FileDialog(self.frame, "Choose a destination", self._config.last_used_dir, "", filters, wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            self._config.last_used_dir=dlg.GetDirectory()
            file_path = "%s/%s" % (self._config.last_used_dir, filename)
            w2i  = vtk.vtkWindowToImageFilter()
            w2i.SetInput(self.frame.view3d.GetRenderWindow()); 
            w2i.Update()
            writer = vtk.vtkPNGWriter()
            writer.SetInput(w2i.GetOutput())
            writer.SetFileName(file_path)
            writer.Update()
            result = writer.Write()
        dlg.Destroy()

    def _reset_frame(self, event = None):
        """Handler for resetting the frame
        """
        self._reset_controls()
        self._reset_all_viewers()

    def _reset_controls(self, event = None):
        """Handler for resetting the controls
        """
        self.frame._reset_controls()
        self._calculate_selection()

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
        try:
            self.slice_viewer_top.set_input(input_stream)
            self.slice_viewer_side.set_input(input_stream)
            self.slice_viewer_front.set_input(input_stream)
        except:
            print "ISSUE: adding input_streams"
            

    def _update_3d_renderer(self, input_stream):
        """Calculate the contour based on the input data
        """
        self._config.iso_value = 128
        contourFilter = vtk.vtkContourFilter()
        contourFilter.SetInput(input_stream)
        contourFilter.Update()
        data = contourFilter.GetOutput()
        self.contour_mapper.SetInput(data)
        self.contour_mapper.Update()
        self._calculate_selection()
        self.renderer_3d.ResetCamera()

        return data

    def _calculate_selection(self):
        """Calculate the selection contour based on the input data and seedpoints
        """
        for actor in self.contour_selected_actors:
            #self.renderer_top.RemoveActor(actor)
            #self.renderer_side.RemoveActor(actor)
            #self.renderer_front.RemoveActor(actor)
            self.renderer_3d.RemoveActor(actor)

        # initial cleanup
        self.selectedData = []
        self.contour_selected_actors = []

        if self.frame.continuous_check.GetValue():
            for seed_point in self.seedPoints:

                #self._config._thresh_interval = 5
                _image_threshold = vtk.vtkImageThreshold()
                # seedconnect wants unsigned char at input
                _image_threshold.SetOutputScalarTypeToUnsignedChar()
                _image_threshold.SetInValue(1)
                _image_threshold.SetOutValue(0)
                _image_threshold.SetInput(self._inputs[0]['inputData'])
                
                _seed_connect = vtk.vtkImageSeedConnectivity()
                _seed_connect.SetInputConnectValue(1)
                _seed_connect.SetOutputConnectedValue(1)
                _seed_connect.SetOutputUnconnectedValue(0)
                _seed_connect.SetInput(_image_threshold.GetOutput())

                # extract a list from the input points
                _seed_connect.RemoveAllSeeds()
                # we need to call Modified() explicitly as RemoveAllSeeds()
                # doesn't.  AddSeed() does, but sometimes the list is empty at
                # this stage and AddSeed() isn't called.
                _seed_connect.Modified()
                
                for seedPoint in self.seedPoints:
                    _seed_connect.AddSeed(seedPoint[0], seedPoint[1], seedPoint[2])

                    #Determine threshold
                    iso_value = seed_point[3]
                    lower_thresh = iso_value + self.frame.lower_slider.GetValue()
                    upper_thresh = iso_value + self.frame.upper_slider.GetValue()
                    _image_threshold.ThresholdBetween(lower_thresh, upper_thresh)

                    #Update all stuff
                    _image_threshold.GetInput().Update()
                    _image_threshold.Update()
                    _seed_connect.Update()

                    #Create the contour
                    contourFilter = vtk.vtkContourFilter()
                    contourFilter.SetInput(_seed_connect.GetOutput())
                    contourFilter.GenerateValues(contourFilter.GetNumberOfContours(), 1, 1) #because 1 is output in-value
                    contourFilter.Update()

                    # Setup Actor and Mapper
                    actor = vtk.vtkActor()
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.ScalarVisibilityOff()
                    actor.SetMapper(mapper)
                    self.renderer_3d.AddActor(actor)

                    # Set output to mapper
                    data = contourFilter.GetOutput()
                    print data
                    mapper.SetInput(data)
                    mapper.Update()

                    # Save result
                    self.selectedData.append(data)
                    self.contour_selected_actors.append(actor)
                    #End for-loop

        else:
            for seedPoint in self.seedPoints:
                iso_value = seedPoint[3]

                # Setup Actor and Mapper
                actor = vtk.vtkActor()
                mapper = vtk.vtkPolyDataMapper()
                mapper.ScalarVisibilityOff()
                actor.SetMapper(mapper)
                #self.renderer_top.AddActor(actor)
                #self.renderer_side.AddActor(actor)
                #self.renderer_front.AddActor(actor)
                self.renderer_3d.AddActor(actor)

                # Calculate Polydata
                contourFilter = vtk.vtkContourFilter()
                contourFilter.SetInput(self._inputs[0]['inputData'])
                contourFilter.GenerateValues(contourFilter.GetNumberOfContours(), iso_value + self.frame.lower_slider.GetValue(), iso_value + self.frame.upper_slider.GetValue())
                contourFilter.Update()

                # Set output to mapper
                data = contourFilter.GetOutput()
                mapper.SetInput(data)
                mapper.Update()

                # Save result
                self.selectedData.append(data)
                self.contour_selected_actors.append(actor)

        # Set colors
        self._on_select_new_color()

        return self.selectedData

    def addContourObject(self, contourObject, prop3D):
        """Activate contouring for the contourObject.  The contourObject
        is usually a tdObject and specifically a vtkPolyData.  We also
        need the prop3D that represents this polydata in the 3d scene.
        """


        #TODO include this to show selection in 2d renders
        if self._contourObjectsDict.has_key(contourObject):
            # we already have this, thanks
            return

        try:
            contourable = contourObject.IsA('vtkPolyData')
        except:
            contourable = False

        if contourable:
            # we need a cutter to calculate the contours and then a stripper
            # to string them all together
            cutter = vtk.vtkCutter()
            plane = vtk.vtkPlane()
            cutter.SetCutFunction(plane)
            trfm = vtk.vtkTransform()
            trfm.SetMatrix(prop3D.GetMatrix())
            trfmFilter = vtk.vtkTransformPolyDataFilter()
            trfmFilter.SetTransform(trfm)
            trfmFilter.SetInput(contourObject)
            cutter.SetInput(trfmFilter.GetOutput())
            stripper = vtk.vtkStripper()
            stripper.SetInput(cutter.GetOutput())
            
            #
            #tubef = vtk.vtkTubeFilter()
            #tubef.SetNumberOfSides(12)
            #tubef.SetRadius(0.5)
            #tubef.SetInput(stripper.GetOutput())

            # and create the overlay at least for the 3d renderer
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInput(stripper.GetOutput())
            mapper.ScalarVisibilityOff()
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            c = self.sliceDirections.slice3dVWR._tdObjects.getObjectColour(
                contourObject)
            actor.GetProperty().SetColor(c)
            actor.GetProperty().SetInterpolationToFlat()

            # add it to the renderer
            self.sliceDirections.slice3dVWR._threedRenderer.AddActor(actor)
            
            # add all necessary metadata to our dict
            contourDict = {'contourObject' : contourObject,
                           'contourObjectProp' : prop3D,
                           'trfmFilter' : trfmFilter,
                           'cutter' : cutter,
                           'tdActor' : actor}
                           
            self._contourObjectsDict[contourObject] = contourDict

            # now sync the bugger
            self.syncContourToObject(contourObject)

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