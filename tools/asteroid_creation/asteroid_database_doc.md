# Generating a landing trajectory generation

## Adapt config file `cfgExamples/wout_paper.json`

This file should contain some key parameters for it to generate the landing trajectory adequately:
```json
	"SENSOR_SETUP": {
		"GENERAL": { "sensorMovementType":"centeredTarget", 
			     "landingMode": true,
			     "finalApproachDistance": 1.05
		},
	},

	"ASSET_SETUP": { 
		"MESHES": [{ "type": MeshAsteroid,
			    "meshParams": { 
					"meshFilePath":"oaisys_data/examples/assets/objects/test_asteroids/4_Vesta_HAMO_256k_rb_0.obj",
					"location": "trajectory_simulation",
					"trajectorySimulation": [-0,-0,-0,-0,-0,-0],
			    },
			    "trajectoryParams": { 
					"trajectoryType": {"mode": "predefinedProbability", "probability":[0.5,0.5,0.0]},
					"rotationPeriod": 8.12,
					"observationTime": 0.1,
					"landingMode": true,
					"finalApproachDistance": 1.0
			    },
		}],
```

## Adapt database generation file `asteroid_database.py`

- Provide cfg, Blender, and mesh directories
- Decide on number of runs, batches and samples to use

## Setup on Slurm Cluster

1. SSH to the slurm head node: 
```bash
ssh rmc-slurm-head-c01
```

2. Allocate resources without restrictions (what specific gpu is used)
```bash
salloc --partition=RMC-C01-BATCH --nodelist=rmc-gpu20 --cpus-per-task=4 --mem=60G --gres=gpu:1 -t 99:00:00 srun --pty bash
```