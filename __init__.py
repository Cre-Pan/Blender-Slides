bl_info = {
    "name": "Slides Pro",
    "author": "Alessandro Pannoli",
    "version": (1, 5, 1),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar (N-Panel) > Slides Pro",
    "description": "Create and control slide-based presentations from the 3D View sidebar.",
    "warning": "",
    "doc_url": "https://github.com/AlessandroPannoli/slides-pro",
    "category": "3D View",
}

import bpy
import blf
from bpy.props import (
    IntProperty, 
    StringProperty, 
    BoolProperty, 
    CollectionProperty, 
    PointerProperty,
    EnumProperty
)

class CheckpointFrame(bpy.types.PropertyGroup):
    frame: IntProperty(name="Frame")
    name: StringProperty(name="Name", default="Checkpoint") 
    tag: StringProperty(name="Tag", default='RADIOBUT_OFF')      

class NoteLine(bpy.types.PropertyGroup): 
    text: StringProperty(name="Note", default="")


def update_smart_transition(self, context):
    slides = context.scene.slides_collection
    current_index = -1
    for i, slide in enumerate(slides):
        if slide == self:
            current_index = i
            break
            
    if current_index > 0:
        prev_slide = slides[current_index - 1]
        new_transition = self.loop_start - prev_slide.loop_end - 1
        try:
            prev_slide.transition = max(0, new_transition)
        except Exception:
            pass


def poll_camera(self, object):
    return object.type == 'CAMERA'

class SlideItem(bpy.types.PropertyGroup):
    title: StringProperty(name="Title", default="New Slide")
    loop_start: IntProperty(name="Loop Start", default=1, min=1, update=update_smart_transition)
    loop_end: IntProperty(name="Loop End", default=80, min=1)
    transition: IntProperty(name="Transition", default=20, min=0)
    notes: CollectionProperty(type=NoteLine) 
    tag: StringProperty(name="Tag", default='RADIOBUT_OFF') 
    camera_object: PointerProperty(name="Camera", type=bpy.types.Object, poll=poll_camera)
    is_collapsed: BoolProperty(name="Collapsed", default=True)
    checkpoint_frames: CollectionProperty(type=CheckpointFrame)
    
    # --- MODIFICA 4: La tendina "Frames" parte chiusa ---
    is_frames_collapsed: BoolProperty(name="Collapse Frames", default=True)
    
def calc_transition(slides, current_index):
    if current_index + 1 >= len(slides): return 0
    cur_end = slides[current_index].loop_end
    next_start = slides[current_index + 1].loop_start
    return max(0, next_start - cur_end)

def force_ui_redraw(context):
    """Forces a redraw of all 3D View UI spaces."""
    if context.screen:
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'UI':
                        region.tag_redraw()

def go_to_loop(scene, index):
    register_notes_handler()
    bpy.ops.screen.animation_cancel(restore_frame=False)
    unregister_transition_handler()
    unregister_loop_handler()
    
    scene.is_transitioning = False
    scene.slide_transition_requested = False
    scene.slide_prev_requested = False
    scene.is_paused_at_checkpoint = False
    scene.next_checkpoint_index = 0
    
    slides = scene.slides_collection
    if not slides or index >= len(slides):
        return

    for i, s in enumerate(slides):
        s.is_collapsed = (i != index)

    slide = slides[index]
    scene.frame_start = slide.loop_start
    scene.frame_end = slide.loop_end
    scene.frame_current = slide.loop_start
    scene.slide_index = index
    
    if slide.camera_object:
        scene.camera = slide.camera_object

    scene.is_looping = True
    register_loop_handler()
    bpy.ops.screen.animation_play()

def play_transition_to_slide(scene, target_index):
    bpy.ops.screen.animation_cancel(restore_frame=False)
    unregister_loop_handler()
    scene.is_looping = False
    
    scene.is_paused_at_checkpoint = False
    scene.next_checkpoint_index = 0
    
    slides = scene.slides_collection
    predecessor_index = (target_index - 1) % len(slides)
    if target_index == 0 and predecessor_index == len(slides) - 1:
        go_to_loop(scene, target_index)
        return
    predecessor_slide = slides[predecessor_index]
    target_slide = slides[target_index]
    transition_frames = predecessor_slide.transition
    if transition_frames == 0:
        transition_frames = calc_transition(slides, predecessor_index)
    if transition_frames <= 0:
        go_to_loop(scene, target_index)
        return
    transition_start = predecessor_slide.loop_end + 1
    transition_end = predecessor_slide.loop_end + transition_frames
    transition_end = min(transition_end, target_slide.loop_start - 1)
    if transition_start > transition_end:
        go_to_loop(scene, target_index)
        return
    scene.frame_start = transition_start
    scene.frame_end = transition_end
    scene.frame_current = transition_start
    scene.is_transitioning = True
    scene.transition_target_index = target_index
    register_transition_handler()
    bpy.ops.screen.animation_play()

