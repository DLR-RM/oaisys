# utility imports
import numpy as np

class CDistance2Depth(object):
    """docstring for CDistance2Depth"""
    def __init__(self, arg):
        super(CDistance2Depth, self).__init__()
        self.arg = arg
        # focal length
        self._f_px = np.zeros((2))  # f_x and f_y [px]
        self._f_mm = np.zeros((2))  # f_x and f_y [mm]

        # central point
        self._c_px = np.zeros((2))  # c_x and c_y [px]
        self._c_mm = np.zeros((2))  # c_x and c_y [mm]

        # baseline
        self._b_px = 0.0            # baseline [px]
        self._b_px = 0.0            # baseline [mm]

    def setupNodes(self):
        pass

    def setCameraParameters(self,params):
        pass

    def getDepthFromDistance(self, distanceImage):
        pass

    def getDisparityFromDistance(self, distanceImage):
        pass