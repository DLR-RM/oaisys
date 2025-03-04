import json
import shutil
import os
import random
import time
# from tqdm import tqdm
import subprocess

# Path to the original JSON file
original_file_path = './cfgExamples/wout_paper.json'
# Directory containing mesh files
mesh_directory = "./oaisys_data/examples/assets/objects/test_asteroids"  # For generating landing views
# mesh_directory = "./oaisys_data/examples/assets/objects/asteroids" # For test purposes

# Get the parent directory of the current working directory
parent_directory = os.getcwd()

# run_oaisys.py script
run_script_path = "./run_oaisys.py"
# Blender install directory
blender_install_path = "/home/guer_an/Desktop"

# Variables to change:
# Simulation parameters -> 15 x (1 x 50) = 2,500 images FOR TRAIN PURPOSES
# Simulation parameters -> 90 x (2 x 15) = 2,700 images FOR TEST PURPOSES -> No deformations, 
num_runs = 15        # Number of runs to execute (DIFFERENT ASTEROIDS)
num_batches = 1      # With a certain asteroid, how many batches of images to generate
samples =  50        # Images per asteroid

# Orbit parameters
rotationPeriod = random.uniform(8, 9)
observationTime = random.uniform(0.01, 0.6)

# # Deformation parameters
# deformation_midlevel = random.uniform(0.2,0.6)
# deformation_strength = random.uniform(0.01, 0.1)

# # Deformation parameters for test purposes
deformation_midlevel = 0
deformation_strength = 0

# Environment conditions
sun_intensity = [random.uniform(0.045, 0.09)]

def create_dataset(original_file_path, mesh_directory, parent_directory,
                   samples, rotationPeriod, observationTime, deformation_midlevel, deformation_strength):
    pass

total_time_start = time.time()

# Create the runs folder in the parent directory
runs_folder = os.path.join(parent_directory, "run")
if not os.path.exists(runs_folder):
    os.makedirs(runs_folder)

for i in range(num_runs):
    print("=========================================================")
    print(f"Run number: {i}/{num_runs} =======================================")
    print("=========================================================")

    run_start = time.time()

    # Randomly select a mesh file
    mesh_file = random.choice(os.listdir(mesh_directory))
    mesh_file_path = os.path.join(mesh_directory, mesh_file)

    # Get the base name of the mesh file (without extension)
    asteroid_name = os.path.splitext(mesh_file)[0]

    # Generate run folder name with timestamp and padded number
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
    run_folder_name = f"{timestamp}_run_{str(i+1).zfill(4)}_{asteroid_name}"
    run_folder = os.path.join(runs_folder, run_folder_name)
    os.makedirs(run_folder, exist_ok=True)

    # Save a copy of the base configuration to the run folder
    run_config_file_path = os.path.join(run_folder, "modified_config.json")

    # Use shutil to copy the file directly
    shutil.copyfile(original_file_path, run_config_file_path)

    # Modify the config data:
    with open(run_config_file_path, 'r+') as file:
        config_data = json.load(file)
        # Modify parameters within the JSON data

        # Change numSamplesPerBatch and numBatches in SIMULATION_SETUP
        if 'SIMULATION_SETUP' in config_data:
            config_data['SIMULATION_SETUP']['numSamplesPerBatch'] = samples
            config_data['SIMULATION_SETUP']['numBatches'] = num_batches
    
        # Change meshFilePath, numSamples, rotationPeriod, and observationTime in ASSET_SETUP -> MESHES
        if 'ASSET_SETUP' in config_data and 'MESHES' in config_data['ASSET_SETUP']:
            for mesh in config_data['ASSET_SETUP']['MESHES']:
                if 'meshParams' in mesh:
                    mesh['meshParams']['meshFilePath'] = mesh_file_path
                    mesh['meshParams']['numSamples'] = samples
                    if 'trajectoryParams' in mesh['meshParams']:
                        mesh['meshParams']['trajectoryParams']['rotationPeriod'] = rotationPeriod
                        mesh['meshParams']['trajectoryParams']['observationTime'] = observationTime

                    if 'assetDisplacementParams' in mesh['meshParams']: 
                        mesh['meshParams']['assetDisplacementParams']['assetDisplacementMidLevel'] = deformation_midlevel
                        mesh['meshParams']['assetDisplacementParams']['assetDisplacementStrength'] = deformation_strength

        # Change sunIntensity in ENVIRONMENT_SETUP
        if 'ENVIRONMENT_EFFECTS_SETUP' in config_data:
            for env in config_data['ENVIRONMENT_EFFECTS_SETUP']['ENVIRONMENT_EFFECTS']:
                if 'environmentEffectsParams' in env:
                    env['environmentEffectsParams']['sunIntensity'] = sun_intensity

        # Write the modified data back to the JSON file
        file.seek(0)
        json.dump(config_data, file, indent=2)
        file.truncate()

    # Command template to execute
    command_template = [
        "python3",
        run_script_path,
        "--blender-install-path",
        blender_install_path,
        "--config-file"
    ]
    # Execute the command with the copied config file path
    subprocess.run(command_template + [run_config_file_path])

    # Record the time taken for this run
    run_end = time.time()

    print(f"Modified configuration saved to: {run_config_file_path}")




total_time_end = time.time()
total_time_taken = total_time_end - total_time_start

print(f"\nTotal time taken for {num_runs} runs: {total_time_taken/(60*60):.2f} hrs")
print(f"Average time per run: {(total_time_taken/num_runs)/(60*60):.2f} hrs")

total_images = num_runs * num_batches * samples
print(f"Total number of images generated per asteroid: {num_batches * samples}")
print(f"Total number of images generated in total: {total_images}")