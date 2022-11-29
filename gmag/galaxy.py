from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt


@dataclass(frozen=True)
class Galaxy:
    """Galaxy class (read only)"""
    objid: str

    u: np.ndarray
    g: np.ndarray
    r: np.ndarray
    i: np.ndarray
    z: np.ndarray
    jpg_data: np.ndarray

    ra: float
    dec: float

    def __repr__(self):
        return f"Galaxy[{self.objid}]"

    @property
    def data(self):
        """Return the ugriz data of the galaxy"""
        return np.array([self.u, self.g, self.r, self.i, self.z])

    def info(self):
        """Print out the information of the galaxy"""
        print(f"SDSS DR17 ObjID: {self.objid:>25.25s}\n"
              f"RA(deg): {self.ra:>33.5f}\n"
              f"DEC(deg): {self.dec:>32.5f}")

    def preview(self):
        """Show the preview jpg image of the galaxy with dpi=40"""

        plt.figure(dpi=40)
        plt.axis('off')
        plt.imshow(self.jpg_data)
        plt.show()

    def show(self):
        """Show the jpg image of the galaxy with dpi=100"""

        plt.figure(dpi=100)
        plt.axis('off')
        plt.imshow(self.jpg_data)
        plt.show()

    def show_band(self, band, cmap='viridis', high_contrast=False, colorbar=False):
        """Show a band of the galaxy image

        :param band: the band to show
        :param cmap: the colormap to use
        :param high_contrast: whether to use high contrast
        :param colorbar: whether to show the colorbar
        """

        if band not in ['u', 'g', 'r', 'i', 'z']:
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