def on_frame_change_LOOP_handler(scene, depsgraph):
    if not scene.is_looping or scene.is_paused_at_checkpoint: 
        return

    slides = scene.slides_collection
    current_index = scene.slide_index
    if current_index < 0 or current_index >= len(slides): 
        return
    
    is_at_end_of_loop = (scene.frame_current >= scene.frame_end)
    
    slide = slides[current_index]
    if 0 <= scene.next_checkpoint_index < len(slide.checkpoint_frames):
        checkpoint = slide.checkpoint_frames[scene.next_checkpoint_index]
        
        if scene.frame_current >= checkpoint.frame:
            bpy.ops.screen.animation_cancel(restore_frame=False)
            scene.is_paused_at_checkpoint = True
            scene.next_checkpoint_index += 1
            print(f"⏸ Paused at Checkpoint {scene.next_checkpoint_index} (Frame {checkpoint.frame})")
            return 

    if scene.slide_transition_requested and is_at_end_of_loop:
        scene.slide_transition_requested = False
        next_index = (current_index + 1) % len(slides)
        play_transition_to_slide(scene, next_index)
    elif scene.slide_prev_requested and is_at_end_of_loop:
        scene.slide_prev_requested = False
        prev_index = (current_index - 1) % len(slides)
        play_transition_to_slide(scene, prev_index)

def register_loop_handler():
    if on_frame_change_LOOP_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(on_frame_change_LOOP_handler)
def unregister_loop_handler():
    if on_frame_change_LOOP_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(on_frame_change_LOOP_handler)

def on_frame_change_TRANSITION_handler(scene, depsgraph):
    if not scene.is_transitioning: return
    if scene.frame_current >= scene.frame_end:
        bpy.ops.screen.animation_cancel(restore_frame=False)
        scene.is_transitioning = False
        unregister_transition_handler()
        next_index = scene.transition_target_index
        go_to_loop(scene, next_index)
def register_transition_handler():
    if on_frame_change_TRANSITION_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(on_frame_change_TRANSITION_handler)
def unregister_transition_handler():
    if on_frame_change_TRANSITION_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(on_frame_change_TRANSITION_handler)

def draw_notes_callback():
    """Draws the notes overlay. Uses bpy.context internally to be robust across calls."""
    context = bpy.context
    scene = context.scene
    region = getattr(context, 'region', None)
    space_data = getattr(context, 'space_data', None)
    
    # If we can't get region or space, bail out
    if region is None or space_data is None:
        return
    
    if not space_data.overlay.show_overlays:
        return
        
    if not scene.slide_show_notes:
        return
        
    if not scene.slides_collection: return
    current_index = scene.slide_index
    if current_index >= len(scene.slides_collection): return
    
    slide = scene.slides_collection[current_index]
    slide_title = slide.title
    title_size = scene.slide_title_fontsize
    note_size = scene.slide_note_fontsize
    
    lines_to_draw = []
    for note_line in slide.notes:
        if note_line.text:
            lines_to_draw.extend(note_line.text.splitlines())
            
    if not lines_to_draw and not slide_title: return

    font_id = 0
    margin = 15
    line_height_note = (note_size * 1.2)
    line_height_title = (title_size * 1.2)
    title_gap = (line_height_note * 0.2) if lines_to_draw and slide_title else 0

    # --- Calcolo Dimensioni ---
    total_note_height = len(lines_to_draw) * line_height_note
    total_height = total_note_height + title_gap
    max_width = 0

    blf.size(font_id, note_size)
    for line in lines_to_draw:
        max_width = max(max_width, blf.dimensions(font_id, line)[0])

    if slide_title:
        blf.size(font_id, title_size)
        title_width = blf.dimensions(font_id, f"{slide_title}:")[0]
        max_width = max(max_width, title_width)
        total_height += line_height_title
        
    # --- Calcolo Posizione (Anchor Point) ---
    pos_x = 0
    pos_y_start = 0 # --- MODIFICA 1: pos_y_start ora è sempre il TOP del blocco
    align_right = False

    if scene.slide_notes_position == 'BOTTOM_LEFT':
        pos_x = margin
        pos_y_start = margin + total_height # --- MODIFICA 1
        align_right = False
    
    elif scene.slide_notes_position == 'TOP_LEFT':
        pos_x = margin
        pos_y_start = region.height - margin
        align_right = False

    elif scene.slide_notes_position == 'BOTTOM_RIGHT':
        pos_x = region.width - margin - max_width
        pos_y_start = margin + total_height # --- MODIFICA 1
        align_right = True

    elif scene.slide_notes_position == 'TOP_RIGHT':
        pos_x = region.width - margin - max_width
        pos_y_start = region.height - margin
        align_right = True

    # --- Disegno ---
    
    def draw_line_with_shadow(fid, text, x, y, size):
        blf.size(fid, size)
        
        draw_x = x
        if align_right:
            text_w = blf.dimensions(fid, text)[0]
            draw_x = x + (max_width - text_w)
            
        blf.color(fid, 0.0, 0.0, 0.0, 0.5)
        blf.position(fid, draw_x + 1, y + 1, 0)
        blf.draw(fid, text)
        blf.color(fid, 1.0, 1.0, 1.0, 1.0)
        blf.position(fid, draw_x, y, 0)
        blf.draw(fid, text)

    # --- MODIFICA 1: Logica di disegno unificata (sempre Top-to-Bottom) ---
    current_y = pos_y_start
    
    if slide_title:
        y_title = current_y - line_height_title
        draw_line_with_shadow(font_id, f"{slide_title}", pos_x, y_title, title_size)
        current_y = y_title - title_gap
    else:
        current_y = pos_y_start # Non c'è titolo, partiamo dall'inizio
        
    blf.size(font_id, note_size)
    for i, line in enumerate(lines_to_draw):
        # Disegna la linea i+1
        y = current_y - line_height_note * (i + 1)
        draw_line_with_shadow(font_id, line, pos_x, y, note_size)
    # --- FINE MODIFICA 1 ---

