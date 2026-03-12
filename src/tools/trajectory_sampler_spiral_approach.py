from typing import Union, Optional, List
import numpy as np
from mathutils import Matrix, Vector, Euler

def sample_points_on_circle(radius, n):
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)  # n angles from 0 to 2pi
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    points = np.vstack((x, y, np.zeros_like(x))).T  # Shape (n, 3)
    return points


# from blenderproc
def build_transformation_mat(translation: Union[np.ndarray, List[float], Vector],
                             rotation: Union[np.ndarray, List[List[float]], Matrix]) -> np.ndarray:
    """ Build a transformation matrix from translation and rotation parts.

    :param translation: A (3,) vector representing the translation part.
    :param rotation: A 3x3 rotation matrix or Euler angles of shape (3,).
    :return: The 4x4 transformation matrix.
    """
    translation = np.array(translation)
    rotation = np.array(rotation)

    mat = np.eye(4)
    if translation.shape[0] == 3:
        mat[:3, 3] = translation
    else:
        raise RuntimeError(f"Translation has invalid shape: {translation.shape}. Must be (3,) or (3,1) vector.")
    if rotation.shape == (3, 3):
        mat[:3, :3] = rotation
    elif rotation.shape[0] == 3:
        mat[:3, :3] = np.array(Euler(rotation).to_matrix())
    else:
        raise RuntimeError(f"Rotation has invalid shape: {rotation.shape}. Must be rotation matrix of shape "
                           f"(3,3) or Euler angles of shape (3,) or (3,1).")

    return mat


# from blenderproc
def rotation_from_forward_vec(forward_vec: Union[np.ndarray, Vector], up_axis: str = 'Y',
                              inplane_rot: Optional[float] = None) -> np.ndarray:
    """ Returns a camera rotation matrix for the given forward vector and up axis

    :param forward_vec: The forward vector which specifies the direction the camera should look.
    :param up_axis: The up axis, usually Y.
    :param inplane_rot: The inplane rotation in radians. If None is given, the inplane rotation is determined only
                        based on the up vector.
    :return: The corresponding rotation matrix.
    """
    rotation_matrix = Vector(forward_vec).to_track_quat('-Z', up_axis).to_matrix()
    if inplane_rot is not None:
        rotation_matrix @= Euler((0.0, 0.0, inplane_rot)).to_matrix()
    return np.array(rotation_matrix)


def spiral_approach_trajectory(n: int, sat_locs: np.ndarray, r_start: float, r_end: float,
                      plane: str, rotations: int):
    """
    Spiral approach trajectory. Will spiral around the satellite exactly once with linear velocity.
    :param n: Number of steps to sample. Will collide with the satellite at the end.
    :param sat_locs: locations of the satellite in the format (t, 3) with t >= n
    :param start_loc: initial starting point of the camera
    :param end_loc: final ending point of the camera. if None, will take the satellite position as end point
    :return: (n, 4, 4) camera poses
    """
    assert sat_locs.ndim == 2 and sat_locs.shape[0] >= n and sat_locs.shape[1] == 3
    assert r_start > 0 and r_end > 0
    radii = np.linspace(r_start, r_end, n)

    # Angles from 0 to rotations * 2pi
    angles = np.linspace(0, 2 * np.pi * rotations, n)

    # Calculate spiral points relative to target
    offset_x = radii * np.sin(angles)
    offset_y = -radii * np.cos(angles)

    if plane == 'xy':
        offsets = np.vstack((offset_x, offset_y, np.zeros_like(offset_x))).T
    elif plane == 'xz':
        offsets = np.vstack((offset_x, np.zeros_like(offset_x), offset_y)).T
    elif plane == 'yz':
        offsets = np.vstack((np.zeros_like(offset_x), offset_x, offset_y)).T
    else:
        raise NotImplementedError(f"Unknown plane: {plane}")

    # Add offsets to target positions
    spiral_positions = sat_locs[:n] + offsets

    return spiral_positions