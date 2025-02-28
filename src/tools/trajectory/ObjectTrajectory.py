import bpy
import numpy as np
import mathutils


def get_single_mesh_data(mesh):
    """
    Get the vertices and faces of the single mesh object in the Blender scene.

    Returns:
    =
    - vertices (numpy.ndarray): Array of vertices.
    - faces (numpy.ndarray): Array of faces.
    """
    '''
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    print(f"get_single_mesh_data: {get_single_mesh_data}")

    if len(mesh_objects) != 1:
        print("Error: There should be exactly one mesh object in the scene, but there are:", len(mesh_objects))
        return None, None

    mesh = mesh_objects[0].data
    '''
    mesh_data = mesh.data
    vertices = np.array([v.co for v in mesh_data.vertices])
    faces = np.array([f.vertices for f in mesh_data.polygons])

    return vertices, faces


def compute_center_of_mass(vertices, faces, density):
    """
    Compute the center of mass of an object given its vertices, faces, and density.

    Args:
    =
    - vertices (numpy.ndarray): Array of vertices.
    - faces (numpy.ndarray): Array of faces.
    - density (float): Density of the object.

    Returns:
    =
    - center_of_mass (numpy.ndarray): Coordinates of the center of mass.
    """
    total_mass = 0
    center_of_mass = np.zeros(3)

    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normal = np.cross(v1 - v0, v2 - v0)
        area = 0.5 * np.linalg.norm(normal)
        centroid = (v0 + v1 + v2) / 3
        mass = density * area
        total_mass += mass
        center_of_mass += mass * centroid

    center_of_mass /= total_mass

    return center_of_mass


def find_furthest_point(vertices, center):
    """
    Find the furthest point from the center of mass of an object.

    Args:
    =
        - vertices (numpy.ndarray): Coordinates of the object vertices.
        - center (float): Coordiantes of the center of mass of the object.

    Returns:
    =
        - furthest_point (numpy.ndarray): Coordinates of the furthest point.
        - max_distance (float): Maximum distance from the center of mass.
    """
    #Calculate the furthest distance of each vertex from the center of mass.
    distances = [np.linalg.norm(vertex - center) for vertex in vertices]

    #Find the index of the furthest point.
    furthest_point_index = np.argmax(distances)

    return vertices[furthest_point_index], distances[furthest_point_index]


def compute_moments_of_inertia(vertices, faces):
    """
    Compute the moments of inertia of an object.

    Args:
    =
    - vertices (numpy.ndarray): Array of vertices.
    - faces (numpy.ndarray): Array of faces.

    Returns:
    =
    - total_inertia (numpy.ndarray): Moments of inertia matrix.
    """
    total_inertia = np.zeros((3, 3))
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normal = np.cross(v1 - v0, v2 - v0)
        inertia = np.outer(normal, normal)
        total_inertia += inertia

    return total_inertia