_notes_draw_handler = None
        
def register_notes_handler():
    global _notes_draw_handler
    if _notes_draw_handler is None:
        if hasattr(bpy.types, "SpaceView3D"):
            try:
                _notes_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                    draw_notes_callback, 
                    (), 
                    'WINDOW', 
                    'POST_PIXEL'
                )
            except Exception as e:
                print(f"Slides Pro: Could not attach to 3D View for notes. {e}")
        else:
            print("Slides Pro: SpaceView3D type not available.")
            
def unregister_notes_handler():
    global _notes_draw_handler
    if _notes_draw_handler is not None:
        if hasattr(bpy.types, "SpaceView3D"):
            try:
                bpy.types.SpaceView3D.draw_handler_remove(_notes_draw_handler, 'WINDOW')
            except Exception:
                pass
    _notes_draw_handler = None

class PASTE_FRAME_OT_operator(bpy.types.Operator):
    bl_idname = "scene.paste_current_frame"
    bl_label = "Paste Current Frame"
    slide_index: IntProperty()
    target_prop: StringProperty()
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        setattr(slide, self.target_prop, context.scene.frame_current)
        if getattr(context, 'region', None):
            context.region.tag_redraw()
        return {'FINISHED'}

class NEXT_SLIDE_OT_operator(bpy.types.Operator):
    bl_idname = "scene.next_slide"
    bl_label = "Next Slide (Smart)"
    bl_description = "Go to next slide (with transition) or Continue from checkpoint"
    def execute(self, context):
        scene = context.scene
        if scene.is_paused_at_checkpoint:
            scene.is_paused_at_checkpoint = False
            register_notes_handler()
            bpy.ops.screen.animation_play()
            return {'FINISHED'}
        if context.scene.is_transitioning: return {'CANCELLED'}
        context.scene.slide_prev_requested = False 
        context.scene.slide_transition_requested = True
        return {'FINISHED'}

class PREV_SLIDE_OT_operator(bpy.types.Operator):
    bl_idname = "scene.prev_slide"
    bl_label = "Previous Slide (Smart)"
    bl_description = "Go to previous slide (with transition)"
    def execute(self, context):
        scene = context.scene
        if context.scene.is_transitioning: return {'CANCELLED'}
        context.scene.is_paused_at_checkpoint = False
        context.scene.slide_transition_requested = False
        context.scene.slide_prev_requested = True
        return {'FINISHED'}

class ADD_SLIDE_OT_operator(bpy.types.Operator):
    bl_idname = "scene.add_slide"
    bl_label = "Add New Slide"
    def execute(self, context):
        slides = context.scene.slides_collection
        new_slide = slides.add()
        new_index = len(slides) - 1
        new_slide.loop_start = context.scene.frame_current
        new_slide.loop_end = context.scene.frame_current + 80
        if new_index > 0:
            last_slide = slides[new_index - 1]
            last_end = last_slide.loop_end
            new_slide.loop_start = last_end + last_slide.transition + 1
            new_slide.loop_end = new_slide.loop_start + 80
        else:
            new_slide.loop_start = 1
            new_slide.loop_end = 80
        new_slide.title = f"Slide {new_index + 1}"
        new_slide.notes.add().text = "Note..." 
        
        if context.space_data and context.space_data.type == 'VIEW_3D':
            if getattr(context.space_data, 'region_3d', None) and getattr(context.space_data.region_3d, 'view_perspective', '') == 'CAMERA':
                if context.scene.camera:
                    new_slide.camera_object = context.scene.camera
        go_to_loop(context.scene, new_index)
        
        force_ui_redraw(context)
        
        return {'FINISHED'}

class REMOVE_SLIDE_OT_operator(bpy.types.Operator):
    bl_idname = "scene.remove_slide"
    bl_label = "Delete Slide"
    index_to_remove: IntProperty()
    def execute(self, context):
        scene = context.scene
        slides = scene.slides_collection
        if 0 <= self.index_to_remove < len(slides):
            slides.remove(self.index_to_remove)
            new_index = scene.slide_index
            if new_index >= self.index_to_remove:
                new_index = max(0, new_index - 1)
            if slides:
                go_to_loop(scene, new_index)
            else:
                scene.frame_start = 1; scene.frame_end = 250; scene.frame_current = 1
        
        force_ui_redraw(context) 
        return {'FINISHED'}

class GOTO_SLIDE_OT_operator(bpy.types.Operator):
    bl_idname = "scene.goto_slide"
    bl_label = "Go to Slide"
    index_to_go: IntProperty()
    def execute(self, context):
        go_to_loop(context.scene, self.index_to_go)
        return {'FINISHED'}

