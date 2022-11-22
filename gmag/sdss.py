import warnings
from urllib.request import urlopen

import numpy as np
import requests
from PIL import Image
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning

from .galaxy import Galaxy


def get_random_galaxy():
    """"""

    # Get a random galaxy objid
    objid = __get_random_galaxy_objid()
    print(f"objid: {objid}")
    # Get imaging data
    imaging_data = __get_galaxy_imaging_data(objid)
    # Get jpg image
    jpg_data = __get_galaxy_jpg_image(imaging_data['ra'], imaging_data['dec'], imaging_data['petroRad_r'])
    # Get fits images data
    cutout_images = __get_galaxy_fits_images_data(**imaging_data)

    # Create galaxy instance
    galaxy = Galaxy()
    galaxy.jpg_data = jpg_data
    galaxy.data = cutout_images

    return galaxy


def __get_random_galaxy_objid():
    """Request random galaxy from SDSS in a random field"""

    # Get random objid
    req = requests.get(f"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                       f"SELECT TOP 1 g.objid FROM Galaxy AS g "
                       f"JOIN ZooNoSpec as z ON g.objid = z.objid "
                       f"WHERE g.clean = 1 AND g.petroRad_r>12 AND g.petroRadErr_r!=-1000 "
                       f"ORDER BY NEWID()")

    return req.json()[0]['Rows'][0]['objid']


def __get_galaxy_imaging_data(objid):
    """Get imaging data for a given galaxy objid

    :param objid: galaxy ssds dr17 objid

    :return: dict with imaging data (run, camcol, field, ra, dec, petroRad_r)
    """

    # Get imaging data
    req = requests.get(f"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                       f"SELECT run, camcol, field, ra, dec, petroRad_r FROM Galaxy "
                       f"WHERE objid = {objid}")

    return req.json()[0]['Rows'][0]


def __get_galaxy_jpg_image(ra, dec, petroRad_r):
    """Get jpg image for a given galaxy imaging data

    :param ra: right ascension, in degrees
    :param dec: declination, in degrees
    :param petroRad_r: Petrosian radius, in arcsec
    """

    # Compute scale, defined as "/pix
    # Fix image size 2*1.25*radius arcsec
    img_size = 256
    scale = 2 * 1.25 * petroRad_r / img_size

    url = f"https://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg?" \
          f"ra={ra}&dec={dec}&scale={scale}&width={img_size}&height={img_size}"

    # Read jpg image url into numpy array
    jpg_data = np.asarray(Image.open(urlopen(url)))
    return jpg_data


def __get_galaxy_fits_images_data(run, camcol, field, ra, dec, petroRad_r):
    """Get fits images data for a given galaxy imaging data

    :param run: the run number, which identifies the specific scan
    :param camcol: the camera column, a number from 1 to 6, identifying the scanline within the run
    :param field: the field number
    :param ra: right ascension, in degrees
    :param dec: declination, in degrees
    :param petroRad_r: Petrosian radius, in arcsec
    """

    cutout_images = []
    r = petroRad_r / 3600  # convert to deg

    for band in ['u', 'g', 'r', 'i', 'z']:
        url = f"https://dr17.sdss.org/sas/dr17/eboss/photoObj/frames/301/" \
              f"{run}/{camcol}/frame-{band}-{run:06d}-{camcol}-{field:04d}.fits.bz2"

        # Read fits file
        hdu = fits.open(url, cache=False)

        # Read wcs, ignore warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FITSFixedWarning)
            wcs = WCS(hdu[0].header)

        # Compute cutout size
        coord = SkyCoord(ra, dec, unit='deg')
        edge_coord = SkyCoord(ra + r, dec + r, unit='deg')
        x, y = wcs.world_to_pixel(coord)
        x_edge, y_edge = wcs.world_to_pixel(edge_coord)
        # radius is max of x and y, cutout radius is 1.25*radius rounded up to nearest 10
        radius = max(abs(x - x_edge), abs(y - y_edge))
        cutout_radius = int(np.ceil(1.25 * radius / 10) * 10)

        # Get cutout, indices in integer
        min_y, max_y = int(y - cutout_radius), int(y + cutout_radius)
        min_x, max_x = int(x - cutout_radius), int(x + cutout_radius)
        cutout_image = hdu[0].data[min_y:max_y, min_x:max_x]

        cutout_images.append(cutout_image)

    # Return cutout image
    return cutout_images
