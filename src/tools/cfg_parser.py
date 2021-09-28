# blender imports
import bpy

# system imports
import json
import copy as cp

class CCfgParser():
    def __init__(self):
        super(CCfgParser, self).__init__()
        self.simulationSetupDict = None
        self.renderSetupDict = None
        self.postEffectsSetupDict = None
        self.cameraDict = None
        self.lightSetupDict = None
        self.assetsDict = None
        self.jsonDict = None
        self.envDict = None

    def readInCfg(self, cfgPath):
        with open(cfgPath, 'r') as f:
            # load json file
            self.jsonDict = json.load(f)
            
            # read in dicts for specific setups
            self.simulationSetupDict = self.jsonDict['SIMULATION_SETUP']
            self.renderSetupDict = self.jsonDict['RENDER_SETUP']
            self.postEffectsSetupDict = self.jsonDict['RENDER_POST_PROCESSING_EFFECTS_SETUP']
            #self.cameraDict = self.jsonDict['cameraSetup']
            #self.lightSetupDict = self.jsonDict['lightSetup']
            self.assetsDict = self.jsonDict['ASSET_SETUP']
            self.envDict = self.jsonDict['ENVIRONMENT_EFFECTS_SETUP']
            self.sensorDict = self.jsonDict['SENSOR_SETUP']

            # go through terrain cfg and replace template cfg by cfg
            #self.loadTemplateForAssets()

    def loadTemplateForAssets(self):
        for terrainSample in self.assetsDict["terrains"]:
            self.loadTemplate(terrainSample)

    def loadTemplate(self, cfg):
        if "templatePath" in cfg:
            with open(cfg["templatePath"], 'r') as templateFile:
                _overwriteDict = cp.deepcopy(cfg)
                _templateDict = json.load(templateFile)

                # load template keys
                for templateSample in _templateDict:
                    cfg[templateSample] = _templateDict[templateSample]

                # load overwrite keys
                for overwriteSample in _overwriteDict:
                    cfg[overwriteSample] = _overwriteDict[overwriteSample]

    def getSimulationSetupCFG(self):
        return self.simulationSetupDict

    def getEnvSetupCFG(self):
        return self.envDict

    def getRenderSetupCFG(self):
        return self.renderSetupDict

    def getPostEffectSetupCFG(self):
        return self.postEffectsSetupDict

    def getSensorSetupCFG(self):
        return self.sensorDict

    def getLightSetupCFG(self):
        return self.lightSetupDict

    def getAssetsCFG(self):
        return self.assetsDict