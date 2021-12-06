# Source files

Components and folders:

* [assets](assets): This component is responsible for all meshes and materials in the scene.
* [environment_effects](environment_effects): In this component all the environment efefcts are defined, e.g. the light setup
* [sensors](sensors): This component deals with all sensors in the scene.
* [rendering](rendering): This component contains the render pass modules.
* [render_post_processing](render_post_processing): This component contains the moudles, which are working in the compositor and perform post processing steps on the rendered image. Note this is not the post processing, which is applied when creating hdf5 files.
* [tools](tools): In this folder usefull tools are stored, which the components can make use of.
* [handle](handle): This folder contains the handle functions.


Files:

* [TSSBase.py](TSSBase.py): This is the basic class for all OAISYS components.
* [TSS_simulation.py](TSS_simulation.py): This is teh main file of the simulator.
