# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
#from itertools import cycle

# system imports
import sys
import os
import copy

class CMesh(object):
    """docstring for CMesh"""
    def __init__(self):
        super(CMesh, self).__init__()
        # init private variables
        self._meshFilePath = None
        self._meshMovementType = None
        self._meshMovementPose = None
        self._numberInstances = None
        self._instanceSizeVariationMin = None
        self._instanceSizeVariationMax = None
        self._meshList = []

        
    def readInPoseFromCSV(self,csvFilePath,renderLabelsActive):
        poseList = []
        channelIndex = 0

        with open(csvFilePath) as csvFile:
            csvReader = csv.reader(csvFile, delimiter=',')
            line_count = 0
            for row in csvReader:
                pose = np.zeros((8))

                # read frame ID
                pose[0] = int(row[0]) + channelIndex

                # read position
                pose[1] = float(row[1])  # posX
                pose[2] = float(row[2])  # posY
                pose[3] = float(row[3])  # posZ
                
                # read quaternion
                pose[4] = float(row[4])  # quatW
                pose[5] = float(row[5])  # quatX
                pose[6] = float(row[6])  # quatY
                pose[7] = float(row[7])  # quatZ

                poseList.append(pose)

                #print(pose)
                # TODO: generalize for different rendering passes, like depth
                # if labels get rendered as well, attach pose again for label rendering
                if(renderLabelsActive):
                    channelIndex += 1
                    poseLabel = copy.deepcopy(pose)
                    poseLabel[0] += 1
                    poseList.append(poseLabel)

        return poseList

    def step():
        pass # TODO: to be filled!

    def activateLabelPass(self,labelID=1):
        pass # TODO: to be filled!

    def activateInstancePass(self):
        pass # TODO: to be filled!
        
    def activateRGBPass(self):
        pass # TODO: to be filled!

    def setUpMeshMovements(self,mesh,poseList):
        for pose in poseList:
            #print(pose)
            mesh.location = (pose[1],pose[2],pose[3])
            mesh.rotation_quaternion = (pose[4],pose[5],pose[6],pose[7])
            mesh.keyframe_insert('location', frame=pose[0])
            mesh.keyframe_insert('rotation_quaternion', frame=pose[0])

    def createScene(self,numBatches,samplesInBatch,labelsActivate):
        pass

    def setUpMesh(self,meshSettingsCfg, meshID):
        # save cfg parameters to variables
        self._meshFilePath = meshSettingsCfg['meshFilePath']
        self._meshMovementType = meshSettingsCfg['meshMovementType']
        if self._meshMovementType == 'deterministic':
            self._meshMovementPose = meshSettingsCfg['meshMovementPose']
        self._numberInstances = meshSettingsCfg['numberInstances']
        if self._numberInstances > 1:
            self._instanceSizeVariationMin = meshSettingsCfg['instanceSizeVariationMin']
            self._instanceSizeVariationMax = meshSettingsCfg['instanceSizeVariationMax']

        # load mesh from blend file
        meshObjectFileName = os.path.basename(os.path.normpath(os.path.splitext(self._meshFilePath)[0]))
        if 'meshInstanceName' in meshSettingsCfg:
            if not meshSettingsCfg['meshInstanceName'] == "":
                meshObjectFileName = meshSettingsCfg['meshInstanceName']
        mesh = None

        # go trough all instances
        for instanceID in range(0,self._numberInstances):
            if mesh == None:
                 # first mesh; load blender file
                bpy.ops.wm.append(directory=os.path.join(self._meshFilePath,"Object"), link=False, filename=meshObjectFileName)
                mesh = bpy.context.scene.objects[meshObjectFileName]
                mesh.name = 'mesh_' + str(meshID) + '_' + meshObjectFileName + str(instanceID+1)
                mesh.hide_viewport = False
                mesh.hide_render = False
                self._meshList.append(mesh)
            else:
                bpy.ops.object.duplicate({"object" : mesh,"selected_objects" : [mesh]}, linked=False)
                    
                # TODO: find better way for remapping, instead of over name
                # rename mesh
                ### TODO: fix!!!! just one instance works right now, check stage for reference!!!!!!!!!!!
                objName = meshObjectFileName+'.001'
                newObjName = 'mesh_' + str(meshID) + '_' + meshObjectFileName + str(instanceID+1)
                newMesh = bpy.data.objects[objName]
                newMesh.name = newObjName
                newMesh.hide_viewport = False
                newMesh.hide_render = False
                self._meshList.append(newMesh)

        # set up movement pattern of mesh
        if self._meshMovementType == 'deterministic':
            meshPoseList = self.readInPoseFromCSV(self._meshMovementPose,renderLabelsActive) # TODO: fix! removec renderLabelsActive. get it from cfg
            for meshInstance in self._meshList:
                self.setUpMeshMovements(meshInstance,meshPoseList)