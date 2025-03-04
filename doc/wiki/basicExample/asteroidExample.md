# Asteroid Crater Creation

This Readme serves as a basic example to create a synthetic dataset with segmented craters on asteroid surfaces, as presented in the paper "Bridging the Data Gap of Asteroid Exploration: OAISYS Extention for Synthetic Asteriods Creation", accepted at the IEEE Aeroconf 2025. We refer to the paper for further details.

If you found the paper or this code useful, please consider citing

```
@InProceedings{Mueller2025,
	author    = {M{\"{u}}ller, Marcus G. and Boerdijk, Wout and Hern{\'{a}}ndez, An{\'{i}}bal Guerrero and Kl{\"{u}}pfel, Leonard and Durner, Maximilian and Triebel, Rudolph},
	title     = {{Bridging the Data Gap of Asteroid Exploration: OAISYS Extension for Synthetic Asteroids Creation}},
	booktitle = {{IEEE Aerospace Conference}},
	year      = {2025}
}
```

The main procedure consists of **material generation** and **data rendering**, each of which will be explained in detail in the following.

---

### 1. Environment creation

Create an environment with the following required packages:
```python
pip install numpy
pip install git+git://github.com/cheind/py-thin-plate-spline
```

---

### 2. Material generation

Download crater Digital Elevation Maps (DEMs), and manually pre-process them with e.g. Inkscape. The final result should be a grayscale crater saved as a normalized int64 .png file, and an accompanying binary mask saved as uint8 .png file which labels the crater's inside.

Then, you can run the following script to generate 4k displacement and label maps
```python
python3 tools/asteroid_creation/generate_crater_map.py --data-root /path/to/crater_images --output-dir /path/to/output_dir
```
The script generates a single crater map, visualizes it (press any key to continue after the visualization) and then saves the images.

Optional arguments include:
```
--size [int]: size of the final output maps, (default: 4k)
--border [int]: border size of the material maps (default: 64 pixels)
--num-craters [int]: the number of craters to sample (default: 20)
--merge-type [str, one of {mean, mean_outside, argmax}]: the merge type, see Fig. 6 of the paper
```

