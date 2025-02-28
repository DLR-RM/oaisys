# Trajectory Generation for MeshAsteroid 

To generate the trajectory of any object, one must perform the following steps:

1. Calculate the object's center of mass with `compute_center_of_mass()`.
2. Calculate the moments of inertia around the object with `compute_moments_of_inertia()`.
3. Calculate the rotational matrix used to update the object's position later with `rotational_matrix()`.
4. Calculate the next rotation at the next step, taking the previous rotation and multiplying by the rotational matrix `update_rotation()`.

