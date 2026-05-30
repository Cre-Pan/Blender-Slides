bl_info = {
    "name": "Slides PRO Layout Test",
    "author": "Alessandro Pannoli",
    "version": (1, 6, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Slides PRO",
    "description": "Single-file test build for adjusting the Slides PRO layout inside the 3D View.",
    "category": "3D View",
}

ADDON_NAME = "Slides PRO"
ADDON_VERSION = (1, 6, 0)

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
TAG_ICON_ITEMS = (
    ('SELECT_SET', "Default", "Default slide tag", 'CHECKBOX_DEHLT', 0),
    ('STRIP_COLOR_01', "Red", "Red tag", 'STRIP_COLOR_01', 1),
    ('STRIP_COLOR_02', "Orange", "Orange tag", 'STRIP_COLOR_02', 2),
    ('STRIP_COLOR_03', "Yellow", "Yellow tag", 'STRIP_COLOR_03', 3),
    ('STRIP_COLOR_04', "Green", "Green tag", 'STRIP_COLOR_04', 4),
    ('STRIP_COLOR_05', "Blue", "Blue tag", 'STRIP_COLOR_05', 5),
    ('STRIP_COLOR_06', "Purple", "Purple tag", 'STRIP_COLOR_06', 6),
    ('STRIP_COLOR_07', "Magenta", "Magenta tag", 'STRIP_COLOR_07', 7),
    ('STRIP_COLOR_08', "Brown", "Brown tag", 'STRIP_COLOR_08', 8),
    ('STRIP_COLOR_09', "Gray", "Gray tag", 'STRIP_COLOR_09', 9),
)

TAG_ICON_MAP = {item[0]: item[3] for item in TAG_ICON_ITEMS}

def tag_icon(tag):
    return TAG_ICON_MAP.get(tag, 'CHECKBOX_DEHLT')


class CheckpointFrame(bpy.types.PropertyGroup):
    frame: IntProperty(name="Frame")
    name: StringProperty(name="Name", default="Checkpoint")
    tag: EnumProperty(name="Tag", description="Visual tag", items=TAG_ICON_ITEMS, default='SELECT_SET')

class NoteLine(bpy.types.PropertyGroup):
    text: StringProperty(name="Note", default="")


def ensure_slide_has_note(slide):
    if slide is not None and len(slide.notes) == 0:
        slide.notes.add().text = ""


def update_slide_index(self, context):
    slides = self.slides_collection
    if slides and 0 <= self.slide_index < len(slides):
        slide = slides[self.slide_index]
        ensure_slide_has_note(slide)
        self.frame_current = slide.loop_start
        if slide.camera_object:
            self.camera = slide.camera_object
        force_ui_redraw(context)


def ensure_scene_slide_notes(scene):
    slides = getattr(scene, "slides_collection", None)
    if slides:
        for slide in slides:
            ensure_slide_has_note(slide)


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
    tag: EnumProperty(name="Tag", description="Visual tag", items=TAG_ICON_ITEMS, default='SELECT_SET')
    camera_object: PointerProperty(name="Camera", type=bpy.types.Object, poll=poll_camera)
    is_collapsed: BoolProperty(name="Collapsed", default=True)
    checkpoint_frames: CollectionProperty(type=CheckpointFrame)

    is_frames_collapsed: BoolProperty(name="Collapse Frames", default=True)

def calc_transition(slides, current_index):
    if current_index + 1 >= len(slides): return 0
    cur_end = slides[current_index].loop_end
    next_start = slides[current_index + 1].loop_start
    return max(0, next_start - cur_end)

def force_ui_redraw(context):
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
    ensure_slide_has_note(slide)
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

    pos_x = 0
    pos_y_start = 0
    align_right = False

    if scene.slide_notes_position == 'BOTTOM_LEFT':
        pos_x = margin
        pos_y_start = margin + total_height
        align_right = False

    elif scene.slide_notes_position == 'TOP_LEFT':
        pos_x = margin
        pos_y_start = region.height - margin
        align_right = False

    elif scene.slide_notes_position == 'BOTTOM_RIGHT':
        pos_x = region.width - margin - max_width
        pos_y_start = margin + total_height
        align_right = True

    elif scene.slide_notes_position == 'TOP_RIGHT':
        pos_x = region.width - margin - max_width
        pos_y_start = region.height - margin
        align_right = True


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

    current_y = pos_y_start

    if slide_title:
        y_title = current_y - line_height_title
        draw_line_with_shadow(font_id, f"{slide_title}", pos_x, y_title, title_size)
        current_y = y_title - title_gap
    else:
        current_y = pos_y_start

    blf.size(font_id, note_size)
    for i, line in enumerate(lines_to_draw):
        y = current_y - line_height_note * (i + 1)
        draw_line_with_shadow(font_id, line, pos_x, y, note_size)

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
                print(f"Slides PRO: Could not attach to 3D View for notes. {e}")
        else:
            print("Slides PRO: SpaceView3D type not available.")

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
        new_slide.notes.add().text = ""

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



CLEAN_OVERLAY_BOOL_PROPS = (
    "show_floor",
    "show_axis_x",
    "show_axis_y",
    "show_axis_z",
    "show_cursor",
    "show_annotation",
    "show_extras",
    "show_relationship_lines",
    "show_outline_selected",
    "show_object_origins",
    "show_object_origins_all",
    "show_face_orientation",
    "show_bones",
    "show_motion_paths",
    "show_statistics",
    "show_text",
    "show_indices",
    "show_faces",
    "show_face_center",
    "show_edge_crease",
    "show_edge_sharp",
    "show_edge_bevel_weight",
    "show_edge_seams",
    "show_vertex_normals",
    "show_split_normals",
    "show_face_normals",
    "show_extra_face_area",
    "show_extra_indices",
    "show_weight",
    "show_occlude_wire",
    "show_wireframes",
)


def set_clean_overlays(space, enable_clean_view):
    overlay = getattr(space, "overlay", None)
    if overlay is None:
        return

    try:
        overlay.show_overlays = True
    except Exception:
        pass

    for prop in CLEAN_OVERLAY_BOOL_PROPS:
        if hasattr(overlay, prop):
            try:
                setattr(overlay, prop, not enable_clean_view)
            except Exception:
                pass

class SLIDESPRO_OT_toggle_viewport_overlays(bpy.types.Operator):
    bl_idname = "scene.slides_toggle_viewport_overlays"
    bl_label = "Toggle Overlays"
    bl_description = "Show or hide all Viewport Overlays in the current 3D View"

    @classmethod
    def poll(cls, context):
        return bool(context.space_data and context.space_data.type == 'VIEW_3D')

    def execute(self, context):
        space = context.space_data
        scene = context.scene
        try:
            scene.slides_clean_overlays_on = not scene.slides_clean_overlays_on
            set_clean_overlays(space, scene.slides_clean_overlays_on)
            if scene.slide_show_notes:
                register_notes_handler()
        except Exception:
            self.report({'WARNING'}, "Viewport Overlays are not available here")
            return {'CANCELLED'}
        return {'FINISHED'}


class SLIDESPRO_OT_toggle_rendered_view(bpy.types.Operator):
    bl_idname = "scene.slides_toggle_rendered_view"
    bl_label = "Toggle Rendered View"
    bl_description = "Switch the current 3D View between Rendered and Solid shading"

    @classmethod
    def poll(cls, context):
        return bool(context.space_data and context.space_data.type == 'VIEW_3D')

    def execute(self, context):
        space = context.space_data
        try:
            space.shading.type = 'SOLID' if space.shading.type == 'RENDERED' else 'RENDERED'
        except Exception:
            self.report({'WARNING'}, "Viewport shading mode is not available here")
            return {'CANCELLED'}
        return {'FINISHED'}


class CLEAR_ANNOTATIONS_OT_operator(bpy.types.Operator):
    bl_idname = "scene.clear_annotations"
    bl_label = "Clear Annotations"
    bl_description = "Clears all annotation drawings"

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

        frames = sorted([(cp.frame, cp.name, cp.tag) for cp in slide.checkpoint_frames] + [(current_frame, "Checkpoint", 'SELECT_SET')])
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
        if len(slide.notes) <= 1:
            ensure_slide_has_note(slide)
            slide.notes[0].text = ""
        elif 0 <= self.note_index < len(slide.notes):
            slide.notes.remove(self.note_index)
        if getattr(context, 'region', None):
            context.region.tag_redraw()
        return {'FINISHED'}


class SLIDES_PT_impostazioni(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "SCENE_PT_slides_impostazioni"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Slides PRO"
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon='PREFERENCES') ### icon: PREFERENCES

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        notes_box = layout.box()
        col = notes_box.column(align=False)
        col.label(text="Notes Overlay", icon='WORDWRAP_ON') ### icon: OVERLAY
        col.separator()

        row = col.row(align=False)
        row.prop(scene, "slide_show_notes", text="Show Notes", icon='HIDE_OFF', toggle=True) ### icon: HIDE_OFF
        row.prop(scene, "slide_notes_position",  text="", icon='FILE_TEXT')

        sizes = col.column(align=False)
        row = sizes.row(align=False)
        row.label(icon='SMALL_CAPS')
        row.prop(scene, "slide_title_fontsize", text="Title Size")

        row.label(icon='SYNTAX_OFF')
        row.prop(scene, "slide_note_fontsize", text="Notes Size")
        col.separator()

        row = col.row(align=False)
        row.label(text="Prev / Next Slide              Alt + ⬅ / ➡")
        
        row = col.row(align=False)
        row.label(text="Skip Transition        ⬆ + Alt + ⬅ / ➡ ")
        col.separator()

        row = col.row(align=False)
        row.label(icon='USER', text="Created by Alessandro Pannoli")


class SLIDES_UL_slide_list(bpy.types.UIList):
    bl_idname = "SLIDES_UL_slide_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        slide = item

        row = layout.row(align=False)

        active_icon = 'RECORD_ON' if index == scene.slide_index else 'DOT'
        row.label(text="", icon=active_icon) ### icon: active_icon

        row.label(text="", icon=tag_icon(slide.tag)) ### icon: tag_icon(slide.tag)

        title = slide.title if slide.title else "Untitled Slide"
        row.label(text=f"{index + 1:02d} - {title}")


class SLIDES_PT_elenco(bpy.types.Panel):
    bl_label = "Slides"
    bl_idname = "SCENE_PT_slides_elenco"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Slides PRO"
    bl_order = 1

    def draw_header(self, context):
        self.layout.label(text="a", icon='RESTRICT_VIEW_OFF') ### icon: RESTRICT_VIEW_OFF

    def _draw_selected_slide_details(self, layout, scene, slide, index):
        card = layout.column(align=True)

        content = card.box()
        col = content.column(align=False)

        row_title = col.row(align=False)
        title_label = row_title.column(align=False)
        title_label.scale_x = 0.65
        title_label.label(text="Title:")

        title_field = row_title.column(align=False)
        title_field.scale_x = 3.6
        title_field.prop(slide, "title", text="", icon='SMALL_CAPS') ### icon: SMALL_CAPS

        tag_field = row_title.column(align=False)
        tag_field.scale_x = 1.5
        tag_field.prop(slide, "tag", text="", icon_only=False)

        if slide.notes:
            for note_idx, note_line in enumerate(slide.notes):
                row_note = col.row(align=False)

                note_label = row_note.column(align=False)
                note_label.scale_x = 0.65
                note_label.label(text="Note:" if note_idx == 0 else f"Note {note_idx + 1}:")

                note_field = row_note.column(align=False)
                note_field.scale_x = 4.1
                note_field.prop(note_line, "text", text="", icon='SYNTAX_OFF') ### icon: SYNTAX_OFF

                buttons = row_note.row(align=True)
                buttons.scale_x = 5

                if note_idx == 0:
                    op_add_note = buttons.operator("slide.add_note_line", text="", icon='ADD') ### icon: ADD
                    op_add_note.slide_index = index

                if note_idx > 0:
                    op_rem_note = buttons.operator("slide.remove_note_line", text="", icon='TRASH') ### icon: TRASH
                    op_rem_note.slide_index = index
                    op_rem_note.note_index = note_idx
                
        else:
            row_note = col.row(align=False)

            note_label = row_note.column(align=False)
            note_label.scale_x = 0.65
            note_label.label(text="Note:")

            note_field = row_note.column(align=False)
            note_field.scale_x = 4.1
            note_field.label(text="", icon='SYNTAX_OFF') ### icon: SYNTAX_OFF

            buttons = row_note.row(align=True)
            buttons.scale_x = 1
            op_add_note = buttons.operator("slide.add_note_line", text="", icon='ADD') ### icon: ADD
            op_add_note.slide_index = index

        timing = card.box()
        col = timing.column(align=False)

        row_frames = col.row(align=True)

        col_left = row_frames.column(align=False)
        row_start = col_left.row(align=True)
        row_start.prop(slide, "loop_start", text="In")
        op_start = row_start.operator("scene.paste_current_frame", text="", icon='EYEDROPPER') ### icon: EYEDROPPER
        op_start.slide_index = index
        op_start.target_prop = "loop_start"

        row_end = col_left.row(align=True)
        row_end.prop(slide, "loop_end", text="Out")
        op_end = row_end.operator("scene.paste_current_frame", text="", icon='EYEDROPPER') ### icon: EYEDROPPER
        op_end.slide_index = index
        op_end.target_prop = "loop_end"

        col_right = row_frames.column(align=False)
        row_trans = col_right.row(align=False)
        row_trans.prop(slide, "transition", text="Transition")

        row_cam = col_right.row(align=False)
        row_cam.prop(slide, "camera_object", text="")

        checkpoints = card.box()
        col = checkpoints.column(align=False)
        row_cp_header = col.row(align=False)
        row_cp_header.label(text="Add Checkpoint", icon='BOOKMARKS') ### icon: BOOKMARKS
        op_add_cp = row_cp_header.operator("slide.add_checkpoint", text="", icon='ADD') ### icon: ADD
        op_add_cp.slide_index = index

        for cp_idx, cp in enumerate(slide.checkpoint_frames):
            row_cp = col.row(align=False)
            row_cp.label(text=f"        {cp_idx + 1:02d}")
            row_cp.label(text=f"Stop at: {cp.frame}") ### icon: BOOKMARKS
            row_cp.prop(cp, "tag", text="", icon_only=True)
            op_rem_cp = row_cp.operator("slide.remove_checkpoint", text="", icon='TRASH') ### icon: TRASH
            op_rem_cp.slide_index = index
            op_rem_cp.cp_index = cp_idx

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        slides = scene.slides_collection

        layout.use_property_split = False
        layout.use_property_decorate = False

        top_split = layout.split(factor=0.67, align=True)

        add_col = top_split.column(align=True)
        add_col.scale_y = 1.2
        add_col.operator("scene.add_slide", text="", icon='ADD') ### icon: ADD

        trash_col = top_split.column(align=True)
        trash_col.scale_y = 1.2
        trash_col.enabled = bool(slides)
        op_rem = trash_col.operator("scene.remove_slide", text="", icon='TRASH') ### icon: TRASH
        op_rem.index_to_remove = scene.slide_index if slides else 0

        if not slides:
            empty = layout.box()
            empty_col = empty.column(align=True)
            empty_col.alignment = 'CENTER'
            empty_col.label(text="No slides yet", icon='INFO') ### icon: INFO
            empty_col.label(text="Create the first slide to start.")
            return

        list_box = layout.box()
        list_box.template_list(
            "SLIDES_UL_slide_list",
            "",
            scene,
            "slides_collection",
            scene,
            "slide_index",
            rows=scene.slide_list_rows,
            maxrows=20,
        )

        active_index = scene.slide_index
        if active_index < 0 or active_index >= len(slides):
            active_index = 0
        slide = slides[active_index]

        detail_box = layout.box()
        header = detail_box.row(align=False)
        detail_icon = 'TRIA_DOWN' if scene.slide_details_expanded else 'TRIA_RIGHT'
        header.prop(scene, "slide_details_expanded", text="Selected Slide", icon=detail_icon, emboss=False) ### icon: detail_icon

        if scene.slide_details_expanded:
            self._draw_selected_slide_details(detail_box, scene, slide, active_index)


class SLIDES_PT_controlli(bpy.types.Panel):
    bl_label = "Controller"
    bl_idname = "SCENE_PT_slides_controlli"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Slides PRO"
    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="", icon='WORKSPACE') ### icon: WORKSPACE

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        screen = context.screen if hasattr(context, "screen") else bpy.context.screen
        slides = scene.slides_collection

        layout.use_property_split = False
        layout.use_property_decorate = False

        status_box = layout.box()
        status = status_box.column(align=True)
        if slides and 0 <= scene.slide_index < len(slides):
            slide_name = slides[scene.slide_index].title or "Untitled Slide"
            status.label(text=f"Current Slide {scene.slide_index + 1}/{len(slides)}", icon='RESTRICT_VIEW_OFF') ### icon: RESTRICT_VIEW_OFF
            status.label(text=slide_name)
        else:
            status.label(text="No active slide", icon='INFO') ### icon: INFO

        nav_box = layout.box()
        row_nav = nav_box.row(align=True)
        row_nav.scale_y = 1.35

        col_prev_hard = row_nav.column()
        col_prev_hard.scale_x = 1.2
        op_prev_hard = col_prev_hard.operator("scene.hard_skip_slide", text="", icon='PREV_KEYFRAME') ### icon: PREV_KEYFRAME
        op_prev_hard.direction = -1

        col_rew = row_nav.column()
        col_rew.scale_x = 1.4
        col_rew.operator("scene.prev_slide", text="", icon='REW') ### icon: REW

        row_play = row_nav.row(align=True)
        row_play.scale_x = 1.0

        if scene.is_paused_at_checkpoint:
            row_play.operator("scene.next_slide", text="Continue", icon='PLAY') ### icon: PLAY
        elif scene.slide_transition_requested or scene.slide_prev_requested:
            row_wait = row_play.row()
            row_wait.enabled = False
            row_wait.operator("screen.animation_play", text="Waiting", icon='SORTTIME') ### icon: SORTTIME
        elif scene.is_transitioning:
            row_trans = row_play.row()
            row_trans.enabled = False
            row_trans.operator("screen.animation_play", text="Transition", icon='ONIONSKIN_ON') ### icon: ONIONSKIN_ON
        elif screen and getattr(screen, "is_animation_playing", False):
            row_play.operator("scene.stop_slides_presentation", text="Stop", icon='PAUSE') ### icon: PAUSE
        else:
            op_play = row_play.operator("scene.start_slides_presentation", text="Start", icon='PLAY') ### icon: PLAY
            op_play.index_to_start = scene.slide_index

        col_ff = row_nav.column()
        col_ff.scale_x = 1.4
        col_ff.operator("scene.next_slide", text="", icon='FF') ### icon: FF

        col_next_hard = row_nav.column()
        col_next_hard.scale_x = 1.2
        op_next_hard = col_next_hard.operator("scene.hard_skip_slide", text="", icon='NEXT_KEYFRAME') ### icon: NEXT_KEYFRAME
        op_next_hard.direction = 1

        view_box = layout.box()
        view_row = view_box.row(align=True)
        view_row.scale_y = 1.1

        overlay_text = "Hide Overlays"
        rendered_text = "Rendered View"
        try:
            if context.space_data and context.space_data.type == 'VIEW_3D':
                overlay_text = "Show Overlays" if scene.slides_clean_overlays_on else "Hide Overlays"
                rendered_text = "Solid View" if context.space_data.shading.type == 'RENDERED' else "Rendered View"
        except Exception:
            pass

        view_row.operator("scene.slides_toggle_viewport_overlays", text=overlay_text, icon='OVERLAY') ### icon: OVERLAY
        view_row.operator("scene.slides_toggle_rendered_view", text=rendered_text, icon='SHADING_RENDERED') ### icon: SHADING_RENDERED

        projection = layout.row(align=True)
        projection.scale_y = 1.15
        projection.operator("wm.new_projection_window", text="Open Projection Window", icon='WINDOW') ### icon: WINDOW

