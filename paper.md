title: 'IndeterminateBeam: A Python package for solving 1D indeterminate beams'
tags:
- bending moment diagram
- shear force diagram
- normal force diagram
- deflection
- statics
- structural engineering
- civil engineering
- indeterminate
- Python
authors:
  - name: Jesse Bonanno
    orcid: 0000-0002-4996-6813
date: 15 December 2020
bibliography: paper.bib


# Summary

IndeterminateBeam is a Python Package aiming to serve as a foundation for civil and structural engineering projects in Python. The module is based on engineering concepts of statics __references__. The module can also serve as a standalone program and is useful for determining:

  - reaction forces for indeterminate beams
  - Internal forces for indeterminate beams (shear, bending, axial)
  - deflection of the beam due to resulting forces
  - axial force, shear force, and bending moment diagrams

The package documentation can be accessed [here](https://indeterminatebeam.readthedocs.io/en/main/), where a brief overview of the theory behind the module is provided.

As the package represents a foundational element of civil, structural and mechanical engineering (often taught in first year university) the package can be used by:

* teachers generating problems to solve
* students experimenting on how differnt changes affect the system
* engineers trying to solve for real world problems on 1D beams
* engineers trying to implement higher order python solutions that rely on the use of 1D beams


The `indeterminatebeam` package is ready for installation using `pip` or can be tested online using the provided [Jupyter notebook](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/readme_example.ipynb).


## Statement of Need

In the civil and structural engineering industry in-house software generally consists of numerous standalone excel files. Although the excel files can often be greatly valueable once created, they are often created from scratch with difficulty in making use of previous excel projects.

Python can be utilised to combat this problem, allowing for the adoption of previous work as a python module. This will allow for in-house engineering software to be more uniform, readable, manageable, and reliable.

The demand for such a calculation module can be observed with the existence of many websites that perform such a calculation. Although there are many websites that allow for solving indeterminate beams, there are no well documented python packages. The websites often require payment for full access to software, and do not allow for the creation of higher order software.

This python package was heavily inspired by [simplebendingpractice](https://github.com/alfredocarella/simplebendingpractice), a module created by [Alfredo Carella](https://github.com/alfredocarella) of the Oslo Metropolitan University
for educational purposes. The beambending module, although well documented, can only solve for simply supported beams consisting of a pin and roller support. The full documentation for this project can be found [here](https://alfredocarella.github.io/simplebendingpractice/index.html).

The following has been taken from @alfredo, and has been modified slightly to add aditional information.

PUT FIGURE.

Add column for - can solve indeterminate beam, can add any type of support. (any is a  loose word should try to word better).


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



