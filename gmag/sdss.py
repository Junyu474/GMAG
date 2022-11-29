import bz2
import csv
import pathlib
import shutil
import warnings
from datetime import datetime
from multiprocessing import Pool
from urllib.request import urlopen

import numpy as np
import requests
from PIL import Image
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table as AstropyTable
from astropy.wcs import WCS, FITSFixedWarning
from matplotlib import pyplot as plt
from tqdm.auto import tqdm

from . import _print_util as pu
from .galaxy import Galaxy


def get_random_galaxy(verbose=True):
    """Get a random galaxy from SDSS

    Parameters
    ----------
    verbose: `bool`, default=True
        Whether to print progress

    Returns
    -------
    galaxy: `.Galaxy`
        Galaxy object

    Notes
    -----
    If not running in a notebook, must run in `__main__` to avoid multiprocessing issues
    """

    # Get a random galaxy objid
    objid = __get_random_galaxy_objid()

    # Get imaging data
    imaging_data = __get_galaxy_imaging_data(objid)

    pu.verbose_print(verbose, "Fetching...", end='')

    # Get jpg image
    jpg_data = __get_galaxy_jpg_image(imaging_data['ra'], imaging_data['dec'], imaging_data['petroRad_r'])

    if verbose:
        print("\rStill fetching ugriz data..., here is a preview:")
        plt.figure(dpi=40)
        plt.axis('off')
        plt.imshow(jpg_data)
        plt.show()

    # Get fits images urls
    fits_urls = [__get_url_from_imaging_data(imaging_data['run'], imaging_data['camcol'], imaging_data['field'], band)
                 for band in 'ugriz']

    # Get cutout fits images data using multiprocessing
    params = [(url, imaging_data['ra'], imaging_data['dec'], imaging_data['petroRad_r'])
              for url in fits_urls]
    with Pool(5) as p:
        cutout_images = p.starmap(__cutout_galaxy_fits_image, params)

    galaxy = Galaxy(
        objid=str(objid),
        u=cutout_images[0],
        g=cutout_images[1],
        r=cutout_images[2],
        i=cutout_images[3],
        z=cutout_images[4],
        jpg_data=jpg_data,
        ra=imaging_data['ra'],
        dec=imaging_data['dec'],
    )

    pu.verbose_print(verbose, "Done!")

    return galaxy


