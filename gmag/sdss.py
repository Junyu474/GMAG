from .galaxy import Galaxy
import numpy as np
import requests
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from astropy.coordinates import SkyCoord
import warnings


def get_random_galaxy():
    """"""

    # Get a random galaxy objid
    objid = __get_random_galaxy_objid()
    # Get imaging data
    imaging_data = __get_galaxy_imaging_data(objid)
    # Get jpg image
    url = __get_galaxy_jpg_image(**imaging_data)
    print(url)
    # Get fits images data
    cutout_images = __get_galaxy_fits_images_data(**imaging_data)

    # Create galaxy instance
    galaxy = Galaxy()
    galaxy.data = cutout_images

    return galaxy


def __get_random_field():
    """Return random ra and dec (10 deg range, integer)
    need to exclude these fields:
        1. Dec in [-90, -30] for any RA
        2. Dec in [50, 90] and RA in [0, 20]
        3. Dec in [-30, -10] and RA in [140, 160]
        4. Dec in [70, 90] and RA in [200, 220]
    """
    # note: still cant guarantee the field can hit a galaxy
    # but this 10x10 deg size has a small enough request time (~1s)
    # increase field size to 20x20 will increase request time to ~10s
    # current solution is to handled in __get_random_galaxy_objid

    # Start from region excluding field 1, then check for 2,3,4
    while True:
        ra = np.random.randint(0, 350)
        dec = np.random.randint(-30, 80)

        if (50 < dec < 90 and 0 < ra < 20) or \
                (-30 < dec < -10 and 140 < ra < 160) or \
                (70 < dec < 90 and 200 < ra < 220):
            continue
        else:
            return ra, ra + 10, dec, dec + 10


def __get_random_galaxy_objid():
    """Request random galaxy from SDSS in a random field"""

    # random field could potentially not have a galaxy, try again if so
    while True:
        # Get random field
        ra_min, ra_max, dec_min, dec_max = __get_random_field()

        # Get random objid
        req = requests.get(f"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                           f"SELECT TOP 1 g.objid FROM Galaxy AS g "
                           f"WHERE g.ra BETWEEN {ra_min} AND {ra_max} AND g.dec BETWEEN {dec_min} AND {dec_max} "
                           f"ORDER BY NEWID()")

        if len(req.json()[0]['Rows']) == 0:
            continue

        return req.json()[0]['Rows'][0]['objid']


def __get_galaxy_imaging_data(objid):
    """Get imaging data (run, camcol, field, ra, dec, petroR90_r) for a given galaxy objid"""

    # Get imaging data
    req = requests.get(f"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                       f"SELECT run, camcol, field, ra, dec, petroRad_r FROM Galaxy "
                       f"WHERE objid = {objid}")

    return req.json()[0]['Rows'][0]


def __get_galaxy_jpg_image(run, camcol, field, ra, dec, petroRad_r):
    """Get jpg image for a given galaxy imaging data"""

    # TODO: cutout image

    return f"https://dr17.sdss.org/sas/dr17/eboss/photoObj/frames/301/" \
           f"{run}/{camcol}/frame-irg-{run:06d}-{camcol}-{field:04d}.jpg"


def __get_galaxy_fits_images_data(run, camcol, field, ra, dec, petroRad_r):
    """Get fits images data for a given galaxy imaging data"""

    # TODO: make this async

    cutout_images = []
    r = petroRad_r/3600  # convert to deg

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

        print(f"cutout radius: {cutout_radius}")

        # Get cutout, indices in integer
        min_y, max_y = int(y - cutout_radius), int(y + cutout_radius)
        min_x, max_x = int(x - cutout_radius), int(x + cutout_radius)
        cutout_image = hdu[0].data[min_y:max_y, min_x:max_x]

        cutout_images.append(cutout_image)

    # Return cutout image
    return cutout_images
