# GMAG

_Give Me A Galaxy! | Fast SDSS Galaxy Image Download_

---

__Get a galaxy with 3 lines of code__

```python
from gmag import sdss

galaxy = sdss.get_random_galaxy()
galaxy.show()
```

![output](https://user-images.githubusercontent.com/48139961/203444526-e9b367b4-2d9a-45e4-8147-4e50ac384e9c.png)

__or, download galaxy muliband image data accelerated by multiprocessing__

```python
sdss.download_images('some_galaxies.fit')  # require ra and dec columns

# ---example outout---
# Searching galaxies: 100%|██████████| 10/10 [00:02<00:00,  3.73obj/s]
# ...Found 7 out of 10 galaxies
# ...Created directories for images at /images_2022-11-26_11-01-05
# Downloading images: 100%|██████████| 35/35 [00:19<00:00,  1.84img/s]
# ...Saving info file at /images_2022-11-26_11-01-05/info.csv
# ALL DONE!
```

---

### Table of Contents

- [Installation](#installation)
- [Usage](#usage)
    - [Download Galaxy Images](#download-galaxy-images)
    - [Get a Random Galaxy](#get-a-random-galaxy)

## Installation

<a name="installation"></a>

```bash
pip install gmag
```

## Usage

<a name="usage"></a>

### Download Galaxy Images

<a name="download-galaxy-images"></a>

Provide a table with `ra` and `dec` columns,
and `gmag` will download galaxy multi-bands images for you accelerated by multiprocessing.
Images can even be cutout instead of the full frame provided by SDSS.

```python
from gmag import sdss

sdss.download_images(
    "some_galaxies.fit",  # file containing ra and dec for galaxies
    bands="ugriz",        # bands to download
    cutout=True,          # crop the galaxy out of the standard sdss frame
    num_workers=8,        # number of processes to use
    # ...
)
```

Downloaded images will be organized in a directory with the following structure:

```
images_<YYYY-MM-DD>_<Hr-Min-Sec>
├── info.csv
├── <galaxy_name or rowid_objid>
│   ├── u.fits
│   ├── g.fits
│   ├── r.fits
│   ├── i.fits
│   └── z.fits
└── <galaxy_name or rowid_objid>
│   ├── u.fits
│   ├── g.fits
│   ├── r.fits
│   ├── i.fits
│   └── z.fits
└── ...
```

### Get a Random Galaxy

<a name="get-a-random-galaxy"></a>

```python
from gmag.sdss import get_random_galaxy

galaxy = get_random_galaxy()
```

Get galaxy information:

```python
galaxy.info()

# ---example output---
# SDSS DR17 ObjID:       1237655370354851898
# RA(deg):                         152.99248
# DEC(deg):                         58.86462
```

Show galaxy (jpg image):

```python
galaxy.show()
```

![main](https://user-images.githubusercontent.com/48139961/203444598-947ec45f-7e43-4a45-9ca0-a6e99e1770b2.png)

### Plotting

Other than the `show()` method to plot the jpg image,
you can also plot each of the bands (u, g, r, i, z) using the `show_band()` method:

```python
galaxy.show_band('r')
```

![r](https://user-images.githubusercontent.com/48139961/203445080-1bc738aa-bd44-46ae-bca6-64211e53201e.png)

more control over the plot:

```python
galaxy.show_band('r', cmap='viridis', high_contrast=True, colorbar=True)
```

![r_more](https://user-images.githubusercontent.com/48139961/203445176-5219608e-1a99-4e92-8ffb-23959460f94d.png)

or show all bands:

```python
galaxy.show_all_bands(high_contrast=True)
```

![all](https://user-images.githubusercontent.com/48139961/203445308-a2ad538c-847a-4dbd-9b28-70f8c13d4187.png)
