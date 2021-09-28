# Basic OAISYS Tutorial (Under Construction!)

The goal of this tutorial is to get you familiar with the basic functionalities and usage of the simulator OAISYS.

In order to do that, let us define a dataset, we would like to create. In this dataset we would like to  feature a planetary landscape. That landscape shall have three different terrains. One should be clay, another one bedrock, another one gravel. Furthermore, we want to place about 10000 rocks on the surface of our terrain. The data should be recorded by sunset and we would like to simulate a stereo sensor setup. Our dataset will be used by a roboticist and a geologist, which want different semantic labels for the terrains, rocks and the sky in the scene. The following semantic labels are requested:


| semantic item  | semantic ID (roboticist) | semantic ID (geologist) |
| ------------- | ------------- | ------------- |
| gravel | 10 | 75 |
| clay | 20 | 150 |
| bed rock | 30 | 200 |
| rocks | 40 | 200 |
| sky | 500 | 500 |


We would like to use a stereo camera setup.
Furthermore, we would like to have 5 different looking terrains and from each 2 samples.
In the end, we would like to have hdf5 files, so that we can directly use the dataset for further processing.

In this tutorial, we have a look into how to create such a dataset.

# download OAISYS

Before we can start to create our own environment, we have to download this repository.
Navigate to the folder, where you would like to download OAISYS and execute:

`git clone https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator.git`

# running OAISYS for the first time

To run OAISYS you just have to execute the following command

`python run_oaisys.py --blender-install-path /path/to/blender/ --config-file /path/to/cfg/file/cfg_file.json`

OAISYS needs as input your blender installation. If you have not blender installed yet, just provide the path where you would like it to be installed (with _blender-install-path_), and OAISYS will do the rest for you. Since everything is controlled via a cfg file, the path to this file has to be provided as well (with _config-file_).

Although, you will most likely always use OAISYS with your own custom cfg file, the simulator also ships with a default cfg file, which will be loaded, if no cfg file is provided.
Therefore, to get fimiliar with OAISYS we will start by calling OAISYS without any cfg file.
For that, navigate into the OAISYS repo and execute the following lines (with your prefered blender path):

`python run_oaisys.py --blender-install-path /path/to/blender/`

If you have not blender installed yet or not the correct version, it will take a while to download the correct blender version. After the installation you will be greeted by OAISYS:

![Welcome splash screen of OAISYS](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/doc/wiki/figures/BasicTutorial/oaisys_start_screen.jpg)

After that you find multiple outputs of OAISYS, which gives you information about the processing of the default cfg file. Wait till this process is completed, that will take a moment depending on your working machine, since also some images are rendered by default.

Let's have first a look into what OAISYS made out of the default cfg file, before we get into the details of the cfg file and how we can modify it. In the repository you will find a new folder called `oaisys_tmp`, which was just created wiht the execution of the script.
Navigating into this folder, you will find another folder, with the current date. This folder contains all of the simulated data for our cfg file. If you execute OAISYS again, another folder with the current date will be created. It contains all batches, which were created by the simulation. Since the default cfg is just requesting one batch, just one folder can be found.
Open the folder `batch_001`.

Every batch folder contains all of the sensor rendering outputs and the corresponding blender file. The default cfg just defines one sensor, called _sensor_1_, there you are faced with the two folders: `blender_file` and `sensor_1`. Navigate into the `sensor_1` folder.
The `sensor_1` folder contains all images, which where rendered for _sensor_1_ for _batch_001_. In this case it is only one sample, which five render pass files (rgb, depth, semantic_level_1, semantic_level_2, instance) belong to.

| rgb  | semantic 01 | semantic 02 | instance |
| ------------- | ------------- | ------------- | ------------- |
| ![](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/doc/wiki/figures/BasicTutorial/0002sensor_1_rgb_00.png) | ![](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/doc/wiki/figures/BasicTutorial/0002sensor_1_semantic_label_00.png) | ![](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/doc/wiki/figures/BasicTutorial/0002sensor_1_semantic_label_01.png) | ![](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/doc/wiki/figures/BasicTutorial/0002sensor_1_instance_label_00.png) |

