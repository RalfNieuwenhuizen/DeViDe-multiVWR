# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.
# ---------------------------------------
# Edited by Corine Slagboom & Noeska Smit to add possibility of adding overlay to the sliceviewer and some special synching.
# And by edited we mean mutilated :)

from module_kits.vtk_kit.utils import DVOrientationWidget
import operator
import vtk
import wx

class CMSliceViewer:
    """Simple class for enabling 1 or 3 ortho slices in a 3D scene.
    """

    def __init__(self, view3d, renderer):
        # nnsmit-edit
        self.overlay_active = 0;
        # end edit
        self.view3d = view3d
        self.renderer = renderer

        istyle = vtk.vtkInteractorStyleTrackballCamera()
        view3d.SetInteractorStyle(istyle)

        # we unbind the existing mousewheel handler so it doesn't
        # interfere
        view3d.Unbind(wx.EVT_MOUSEWHEEL)
        view3d.Bind(wx.EVT_MOUSEWHEEL, self._handler_mousewheel)

        self.ipws = [vtk.vtkImagePlaneWidget() for _ in range(3)]
        lut = self.ipws[0].GetLookupTable()
        for ipw in self.ipws:
            ipw.SetInteractor(view3d)
            ipw.SetLookupTable(lut)

	    # nnsmit-edit
    	self.overlay_ipws = [vtk.vtkImagePlaneWidget() for _ in range(3)]
        lut2 = self.overlay_ipws[0].GetLookupTable()
        lut2.SetNumberOfTableValues(3)
        lut2.SetTableValue(0,0,0,0,0)
        lut2.SetTableValue(1,0.5,0,1,1)
        lut2.SetTableValue(2,1,0,0,1)
        lut2.Build()
        for ipw_overlay in self.overlay_ipws:
            ipw_overlay.SetInteractor(view3d)
            ipw_overlay.SetLookupTable(lut2)
            ipw_overlay.AddObserver('InteractionEvent', wx.EVT_MOUSEWHEEL)

        # now actually connect the sync_overlay observer
        for i,ipw in enumerate(self.ipws):
            ipw.AddObserver('InteractionEvent',lambda vtk_o, vtk_e, i=i: self.observer_sync_overlay(self.ipws,i))
        # end edit

        # we only set the picker on the visible IPW, else the
        # invisible IPWs block picking!
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.ipws[0].SetPicker(self.picker)

        self.outline_source = vtk.vtkOutlineCornerFilter()
        m = vtk.vtkPolyDataMapper()
        m.SetInput(self.outline_source.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.PickableOff()
        self.outline_actor = a

        #self.dv_orientation_widget = DVOrientationWidget(view3d)

        # this can be used by clients to store the current world
        # position
        self.current_world_pos = (0,0,0)
        self.current_index_pos = (0,0,0)

	# nnsmit-edit
    def observer_sync_overlay(self,ipws,ipw_idx):
	    # get the primary IPW
        pipw = ipws[ipw_idx]
        # get the overlay IPW
        oipw = self.overlay_ipws[ipw_idx] 
        # get plane geometry from primary
        o,p1,p2 = pipw.GetOrigin(),pipw.GetPoint1(),pipw.GetPoint2()
        # and apply to the overlay
        oipw.SetOrigin(o)
        oipw.SetPoint1(p1)
        oipw.SetPoint2(p2)
        oipw.UpdatePlacement()   
    # end edit

    def close(self):
        self.set_input(None)
        #self.dv_orientation_widget.close()
        self.set_overlay_input(None)

    def activate_slice(self, idx):
        if idx in [1,2]:
            self.ipws[idx].SetEnabled(1)
            self.ipws[idx].SetPicker(self.picker)


    def deactivate_slice(self, idx):
        if idx in [1,2]:
            self.ipws[idx].SetEnabled(0)
            self.ipws[idx].SetPicker(None)

    def get_input(self):
        return self.ipws[0].GetInput()

    def get_world_pos(self, image_pos):
        """Given image coordinates, return the corresponding world
        position.
        """

        idata = self.get_input()
        if not idata:
            return None

        ispacing = idata.GetSpacing()
        iorigin = idata.GetOrigin()
        # calculate real coords
        world = map(operator.add, iorigin,
                    map(operator.mul, ispacing, image_pos[0:3]))


    def set_perspective(self):
        cam = self.renderer.GetActiveCamera()
        cam.ParallelProjectionOff()

    def set_parallel(self):
        cam = self.renderer.GetActiveCamera()
        cam.ParallelProjectionOn()
        
    # nnsmit edit    
    def set_opacity(self,opacity):
        lut = self.ipws[0].GetLookupTable()
        lut.SetAlphaRange(opacity, opacity)
        lut.Build()
        self.ipws[0].SetLookupTable(lut)
    # end edit
    
    def _handler_mousewheel(self, event):
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
            try:
                self.rwi.OnMouseWheel(event)
            except:
                someBoolean = 0
            return
            
        if event.GetWheelRotation() > 0:
            self._ipw1_delta_slice(+delta)
        else:
            self._ipw1_delta_slice(-delta)

        self.render()
        self.ipws[0].InvokeEvent('InteractionEvent')

    def _ipw1_delta_slice(self, delta):
        """Move to the delta slices fw/bw, IF the IPW is currently
        aligned with one of the axes.
        """

        ipw = self.ipws[0]
        if ipw.GetPlaneOrientation() < 3:
            ci = ipw.GetSliceIndex()
            ipw.SetSliceIndex(ci + delta)

    def render(self):
        self.view3d.GetRenderWindow().Render()
        # nnsmit edit
        # synch those overlays:
        if self.overlay_active == 1:
            for i, ipw_overlay in enumerate(self.overlay_ipws):
                self.observer_sync_overlay(self.ipws, i)
        # end edit    

    def reset_camera(self):
        self.renderer.ResetCamera()
        cam = self.renderer.GetActiveCamera()
        cam.SetViewUp(0,-1,0)

    def reset_to_default_view(self, view_index):
        """
        @param view_index 2 for XY
        """

        if view_index == 2:
            
            cam = self.renderer.GetActiveCamera()
            # then make sure it's up is the right way
            cam.SetViewUp(0,-1,0)
            # just set the X,Y of the camera equal to the X,Y of the
            # focal point.
            fp = cam.GetFocalPoint()
            cp = cam.GetPosition()
            if cp[2] < fp[2]:
                z = fp[2] + (fp[2] - cp[2])
            else:
                z = cp[2]

            cam.SetPosition(fp[0], fp[1], z)

            # first reset the camera
            self.renderer.ResetCamera() 
        # nnsmit edit
        # synch overlays as well:
        if self.overlay_active == 1:
            for i, ipw_overlay in enumerate(self.overlay_ipws):
                ipw_overlay.SetSliceIndex(0)       
        for i, ipw in enumerate(self.ipws):
                ipw.SetWindowLevel(500,-800,0)
        self.render()
        # end edit

    def set_input(self, input):
        ipw = self.ipws[0]
        ipw.DisplayTextOn()
        if input == ipw.GetInput():
            return

        if input is None:
            # remove outline actor, else this will cause errors when
            # we disable the IPWs (they call a render!)
            self.renderer.RemoveViewProp(self.outline_actor)
            self.outline_source.SetInput(None)

            #self.dv_orientation_widget.set_input(None)

            for ipw in self.ipws:
                # argh, this disable causes a render
                ipw.SetEnabled(0)
                ipw.SetInput(None)

        else:
            self.outline_source.SetInput(input)
            self.renderer.AddViewProp(self.outline_actor)

            orientations = [2, 0, 1]
            active = [1, 0, 0]
            for i, ipw in enumerate(self.ipws):
                ipw.SetInput(input)
                ipw.SetWindowLevel(500,-800,0)
                ipw.SetPlaneOrientation(orientations[i]) # axial
                ipw.SetSliceIndex(0)
                ipw.SetEnabled(active[i])

            #self.dv_orientation_widget.set_input(input)

    # nnsmit-edit
    # FIXME: Create pretty fix for this codeclone.
    def set_overlay_input(self, input):
        self.overlay_active = 1
        ipw = self.overlay_ipws[0]
        if input == ipw.GetInput():
            return
        if input is None:
            self.overlay_active = 0;
            for ipw_overlay in self.overlay_ipws:
                ipw_overlay.SetEnabled(0)
                ipw_overlay.SetInput(None)
        else:
            active = [1, 0, 0]
            orientations = [2, 0, 1]
            for i, ipw_overlay in enumerate(self.overlay_ipws):
                self.observer_sync_overlay(self.ipws, i)        
                ipw_overlay.SetInput(input)
                ipw_overlay.SetPlaneOrientation(orientations[i]) # axial
                ipw_overlay.SetEnabled(active[i]) 
        self.render()
    # end edit

