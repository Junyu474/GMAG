# GMAG

_GIVE ME A GALAXY!_

```python
from gmag.sdss import get_random_galaxy

galaxy = get_random_galaxy()
galaxy.show()
```

![output](https://user-images.githubusercontent.com/48139961/203444526-e9b367b4-2d9a-45e4-8147-4e50ac384e9c.png)

## Installation

```bash
pip install gmag
```

## Usage

### Basics

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