Note that your OAISYS render output will look different, since the generation process contains multiple random parameters.

OAISYS also saves the blender file it created and used to simulate the scene. This is particular useful, if you want to adjust parameters for your assets, since you can use it as a reference file. Furthermore, it is very useful, when you create your own OAISYS module.

![Screenshot of Blender File](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/doc/wiki/figures/BasicTutorial/oaisys_blender_file_preview.jpg)

Let us now have a look at the default cfg, which can be found here: [default cfg file](https://rmc-github.robotic.dlr.de/moro/TerrainStageSimulator/blob/master/cfgExamples/OAISYS_default_cfg.json)

Note that the cfg file is a json file and contains of a dictionary. The dictionary has the following main entries: _SIMULATION_SETUP_, _RENDER_SETUP_, _RENDER_POST_PROCESSING_EFFECTS_SETUP_, _SENSOR_SETUP_, _ENVIRONMENT_EFFECTS_SETUP_, _ASSET_SETUP_.

Each of the entries contains the information about a specific setup of the simulation. The _SENSOR_SETUP_ for instance defines how the the sensors are setup in the simulator, while _ASSET_SETUP_ defines which assets are used and how they are used.

In the following we will have a look into each of this main components. We have a first look how the default cfg file is setting them up, and then modify them as we need them.

# setting up the cfg file

As we already have seen, the cfg file consist of mainy different main components. In the current version OAISYS has the following main components:


* SIMULATION_SETUP: This component is responsible to setup all main parameters for the simulator. For instance how many samples are rendered, and where the data is stored.
* RENDER_SETUP: This components provides information of which render passes are activated.
* ASSET_SETUP: This component contains all information about the assets which are used for the simulation.
* SENSOR_SETUP: In this components all sensors are defined.
* ENVIRONMENT_EFFECTS_SETUP: This components include all modules, which will change the world setup of blender. In this component the light is setup.
* RENDER_POST_PROCESSING_EFFECTS_SETUP: This component provides modules, which interact in the compositor editor of blender. Here, one can for instance activate effects like blooming effect.

All of the components are following a certain structure.
Each component contains a _GENERAL_ section, which contains general parameters of the component.
Furthermore, each component has a specific section in a form of a list.
This section, gives you the possibility to list all modules which be used by the component.
For the sensors that might the list of sensors you want to use. For the render passes it will be the list of render passes, which will be activated. For the object assets, it will the list of objects which will be placed on the stage.

Before, we start making adjustments of the default cfg file, make a copy of it, which we can modify in the following.

## render passes setup

Let us first have a look into the render component. This component defines, which render passes will be used by the simulation and the general 

```json
"RENDER_SETUP": {

		"GENERAL": {
			     "renderEngine":"CYCLES",
			     "renderFeatureSet":"EXPERIMENTAL",
			     "renderDevice": "GPU",
 			     "performanceTilesX": 256,
 			     "performanceTilesY": 256
			   },

		"RENDER_PASSES": [{
 				    "type": "RGBDPass",
				    "passParams": {
						    "numIter": 1,
						    "renderDepthActive": true,
						    "renderSamples":128,
						    "lightPathesMaxBounces": 6
						   }
				  },
				  {
				    "type": "SemanticPass",
				    "passParams": {
						    "numIter": 2,
 						    "renderSamples":1
						   }
				  },
				  {
  				     "type": "InstancePass",
				     "passParams": {
	                                            "numIter": 1,
     					            "renderSamples":1
						    }
			         }]
				
	}
```

First note the structure of the component. As mentioned before it has a _GENERAL_ section and a sepcifc section, here called _RENDER_PASSES_.

In the general section, we general parameters, how the simulation should render images. For instance which Engine will be used and which device. For the current version of OAISYS we highly recommend to use _CYCLES_ as render engine.

In the specific section _RENDER_PASSES_, we see three list entries by default. Each of three modules has again two section: _type_ and _passParams_. _type_ defines which module will be loaded. _passParams_ defines the dictionary , which will be passed to the module.
In the default case, three different modules are used: _RGBDPass_, _SemanticPass_ and _InstancePass_.
Each render pass module must have the parameter _numIter_, which defines how often this pass will be executed.

The _RGBDPass_ is responsible for the rgb and depth render passes. Next to the necessary _numItr_ entry, the module takes three more parameters. _renderDepthActive_, is a boolean flag, if depth is rendered as well or not. _renderSamples_ defines how many render samples are used for an image by blender. In many cases 128 should be a solid value. If you experience any so called "fire flies" in your image you should increase this number. However, be aware that this number has a strong effect on your render time. As higher the number as higher the render time. Same counts for _lightPathesMaxBounces_, in most cases the default number of 6 should be enough. This entry defines, how many times a light beam is allow to bounce. As higher the number, as more accurate the result, however as higher also the render times.

The two other passes _SemanticPass_ and _InstancePass_ have as additional parameter also the _renderSamples_ parameter. Note that it is set to 1 for each of them. Since we are using the diffuse color channel for these passes, a sample number of 1 is enough. You should NOT change this number since it will increase your render time, but not giving you any other result.
Note also that the _numItr_ value for the _SemanticPass_ is set to 2, meaning that by default two render passes for the semantic are rendered out, which we were already able to see in the output folder.

Since the render passes are very much linked to all other components, we will see them often again in the other components.

For our use case we do not have to change anything in this file.

## sensor setup

All sensors which are used for the simulation are attached to the base frame, like it is for the most real robots as well.
The movement of the base frame can be defined, and the attached sensors will be moved correspondingly.

Let us have a look into the sensor component of the cfg file:

```json
"SENSOR_SETUP": {
		"GENERAL": {"sensorMovementType":"randomEuclideanTarget",
					"hoverBaseModeEnabled": true,
					"hoverBaseStage":"landscape01",
					"hoverBaseDistance":1.5,
					"hoverBaseDistanceNoise": 0.5,
					"hoverTargetModeEnabled": true,
					"hoverTargetStage":"landscape01",
					"hoverTargetDistance":0.0,
					"positionOffsetEnabled":true,
					"randomEuclideanPosMin": [-8.0,-8.0,0.0],
					"randomEuclideanPosMax": [8.0,8.0,5.0],
					"randomEuclideanEulerMin": [0,0,0],
					"randomEuclideanEulerMax": [0,0,0],
					"randomTargetPosMin": [-20.0,-20.0,-3.0],
					"randomTargetPosMax": [20.0,20.0,-0.2],
					"randomTargetEulerMin": [0,0,0],
					"randomTargetEulerMax": [0,0,0],
					"randomTargetRollDeg": [-10.0,10.0],
					"targetObjectActive":true,
					"tragetObjectMovementType":"random"},

		"SENSORS": [{"type": "SensorCameraRGBD",
				     "sensorParams": {	
					"outputBaseName":"sensor_1",
					"imageResolution": [640,480],
 					"KMatrix": [541.14,      0, 320,
							 0, 541.14, 240,
						         0,      0,   1],
					"transformation": [0.0,0,0,1.0,0.0,0,0],
					"triggerInterval": 1,
 					"renderPasses": {
 						  "RGBDPass": {"activationSlot":[1], "DepthEnabled": true},
						  "SemanticPass": {"activationSlot":[1,1]},
						  "InstancePass": {"activationSlot":[1]}
							}
				        }
			   }]
	}
```

The _GENERAL_ part of the cfg file, defines the movement behavior of the base frame. We ignore this section for now and just concentrate on the _SENSORS_ part of the component.
The _SENSORS_ part is a list, which contains all to be used sensors.
In the default cfg case that this one sensor of the type `SensorCameraRGBD`.
Looking into the specific _sensorParams_ section of the sensor, we can see the specific parameters of the sensor, like resolution of the camera, KMatrix and so on.

As mentioned before, there are several components, which will have a entry for the render passes. So does the sensor modules. They require to have a entry named _renderPasses_, which defines, for which render pass they are active and if they have further information for the pass.
The activation is provided by the _activationSlot_ entry. A 1 defines that the sensor will be rendered for the pass and iteration, while a 0 indicates deactivation. In this case, we can see that the sensor is activated for the rgbd, instance and the 2 semantic passes. Furthermore, we can see that additional information is passed to the rgbd pass; here the information if the depth is rendered for the pass as well or not.

Since we want to have a stereo setup four our dataset, we add another sensor and adjust the corresponding parameters. Since we do not need the depth for the right camera, and also not the instance segmentation map, we can deactivate these passes. Furthermore, we are not interested in the second semantic pass for this camera. Therefore, the _SENSORS_ section should look like this:

```json
"SENSORS": [{"type": "SensorCameraRGBD",
	     "sensorParams": {
                                "outputBaseName":"sensorLeft",
				"imageResolution": [640,480],
			        "KMatrix": [541.14,	0,		320,
						 0,	541.14,		240,
						 0,	0,		1],
                                "transformation": [0.0,0,0,1.0,0.0,0,0],
				"triggerInterval": 1,
				"renderPasses": {
						  "RGBDPass": {"activationSlot":[1], "DepthEnabled": true},
						  "SemanticPass": {"activationSlot":[1,1]},
						  "InstancePass": {"activationSlot":[1]}
						}
			     }
	    },
	    {
	     "type": "SensorCameraRGBD",
	     "sensorParams": {	
  			        "outputBaseName":"sensorRight",
			        "imageResolution": [640,480],
				"KMatrix": [541.14,	0,	320,
					         0,	541.14,	240,
						 0,	0,       1],
				"transformation": [0.065,0,0,1,0,0,0],
				"triggerInterval": 1,
				"renderPasses": {
						  "RGBDPass": {"activationSlot":[1], "DepthEnabled": false},
						  "SemanticPass": {"activationSlot":[1,0]},
						  "InstancePass": {"activationSlot":[0]}
						}
			     }
}]
```

If you let the simulator now run with our custom cfg, you will see two output folders, with renderings. One for each sensor.
Note when you do this, we just obtain the two image files for _sensorRight_, as requested in our cfg file.

## setting up the assets

Next let's have a look into the assets. The asset component is a special component, and has a slightly different structure, compared to all other components. Like other components it also contains a _GENERAL_ section, but instead of one specific section it contains three specific sections. One for each specific asset type: stages, materials, objects. The reason they are all part of the same component is that they interact with each other. Let us have a look at the purpose of the 3 specific sections.

The _STAGES_ section is responsible for all stages used in the simulator.

The _MATERIALS_ section defines all terrain materials which are used in the simulator. Each material module is than assign to one stage module.

The _OBJECTS_ section defines all objects which are used in the simulator. Each object module is assigned to one stage module, like in the case ob the materials.

Additionally to the _type_ and specific params field of the modules, the modules of all asset sub-component have the additional entry of the _name_. This entry is very important for the interaction of the asset modules, since they can be identified with it.

### material setup

As the name suggests, in the _MATERIALS_ sub-component the materials are defined.
The materials are the textures, which are applied to the stages.

Looking at the default cfg file, we see one material module type in use of type _MaterialTerrain_.

The _MaterialTerrain_ module has a _general_ part in its specific parameters and the entry _terrainTextureList_. This module takes a list of textures, merges them with each other and creates a  material, which can be applied to a stage. In the _general_ section, the user can define, how many textures are merged and some some material properties. The _terrainTextureList_ contains the textures, which are used by the module.

```json
"MATERIALS": [	{
                "name": "terrain_01",
	        "type":"MaterialTerrain",
 		"materialParams":{
 				   "general": {"numMixTerrains":2,
					       "hardLabelBorders":true,
					       "withReplacement":false,
 					       "dispMidLevel":0.0,
 					       "dispScale":1.0,
					       "normalStrength":1.0,
 					       "mergingNoise": {
								"Scale": [3.0,7.0],
								"Detail": [1.0,3.0],
								"Roughness": [0.2,0.5],
								"Distortion": [0.0,0.6]
								}
                                               },
				   "terrainTextureList": [

			       {
 			        "templatePath": "examples/assets/materials/rock_ground/rock_ground.json",
			        "passParams": {
                                                "rgb": {},	                                    
                                                "semantic_label": {"labelIDVec": [30,500,5,2]},
					        "instance_label": {}		
                                              }
                               },
			       {
                 	        "templatePath": "examples/assets/materials/dry_ground_01/dry_ground_01.json",
 				"passParams": { "rgb": {},
                                                "semantic_label": {"labelIDVec": [30,500,5,2]},
                                                "instance_label": {}	
                                              },
				}
			]
		   }}
	     ]
```

We will not go into details here about all parameters of this module and refer the reader to the particular README of the module for more information. However, we will have a look at some parameters, which we want to adapt in order to create our dataset.

### stage setup

The stage sub-component is defining the stages, which are used in the simulator. Stages are the main meshes, on which materials will be applied an objects placed. In most cases, one stage is enough, however, you can also add multiple stages, for instance when simulating bodies of water.

Let us have a look at the default stage sub-component definition:

```json
"STAGES": [{"name": "landscape01",
	    "type": "StageBlenderLandscape",
	    "stageParams": {
			     "stageName": "landscape",		
			     "stageSizeX": 200,
 			     "stageLandscapePreset": "another_noise",
			     "assetMaterial": "terrain_01",
			     "landscapeParams": {"random_seed":[0,1000]}
			    }
	    }
	 ]
```

Note, that all assets have an additional parameter, which is there _name_. This entry has to be unique, and is important as identifier for the other sub-components.
As type we are using the _StageBlenderLandscape_, which uses the A.N.T. of blender to create a realistic basic stage mesh.
This module takes a _stageName_ to name the actual mesh for the blender file.  Furthermore, the user can define the size of the x dimension of the mesh with _stageSizeX_. The y and z value will be scaled accordingly. With _landscapeParams_ the user can provide any information about the landscape parameters. Alternative, the _StageBlenderLandscape_ modules provides also multiple preset terrains, which can be used with the _stageLandscapePreset_ parameter. Parameters now given in _landscapeParams_ will overwrite the preset values. In the default config case, that is the parameter for the random_seed. With "assetMaterial" the material can be defined, which will be applied to the stage.


### object setup

```json
"MESHES": [ {"name": "rock1",
					 "type": "MeshMultipleRandom",
					 "meshParams": {
					 		"meshType":"RANDOM_MULTIPLE",
							"meshFilePath":"examples/assets/objects/rocks/rocks_arches01.blend",
							"meshInstanceName": "rock_01",
							"numberInstances": [300,500],
							"randomSwitchOnOff": false,
							"labelIDVec": [[60,200,0,200]],
							"instanceLabelActive": true,
							"useDensityMap": true,
							"densityMapSettings": {
								"numberInstances": [13000,15000],
								"randomSwitchOnOff": false,
								"densityMap": {
									"noiseType": "VORONOI",
									"intensity": 1.2,
									"size": 0.2,
									"colorStopPosition_0":0.6,
									"colorStopColor_0":[0,0,0,1],
									"colorStopPosition_1":1.0,
									"colorStopColor_1":[1,1,1,1]
								}
							},
							"refreshFreq": 3,
							"defaultSize": 1.0,
							"strengthRandomScale": 1.0,
							"randomRotationEnabled": true,
							"rotationOptionMode":"NOR",
							"rotationOptionFactor":0.4,
							"rotationOptionPhase":0.3,
							"rotationOptionPhaseRandom":0.7,
							"meshEmitter":"STAGE",
							"appliedOnStage":"landscape01",
							"passParams": 	{ 	"rgb": {},
												"semantic_label": {"labelIDVec": [30,500,5,2]},
												"instance_label": {}
											}
					 		}
					},
					{"name": "rock2",
					 "type": "MeshMultipleRandom",
					 "meshParams": {
					 		"meshType":"RANDOM_MULTIPLE",
							"meshFilePath":"examples/assets/objects/rocks/rocks_arches01.blend",
							"meshInstanceName": "rock_02",
							"numberInstances": [300,500],
							"randomSwitchOnOff": false,
							"labelIDVec": [[60,200,0,200]],
							"instanceLabelActive": true,
							"useDensityMap": true,
							"densityMapSettings": {
								"numberInstances": [5000,8000],
								"randomSwitchOnOff": false,
								"densityMap": {
									"noiseType": "VORONOI",
									"intensity": 1.2,
									"size": 0.2,
									"colorStopPosition_0":0.6,
									"colorStopColor_0":[0,0,0,1],
									"colorStopPosition_1":1.0,
									"colorStopColor_1":[1,1,1,1]
								}
							},
							"refreshFreq": 3,
							"defaultSize": 3.0,
							"strengthRandomScale": 1.0,
							"randomRotationEnabled": true,
							"rotationOptionMode":"NOR",
							"rotationOptionFactor":0.4,
							"rotationOptionPhase":0.3,
							"rotationOptionPhaseRandom":0.7,
							"meshEmitter":"STAGE",
							"appliedOnStage":"landscape01",
							"passParams": 	{ 	"rgb": {},
												"semantic_label": {"labelIDVec": [30,500,5,2]},
												"instance_label": {}
											}
					 		}
					}
				]
```

## environment setup

```json
"ENVIRONMENT_EFFECTS_SETUP": {

		"GENERAL": {"backgroundStrength": [0.1],
					"stepInterval": 1
					},

		"ENVIRONMENT_EFFECTS": [	{"type": "EnvLightBlenderSky",
									"stepInterval": 1,
									"environmentEffectsParams": {
																"stepIntervalOption": "GLOBAL",
																"stepInterval": 2,
																"SunSize": [0.545],
																"SunIntensity": [1.0],
																"SunElevation": [15.0,90.0],
																"SunRotation": [0.0,360.0],
																"SunAltitude": [3000.0,3350.0],
																"AirDensity": [1.0,2.0],
																"DustDensity": [0.0,10.0],
																"OzoneDensity": [0.0,5.0],
																"SunStrength": [0.0001,0.1],
																"passParams": 	{ "RGBDPass": {"rgbIDVec": [1,-1,-1,-1]},
																				  "SemanticPass": {"semanticIDVec": [500,500,500,500]},
																				  "InstancePass": {"instanceIDVec": [-1]}
																				}
															}

									}
								]
	}
```

## setup general settings

```json
"SIMULATION_SETUP": {
		"outputPath":"",
		"defaultCfg": "",
		"numBatches":1,
		"numSamplesPerBatch":1,
		"pureBatchesActive":false,
		"renderImages": false,
		"saveBlenderFiles": true,
		"outputIDOffset":0,
		
		"hardLabelBorders":true,
		"noisePhaseShiftEnabled":true,
		"noisePhaseRate":1.0,
		"mixSamplingWithReplacment":false
	}
```

# run the simulator

[TODO] fill in


# post-processing

[TODO] fill in

