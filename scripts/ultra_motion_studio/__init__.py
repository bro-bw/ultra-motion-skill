bl_info = {'name':'Ultra Motion Studio','author':'Ultra Motion Studio contributors',
           'version':(0,1,0),'blender':(4,2,0),'location':'View3D > Sidebar > Ultra Motion',
           'description':'Video pose JSON to isolated MMD-compatible FK motion','category':'Animation'}

import json
import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, PointerProperty
from . import core, rig

class UMSSettings(bpy.types.PropertyGroup):
    pose_file: StringProperty(name='姿态 JSON',subtype='FILE_PATH')
    mapping_file: StringProperty(name='骨骼映射 JSON（可选）',subtype='FILE_PATH')
    smoothing: FloatProperty(name='平滑 %',default=65,min=0,max=100)
    foot_lock: BoolProperty(name='脚底锁定（接触检测）',default=True)
    loop: BoolProperty(name='循环动画（追加接缝）',default=False)
    start_frame: IntProperty(name='起始帧',default=1,min=1)
    status: StringProperty(default='选择骨架，导入提取好的姿态 JSON')

class UMS_OT_bake(bpy.types.Operator):
    bl_idname='ums.bake'
    bl_label='生成动作到骨架副本'
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context):
        return context.mode == 'OBJECT' and context.object is not None and context.object.type == 'ARMATURE'
    def execute(self,context):
        settings=context.scene.ums_settings
        try:
            with open(bpy.path.abspath(settings.pose_file),encoding='utf-8-sig') as f: data=json.load(f)
            overrides=None
            if settings.mapping_file:
                with open(bpy.path.abspath(settings.mapping_file),encoding='utf-8-sig') as f: overrides=json.load(f)
                if not isinstance(overrides,dict): raise ValueError('Mapping must be a JSON object')
            obj,report=rig.bake(context.object,data,settings.smoothing/100,settings.foot_lock,settings.loop,settings.start_frame,overrides)
            settings.status='完成：%d 帧；不可达脚位 %d（详见对象 ums_report）' % (report['frames'],report['unreachable_foot_frames'])
            self.report({'INFO'},settings.status)
            return {'FINISHED'}
        except Exception as exc:
            settings.status=str(exc)
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}

class UMS_OT_demo(bpy.types.Operator):
    bl_idname='ums.demo'
    bl_label='运行内置演示（无需模型）'
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context): return context.mode == 'OBJECT'
    def execute(self,context):
        settings=context.scene.ums_settings
        source=rig.demo_rig()
        obj,report=rig.bake(source,core.demo_data(),settings.smoothing/100,settings.foot_lock,settings.loop,settings.start_frame)
        context.scene.frame_end=settings.start_frame+round(89*(context.scene.render.fps/context.scene.render.fps_base)/30)
        settings.status='合成演示已生成：90 帧（不是视频识别结果）'
        return {'FINISHED'}

class UMS_PT_panel(bpy.types.Panel):
    bl_label='Ultra Motion Studio · MVP'
    bl_idname='UMS_PT_panel'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Ultra Motion'
    def draw(self,context):
        l=self.layout; s=context.scene.ums_settings
        l.label(text='视频 → 外部提取脚本 → 姿态 JSON')
        l.prop(s,'pose_file'); l.prop(s,'mapping_file')
        l.prop(s,'smoothing'); l.prop(s,'foot_lock'); l.prop(s,'loop'); l.prop(s,'start_frame')
        l.operator('ums.bake'); l.operator('ums.demo')
        l.label(text=s.status)
        l.label(text='输出：骨架副本；原网格仍绑定原骨架')

CLASSES=(UMSSettings,UMS_OT_bake,UMS_OT_demo,UMS_PT_panel)
def register():
    for cls in CLASSES: bpy.utils.register_class(cls)
    bpy.types.Scene.ums_settings=PointerProperty(type=UMSSettings)
def unregister():
    del bpy.types.Scene.ums_settings
    for cls in reversed(CLASSES): bpy.utils.unregister_class(cls)