class HARD_SKIP_SLIDE_OT_operator(bpy.types.Operator):
    bl_idname = "scene.hard_skip_slide"
    bl_label = "Hard Skip Slide"
    bl_description = "Go to next/prev slide (NO transition)"
    direction: IntProperty(default=1)
    def execute(self, context):
        scene = context.scene
        slides = scene.slides_collection
        if not slides: return {'CANCELLED'}
        current_index = scene.slide_index
        next_index = (current_index + self.direction) % len(slides)
        go_to_loop(scene, next_index)
        return {'FINISHED'}

class START_PRESENTATION_OT_operator(bpy.types.Operator):
    bl_idname = "scene.start_slides_presentation"
    bl_label = "Start Presentation"
    bl_description = "Start the slide presentation and enable only the handlers needed for playback"
    index_to_start: IntProperty(default=-1)

    def execute(self, context):
        scene = context.scene
        slides = scene.slides_collection
        if not slides:
            self.report({'WARNING'}, "No slides available")
            return {'CANCELLED'}

        target_index = self.index_to_start
        if target_index < 0 or target_index >= len(slides):
            target_index = max(0, min(scene.slide_index, len(slides) - 1))

        register_notes_handler()
        go_to_loop(scene, target_index)
        return {'FINISHED'}


class STOP_PRESENTATION_OT_operator(bpy.types.Operator):
    bl_idname = "scene.stop_slides_presentation"
    bl_label = "Stop Presentation"
    bl_description = "Stop playback and remove slide presentation handlers"

    def execute(self, context):
        scene = context.scene
        try:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        except TypeError:
            bpy.ops.screen.animation_cancel()

        scene.is_looping = False
        scene.is_transitioning = False
        scene.slide_transition_requested = False
        scene.slide_prev_requested = False
        scene.is_paused_at_checkpoint = False
        scene.next_checkpoint_index = 0

        unregister_loop_handler()
        unregister_transition_handler()
        unregister_notes_handler()
        return {'FINISHED'}


class WINDOW_OT_new_projection(bpy.types.Operator):
    bl_idname = "wm.new_projection_window"
    bl_label = "Projection Window"
    bl_description = "Opens a new 3D window in Camera View without overlays"
    def execute(self, context):
        bpy.ops.wm.window_new()
        new_window = context.window_manager.windows[-1]
        area = None
        max_size = 0
        for a in new_window.screen.areas:
            size = a.width * a.height
            if size > max_size:
                max_size = size
                area = a
        if not area:
            area = new_window.screen.areas[0]
        area.type = 'VIEW_3D'
        try:
            # robustly find the VIEW_3D space in the area
            for space in area.spaces:
                try:
                    if getattr(space, 'type', '') == 'VIEW_3D':
                        if getattr(space, 'region_3d', None):
                            space.region_3d.view_perspective = 'CAMERA'
                        try:
                            space.overlay.show_overlays = False
                        except Exception:
                            pass
                        try:
                            space.show_gizmo = False
                        except Exception:
                            pass
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"Error configuring 3D space: {e}")
        with context.temp_override(window=new_window, area=area):
            bpy.ops.screen.screen_full_area(use_hide_panels=True)
        return {'FINISHED'}

class CLEAR_ANNOTATIONS_OT_operator(bpy.types.Operator):
    bl_idname = "scene.clear_annotations"
    bl_label = "Clear Annotations"
    bl_description = "Clears all drawings (Blender 4.x+ system)"

    @classmethod
    def poll(cls, context):
        if context.space_data and context.space_data.type == 'VIEW_3D':
            return context.space_data.annotation_data is not None
        return False

    def execute(self, context):
        gpd = context.space_data.annotation_data
        if gpd:
            for layer in gpd.layers:
                layer.frames.clear()
        return {'FINISHED'}

class ADD_CHECKPOINT_OT_operator(bpy.types.Operator):
    bl_idname = "slide.add_checkpoint"
    bl_label = "Add Checkpoint"
    bl_description = "Adds a pause point at the current frame"
    slide_index: IntProperty()
    
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        current_frame = context.scene.frame_current
        
        if not (slide.loop_start < current_frame < slide.loop_end):
            self.report({'WARNING'}, "Checkpoint must be *inside* the loop (not at start/end)")
            return {'CANCELLED'}
        for cp in slide.checkpoint_frames:
            if cp.frame == current_frame:
                return {'CANCELLED'}
        
        frames = sorted([(cp.frame, cp.name, cp.tag) for cp in slide.checkpoint_frames] + [(current_frame, "Checkpoint", 'RADIOBUT_OFF')])
        slide.checkpoint_frames.clear()
        for f, n, t in frames:
            cp = slide.checkpoint_frames.add()
            cp.frame = f; cp.name = n; cp.tag = t
            
        if getattr(context, 'region', None):
            context.region.tag_redraw()
        return {'FINISHED'}

class REMOVE_CHECKPOINT_OT_operator(bpy.types.Operator):
    bl_idname = "slide.remove_checkpoint"
    bl_label = "Remove Checkpoint"
    slide_index: IntProperty()
    cp_index: IntProperty()
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        if 0 <= self.cp_index < len(slide.checkpoint_frames):
            slide.checkpoint_frames.remove(self.cp_index)
            
        if getattr(context, 'region', None):
            context.region.tag_redraw()
        return {'FINISHED'}

