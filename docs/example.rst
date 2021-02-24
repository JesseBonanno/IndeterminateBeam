.. _example:

Indeterminate Beam with Point Load and Distributed Load
========================================================

This example demonstrates some functionality of the ``indeterminatebeam`` package. It has been taken from example 12.21 of the Hibbeler textbook :cite:`HibbelerRussell2013MoM`.

Try it in online: |colab|

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/example_1.ipynb

Specifications
--------------

A 3m long propped cantilever AB is fixed at A (x = 0 m), and supported on a roller at B (x = 3 m).

The beam is subject to a load of 8kN acting downwards at the midspan, and a UDL of 6kN/m across the length of the support.

E and I are constant.

Results
--------

The following values can be directly extracted using the `get_shear_force`, `get_bending_moment` and `get_reaction` methods:

   #. The absolute maximum shear force 	  --> 16.75 kN
   #. The absolute maximum bending moment --> 11.25 kN.m
   #. The reaction at B         	  --> 9.25 kN

A plot of the axial force, shear force, and bending moments is shown below. A deflection graph is also presented however this depends on the beam properties E and I which werent included in this question.
As a default the values E and I are taken as the values for a 150UB18.0 steel beam. 

.. figure:: examples/example_1.png
  :width: 700
  :alt: example_1

Code
----

.. literalinclude:: examples/example_1.py

