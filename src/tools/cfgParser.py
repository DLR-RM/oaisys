# blender imports
import bpy

# system imports
import json

class TSS_OP_readInCFG(bpy.types.Operator):
    bl_idname = "example.func_1"
    bl_label = "read in config"

    def execute(self, context):
        #print("read in cfg!")

        jsonDict = None
        jsonPath = "C:/Users/MGM/AppData/Roaming/Blender Foundation/Blender/2.82/scripts/TerrainStageSimulator/terrainTestcfg.json"

        with open(jsonPath, 'r') as f:
            # load json file
            jsonDict = json.load(f)
            #print(json.dumps(jsonDict, indent=4))

            # read in dicts for specific setups
            simulationSetupDict = jsonDict['simulationSetup']
            lightSetupDict = jsonDict['lightSetup']
            assetsDict = jsonDict['assets']

        return {'FINISHED'} 