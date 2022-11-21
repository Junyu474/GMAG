import numpy as np
from dataclasses import dataclass
import warnings


@dataclass
class Galaxy:
    """Galaxy class"""
    _u: np.ndarray = np.empty(0)
    _g: np.ndarray = np.empty(0)
    _r: np.ndarray = np.empty(0)
    _i: np.ndarray = np.empty(0)
    _z: np.ndarray = np.empty(0)
    _jpg_data: np.ndarray = np.empty(0)

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
        """Return the data of the galaxy"""
        return self._u, self._g, self._r, self._i, self._z

    @data.setter
    def data(self, data):
        """Set the data of the galaxy"""
        self._u, self._g, self._r, self._i, self._z = data

    @property
    def jpg_data(self):
        """Return the jpg image of the galaxy"""
        return self._jpg_data

    @jpg_data.setter
    def jpg_data(self, jpg):
        """Set the jpg image of the galaxy"""
        self._jpg_data = jpg
