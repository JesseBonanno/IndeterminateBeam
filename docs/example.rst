.. _example:

Beam with two point loads and two distributed loads
===================================================

This example demonstrates some functionality of the indeterminatebeam_ package. It has been taken from example 4.17 of this `Document <https://engineering.purdue.edu/~ce474/Docs/Beam_Examples02.pdf>`_ [document](

Try it in online: |binder| |colab|

.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/alfredocarella/simplebendingpractice/master?filepath=simple_demo.ipynb

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/alfredocarella/simplebendingpractice/blob/master/simple_demo.ipynb

Specifications
--------------

A propped cantilever ABC is fixed at A, support on a roller at C and carries a mid span point load of 15kN.

E and I are constant.

Results
--------

The following values can be directly extracted:

   #. The degree of determinancy --> 1
   #. The maximum shear force 	 --> 8.906 kN
   #. The maximum bending moment --> 16.875 kN

A plot of the axial force, shear force, and bending moments is shown below. A deflection graph is also presented however this depends on the beam properties E and I which werent included in this question.
As a default the values E and I are taken as the values for a 150UB18.0 steel beam. 

.. figure:: examples/example_1.png

Code
----

.. literalinclude:: examples/example_1.py

