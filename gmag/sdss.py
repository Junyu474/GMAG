import warnings
from multiprocessing import Pool
from urllib.request import urlopen

import numpy as np
import requests
from PIL import Image
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table as AstropyTable
from astropy.wcs import WCS, FITSFixedWarning
from tqdm import tqdm

from .galaxy import Galaxy


def get_random_galaxy(verbose=True):
    """Get random galaxy from SDSS

    :param verbose: show verbose, defaults to True
    """
    # Create galaxy instance
    galaxy = Galaxy()

    # Get a random galaxy objid
    objid = __get_random_galaxy_objid()

    # Get imaging data
    imaging_data = __get_galaxy_imaging_data(objid)

    # Set galaxy objid, ra, and dec
    galaxy.objid = str(objid)
    galaxy.ra, galaxy.dec = imaging_data['ra'], imaging_data['dec']

    if verbose:
        print("Fetching...", end='')

    # Get jpg image
    jpg_data = __get_galaxy_jpg_image(imaging_data['ra'], imaging_data['dec'], imaging_data['petroRad_r'])
    galaxy.jpg_data = jpg_data

    if verbose:
        print("\rStill fetching ugriz data..., here is a preview:")
        galaxy.preview()

    # Get fits images urls
    fits_urls = [__get_url_from_imaging_data(imaging_data['run'], imaging_data['camcol'], imaging_data['field'], band)
                 for band in 'ugriz']

    # Get cutout fits images data using multiprocessing
    params = [(url, imaging_data['ra'], imaging_data['dec'], imaging_data['petroRad_r'])
              for url in fits_urls]
    with Pool(5) as p:
        cutout_images = p.starmap(__cutout_galaxy_fits_image, params)
    galaxy.data = cutout_images

    if verbose:
        print("\rDone!")

    return galaxy


def download_images(file, ra_col_name='ra', dec_col_name='dec', bands='ugriz', max_search_radius=8,
                    num_workers=16, progress_bar=True, verbose=False):
    """Read ra dec from file and download galaxy fits images

    :param file: file path, any format readable by astropy.table.Table, with columns ra and dec
    :param ra_col_name: name of ra column, defaults to 'ra'
    :param dec_col_name: name of dec column, defaults to 'dec'
    :param bands: bands to download, can be a string (e.g. 'gri') or a list (e.g. ['g', 'r', 'i']), default is 'ugriz'
    :param max_search_radius: max search radius in arcmimutes, defaults to 10
    :param num_workers: number of workers for multiprocessing, defaults to 16
    :param progress_bar: show progress bar, defaults to True
    :param verbose: show verbose, defaults to False
    """

    # Check if bands are valid
    if isinstance(bands, str):
        bands = list(bands)
    elif not isinstance(bands, list):
        raise ValueError("bands must be a string or a list")

    for band in bands:
        if band not in 'ugriz':
            raise ValueError(f"Invalid band {band}")

    # Try to open fits file
    try:
        table = AstropyTable.read(file)
    except OSError:
        raise OSError(f"Could not open file {file}")

    # Try to get ra and dec columns
    try:
        ra_list = table[ra_col_name]
        dec_list = table[dec_col_name]
    except KeyError:
        raise KeyError(f"Could not find ra column '{ra_col_name}' or dec column '{dec_col_name}' in file {file}")

    # Create args for multiprocessing in searching nearby galaxies
    args = list(zip(ra_list, dec_list, [max_search_radius] * len(ra_list)))

    # Create pool of workers to search for galaxies, track progress with tqdm if progress_bar is True
    with Pool(num_workers) as pool:
        obj_ids = list(tqdm(pool.imap(__search_nearby_galaxy_objid_wrapper, args),
                            total=len(args), disable=not progress_bar,
                            desc="Searching galaxies", unit="obj"))

    found_gal_row_ids = [i for i, obj_id in enumerate(obj_ids) if obj_id is not None]

    if verbose:
        print(f"Found {len(found_gal_row_ids)} out of {len(obj_ids)} galaxies")


def __get_random_galaxy_objid():
    """Request random galaxy from SDSS in a random field

    :return: galaxy objid
    """

    # Get random objid
    req = requests.get(f"http://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
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
    req = requests.get(f"http://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
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

    url = f"http://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg?" \
          f"ra={ra}&dec={dec}&scale={scale}&width={img_size}&height={img_size}"

    # Read jpg image url into numpy array
    jpg_data = np.asarray(Image.open(urlopen(url)))
    return jpg_data


def __get_url_from_imaging_data(run, camcol, field, band):
    """Get fits image url from imaging data

    :param run: run
    :param camcol: camcol
    :param field: field
    :param band: band

    :return: fits image url
    """

    url = f"http://dr17.sdss.org/sas/dr17/eboss/photoObj/frames/301/" \
          f"{run}/{camcol}/frame-{band}-{run:06d}-{camcol}-{field:04d}.fits.bz2"
    return url


def __cutout_galaxy_fits_image(fits_file, ra, dec, petro_r):
    """Cutout galaxy fits image

    :param fits_file: fits file path, can be a local file or an url
    :param ra: right ascension of the target, in degrees
    :param dec: declination of the target, in degrees
    :param petro_r: Petrosian radius of the target, in arcsec

    :return: cutout image data in numpy array
    """

    r = petro_r / 3600  # convert to degrees

    # Read fits file
    hdu = fits.open(fits_file, cache=False)

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

    return cutout_image


def __search_nearby_galaxy_objid_wrapper(args):
    """Wrapper for __search_nearby_galaxy_objid for multiprocessing

    :param args: tuple of ra, dec, max_search_radius, verbose
    """

    return __search_nearby_galaxy_objid(*args)


def __search_nearby_galaxy_objid(ra, dec, max_search_radius, verbose=False):
    """Search for a galaxy by ra dec and return objid

    Use the fGetNearbyObjEq function from the SDSS SkyServer API.
    Start with a search radius of 1 arcmin and double the radius until over the max_search_radius.
    If max_search_radius is not power of 2, try one last search at max_search_radius.

    :param ra: right ascension, in degrees
    :param dec: declination, in degrees
    :param max_search_radius: maximum search radius, in arcmin
    :param verbose: print message if not found, defaults to False

    :return: objid of nearby galaxy or None if no galaxy found
    """

    search_radius = 1
    while search_radius < max_search_radius:
        req = requests.get(f"http://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                           f"SELECT TOP 1 G.objid "
                           f"FROM Galaxy as G JOIN dbo.fGetNearbyObjEq({ra}, {dec}, {search_radius}) AS GN "
                           f"ON G.objID = GN.objID "
                           f"ORDER BY GN.distance")
        if req.json()[0]['Rows']:
            return req.json()[0]['Rows'][0]['objid']
        search_radius *= 2

    # Try one last search at max_search_radius
    if search_radius * 2 != max_search_radius:
        req = requests.get(f"http://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                           f"SELECT TOP 1 G.objid "
                           f"FROM Galaxy as G JOIN dbo.fGetNearbyObjEq({ra}, {dec}, {max_search_radius}) AS GN "
                           f"ON G.objID = GN.objID "
                           f"ORDER BY GN.distance")
        if req.json()[0]['Rows']:
            return req.json()[0]['Rows'][0]['objid']

    if verbose:
        print(f"No nearby galaxy found within {max_search_radius} arcmin")

    return None
