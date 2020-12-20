.. _docstrings:

===========================
IndeterminateBeam Reference
===========================
.. automodule:: indeterminatebeam

Support
---------
.. autoclass:: indeterminatebeam.Support
.. autofunction:: indeterminatebeam.Support.__init__

Beam
----
.. autoclass:: indeterminatebeam.Beam
.. autofunction:: indeterminatebeam.Beam.__init__
.. autofunction:: indeterminatebeam.Beam.add_loads
.. autofunction:: indeterminatebeam.Beam.remove_loads
.. autofunction:: indeterminatebeam.Beam.add_supports
.. autofunction:: indeterminatebeam.Beam.remove_supports
.. autofunction:: indeterminatebeam.Beam.get_support_details
.. autofunction:: indeterminatebeam.Beam.check_determinancy
.. autofunction:: indeterminatebeam.Beam.analyse
.. autofunction:: indeterminatebeam.Beam.get_bending_moment
.. autofunction:: indeterminatebeam.Beam.get_shear_force
.. autofunction:: indeterminatebeam.Beam.get_normal_force
.. autofunction:: indeterminatebeam.Beam.get_deflection
.. autofunction:: indeterminatebeam.Beam.add_query_points
.. autofunction:: indeterminatebeam.Beam.remove_query_points
.. autofunction:: indeterminatebeam.Beam.plot
.. autofunction:: indeterminatebeam.Beam.plot_beam_diagram
.. autofunction:: indeterminatebeam.Beam.plot_normal_force
.. autofunction:: indeterminatebeam.Beam.plot_shear_force
.. autofunction:: indeterminatebeam.Beam.plot_bending_moment
.. autofunction:: indeterminatebeam.Beam.plot_deflection

PointTorque
------------
.. autoclass:: indeterminatebeam.PointTorque

PointLoad
---------
.. autoclass:: indeterminatebeam.PointLoad
.. autoclass:: indeterminatebeam.PointLoadH
.. autoclass:: indeterminatebeam.PointLoadV

DistributedLoad
---------------
.. autoclass:: indeterminatebeam.DistributedLoadV
.. autoclass:: indeterminatebeam.DistributedLoadH
.. autofunction:: indeterminatebeam.TrapezoidalLoad