addon_keymaps = []
def register_keymaps():
    wm = bpy.context.window_manager
    keyconfig = getattr(wm.keyconfigs, "addon", None)
    if keyconfig is None:
        return

    km = keyconfig.keymaps.new(name='3D View', space_type='VIEW_3D')

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
    SLIDESPRO_OT_toggle_viewport_overlays,
    SLIDESPRO_OT_toggle_rendered_view,
    CLEAR_ANNOTATIONS_OT_operator,
    ADD_CHECKPOINT_OT_operator,
    REMOVE_CHECKPOINT_OT_operator,
    ADD_NOTE_LINE_OT_operator,
    REMOVE_NOTE_LINE_OT_operator,
    SLIDES_PT_impostazioni,
    SLIDES_UL_slide_list,
    SLIDES_PT_elenco,
    SLIDES_PT_controlli,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.slides_collection = CollectionProperty(type=SlideItem)
    bpy.types.Scene.slide_index = IntProperty(default=0, update=update_slide_index)
    bpy.types.Scene.is_looping = BoolProperty(default=False)
    bpy.types.Scene.is_transitioning = BoolProperty(default=False)
    bpy.types.Scene.slide_transition_requested = BoolProperty(default=False)
    bpy.types.Scene.slide_prev_requested = BoolProperty(default=False)
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
            ('BOTTOM_LEFT', "Bottom Left", "Bottom Left", 'ANCHOR_BL', 0),
            ('TOP_LEFT', "Top Left", "Top Left", 'ANCHOR_TL', 1),
            ('BOTTOM_RIGHT', "Bottom Right", "Bottom Right", 'ANCHOR_BR', 2),
            ('TOP_RIGHT', "Top Right", "Top Right", 'ANCHOR_TR', 3),
        ],
        default='BOTTOM_LEFT'
    )

    bpy.types.Scene.slide_info_expanded = BoolProperty(
        name="Show Info", default=False)
    bpy.types.Scene.slide_details_expanded = BoolProperty(
        name="Show Selected Slide Settings", default=False)
    bpy.types.Scene.slide_list_rows = IntProperty(
        name="Rows", default=6, min=3, max=20)
    bpy.types.Scene.slides_clean_overlays_on = BoolProperty(
        name="Clean View", default=False)

    for scene in bpy.data.scenes:
        ensure_scene_slide_notes(scene)

    register_keymaps()

    print(f"{ADDON_NAME} v{ADDON_VERSION} active")

def unregister():
    unregister_keymaps()
    unregister_loop_handler()
    unregister_transition_handler()
    unregister_notes_handler()

    props_to_del = [
        "slides_collection", "slide_index", "is_looping", "is_transitioning",
        "slide_transition_requested", "slide_prev_requested",
        "transition_target_index", "is_paused_at_checkpoint",
        "next_checkpoint_index", "slide_show_notes",
        "slide_title_fontsize", "slide_note_fontsize",
        "slide_notes_position",
        "slide_info_expanded", "slide_details_expanded",
        "slide_list_rows", "slides_clean_overlays_on"
    ]
    for prop in props_to_del:
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
            except Exception:
                pass

    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception:
            pass

    print(f"{ADDON_NAME} v{ADDON_VERSION} deactivated")

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()