def download_images(file, ra_col='ra', dec_col='dec', bands='ugriz', max_search_radius=8, cutout=True,
                    name_col=None, num_workers=16, progress_bar=True, verbose=True, info_file=True):
    """Read ra dec from file and download galaxy fits images

    Parameters
    ----------
    file: `str` or `pathlib.Path`
        File to read ra dec from
    ra_col: `str`, default='ra'
        Name of ra column
    dec_col: `str`, default='dec'
        Name of dec column
    bands: `str`, default='ugriz'
        Bands to download
    max_search_radius: `float`, default=8
        Maximum search radius in arcmin
    cutout: `bool`, default=True
        Whether to cutout images
    name_col: `str`, default=None
        Name of galaxy name column
    num_workers: `int`, default=16
        Number of workers to use
    progress_bar: `bool`, default=True
        Whether to show progress bar
    verbose: `bool`, default=True
        Whether to print progress
    info_file: `bool`, default=True
        Whether to save info file

    Raises
    ------
    ValueError
        Raised if bands is invalid
    OSError
        Raised if can not read file
    KeyError
        Raised if ra or dec column is not found in file

    Notes
    -----
    If not running in a notebook, must run in `__main__` to avoid multiprocessing issues
    """

    # 1. Check if bands are valid
    if isinstance(bands, str):
        bands = list(bands)
    elif not isinstance(bands, list):
        raise ValueError("bands must be a string or a list")

    for band in bands:
        if band not in 'ugriz':
            raise ValueError(f"Invalid band {band}")

    # 2. Try to open fits file
    try:
        table = AstropyTable.read(file)
    except OSError:
        raise OSError(f"Could not open file {file}")

    # 3. Try to get ra and dec columns
    try:
        orig_ra_list = table[ra_col]
        orig_dec_list = table[dec_col]
    except KeyError:
        raise KeyError(f"Could not find ra column '{ra_col}' or dec column '{dec_col}' in file {file}")

    # 4. Create search_args for multiprocessing, and search for galaxies, track progress by tqdm
    search_args = list(zip(orig_ra_list, orig_dec_list, [max_search_radius] * len(orig_ra_list)))
    with Pool(num_workers) as pool:
        # galaxies is a list of tuples (ra, dec, objid, run, camcol, field), can be None, in order of original table
        galaxies = list(tqdm(pool.imap(__search_nearby_galaxy_wrapper, search_args),
                             total=len(search_args), disable=not progress_bar,
                             desc="Searching galaxies", unit="obj"))

    found_gal_row_ids = [i for i, g in enumerate(galaxies) if g is not None]

    pu.verbose_print(verbose, f"...Found {len(found_gal_row_ids)} out of {len(galaxies)} galaxies")

    # 5. Try to get name column, if None, use rowid_objid
    if name_col is not None:
        try:
            names = table[name_col]
            # Replace empty names with unknown_rowid
            names = [name if name else f"unknown_rowid_{i}" for i, name in enumerate(names)]
            # Check if names are unique
            if len(set(names)) != len(names):
                raise ValueError()
        except KeyError:
            print(pu.red(f"Could not find name column '{name_col}' in file {file}, using rowid_objid instead"))
            names = [f"{i}_{g['objid']}" if g is not None else None for i, g in enumerate(galaxies)]
        except ValueError:
            print(pu.red(f"Names are not unique, using rowid_objid instead"))
            names = [f"{i}_{g['objid']}" if g is not None else None for i, g in enumerate(galaxies)]
    else:
        names = [f"{i}_{g['objid']}" if g is not None else None for i, g in enumerate(galaxies)]

    # 6. Create output parent directory
    parent_dir = pathlib.Path.cwd() / f"images_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    parent_dir.mkdir()
    pu.verbose_print(verbose, f"...Created directories for images at {pu.blue(parent_dir)}")

    # 7. Prepare download args for multiprocessing, create output directories
    download_args = []
    for i, gal in enumerate(galaxies):
        if gal is None:
            continue

        target_dir = parent_dir / names[i]
        target_dir.mkdir()
        for band in bands:
            url = __get_url_from_imaging_data(gal['run'], gal['camcol'], gal['field'], band)
            file_path = target_dir / f"{band}.fits"
            if cutout:
                download_args.append((url, target_dir / file_path, gal['ra'], gal['dec'], gal['petroRad_r']))
            else:
                download_args.append((url, target_dir / file_path))

    # 8. Download images # TODO: flag if petroRad_err is -1000
    download_func = __download_fits_image_with_cutout_wrapper if cutout else __download_fits_image_wrapper
    with Pool(num_workers) as pool:
        return_val = list(tqdm(pool.imap(download_func, download_args),
                               total=len(download_args), disable=not progress_bar,
                               desc="Downloading images", unit="img"))

    # 9. Create cutout shape column based on return value
    if cutout:
        # return_val is list of shapes in order, same galaxy will have duplicate shapes for each band, only keep one
        found_cutout_shapes = [shape for i, shape in enumerate(return_val) if i % len(bands) == 0]
        # Create column for cutout shape including not found galaxies
        cutout_shapes = [None] * len(galaxies)
        for i, shape in zip(found_gal_row_ids, found_cutout_shapes):
            cutout_shapes[i] = shape
    else:
        cutout_shapes = ['Uncut'] * len(galaxies)

    # 10. Save info file
    if info_file:
        pu.verbose_print(verbose, f"...Saving info file at {pu.blue(parent_dir / 'info.csv')}")
        with open(parent_dir / 'info.csv', 'w') as f:
            # Write comments on top
            f.write(f"# Found {len(found_gal_row_ids)} out of {len(galaxies)} galaxies in {file}\n")
            if cutout:
                f.write(f"# Images are cutout based on galaxy's petrosian radius\n")
            else:
                f.write(f"# Images are standard SDSS frame (not cropped)\n")
            f.write(f"# -- Bands: {' '.join(bands)}\n")
            f.write(f"# -- Max search radius: {max_search_radius} arcmin\n")
            f.write(f"{'-' * 40}\n")

            writer = csv.writer(f)

            # Write header
            writer.writerow(['ra_orig', 'dec_orig', 'found', 'ra', 'dec', 'dir_name', 'objid', 'cutout_shape'])

            # Write data
            for i, gal in enumerate(galaxies):
                if gal is None:
                    writer.writerow([orig_ra_list[i], orig_dec_list[i], False, None, None, None, None, None])
                else:
                    writer.writerow(
                        [orig_ra_list[i], orig_dec_list[i], True, gal['ra'], gal['dec'], names[i], gal['objid'],
                         cutout_shapes[i]])

    pu.verbose_print(verbose, pu.bold(f"ALL DONE!"))


def __get_random_galaxy_objid():
    """Request random galaxy from SDSS in a random field

    Returns
    -------
    objid : `int`
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

    Parameters
    ----------
    objid : `int`

    Returns
    -------
    data : `dict`
        Dictionary with keys 'run', 'camcol', 'field', 'ra', 'dec', 'objid', 'petroRad_r'
    """

    # Get imaging data
    req = requests.get(f"http://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                       f"SELECT run, camcol, field, ra, dec, petroRad_r FROM Galaxy "
                       f"WHERE objid = {objid}")

    return req.json()[0]['Rows'][0]


def __get_galaxy_jpg_image(ra, dec, petro_r):
    """Get jpg image for a given galaxy imaging data

    Parameters
    ----------
    ra : `float`
        right ascension in degrees
    dec : `float`
        declination in degrees
    petro_r : `float`
        petrosian radius in arcsec

    Returns
    -------
    image : `numpy.ndarray`
        Image data as numpy array
    """

    # Compute scale, defined as "/pix
    # Fix image size 2*1.25*radius arcsec
    img_size = 256
    scale = 2 * 1.25 * petro_r / img_size

    url = f"http://skyserver.sdss.org/dr17/SkyServerWS/ImgCutout/getjpeg?" \
          f"ra={ra}&dec={dec}&scale={scale}&width={img_size}&height={img_size}"

    # Read jpg image url into numpy array
    jpg_data = np.asarray(Image.open(urlopen(url)))
    return jpg_data


