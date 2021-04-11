# Indeterminate Beam


[![Version](https://img.shields.io/badge/version-v2.0.3-blue.svg)](https://github.com/JesseBonanno/IndeterminateBeam/releases/tag/v2.0.3)
[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/indeterminatebeam/badge/?version=main)](https://indeterminatebeam.readthedocs.io/en/main/?badge=main)
[![Build Status](https://travis-ci.org/JesseBonanno/IndeterminateBeam.svg?branch=main)](https://travis-ci.org/JesseBonanno/IndeterminateBeam)
[![CodeFactor](https://www.codefactor.io/repository/github/jessebonanno/indeterminatebeam/badge)](https://www.codefactor.io/repository/github/jessebonanno/indeterminatebeam)
[![codecov](https://codecov.io/gh/JesseBonanno/IndeterminateBeam/branch/main/graph/badge.svg?token=VPN022HBRA)](https://codecov.io/gh/JesseBonanno/IndeterminateBeam)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/simple_demo.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/JesseBonanno/IndeterminateBeam/main?filepath=docs%2Fexamples%2Fsimple_demo.ipynb)
[![Website](https://img.shields.io/website?down_color=lightgrey&down_message=offline&up_color=green&up_message=up&url=https%3A%2F%2Findeterminate-beam.herokuapp.com%2F)](https://indeterminate-beam.herokuapp.com/)

IndeterminateBeam is a Python Package aiming to serve as a foundation for civil and structural engineering projects in Python. The module can also serve as a stand-alone program and is useful for determining:

  - reaction forces for indeterminate beams
  - internal forces for indeterminate beams (shear, bending, axial)
  - deflections of beams due to resulting forces
  - axial force, shear force, bending moment and deflection diagrams.

The package documentation can be accessed [here](https://indeterminatebeam.readthedocs.io/en/main/).


## Statement of Need

In the civil and structural engineering industry in-house software generally consists of numerous stand-alone spreadsheet files. Different spreadsheet files often share similar engineering calculations, but the programming style of these spreadsheets does not allow for an easy way to reliably share these calculations.

Python can be utilised to address this problem, allowing for the adoption of previous work as a Python module. This will allow for in-house engineering software to be more uniform, readable, manageable, and reliable.

The demand for such a calculation module in the engineering industry can be observed with the existence of many websites that perform such a calculation. Most of these websites require payment for full access to the software and only displays a graphical user interface, preventing the creation of higher order engineering programming projects.

This python package was heavily inspired by [simplebendingpractice](https://github.com/alfredocarella/simplebendingpractice), a module created by [Alfredo Carella](https://github.com/alfredocarella) of the Oslo Metropolitan University
for educational purposes. The beambending module, although well documented, can only solve for simply supported beams. The full documentation for this project can be found [here](https://alfredocarella.github.io/simplebendingpractice/index.html).

## Functionality and Usage

A typical use case of the ```IndeterminateBeam``` package involves the following steps:

1. Create a `Beam` object
2. Create `Support` objects and assign to `Beam`
3. Create `Load` objects and assign to `Beam`
4. Solve for forces on `Beam` object
5. Plot results

You can follow along with the example below in this web-based [Jupyter Notebook](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example.ipynb). Units and load direction conventions are described in the [package documentation](https://indeterminatebeam.readthedocs.io/en/main/theory.html).

### Creating a Beam

The creation of a `Beam` instance involves the input of the beam length (m) and optionally the input of the Young's Modulus (E), second moment of area (I), and cross-sectional area (A). E, I and A are optional and by default are the properties of a steel 150UB18.0. For a beam with constant properties, these parameters will only affect the deflections calculated and not the distribution of forces, unless spring supports are specified.

```python
from indeterminatebeam import Beam
# Create 7 m beam with E, I, A as defaults
beam = Beam(7)                          
# Create 9 m beam with E, I, and A assigned by user
beam_2 = Beam(9,E=2000, I =10**6, A = 3000)     
```

### Defining Supports
`Support` objects are created separately from the `Beam` object, and are defined by an x-coordinate (m) and the beams translational and rotational degrees of freedom.

Degrees of freedom are represented by a tuple of 3 booleans, representing the x , y , and m directions respectively. A `1` indicates the support is fixed in a direction and a `0` indicates it is free.

Optionally, stiffness can be specified in either of the translational directions, which overrides the boolean specified.

```python
from indeterminatebeam import Support
# Defines a pin support at location x = 5m  
a = Support(5,(1,1,0))      
# Defines a roller support at location x = 0m
b = Support(0,(0,1,0))      
# Defines a fixed support at location x = 7m
c = Support(7,(1,1,1))      
# Assign the support objects to a beam object created earlier
beam.add_supports(a,b,c)    
```

### Defining loads
`Load` objects are created separately from the `Beam` object, and are generally defined by a force value and then a coordinate value, however this varies slightly for different types of loading classes.

```python
from indeterminatebeam import PointLoadV, PointTorque, DistributedLoadV
# Create 1kN point load at x = 2m
load_1 = PointLoadV(1,2)
# Create a 2kN UDL from x = 1m to x = 4m
load_2 = DistributedLoadV(2,(1,4))
# Defines a 2kN.m point torque at x = 3.5m
load_3 = PointTorque(2, 3.5)
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

## License

[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)

Copyright (c) 2020, Jesse Bonanno