TAG_ICONS = ['NODE_SOCKET_VECTOR', 'SOLO_ON', 'RADIOBUT_OFF']

class CYCLE_SLIDE_TAG_OT_operator(bpy.types.Operator):
    bl_idname = "slide.cycle_tag"
    bl_label = "Cycle Slide Tag"
    bl_description = "Cycle a visual tag for this slide"
    slide_index: IntProperty()
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        try:
            current_icon_index = TAG_ICONS.index(slide.tag)
            next_index = (current_icon_index + 1) % len(TAG_ICONS)
        except ValueError:
            next_index = 0
        slide.tag = TAG_ICONS[next_index]
        return {'FINISHED'}

class CYCLE_CHECKPOINT_TAG_OT_operator(bpy.types.Operator):
    bl_idname = "checkpoint.cycle_tag"
    bl_label = "Cycle Checkpoint Tag"
    bl_description = "Cycle a visual tag for this checkpoint"
    slide_index: IntProperty()
    cp_index: IntProperty()
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        if 0 <= self.cp_index < len(slide.checkpoint_frames):
            cp = slide.checkpoint_frames[self.cp_index]
            try:
                current_icon_index = TAG_ICONS.index(cp.tag)
                next_index = (current_icon_index + 1) % len(TAG_ICONS)
            except ValueError:
                next_index = 0
            cp.tag = TAG_ICONS[next_index]
        return {'FINISHED'}

class ADD_NOTE_LINE_OT_operator(bpy.types.Operator):
    bl_idname = "slide.add_note_line"
    bl_label = "Add Note Line"
    slide_index: IntProperty()
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        slide.notes.add()
        if getattr(context, 'region', None):
            context.region.tag_redraw()
        return {'FINISHED'}

class REMOVE_NOTE_LINE_OT_operator(bpy.types.Operator):
    bl_idname = "slide.remove_note_line"
    bl_label = "Remove Note Line"
    slide_index: IntProperty()
    note_index: IntProperty()
    def execute(self, context):
        slide = context.scene.slides_collection[self.slide_index]
        if 0 <= self.note_index < len(slide.notes):
            slide.notes.remove(self.note_index)
        if getattr(context, 'region', None):
            context.region.tag_redraw()
        return {'FINISHED'}

class SLIDES_PT_impostazioni(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "SCENE_PT_slides_impostazioni"
    bl_space_type = 'VIEW_3D'; 
    bl_region_type = 'UI'
    bl_category = "Slides Pro"; bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon='PREFERENCES')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box_notes = layout.box()
        
        row_notes_toggle = box_notes.row() 
        row_notes_toggle.prop(scene, "slide_show_notes", text="Show / Hide Notes", icon='HIDE_OFF', toggle=True) 
        
        row_notes_pos = box_notes.row(align=True)
        row_notes_pos.label(text="Note Position:", icon='MENU_PANEL')
        row_notes_pos.prop(scene, "slide_notes_position", text="", expand=False)
        
        row_title = box_notes.row(align=True)
        row_title.label(text="Title Size:", icon='SMALL_CAPS') 
        row_title.prop(scene, "slide_title_fontsize", text=" ") 

        row_note_size = box_notes.row(align=True)
        row_note_size.label(text="Notes Size:", icon='FILE_TEXT') 
        row_note_size.prop(scene, "slide_note_fontsize", text=" ") 

        box_info = layout.box()
        row_info_header = box_info.row()
        row_info_header.alignment = 'LEFT'
        
        row_info_header.prop(scene, "slide_info_expanded", text="More info:", icon='INFO', emboss=False)

        if scene.slide_info_expanded:
            col = box_info.column(align=True)
            col.label(text="If u don't see Title or Notes check your Overlay :")
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="From 3D Viewport press")
            row.label(icon='OVERLAY')
            row.label(text=" this icon.")
            
            col.label(text="......................................................................................................................................................................................................................................................................................")
            
            col.label(text="Shortcuts", icon='RESTRICT_SELECT_OFF')
            
            col.label(text="")
            
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(icon='BLANK1')
            row.label(icon='BLANK1')
            row.label(icon='EVENT_ALT')
            row.label(text="   +")
            row.label(icon='EVENT_LEFT_ARROW')
            row.label(text=" =  Previous Slide")
            
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(icon='BLANK1')
            row.label(icon='BLANK1')
            row.label(icon='EVENT_ALT')
            row.label(text="   +")
            row.label(icon='EVENT_RIGHT_ARROW')
            row.label(text=" =  Next Slide")
            
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(text=" ")
            row.label(icon='EVENT_SHIFT')
            row.label(text=" +")
            row.label(icon='EVENT_ALT')
            row.label(text="   +")
            row.label(icon='EVENT_LEFT_ARROW')
            row.label(text=" =  Skip Transition")
            
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.label(text=" ")
            row.label(icon='EVENT_SHIFT')
            row.label(text=" +")
            row.label(icon='EVENT_ALT')
            row.label(text="   +")
            row.label(icon='EVENT_RIGHT_ARROW')
            row.label(text=" =  Skip Transition")
            
            col.label(text="......................................................................................................................................................................................................................................................................................")
            col.label(text=" ")
            
            row_credits = col.row(align=True)
            row_credits.alignment = 'LEFT'
            row_credits.label(text="Add-on created by Alessandro Pannoli.")
            
            row_credits = col.row(align=True)
            row_credits.alignment = 'LEFT'
            row_credits.label(icon='ERROR')
            row_credits.label(text="Report bugs on GitHub Issues or public community forums.", icon='GHOST_DISABLED')


