# Indeterminate Beam

[![Version](https://img.shields.io/badge/version-v2.2.0-blue.svg)](https://github.com/JesseBonanno/IndeterminateBeam/releases/tag/v2.2.0)
[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)
[![DOI](https://jose.theoj.org/papers/10.21105/jose.00111/status.svg)](https://doi.org/10.21105/jose.00111)
[![Documentation Status](https://readthedocs.org/projects/indeterminatebeam/badge/?version=main)](https://indeterminatebeam.readthedocs.io/en/main/?badge=main)
[![Build Status](https://travis-ci.org/JesseBonanno/IndeterminateBeam.svg?branch=main)](https://travis-ci.org/JesseBonanno/IndeterminateBeam)
[![CodeFactor](https://www.codefactor.io/repository/github/jessebonanno/indeterminatebeam/badge)](https://www.codefactor.io/repository/github/jessebonanno/indeterminatebeam)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/simple_demo.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/JesseBonanno/IndeterminateBeam/main?filepath=docs%2Fexamples%2Fsimple_demo.ipynb)
[![Website](https://img.shields.io/badge/website-up-brightgreen)](https://indeterminate-beam.herokuapp.com/)
[![Downloads](https://pepy.tech/badge/indeterminatebeam)](https://pepy.tech/project/indeterminatebeam)


IndeterminateBeam is a Python Package aiming to serve as a foundation for civil and structural engineering projects in Python. The module can also serve as a stand-alone program and is useful for determining:

  - reaction forces for indeterminate beams
  - internal forces for indeterminate beams (shear, bending, axial)
  - deflections of beams due to resulting forces
  - axial force, shear force, bending moment and deflection diagrams.

The package is based mainly on engineering concepts of statics as described in (Hibbeler, 2013), and Python packages Sympy (Meurer et al., 2017) and Plotly (Plotly Technologies Inc, 2015). 

The [package documentation](https://indeterminatebeam.readthedocs.io/en/main/theory.html) provides a brief overview of the theory behind the solutions used to calculate the forces on the indeterminate beam. The full package documentation can be accessed [here](https://indeterminatebeam.readthedocs.io/en/main/).

Text-based examples of the package presented in the [documentation](https://indeterminatebeam.readthedocs.io/en/main/examples.html) can be found on this [Jupyter Notebook](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/simple_demo.ipynb) and a web-based graphical user interface (GUI) is available at https://indeterminate-beam.herokuapp.com/.

## Project Purpose

The purpose of this project is two-fold:
1.	Create a [free website](https://indeterminate-beam.herokuapp.com/) that has more features than paid and free beam calculators that exist on the web.
2.	Provide a foundation for civil and structural engineers who want to create higher order engineering Python programs.

Several (mostly paid) beam calculator websites currently exist online, providing the same service as this package, with web traffic in the hundreds of thousands per month (Similiarweb, 2021). Despite this, no online service exists (to the authors knowledge) that has all the features of `IndeterminateBeam` and is also free.

Similiarly, there are no well-documented indeterminate beam solving Python packages (to the authors knowledge) despite the importance of such a calculation in engineering. Several python finite element analysis (FEA) packages do exist, however they are vastly overcomplicated for someone wanting to only solve for forces on a one-dimensional beam.

This python package was heavily inspired by [beambending](https://github.com/alfredocarella/simplebendingpractice) (Carella, 2019), a module created for educational purposes by Alfredo Carella of the Oslo Metropolitan University. The beambending module, although well documented, can only solve for simply supported beams consisting of a pin and roller support. The [package documentation](https://simplebendingpractice.readthedocs.io/en/latest/?badge=latest)  for this project includes a more rigorous overview of the theory behind the basics for solving determinate structures.

## Functionality and Usage

A typical use case of the ```IndeterminateBeam``` package involves the following steps:

1. Create a `Beam` object
2. Create `Support` objects and assign to `Beam`
3. Create `Load` objects and assign to `Beam`
4. Solve for forces on `Beam` object
5. Plot results

You can follow along with the example below in this web-based [Jupyter Notebook](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example.ipynb). 
Alternatively, you can download the jupyter-notebook for this example [here](https://raw.githubusercontent.com/JesseBonanno/IndeterminateBeam/main/docs/examples/readme_example.ipynb), or the python file for this code [here](https://raw.githubusercontent.com/JesseBonanno/IndeterminateBeam/main/docs/examples/readme_example.py).

The units used throughout the Python package are the base SI units (newtons and metres), but can be updated using the `update_units` method. Units and load direction conventions are described in the [package documentation](https://indeterminatebeam.readthedocs.io/en/main/theory.html#sign-convention).

### Creating a Beam

The creation of a `Beam` instance involves the input of the beam length (m) and optionally the input of the Young's Modulus (E), second moment of area (I), and cross-sectional area (A). E, I and A are optional and by default are the properties of a steel 150UB18.0. For a beam with constant properties, these parameters will only affect the deflections calculated and not the distribution of forces, unless spring supports are specified.

```python
from indeterminatebeam import Beam
# Create 7 m beam with E, I, A as defaults
beam = Beam(7)                          
# Create 9 m beam with E, I, and A assigned by user
beam_2 = Beam(9, E=2000, I=10**6, A=3000)     
```

### Defining Supports
`Support` objects are created separately from the `Beam` object, and are defined by an x-coordinate (m) and the beams translational and rotational degrees of freedom.

Degrees of freedom are represented by a tuple of 3 booleans, representing the x , y , and m directions respectively. A `1` indicates the support is fixed in a direction and a `0` indicates it is free.

Optionally, stiffness can be specified in either of the translational directions, which overrides the boolean specified.

```python
from indeterminatebeam import Support
# Defines a pin support at location x = 5 m  
a = Support(5, (1,1,0))      
# Defines a roller support at location x = 0 m
b = Support(0, (0,1,0))      
# Defines a fixed support at location x = 7 m
c = Support(7, (1,1,1))      
# Assign the support objects to a beam object created earlier
beam.add_supports(a,b,c)    
```

### Defining loads
`Load` objects are created separately from the `Beam` object, and are generally defined by a force value and then a coordinate value, however this varies slightly for different types of loading classes.

```python
from indeterminatebeam import PointLoadV, PointTorque, DistributedLoadV
# Create a 1000 N point load at x = 2 m
load_1 = PointLoadV(1000, 2)
# Create a 2000 N/m UDL from x = 1 m to x = 4 m
load_2 = DistributedLoadV(2000, (1, 4))
# Defines a 2 kN.m point torque at x = 3.5 m
load_3 = PointTorque(2*10**3, 3.5)
# Assign the load objects to the beam object
beam.add_loads(load_1,load_2,load_3)
```

### Solving for Forces
Once the `Beam` object has been assigned with `Load` and `Support` objects it can then be solved. To solve for reactions and internal forces we call the analyse function.

```python
beam.analyse()  
```

### Plotting results
After the beam has been analysed we can plot the results.

```python
fig_1 = beam.plot_beam_external()
fig_1.show()

fig_2 = beam.plot_beam_internal()
fig_2.show()
```

The `plot_beam_external` and `plot_beam_internal` methods collate otherwise seperate plots.

The script above produces the following figures:
![example_1 beam diagram plot](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example_external_HD.png)
![example_1 beam internal plot](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example_internal_HD.png)


## Installing the package

If you want to install the `indeterminatebeam` package, you run this one-liner:

```shell
pip install indeterminatebeam
```

> **NOTE**: You need Python 3 to install this package (you may need to write `pip3` instead of `pip`).

The library dependencies are listed in the file `requirements.txt`, but you only need to look at them if you clone the repository.
If you install the package via `pip`, the listed dependencies should be installed automatically.

## Future Work

The following are areas that can be implemented in future:
- allow for segmental beam properties (E,I,A)
- calculate axial deflections
- Latex or PDF output of calculations
- More indeterminate beams in testing

## Contributing

The guidelines for contributing are specified [here](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/CONTRIBUTING.md).

## Support

The guidelines for support are specified [here](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/SUPPORT.md).


## License

[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)

Copyright (c) 2020, Jesse Bonanno

## References

1. Carella, A. (2019). BeamBending: A teaching aid for 1-d shear force and bending moment
diagrams. *Journal of Open Source Education, 2*(16), 65. https://doi.org/10.21105/
jose.00065
2. Hibbeler, R. (2013). *Mechanics of materials*. P.Ed Australia. ISBN: 9810694369
3. Meurer, A., Smith, C. P., Paprocki, M., Čertík, O., Kirpichev, S. B., Rocklin, M., Kumar,
A., Ivanov, S., Moore, J. K., Singh, S., Rathnayake, T., Vig, S., Granger, B. E., Muller,
R. P., Bonazzi, F., Gupta, H., Vats, S., Johansson, F., Pedregosa, F., … Scopatz, A.
(2017). SymPy: symbolic computing in Python. *PeerJ Computer Science, 3*, e103.
https://doi.org/10.7717/peerj-cs.103
4. *Similiarweb*, 2021, https://www.similarweb.com/. Accessed 1 Mar 2021.
5. Plotly Technologies Inc. *Collaborative data science*. Montréal, QC, 2015. https://plot.ly."
