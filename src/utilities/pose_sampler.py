import math
import random

def get_cartesian_position_on_sphere(r, phi, theta):
    """ get cartesian position on sphere, provided polar coordinates. Note that mathematically phi can only take values
        from [0, 2pi). However, the function also allows the value of 2pi for easier implementation purposes
        Args:
            phi:                azimuth [0, 2pi]
            theta:              inclination [0, phi]
            r:                  radius of sphere
        Returns:
            cartesian position on the sphere x, y, z
    """
    assert r > 0.
    assert 0. <= theta <= math.pi
    assert 0. <= phi <= 2.*math.pi

    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)

    return x, y, z

def get_random_position_on_sphere(r, num_samples=1):
    """ get num_samples random cartesian position on sphere.
        Args:
            r:                  radius of sphere
            num_samples:        number of random cartesian positions to return
        Returns:
            list of cartesian position on the sphere [x, y, z]
    """
    assert r > 0.

    # init pose list
    pose_list = []

    # random sample on sphere
    for i in range(0, num_samples):
        pose_list.append(get_cartesian_position_on_sphere(r=r,
                                                          phi=random.random() * 2 * math.pi,
                                                          theta=random.random() * math.pi))
    return pose_list

def get_random_position_on_sphere_with_noise(r, r_noise=0.1, noise_value_type="relative", num_samples=1):
    """ get num_samples random cartesian position on sphere with radius and angles randomized.
        Args:
            r:                  radius of sphere
            r_noise:            noise value
            noise_value_type:   noise value type:   "absolute":   r_noise is treated as absolute value
                                                    "relative":   r_noise is treated as relative value from r
            num_samples:        number of random cartesian positions to return
        Returns:
            list of cartesian position on the sphere [x, y, z]
    """
    assert r > 0.
    assert 2.*r_noise < r if noise_value_type == "absolute" else True
    assert r_noise < 1.0 if noise_value_type == "relative" else True


    if noise_value_type == "relative":
        r_noise = r_noise * r

    # init pose list
    pose_list = []

    # random sample on sphere
    for i in range(0, num_samples):
        pose_list.append(get_cartesian_position_on_sphere(r=r + random.random() * r_noise - r_noise/2.,
                                                          phi=random.random() * 2 * math.pi,
                                                          theta=random.random() * math.pi))

    return pose_list