class SLIDES_PT_elenco(bpy.types.Panel):
    bl_label = "Slides"
    bl_idname = "SCENE_PT_slides_elenco"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Slides Pro"
    bl_order = 1
    
    def draw_header(self, context):
        self.layout.label(text="", icon='RESTRICT_VIEW_OFF')
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        slides = scene.slides_collection
        current_idx = scene.slide_index

        row_add = layout.row() 
        row_add.scale_y = 1.3
        row_add.operator("scene.add_slide", text="➕ Add Slide")
        layout.separator()

        if not slides:
            layout.label(text="No Slides yet :(") 

        for i, slide in enumerate(slides):
            box = layout.box()
            
            if i == current_idx: box.active = True
            
            # --- Header Row (Metodo robusto a 3 parti) ---
            row_header = box.row() 

            # Parte Sinistra (Collapse + Tag)
            row_left = row_header.row(align=True)
            row_left.alignment = 'LEFT'
            
            # --- MODIFICA QUI ---
            # 1. Aggiungi l'icona ATTIVA a row_left (PRIMA del triangolo)
            icon_active = 'RECORD_ON' if i == current_idx else 'BLANK1'
            row_left.label(text="", icon=icon_active)
            
            # 2. Aggiungi il triangolo COLLAPSE a row_left
            icon_collapse = 'TRIA_DOWN' if not slide.is_collapsed else 'TRIA_RIGHT'
            row_left.prop(slide, "is_collapsed", text="", icon=icon_collapse, emboss=False)
            
            # 3. Aggiungi il TAG a row_left
            op_tag_slide = row_left.operator("slide.cycle_tag", text="", icon=slide.tag, emboss=False) # Messo emboss=False per coerenza
            op_tag_slide.slide_index = i
            
            # Parte Centrale (Titolo - Elastico)
            # Aggiungi il titolo a row_header (la riga principale)
            # Ho rimosso l'icona da qui, visto che l'abbiamo messa a sinistra
            row_header.label(text=f"{i + 1}. {slide.title}")
            
            # Parte Destra (Bottoni)
            row_right = row_header.row(align=True)
            row_right.alignment = 'RIGHT'
            op_rem = row_right.operator("scene.remove_slide", text="", icon='TRASH')
            op_rem.index_to_remove = i
            row_right.separator(factor=0.5)
            op_goto = row_right.operator("scene.goto_slide", text="", icon='RESTRICT_SELECT_OFF')
            op_goto.index_to_go = i
            
            
            if not slide.is_collapsed:
                col = box.column(align=True)
                col.separator()
                
                # --- Titolo e Note ---
                row_title = col.row(align=True)
                row_title.label(text="", icon='SMALL_CAPS')
                row_title.prop(slide, "title", text="")
                
                row_notes_header = col.row(align=True)
                row_notes_header.label(text="", icon='FILE_TEXT')
                if slide.notes:
                    first_note = slide.notes[0]
                    row_notes_header.prop(first_note, "text", text="")
                    op_add_note = row_notes_header.operator("slide.add_note_line", text="", icon='ADD'); op_add_note.slide_index = i
                    op_rem_first_note = row_notes_header.operator("slide.remove_note_line", text="", icon='REMOVE'); op_rem_first_note.slide_index = i; op_rem_first_note.note_index = 0
                else:
                    row_notes_header.label(text="Add a note...")
                    op_add_note = row_notes_header.operator("slide.add_note_line", text="", icon='ADD'); op_add_note.slide_index = i

                col_notes = col.column(align=True)
                if len(slide.notes) > 1:
                    for note_idx in range(1, len(slide.notes)):
                        note_line = slide.notes[note_idx]
                        row_note = col_notes.row(align=True)
                        row_note.label(text="", icon='BLANK1')
                        row_note.prop(note_line, "text", text="")
                        op_rem_note = row_note.operator("slide.remove_note_line", text="", icon='REMOVE'); op_rem_note.slide_index = i; op_rem_note.note_index = note_idx
                
                col.separator()

