import bpy

from .base_node import USDNode
from ... import utils
from . import log


class MergeNode(USDNode):
    """Merges two USD streams"""
    bl_idname = 'usd.MergeNode'
    bl_label = "Merge USD"

    def update_inputs_number(self, context):
        if len(self.inputs) < self.inputs_number:
            for i in range(len(self.inputs), self.inputs_number):
                self.inputs.new(name=f"Input {i + 1}", type="NodeSocketShader")

        elif len(self.inputs) > self.inputs_number:
            for i in range(len(self.inputs), self.inputs_number, -1):
                self.inputs.remove(self.inputs[i - 1])

    inputs_number: bpy.props.IntProperty(
        name="Inputs",
        min=2, max=10, default=2,
        update=update_inputs_number
    )

    def init(self, context):
        self.update_inputs_number(context)
        self.outputs.new(name="Output", type="NodeSocketShader")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'inputs_number')

    def compute(self, **kwargs):
        from pxr import Usd, UsdGeom

        log("MergeNode")

        ref_stages = []
        for i in range(self.inputs_number):
            stage = self.get_input_link(i, **kwargs)
            if stage:
                ref_stages.append(stage)

        if not ref_stages:
            return None

        if len(ref_stages) == 1:
            return ref_stages[0]

        engine = kwargs['engine']
        stage = Usd.Stage.CreateNew(
            str(utils.usd_temp_path(self, engine)))
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        merge_prim = stage.DefinePrim(f"/merge", 'Xform')
        stage.SetDefaultPrim(merge_prim)

        for i, ref_stage in enumerate(ref_stages, 1):
            ref = stage.OverridePrim(f"/merge/ref{i}")
            ref.GetReferences().AddReference(ref_stage.GetRootLayer().realPath)

        return stage
