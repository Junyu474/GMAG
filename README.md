# GMAG

_GIVE ME A GALAXY!_

```python
from gmag.sdss import get_random_galaxy

galaxy = get_random_galaxy()
galaxy.show()
```

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
```

Show galaxy (jpg image):

```python
galaxy.show()
```

### Plotting

Other than the `show()` method to plot the jpg image, 
you can also plot each of the bands (u, g, r, i, z) using the `show_band()` method:

```python
galaxy.show_band('r')
```

more control over the plot:

```python
galaxy.show_band('r', cmap='gray', high_contrast=True, colorbar=True)
```

or show all bands:

```python
galaxy.show_all_bands()
```