from .galaxy import Galaxy
import numpy as np
import requests


def get_random_galaxy():
    """"""

    # Create galaxy instance
    galaxy = Galaxy()

    return galaxy


def __get_random_field():
    """Return random ra and dec (10 deg range, integer)
    need to exclude these fields:
        1. Dec in [-90, -30] for any RA
        2. Dec in [50, 90] and RA in [0, 20]
        3. Dec in [-30, -10] and RA in [140, 160]
        4. Dec in [70, 90] and RA in [200, 220]
    """

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

    # Get random field
    ra_min, ra_max, dec_min, dec_max = __get_random_field()

    # Get random objid
    req = requests.get(f"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                       f"SELECT TOP 1 g.objid FROM Galaxy AS g "
                       f"WHERE g.ra BETWEEN {ra_min} AND {ra_max} AND g.dec BETWEEN {dec_min} AND {dec_max} "
                       f"ORDER BY NEWID()")

    return req.json()[0]['Rows'][0]['objid']


def __get_galaxy_imaging_data(objid):
    """Get imaging data (run, camcol, field) for a given galaxy objid"""

    # Get imaging data
    req = requests.get(f"https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?cmd="
                       f"SELECT run, camcol, field FROM Galaxy "
                       f"WHERE objid = {objid}")

    return req.json()[0]['Rows'][0]
