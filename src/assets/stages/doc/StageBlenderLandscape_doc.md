# StageBlenderLandscape

This stage module can create realistic terrain stages. For that, it uses the [ANT Landscape add-on](https://docs.blender.org/manual/en/latest/addons/add_mesh/ant_landscape.html).

## Parameters

### stageName

Defines the blender name of the created stage.

type of parameter: string

### landscapeParams

Defines the parameters, which are used to create the landscape.
TODO: add information about data type
More information about the parameters can be found [here](https://docs.blender.org/manual/en/latest/addons/add_mesh/ant_landscape.html).

type of parameter: dict

### stageLandscapePreset

The simulator comes with a number of landscape presets, which are based on the [ANT presets](https://github.com/blender/blender-addons/tree/6f0128c332290c6f3639d4d949d3e06bfaa71022/presets/operator/mesh.landscape_add). With that, it is possible to create fast different kind of realistic terrains. The presets parameters can be overwritten by `landscapeParams`. It is also possible to create your own preset and use it. For that specify a preset file and save it into the default_cfg folder of this module. You can load it by inserting the name of the preset file to `stageLandscapePreset`. The following presets are currently available:

* [another_noise]()
* [large_terrain]()
* [canyon]()
* [dunes]()
* [mesa]()
* [mounds]()
* [mountain_1]()
* [mountain_2]()



type of parameter: string

### stageSizeX

Once the landscape stage is created, one can provide the desired x length of the stage with `stageSizeX`. The mesh is scaled accordingly. It is best practice to do the scaling afterwards, instead of specifying to the desired end length with `landscapeParams`.

type of parameter: float

### assetMaterial

Provide the material name of the material, which is applied to the stage.

type of parameter: string

## Example cfg

```json
{
  "name": "landscape01",
  "type": "StageBlenderLandscape",
  "stageParams": {
		  "stageName": "landscape",
		  "stageSizeX": 200,
		  "stageLandscapePreset": "another_noise",
		  "assetMaterial": "terrain_01",
		  "landscapeParams": {"random_seed":[0,1000]}
		  }
}
```