# --- Frames & Camera (Collassabile) ---
                row_frames_header = col.row(align=True) # Usiamo align=True per compattare
                
                # 1. Disegna il triangolo (prop senza testo)
                icon_frames = 'TRIA_DOWN' if not slide.is_frames_collapsed else 'TRIA_RIGHT'
                row_frames_header.prop(slide, "is_frames_collapsed", text="", icon=icon_frames, emboss=False)
                
                # 2. Disegna l'etichetta IN/OUT/TRANS (sempre visibile)
                row_frames_header.label(text=f"In: {slide.loop_start} | Out: {slide.loop_end} | Trans: {slide.transition}")
                
                # Mostra i controlli solo se la tendina è APERTA (if NOT collapsed)
                if not slide.is_frames_collapsed:
                    row_frames = col.row()
                    row_frames.separator(factor=2.0) # Indentazione
                    
                    col_left_frames = row_frames.column()
                    row_start = col_left_frames.row(align=True); row_start.label(text="", icon='AREA_JOIN_DOWN'); row_start.prop(slide, "loop_start", text="In"); op_start = row_start.operator("scene.paste_current_frame", text="", icon='EYEDROPPER'); op_start.slide_index = i; op_start.target_prop = "loop_start"
                    row_end = col_left_frames.row(align=True); row_end.label(text="", icon='AREA_JOIN_UP'); row_end.prop(slide, "loop_end", text="Out"); op_end = row_end.operator("scene.paste_current_frame", text="", icon='EYEDROPPER'); op_end.slide_index = i; op_end.target_prop = "loop_end"
                    
                    col_right_trans = row_frames.column(align=True)
                    row_trans = col_right_trans.row(align=True); row_trans.label(text="", icon='ONIONSKIN_ON'); row_trans.prop(slide, "transition", text="Transition")
                    row_cam = col_right_trans.row(align=True); row_cam.label(text="", icon='VIEW_CAMERA'); row_cam.prop(slide, "camera_object", text="")

                col.separator()
                
                # --- Checkpoints (Sempre visibili) ---
                row_cp_header = col.row()
                row_cp_header.label(text="Checkpoints", icon='BOOKMARKS')
                op_add_cp = row_cp_header.operator("slide.add_checkpoint", text="", icon='ADD')
                op_add_cp.slide_index = i

                row_cp_list = col.row()
                col_cps = row_cp_list.column(align=True)

                if not slide.checkpoint_frames:
                    pass
                    
                for cp_idx, cp in enumerate(slide.checkpoint_frames):
                    row_cp = col_cps.row(align=True)
                    row_cp.label(text=f"{cp_idx+1}.")
                    row_cp.prop(cp, "name", text="")
                    row_cp.label(text=f"(f: {cp.frame})")                       
                    op_tag_cp = row_cp.operator("checkpoint.cycle_tag", text="", icon=cp.tag, emboss=False); op_tag_cp.slide_index = i; op_tag_cp.cp_index = cp_idx
                    op_rem_cp = row_cp.operator("slide.remove_checkpoint", text="", icon='REMOVE'); op_rem_cp.slide_index = i; op_rem_cp.cp_index = cp_idx


class SLIDES_PT_controlli(bpy.types.Panel):
    bl_label = "Control Panel"
    bl_idname = "SCENE_PT_slides_controlli"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Slides Pro"
    bl_order = 2
 
    def draw_header(self, context):
        self.layout.label(text="", icon='WORKSPACE')
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        screen = context.screen if hasattr(context, "screen") else bpy.context.screen
        
        row_nav = layout.row(align=True)
        row_nav.scale_y = 1.3 # Mantengo 1.3 per l'altezza
        
        # --- Pulsante Hard-Skip Sinistro (Più largo) ---
        col_prev_hard = row_nav.column()
        col_prev_hard.scale_x = 1.3 # <-- Aumentato (da 1.2)
        op_prev_hard = col_prev_hard.operator("scene.hard_skip_slide", text="", icon='PREV_KEYFRAME')
        op_prev_hard.direction = -1
        
        # --- Pulsante REW (Più largo) ---
        col_rew = row_nav.column()
        col_rew.scale_x = 1.6  # <-- Aumentato (da 1.5)
        col_rew.operator("scene.prev_slide", text="", icon='REW')
        
        
        # --- Pulsante Play/Pausa (Più stretto) ---
        row_play = row_nav.row(align=True)
        row_play.scale_x = 0.6  # <-- Ristretto (da 0.7)
        slides = scene.slides_collection 
        
        if scene.is_paused_at_checkpoint:
            row_play.operator("scene.next_slide", text="Continue", icon='PLAY')
        elif scene.slide_transition_requested or scene.slide_prev_requested:
            row_wait = row_play.row()
            row_wait.enabled = False
            row_wait.operator("screen.animation_play", text="Waiting...", icon='SORTTIME')
        elif scene.is_transitioning:
            row_trans = row_play.row()
            row_trans.enabled = False
            row_trans.operator("screen.animation_play", text="Transition...", icon='ONIONSKIN_ON')
        elif screen and getattr(screen, "is_animation_playing", False):
            row_play.operator("scene.stop_slides_presentation", text="STOP ◉", icon='RECORD_ON') 
        else:
            op_play = row_play.operator("scene.start_slides_presentation", text="START ▶️", icon='PLAY')
            op_play.index_to_start = scene.slide_index

        # --- Pulsante FF (Più largo) ---
        col_ff = row_nav.column()
        col_ff.scale_x = 1.6  # <-- Aumentato (da 1.5)
        col_ff.operator("scene.next_slide", text="", icon='FF')

        # --- Pulsante Hard-Skip Destro (Più largo) ---
        col_next_hard = row_nav.column()
        col_next_hard.scale_x = 1.3 # <-- Aumentato (da 1.2)
        op_next_hard = col_next_hard.operator("scene.hard_skip_slide", text="", icon='NEXT_KEYFRAME')
        op_next_hard.direction = 1

        row_status = layout.row(align=True)
        
        if slides and 0 <= scene.slide_index < len(slides):
            slide_name = slides[scene.slide_index].title
            row_status.label(text=f"🎞 {scene.slide_index + 1}/{len(slides)}: {slide_name}")
        else:
            row_status.label(text="🎞 No Slide: 0/0")
            
        row_status.operator("wm.new_projection_window", text="Open Projection Window", icon='WINDOW')