def diagonalize_inertia_matrix(moments_of_inertia):
    """
    Diagonalize the inertia matrix to find principal axes.

    Args:
    =
    - moments_of_inertia (numpy.ndarray): Moments of inertia matrix.

    Returns:
    =
    - inertia_matrix (numpy.ndarray): Diagonalized inertia matrix.
    - eigenvectors (numpy.ndarray): Eigenvectors corresponding to the principal axes.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(moments_of_inertia)

    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    inertia_matrix = np.diag(eigenvalues)

    return inertia_matrix, eigenvectors


def rotational_matrix(rotation_period, time_hours, eigenvectors):
    """
    Calculate the rotation matrix for simulating rotation.

    Args:
    =
    - w_x (float): Rotational velocity around z-axis in radians per second.
    - time_hours (float): Time elapsed in hours.
    - eigenvectors (numpy.ndarray): Eigenvectors of the diagonalized inertia matrix.

    Returns:
    =
    - R_aligned (numpy.ndarray): Aligned rotation matrix.
    """
    # Convert degrees to radians & vice versa
    rad2deg = 180 / np.pi
    deg2rad = np.pi / 180

    w = 2 * np.pi / rotation_period     # Rotational velocity (rad/h)    
    theta = w * time_hours #* rad2deg    # Angle of rotation (rad)
    k = np.array([0, 0, 1])             # Axis of rotation
    R = np.eye(3) + np.sin(theta) * np.cross(np.eye(3), k) + (1 - np.cos(theta)) * np.outer(k, k)

    # Verification of the rotation matrix
    # Compute K matrix
    K = np.array([[0, -k[2], k[1]],
                    [k[2], 0, -k[0]],
                    [-k[1], k[0], 0]])    

    # Compute R matrix using Rodrigues' formula
    R_check = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * np.dot(K, K)

    R_aligned = eigenvectors @ R @ np.linalg.inv(eigenvectors)  # Align the rotation matrix with the principal axes, R_aligned = V * R * V^(-1)

    return R_aligned


def update_rotation(previous_rotation, rotation_matrix):
    """
    Calculate the new rotation vector after applying the given rotation matrix.

    Args:
    - previous_rotation (numpy.ndarray): Previous rotation matrix.
    - rotation_matrix (numpy.ndarray): Rotation matrix to apply.

    Returns:
    - new_rotation (numpy.ndarray): New rotation vector.
    """
    new_rotation = rotation_matrix @ previous_rotation

    return new_rotation


def step_rotation(rotational_period, observation_time, previous_rotation, mesh):
    """
    Calculate the new rotation vector after a step of rotation.

    Args:
    =
    - rotational_period (float): Period of rotation in hours.
    - observation_time (float): Time elapsed in hours.
    - previous_rotation (numpy.ndarray): Previous rotation vector.

    Returns:
    =
    - new_rotation (numpy.ndarray): New rotation vector.
    """        
    # 1. Calculate the Center of Mass of the object ##############################
    # Read the vertices and faces of the mesh
    vertices, faces = get_single_mesh_data(mesh)

    # Calculate the Center of Mass  
    center_of_mass = compute_center_of_mass(vertices, faces, density=1.0)

    # 2. Calculate the Inertia Tensor of the object ##############################
    moments_of_inertia = compute_moments_of_inertia(vertices, faces)

    # 3. Diagonalize the Inertia Matrix
    inertia_matrix, eigenvectors = diagonalize_inertia_matrix(moments_of_inertia)

    # 4. Calculate rotation matrix  
    R = rotational_matrix(rotational_period, observation_time, eigenvectors)

    # 5. Apply rotation to the object
    new_rotation = update_rotation(previous_rotation, R)
    return new_rotation


def calculate_fov(sensor_width, sensor_height, focal_length):
    """
    Calculate the field of view (FOV) of a camera.

    Args:
    =
    - sensor_width (float): Width of the camera sensor.
    - sensor_height (float): Height of the camera sensor.
    - focal_length (float): Focal length of the camera lens.

    Returns:
    =
    - horizontal_fov (float): Horizontal field of view.
    - vertical_fov (float): Vertical field of view.
    """
    horizontal_fov = 2 * np.arctan(sensor_width / (2 * focal_length))
    vertical_fov = 2 * np.arctan(sensor_height / (2 * focal_length))

    return horizontal_fov, vertical_fov


def calculate_projected_dimensions(distance, horizontal_fov, vertical_fov):
    """
    Calculate the projected dimensions based on distance and FOV.

    Args:
    =
    - distance (float): Distance from the camera to the target.
    - horizontal_fov (float): Horizontal field of view.
    - vertical_fov (float): Vertical field of view.

    Returns:
    =
    - projected_width (float): Projected width.
    - projected_height (float): Projected height.
    """
    projected_width = 2 * distance * np.tan(horizontal_fov / 2)
    projected_height = 2 * distance * np.tan(vertical_fov / 2)
    
    return projected_width, projected_height


def calculate_initial_point(projected_width, projected_height, landing_mode=False):
    """
    Calculate the initial point based on the projected width and height.
    
    Args:
    =
    - projected_width (float): The width of the projected view.
    - projected_height (float): The height of the projected view.
    
    Returns:
    =
    - numpy.ndarray: The initial point coordinates.
    """

    return np.array([projected_width / 2, projected_height / 2, np.random.uniform(-projected_height, projected_height)])


def calculate_final_point(projected_width, projected_height, landing_mode=False):
    """
    Calculate the final point based on the projected width and height.
    
    Args:
    =
    - projected_width (float): The width of the projected view.
    - projected_height (float): The height of the projected view.
    - landing_mode (bool): Whether landing mode is activated.
    
    Returns:
    =
    - numpy.ndarray: The final point coordinates.
    """
    if landing_mode:
        # For landing mode, the final point is always the origin
        return np.array([0.0, 0.0, 0.0])
    else:
        # Original behavior for non-landing mode
        return np.array([-projected_width / 2, -projected_height / 2, np.random.uniform(-projected_height/8, projected_height/8)])


def init_final_point(projected_width, projected_height):
    """
    Initialize the initial and final points based on projected dimensions.

    Args:
    =
    - projected_width (float): Projected width.
    - projected_height (float): Projected height.

    Returns:
    =
    - init_point (numpy.ndarray): Initial point coordinates.
    - final_point (numpy.ndarray): Final point coordinates.
    """
    init_point = calculate_initial_point(projected_width, projected_height)
    final_point = calculate_final_point(projected_width, projected_height)

    return init_point, final_point
                    

def step_location(current_location, final_point, initial_point, samples):
    """
    Calculate the next location along a straight line based on a given initial point and total distance.
    
    Args:
    =
    - current_location (numpy.ndarray): Current location.
    # - total_distance (float): Total distance to cover. (being corrected)
    - final_point (numpy.ndarray): Final pint coordinates
    - initial_point (numpy.ndarray): Initial point coordinates.
    - samples (int): Number of steps/samples.

    Returns:
    =
    - next_location (numpy.ndarray): Next location along the straight line.
    """

    total_distance = np.linalg.norm(final_point - initial_point)
    direction_vector = (final_point - initial_point) / total_distance

    # Calculate the step distance
    if samples == 1:
        step_distance = total_distance
    else:
        step_distance = total_distance / (samples-1)


    # # Calculate the next location in the specified direction
    next_location = np.array(current_location) + step_distance * direction_vector

    # Calculate progress
    progress = np.linalg.norm(next_location - initial_point) / total_distance

    # Check if we've reached or passed the final point
    if progress >= 1.0:
        next_location = final_point
        
    return next_location