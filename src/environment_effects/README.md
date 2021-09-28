# Environment Effects

Environment Effects is a collection of effects which reside inside the world material of a blender file. The world material is responsible for the display of the background environment. This can be for instance the sky module or the usage of HDRIs.

# Current List of Environment Effects

- ![EnvLightBlenderSky](effects/doc/EnvLightBlenderSky_doc.md): This module allows to simulate realistic skies, with no clouds.
- ![EnvHDRI](effects/doc/EnvHDRI_doc.md): This module allows to simulate background ambient lights with the usage of HDRIs.

# Usage Information

TODO: How do they work, like sequences and so on.

TODO: general explanation of general and specific effects config, how to use it.

TODO: Example cfg

### General Config Options

# Development Information

## Strucutre of General Environment Effect

Environment Effects are


## Environment Effects Base Function

In comparsion to the other main modules, TSS has some specific unique functions and variables, which can be used in your own module:

### Variables

- `self._world_node_tree`: This variable contains the current handle to the world material

### Functions
