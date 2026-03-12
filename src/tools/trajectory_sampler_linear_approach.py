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


def linear_approach_trajectory(n: int, sat_locs: np.ndarray, start_loc: np.ndarray, end_loc: Optional[np.ndarray],
                               v_start: float, v_end: float):
    """
    Linear approach trajectory. Will meet the satellite exactly after n steps.
    :param n: Number of steps to sample. Will collide with the satellite at the end.
    :param sat_locs: locations of the satellite in the format (t, 3) with t >= n
    :param start_loc: initial starting point of the camera
    :param end_loc: final ending point of the camera. if None, will take the satellite position as end point
    :param v_start: starting velocity
    :param v_end: ending velocity
    :return: (n, 4, 4) camera poses
    """
    assert sat_locs.ndim == 2 and sat_locs.shape[0] >= n and sat_locs.shape[1] == 3
    assert v_end <= v_start and v_end > 0

    if end_loc is None:
        end_loc = sat_locs[n]

    # Parameter s from 0 to 1 along the line
    s = np.linspace(0, 1, 1000)

    # Time to reach each s: integral of ds/v(s)
    # Integral of ds/v(s) analytically: t(s) = integral_0^s (1/v(x)) dx
    # Here v(x) = v_start + (v_end - v_start)*x = a + bx
    a = v_start
    b = v_end - v_start

    # Integral of 1/(a + b*s) ds = (1/b) * ln(a + b*s)
    # Time at s=0 is t0 = (1/b) * ln(a), time at s=1 is t1 = (1/b) * ln(a + b)
    # Normalize time to [0, 1]:
    t = (1/b) * np.log(a + b*s)
    t = (t - t[0]) / (t[-1] - t[0])

    # Now invert t(s) to get s(t). We'll sample uniformly spaced times t_i and find corresponding s_i
    t_uniform = np.linspace(0, 1, n)

    # Since t(s) is monotonic, interpolate inverse: s(t)
    s_non_linear = np.interp(t_uniform, t, s)

    # Now map s_non_linear to points on line
    points = start_loc + np.outer(s_non_linear, (end_loc - start_loc))

    return points