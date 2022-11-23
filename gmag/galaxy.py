from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt


@dataclass
class Galaxy:
    """Galaxy class"""
    _u: np.ndarray = np.empty(0)
    _g: np.ndarray = np.empty(0)
    _r: np.ndarray = np.empty(0)
    _i: np.ndarray = np.empty(0)
    _z: np.ndarray = np.empty(0)
    _jpg_data: np.ndarray = np.empty(0)

    _objid: str = None
    _ra: float = 0.0
    _dec: float = 0.0

    def __repr__(self):
        return f"Galaxy[{self._objid}]"

    @property
    def objid(self):
        """The objid of the galaxy"""
        return self._objid

    @objid.setter
    def objid(self, objid):
        """Set the objid of the galaxy"""
        self._objid = objid

    @property
    def ra(self):
        """The RA of the galaxy"""
        return self._ra

    @ra.setter
    def ra(self, ra):
        """Set the RA of the galaxy"""
        self._ra = ra

    @property
    def dec(self):
        """The DEC of the galaxy"""
        return self._dec

    @dec.setter
    def dec(self, dec):
        """Set the DEC of the galaxy"""
        self._dec = dec

    @property
    def data(self):
        """Return the data of the galaxy"""
        return self._u, self._g, self._r, self._i, self._z

    @data.setter
    def data(self, data):
        """Set the data of the galaxy"""
        self._u, self._g, self._r, self._i, self._z = data

    @property
    def u(self):
        """Return the u-band data of the galaxy"""
        return self._u

    @property
    def g(self):
        """Return the g-band data of the galaxy"""
        return self._g

    @property
    def r(self):
        """Return the r-band data of the galaxy"""
        return self._r

    @property
    def i(self):
        """Return the i-band data of the galaxy"""
        return self._i

    @property
    def z(self):
        """Return the z-band data of the galaxy"""
        return self._z

    @property
    def jpg_data(self):
        """Return the jpg image of the galaxy"""
        return self._jpg_data

    @jpg_data.setter
    def jpg_data(self, jpg):
        """Set the jpg image of the galaxy"""
        self._jpg_data = jpg

    def info(self):
        """Print out the information of the galaxy"""
        print(f"SDSS DR17 ObjID: {self.objid:>25.25s}\n"
              f"RA(deg): {self.ra:>33.5f}\n"
              f"DEC(deg): {self.dec:>32.5f}")

    def preview(self):
        """Show the preview jpg image of the galaxy with dpi=40"""

        if self._jpg_data.size == 0:
            raise ValueError("No jpg data found.")
        else:
            plt.figure(dpi=40)
            plt.axis('off')
            plt.imshow(self._jpg_data)
            plt.show()

    def show(self):
        """Show the jpg image of the galaxy with dpi=100"""

        if self._jpg_data.size == 0:
            raise ValueError("No jpg data found.")
        else:
            plt.figure(dpi=100)
            plt.axis('off')
            plt.imshow(self._jpg_data)
            plt.show()

    def show_band(self, band, cmap='viridis', high_contrast=False, colorbar=False):
        """Show a band of the galaxy image

        :param band: the band to show
        :param cmap: the colormap to use
        :param high_contrast: whether to use high contrast
        :param colorbar: whether to show the colorbar
        """

        if self._jpg_data.size == 0:
            raise ValueError("No jpg data found.")
        elif band not in ['u', 'g', 'r', 'i', 'z']:
            raise ValueError(f"{band} is not a valid band. Please choose from u, g, r, i, z.")
        else:
            clim = None if not high_contrast else (np.percentile(getattr(self, band), 1),
                                                   np.percentile(getattr(self, band), 99))
            plt.figure(figsize=(2.5, 2.5))
            plt.imshow(getattr(self, band), cmap=cmap, clim=clim)
            plt.title(f"{band}-band")
            if colorbar:
                plt.colorbar()
            plt.show()

    def show_all_bands(self, cmap='viridis', high_contrast=False, colorbar=False):
        """Show all bands of the galaxy image

        :param cmap: the colormap to use
        :param high_contrast: whether to use high contrast
        :param colorbar: whether to show the colorbar
        """

        if self._jpg_data.size == 0:
            raise ValueError("No jpg data found.")
        else:
            fig, axs = plt.subplots(1, 5, figsize=(15, 3))
            for i, band in enumerate(['u', 'g', 'r', 'i', 'z']):
                clim = None if not high_contrast else (np.percentile(self.data, 1),
                                                       np.percentile(self.data, 99))
                axs[i].imshow(getattr(self, band), cmap=cmap, clim=clim)
                axs[i].set_title(f"{band}")
                axs[i].axis('off')

            if colorbar:
                fig.colorbar(axs[0].get_images()[0], ax=axs.ravel().tolist())

            plt.show()
