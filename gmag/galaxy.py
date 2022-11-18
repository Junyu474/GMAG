import numpy as np
from dataclasses import dataclass
import warnings

@dataclass
class Galaxy:
    """Galaxy class"""
    u: np.ndarray = np.empty(0)
    g: np.ndarray = np.empty(0)
    r: np.ndarray = np.empty(0)
    i: np.ndarray = np.empty(0)
    z: np.ndarray = np.empty(0)

    _name: str = ""
    redshift: float = 0.0
    ra: float = 0.0
    dec: float = 0.0

    @property
    def name(self):
        """Name of the galaxy"""
        return self._name

    @name.setter
    def name(self, name):
        """Set the name of the galaxy"""
        if len(name) > 35:
            warnings.warn("Name is too long, would be truncated in info method.")

        self._name = name

    def info(self):
        """Print out the information of the galaxy"""
        return f"Name: {self.name:>40.35s}\n" \
               f"Redshift: {self.redshift:>36.5f}\n" \
               f"RA: {self.ra:>42.5f}\n" \
               f"DEC: {self.dec:>41.5f}\n"

    @property
    def data(self):
        return np.array([self.u, self.g, self.r, self.i, self.z])