addon_keymaps = []
def register_keymaps():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    
    kmi_next = km.keymap_items.new(NEXT_SLIDE_OT_operator.bl_idname, 'RIGHT_ARROW', 'PRESS', alt=True)
    kmi_prev = km.keymap_items.new(PREV_SLIDE_OT_operator.bl_idname, 'LEFT_ARROW', 'PRESS', alt=True)
    
    kmi_hard_next = km.keymap_items.new(HARD_SKIP_SLIDE_OT_operator.bl_idname, 'RIGHT_ARROW', 'PRESS', alt=True, shift=True)
    kmi_hard_next.properties.direction = 1
    kmi_hard_prev = km.keymap_items.new(HARD_SKIP_SLIDE_OT_operator.bl_idname, 'LEFT_ARROW', 'PRESS', alt=True, shift=True)
    kmi_hard_prev.properties.direction = -1
    
    addon_keymaps.extend([(km, kmi_next), (km, kmi_prev), (km, kmi_hard_next), (km, kmi_hard_prev)])

def unregister_keymaps():
    for km, kmi in addon_keymaps: 
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()

classes = [
    CheckpointFrame,
    NoteLine,
    SlideItem,
    PASTE_FRAME_OT_operator,
    NEXT_SLIDE_OT_operator,
    PREV_SLIDE_OT_operator,
    ADD_SLIDE_OT_operator,
    REMOVE_SLIDE_OT_operator,
    GOTO_SLIDE_OT_operator,
    HARD_SKIP_SLIDE_OT_operator,
    START_PRESENTATION_OT_operator,
    STOP_PRESENTATION_OT_operator,
    WINDOW_OT_new_projection,
    CLEAR_ANNOTATIONS_OT_operator,
    ADD_CHECKPOINT_OT_operator,
    REMOVE_CHECKPOINT_OT_operator,
    CYCLE_SLIDE_TAG_OT_operator,
    CYCLE_CHECKPOINT_TAG_OT_operator,
    ADD_NOTE_LINE_OT_operator,
    REMOVE_NOTE_LINE_OT_operator,
    SLIDES_PT_controlli,
    SLIDES_PT_elenco,
    SLIDES_PT_impostazioni,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.slides_collection = CollectionProperty(type=SlideItem)
    bpy.types.Scene.slide_index = IntProperty(default=0)
    bpy.types.Scene.is_looping = BoolProperty(default=False)
    bpy.types.Scene.is_transitioning = BoolProperty(default=False)
    bpy.types.Scene.slide_transition_requested = BoolProperty(default=False)
    bpy.types.Scene.slide_prev_requested = BoolProperty(False) 
    bpy.types.Scene.transition_target_index = IntProperty()
    bpy.types.Scene.is_paused_at_checkpoint = BoolProperty(default=False)
    bpy.types.Scene.next_checkpoint_index = IntProperty(default=0)
    
    bpy.types.Scene.slide_show_notes = BoolProperty(
        name="Show Notes in Overlay", default=True)
    bpy.types.Scene.slide_title_fontsize = IntProperty(
        name="Title Size", default=24, min=10, max=60)
    bpy.types.Scene.slide_note_fontsize = IntProperty(
        name="Notes Size", default=18, min=10, max=60)
        
    bpy.types.Scene.slide_notes_position = EnumProperty(
        name="Notes Position",
        description="Set the corner for the notes overlay",
        items=[
            # --- CORREZIONE: Testo ripristinato per il menu a tendina ---
            ('BOTTOM_LEFT', "Bottom Left", "Bottom Left", 'ANCHOR_BL', 0),
            ('TOP_LEFT', "Top Left", "Top Left", 'ANCHOR_TL', 1),
            ('BOTTOM_RIGHT', "Bottom Right", "Bottom Right", 'ANCHOR_BR', 2),
            ('TOP_RIGHT', "Top Right", "Top Right", 'ANCHOR_TR', 3),
        ],
        default='BOTTOM_LEFT'
    )
    
    bpy.types.Scene.slide_info_expanded = BoolProperty(
        name="Show Info", default=False)
    
    register_keymaps()
    
    print(f"✅ Slides Pro v{bl_info['version']} ACTIVE")

def unregister():
    unregister_keymaps()
    unregister_loop_handler()
    unregister_transition_handler()
    unregister_notes_handler()
    
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception:
            pass 
    
    props_to_del = [
        "slides_collection", "slide_index", "is_looping", "is_transitioning",
        "slide_transition_requested", "slide_prev_requested", 
        "transition_target_index", "is_paused_at_checkpoint", 
        "next_checkpoint_index", "slide_show_notes", 
        "slide_title_fontsize", "slide_note_fontsize",
        "slide_notes_position",
        "slide_info_expanded"
    ]
    for prop in props_to_del:
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
            except Exception:
                pass
        
    print(f"❌ Slides Pro v{bl_info['version']} DEACTIVATED")