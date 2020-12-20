# Indeterminate Beam


[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/JesseBonanno/IndeterminateBeam/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/indeterminatebeam/badge/?version=main)](https://indeterminatebeam.readthedocs.io/en/main/?badge=main)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/IndeterminateBeam/simple_demo.ipynb)

IndeterminateBeam is a Python Package aiming to serve as a foundation for civil and structural engineering projects in Python. The module can also serve as a standalone program and is useful for determining:

  - reaction forces for indeterminate beams
  - Internal forces for indeterminate beams (shear, bending, axial)
  - deflection of the beam due to resulting forces
  - axial force, shear force, and bending moment diagrams

The package documentation can be accessed [here](https://indeterminatebeam.readthedocs.io/en/main/).


## Statement of Need

In the civil and structural engineering industry in-house software generally consists of numerous standalone excel files. Although the excel files can often be greatly valueable once created, they are often created from scratch with difficulty in making use of previous excel projects.

Python can be utilised to combat this problem, allowing for the adoption of previous work as a python module. This will allow for in-house engineering software to be more uniform, readable, manageable, and reliable.

Although there are many websites that allow for solving indeterminate beams, there are no well documented python packages.

This python package was heavily inspired by [simplebendingpractice](https://github.com/alfredocarella/simplebendingpractice), a module created by [Alfredo Carella](https://github.com/alfredocarella) of the Oslo Metropolitan University
for educational purposes. The beambending module, although well documented, can only solve for simply supported beams. The full documentation for this project can be found [here](https://alfredocarella.github.io/simplebendingpractice/index.html).

## Functionality and Usage

A typical use case of the `indeterminatebeam` package involves the following steps:

1. Create a `Beam` object
2. Create `Support` objects and assign to `Beam`
3. Create `load` objects and assign to `Beam`
4. Solve for forces on `Beam` object
5. Plot results

Default units are kN, m, and kN.m   _(except for E (MPa), and I (mm4))_

Load convention is described in the [package documentation](https://indeterminatebeam.readthedocs.io/en/main/).

You can follow along with the example below in this web based notebook: [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example.ipynb)

##### Creating Beam

The creation of a beam instance involves the input of the beam length (m) and optinally the input of the young's modulus (E), and second moment of area (I). E and I are optional and by default are the properties of a steel 150UB18.0. For a beam with constant EI (bending rigidity) these parameters will only affect the deflections calculated and not the distribution of forces.

```python
from indeterminatebeam import Beam
beam = Beam(7)                          # Initialize a Beam object of length 5m with E and I as defaults
beam_2 = Beam(9,E=2000, I =100000)      # Initialize a Beam object of length 9m with E and I assigned by user
```

##### Defining Supports
Support objects are created separately from the beam object, and are defined by an x-coordinate (m) and the beams translational and rotational degrees of freedom.

Degrees of freedom are represented by a tuple of 3 booleans, representing the x , y , and m directions respectively. A `1` indicates the support is fixed in a direction and a `0` indicates it is free.

```python
from indeterminatebeam import Support
a = Support(5,(1,1,0))                  # Defines a pin support at location x = 5m  
b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0m
c = Support(7,(1,1,1))                  # Defines a fixed support at location x = 7m
beam.add_supports(a,b,c)                # Assign the support objects to a beam object created earlier
```
##### Defining loads
Load objects are created separately from the beam object, and are generally defined by a force value and then a coordinate value, however this varies slightly for different types of loading classes.

```python
from indeterminatebeam import PointLoadV, PointTorque, DistributedLoadV
load_1 = PointLoadV(1,2)                # Defines a point load of 1kn acting up, at location x = 2m
load_2 = DistributedLoadV(2,(1,4))      # Defines a 2kN UDL from location x = 1m to x = 4m 
load_3 = PointTorque(2, 3.5)            # Defines a 2kN.m point torque at location x = 3.5m
beam.add_loads(load_1,load_2,load_3)    # Assign the support objects to a beam object created earlier
```

##### Solving for Forces
Once the beam object has been assigned with loads and supports it can be solved. To solve for reactions and internal forces we simply call the analyse function.

```python
beam.analyse()                          #solves beam for unknowns
```

##### Plot results
After the beam has been analysed we can plot the results.
```python
beam.plot()                            
```

The `plot` method is actually a wrapper that combines these five methods: `plot_beam_diagram`, `plot_normal_force`, `plot_shear_force`, `plot_bending_moment` and `plot_deflection` into a single A4-sized printer-friendly plot.

The script above produces the following figure:
![example_1](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example.png)

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
- allow for spring supports
- better graphing (a more readable or interactive graph)
- indication of support type in graph (currently all supports look like a pin support) 
- GUI user interface
- Latex or PDF output of calculations
- More user input validation checks
- More indeterminate beams in testing

## License

[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)

Copyright (c) 2020, Jesse Bonanno