Afterwards, place the displacement and label map with a texture of your choice (diffusion map, roughness map and so on) in a dedicated material folder (similar to [here](https://github.com/DLR-RM/oaisys/tree/master/oaisys_data/examples/assets/materials/asteroids).
You will notice that we used the same texture and json file as the texture *rock_ground*, with only some slight changes.
The only difference is the additional crater displacement map *craters_disp_4k.png*.
It is important that the generated crater map contains the key phrase *craters_disp* in the file name, in order for OAISYS to find the correct file.
Note, that you can provide an additional disp map with the texture.
OAISYS will take both textures and add them together.

Let us have a look at the corresponding json file:

```json
{
  "path":"oaisys_data/examples/assets/materials/asteroid/",
  "diffuse":true,
  "ref":true,
  "spec":true,
  "normal":false,
  "displacement":true,
  "normalStrength":0.0,
  "dispmapStrength": [[2.0, 5.0], [1.75, 2.25]],
  "size": 60.0,
  "mosaicRotation": 360.0,
  "mosaicNoise": 0.8
}

The json file varies in the displacement settings in comparison to *rock_ground*.
As you can see, for the displacement settings you will only find the param _dispmapStrength_, which lets you control the strength of the displacement map.
The parameter is a list, which contains two entries. The first one is reserved for the setting of the crater disp map. The second one is reserved for the additional disp map.
You can either provide a single float value or a list with a minimun and maximum value. The corresponding value will be taken randomly.
In the example cfg file the value for the crater disp is for instance betwen 2.0 and 5.0.
```
---

### 3. Setup Cfg

Apart from general config settings like setting the output path of the rendered files, adapt the config to fill in the material, label mask, and asteroid mesh like so:
```yaml
{
  "ASSET_SETUP": {
    "MATERIALS": [{
      "materialParams": {
        "terrainTextureList": [{
          "templatePath": "/path/to/generated_material",
          "passParams": {
            "semantic_label": {
              "labelIDVec": [[{
                "filePath": "/path/to/crater_label_mask.png"
              }]]
            }
          }
        }]
      }             
    }]
  },
  "MESHES": [{
    "meshParams": {
      "meshFilePath": "/path/to/asteroid_mesh.obj"
    }
  }]
}
```
We provide a sample cfg file here: [../../../cfgExamples/OAISYS_Aeroconf2025_asteroid_generation.json](../../../cfgExamples/OAISYS_Aeroconf2025_asteroid_generation.json)

Let us have a look at the important parts of the config:

#### SENSOR_SETUP

```yaml
...
"stepInterval": 1,
"sensorMovementType":"centeredTarget",
"sensorMovementPose":"possible_old_files/asteroid_deterministic.csv",
"sensorDistanceScale": [1.5,3.0],
"landingMode": false,
"finalApproachDistance": 1.05,
"hoverBaseModeEnabled": false,
"hoverBaseStage":"landscape01",
"hoverTargetModeEnabled": false,
"hoverBaseDistance":[0.3, 6.0],
"targetObjectActive":false,
"tragetObjectMovementType":"random",
"targetObject": "asteroid"

...
```
In order to point the sensor towards the asteroid, we have to choose "centeredTarget" as *sensorMovementType*.
Furthermore, you have to provide the asset name of the asteroid in "targetObject".

#### MATERIALS

```yaml
...
"templatePath": "oaisys_data/examples/assets/materials/asteroid/asteroid.json",
"passParams": 	{ "rgb": {},
                "semantic_label": {"labelIDVec": [[
                    {
                        "filePath": "oaisys_data/examples/assets/materials/asteroid/label_mask.png",
                        "mappingTable": {
                                                         "1": [[10,10,10],[100]],
                                                         "2": [[20,20,20],[200]],
                                                         "3": [[30,30,30],[300]],
                                                         "4": [[40,40,40],[400]],
                                                         "5": [[50,50,50],[500]],
                                                         "6": [[60,60,60],[600]],
                                                         "7": [[70,70,70],[700]],
                                                         "8": [[80,80,80],[800]],
                                                         "9": [[90,90,90],[900]],
                                                         "10": [[100,100,100],[1000]],
                                                         "11": [[110,110,110],[1100]],
                                                         "12": [[120,120,120],[1200]],
                                                         "13": [[130,130,130],[1300]],
                                                         "14": [[140,140,140],[1400]],
                                                         "15": [[150,150,150],[1500]],
                                                         "16": [[160,160,160],[1600]],
                                                         "17": [[170,170,170],[1700]],
                                                         "18": [[180,180,180],[1800]],
                                                         "19": [[190,190,190],[1900]],
                                                         "20": [[200,200,200],[2000]]
                        }
                    }
                    ,5,2]]},
                "instance_label": {}
                },
...
```

In order to use the previously generated label mask for the craters, we have to provide the mask and the corresponding label coding.
Therefore, provide the mask image with the parameter "filePath". The parameter "mappingTable" lets you remap values from RGB into labelIDs.
For example, the first entrance _[[10,10,10],[100]]_ maps the RGB value (10,10,10) to the label ID 100. Provide for each used RGB value a corresponding labelID.

#### MESHES

```yaml
...
"name": "asteroid",
"type": "MeshAsteroid",
"meshParams": {
"meshFilePath":"oaisys_data/blender_files/rocks/asteroid.blend",
"meshInstanceName": "asteroid",
"location": "trajectory_simulation",
"trajectorySimulation": [-0,-0,-0,-0,-0,-0],
"numSamples": 5,
"assetDistanceScale": [1.2,1.4],
"random_rotation": true,

"assetMaterial": "mesh_material_01", 

"passParams": 	{ "rgb": {},
                  "semantic_label": {"labelIDVec": [[2400,2400,100,100]]},
                  "instance_label": {}
},

"trajectoryParams": { 
"trajectoryType": {"mode": "predefinedProbability", "probability":[0.5,0.5,0.0]},
"rotationPeriod": 8.12,
"observationTime": 0.1
},

"instanceLabelActive": true,
"randomSwitchOnOff": false,
"activationProbability": 0.3,

"assetDisplacementParams":{
"assetDisplacementActive": true,
"assetDisplacementMidLevel": 0.4,
"assetDisplacementStrength": [1,80],
"assetDisplacementNoiseType": "MUSGRAVE",
"assetDisplacementNoiseParams": { 	"noise_scale": 200,
                        "noise_depth": 0.2,
                        "nabla": 0.2
}	
}
...
```

For this example we use the dummy mesh as asteroid. You can also use a obj file. Just provide the path in the parameter "meshFilePath".
Make sure that the "name" you choice here, corresponds with the name in *SENSOR_SETUP*.
The parameters *assetDisplacement** can be used to deform the general base mesh. The parameters *assetDisplacementStrength* and the params of *assetDisplacementNoiseParams* can also be a list in order to provide a min and max value.

### 4. Render data 
Then, call the rendering script to render data:
```python
python3 run_oaisys.py --blender-install-path path/to/blender/ --config-file /path/to/config.yaml
```