def __get_url_from_imaging_data(run, camcol, field, band):
    """Get fits image url from imaging data

    Parameters
    ----------
    run : `int`
    camcol : `int`
    field : `int`
    band : `str`
        'u', 'g', 'r', 'i', 'z'

    Returns
    -------
    url : `str`
    """

    url = f"http://dr17.sdss.org/sas/dr17/eboss/photoObj/frames/301/" \
          f"{run}/{camcol}/frame-{band}-{run:06d}-{camcol}-{field:04d}.fits.bz2"
    return url


def __cutout_galaxy_fits_image(fits_file, ra, dec, petro_r):
    """Cutout galaxy fits image

    Parameters
    ----------
    fits_file : `str`
        Path to fits file, can be url or local path
    ra : `float`
        right ascension in degrees
    dec : `float`
        declination in degrees
    petro_r : `float`
        petrosian radius in arcsec

    Returns
    -------
    cutout : `numpy.ndarray`
        Cutout image data as numpy array
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


def __search_nearby_galaxy_wrapper(args):
    """Wrapper for __search_nearby_galaxy for multiprocessing"""

    return __search_nearby_galaxy(*args)


def __search_nearby_galaxy(ra, dec, max_search_radius, verbose=False):
    """Search for a galaxy by ra dec and return galaxy data

    Use the fGetNearbyObjEq function from the SDSS SkyServer API.
    Start with a search radius of 1 arcmin and double the radius until over the max_search_radius.
    If max_search_radius is not power of 2, try one last search at max_search_radius.

    Parameters
    ----------
    ra : `float`
        right ascension in degrees
    dec : `float`
        declination in degrees
    max_search_radius : `float`
        maximum search radius in arcmin
    verbose : `bool`, default=False
        print verbose output

    Returns
    -------
    gal : `dict` or `None` if no galaxy found
        Dictionary with keys 'objid', 'run', 'camcol', 'field', 'ra', 'dec', 'petroRad_r', 'petroRadErr_r'
    """

    url = "http://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd=" \
          "SELECT TOP 1 G.objid, G.run, G.camcol, G.field, G.ra, G.dec, G.petroRad_r, G.petroRadErr_r " \
          "FROM Galaxy as G JOIN dbo.fGetNearbyObjEq({}, {}, {}) AS GN " \
          "ON G.objID = GN.objID " \
          "ORDER BY GN.distance"

    search_radius = 1
    while search_radius < max_search_radius:
        req = requests.get(url.format(ra, dec, search_radius))
        if req.json()[0]['Rows']:
            return req.json()[0]['Rows'][0]
        search_radius *= 2

    # Try one last search at max_search_radius
    if search_radius * 2 != max_search_radius:
        req = requests.get(url.format(ra, dec, max_search_radius))
        if req.json()[0]['Rows']:
            return req.json()[0]['Rows'][0]

    pu.verbose_print(verbose, f"No nearby galaxy found within {max_search_radius} arcmin")

    return None


def __download_fits_image_wrapper(args):
    """Wrapper for __download_fits_image for multiprocessing"""

    return __download_fits_image(*args)


def __download_fits_image(fits_url, file_path):
    """Download fits image from url to file_path

    Parameters
    ----------
    fits_url : `str`
        url to fits image
    file_path : `str`
        path to save fits image
    """

    # Download fits image
    with urlopen(fits_url) as response, open(f"{file_path}.bz2", 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    # Decompress
    with bz2.open(f"{file_path}.bz2", 'rb') as in_file, open(file_path, 'wb') as out_file:
        shutil.copyfileobj(in_file, out_file)

    # Remove tmp file
    pathlib.Path(f"{file_path}.bz2").unlink()


def __download_fits_image_with_cutout_wrapper(args):
    """Wrapper for __download_fits_image_with_cutout for multiprocessing"""

    return __download_fits_image_with_cutout(*args)


def __download_fits_image_with_cutout(fits_url, file_path, ra, dec, petro_r):
    """Download fits image from url to file_path and cutout galaxy

    Parameters
    ----------
    fits_url : `str`
        url to fits image
    file_path : `str`
        path to save fits image
    ra : `float`
        right ascension in degrees
    dec : `float`
        declination in degrees
    petro_r : `float`
        petrosian radius in arcsec

    Returns
    -------
    cutout : `tuple`
        2d cutout shape
    """

    # Get cutout image np array
    cutout_arr = __cutout_galaxy_fits_image(fits_url, ra, dec, petro_r)

    # Save cutout image as fits
    hdu = fits.PrimaryHDU(cutout_arr)
    hdu.writeto(file_path)

    return cutout_arr.shape
