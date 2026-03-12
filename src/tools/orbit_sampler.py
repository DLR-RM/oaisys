"""
Function to sample different orbital parameters.
"""

import numpy as np

EARTH_RADIUS_KM_XYZ = (6378.0, 6378.0, 6378.0)  # Idealized Earth as sphere

ORBIT_ALTITUDES = {
    'LEO': (200, 2000),
    'MEO': (2000, 35785),
    'GEO': (35786, 35786),  # fixed altitude
    'Polar': (700, 1700),   # usually within LEO altitudes
    'SSO': (600, 800)
}


def sample_orbit_parameters(orbit_type='LEO', earth_radius_km_xyz=EARTH_RADIUS_KM_XYZ):
    """
    Samples scale and orientation for an orbit type.

    Parameters:
        orbit_type (str): One of 'LEO', 'MEO', 'GEO', 'Polar', 'SSO'
        earth_radius_km_xyz (float, float, float): Radius of the planetary body (default: Earth's radius)

    Returns:
        dict: {
            'scale_xyz': np.array([x, y, z]),
            'rotation_rpy': np.array([r, p, y])
        }
    """
    if orbit_type not in ORBIT_ALTITUDES:
        raise ValueError(f"Unsupported orbit type: {orbit_type}")

    min_alt, max_alt = ORBIT_ALTITUDES[orbit_type]
    altitude = np.random.uniform(min_alt, max_alt)

    if orbit_type == 'Polar':
        rotation_rpy = (np.random.uniform(np.deg2rad(80), np.deg2rad(100)), 0., np.random.uniform(-np.pi, np.pi))
    else:
        rotation_rpy = (np.random.uniform(-np.pi, np.pi), 0., np.random.uniform(-np.pi, np.pi))

    return {
        'scale_xyz': (altitude + np.array(earth_radius_km_xyz)) / np.array(earth_radius_km_xyz),
        'rotation_rpy': np.array(rotation_rpy)
    }