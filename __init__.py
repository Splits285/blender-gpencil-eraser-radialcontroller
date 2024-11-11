#This identifier only is here so blender stops wailing that I don't have a "manifest file." 
# SPDX-License-Identifier: UNLICENSE
bl_info = {
    "name": "Eraser Radial Controller",
    "description": "Controls the size of the gpencil eraser like a radial control. Because blender won't give a data path for it to be targeted outside of eraser mode. Set a keymap for gp.radialeraser to use",
    "author": "Splits285",
    "version": (0, 0, 1),
    "blender": (3, 0, 0),
    "location": "Keymaps. Bind an option for gp.radialeraser",
    #"warning": "",
    "doc_url": "https://github.com/addons/object/greasepencil_tools.html",
    "tracker_url": "https://github.com/Splits285/blender-gpencil-eraser-radialcontroller",
    "category": "Grease Pencil",
    "support": "COMMUNITY",
}

import bpy
# Blf is the blender module to draw fonts in the viewport
import blf

# https://blender.stackexchange.com/questions/244572/how-to-write-text-in-the-3d-viewport-as-statistics-does
def draw_callback_px(self, context):
    font_id = 0 #default blender system font. This could be a TTF.
    blf.position(font_id, 15, 100, 0)
    blf.size(font_id, 50)
    blf.color(font_id, 1, 1, 1, 1)
    blf.draw(font_id, "Eraser size: " + str(bpy.app.driver_namespace['newAMT']) )

class Radialeraser(bpy.types.Operator):
    bl_idname = "gp.radialeraser"
    bl_label = "Grease pencil radial eraser control"
    
    #---------------------------------------------------------------
    #access with self.ER_maxRange
    ER_maxRange: bpy.props.IntProperty(
        name="Maximum range", #goes next to textbox ui element
        description="The amount of pixels you have to move your cursor on-screen to achieve your Maximum Difference. This may depend on your monitor",
        min=0,
        max=15360,
        default=400, #about 400 px as a distance on screen seems like a nice difference. Most people are 1080p so it doesnt matter
        )
    #access with self.ER_maxDifference
    ER_maxDifference: bpy.props.IntProperty(
        name="Maximum difference", #goes next to textbox ui element
        description="The highest amount of brush size change you can get in a single swipe, assuming you reached the maximum on-screen range you've set",
        min=0,
        max=500,
        default=50, #about the distance on screen should be the nice 7 change i want
        )
    #access with self.ER_uncapRange
    ER_uncapRange: bpy.props.BoolProperty(
        name="Uncap Range", #goes next to textbox ui element
        description="Allow maximum range to be continued past once it is reached, increasing your brush size change beyond your maximum difference. Basically making it possible to get more than 100% of your maximum difference numbers of increase ",
        default=True,
        )
    #---------------------------------------------------------------
        
    def invoke(self, context, event):
        
        #save current tool in driverspace to restore later.
        current_active_tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname
        bpy.app.driver_namespace['Basetool'] = current_active_tool
        #print("CURRENT ACTIVE TOOL BEFORE SWITCH = ",current_active_tool)
        
        #Change to eraser so it forces this change on the active eraser tool.
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Erase")
        
        
        #handles text##########################################
        args = (self, context)
        
        # Install the draw callback named 'draw_callback_px'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        #######################################################
        
        print("invogue by ",event.type, event.value)
        global TRIGGERKEY
        TRIGGERKEY = event.type
        
        
        bpy.app.driver_namespace['Sy'] = event.mouse_region_y
        bpy.app.driver_namespace['initialY'] = event.mouse_region_y

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        
        #set Sy to new position
        bpy.app.driver_namespace['Sy'] = event.mouse_region_y
        
        initialY = bpy.app.driver_namespace['initialY']
        Sy = bpy.app.driver_namespace['Sy']
        
        Difference = Sy - initialY
        bpy.app.driver_namespace['Diff'] = Difference
        #print("Difference (Sy - initialY):",Difference)
        
                                        #this is 400 default
                                        #this is 400 default
        changePercentage = (Difference / self.ER_maxRange )
        if not self.ER_uncapRange:
            if changePercentage > 1:
                changePercentage = 1
            if changePercentage < -1:
                changePercentage = -1
        changeAMT = round(changePercentage * self.ER_maxDifference)
        print("Percentage", changePercentage)
        print("Suggusting change of ", changeAMT)
        bpy.app.driver_namespace['changeAMT'] = changeAMT
        bpy.app.driver_namespace['newAMT'] = changeAMT + bpy.context.tool_settings.gpencil_paint.brush.size
                
        #handling the text part
        context.area.tag_redraw()
        
        
        if event.type == "MOUSEMOVE":
            self.mouse_pos = event.mouse_region_x, event.mouse_region_y
            print("MOUSEMOVE AT ",event.mouse_region_y)
            print("Diff: ",Difference)
            
        if event.value == 'RELEASE':
            print("new-Y = ", bpy.app.driver_namespace['Sy'])
            print("initial-Y : ",initialY)
            print("Difference (Sy - initialY):",Difference)
                    
            #working y is bigger
            if initialY > Sy:
                print("initial Y is smaller...                     vvvvvvvvvvvv")
            
            #working y is smaller
            if initialY < Sy:
                print("initial Y is BIGGER...            ^^^^^^^^^^^^^^^")
                
            print('FINISHED AFTER CALCULATIONS')
            print('APPLYING SIZE CHANGE')
            bpy.context.tool_settings.gpencil_paint.brush.size = bpy.app.driver_namespace['newAMT']
            print('REMOVING TEXT HANDLER')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            print('RESTORING TOOL')
            bpy.ops.wm.tool_set_by_id(name=bpy.app.driver_namespace['Basetool'])
            return {'FINISHED'}
                

        elif event.type == 'ESC':  # Capture exit event
            print("Cancelled. Removing text handler, restoring tool")
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.wm.tool_set_by_id(name=bpy.app.driver_namespace['Basetool'])
            return {'CANCELLED'}
        else:
            return {'PASS_THROUGH'}
        

def register():
    bpy.utils.register_class(Radialeraser)
    bpy.app.driver_namespace['Basetool'] = "builtin_brush.Draw"
    bpy.app.driver_namespace['newAMT'] = 0
    bpy.app.driver_namespace['changeAMT'] = 0
    bpy.app.driver_namespace['Diff'] = 0
    bpy.app.driver_namespace['initialY'] = 0
    bpy.app.driver_namespace['Sy'] = 0
    bpy.app.driver_namespace['HELD'] = 0

def unregister():
    bpy.utils.unregister_class(Radialeraser)
    del bpy.app.driver_namespace['Basetool']
    del bpy.app.driver_namespace['newAMT']
    del bpy.app.driver_namespace['changeAMT']
    del bpy.app.driver_namespace['Diff']
    del bpy.app.driver_namespace['initialY']
    del bpy.app.driver_namespace['Sy']
    del bpy.app.driver_namespace['HELD']

if __name__ == "__main__":
    unregister()

#bpy.ops.object.example_operator('INVOKE_DEFAULT')