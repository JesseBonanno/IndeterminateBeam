.. _reference:

===========================
IndeterminateBeam Reference
===========================
.. automodule:: model

Support
---------
.. autoclass:: model.Support

Beam
----
.. autoclass:: model.Beam
.. autofunction:: model.Beam.add_loads
.. autofunction:: model.Beam.remove_loads
.. autofunction:: model.Beam.add_supports
.. autofunction:: model.Beam.remove_supports
.. autofunction:: model.Beam.get_support_details
.. autofunction:: model.Beam.check_determinancy
.. autofunction:: model.Beam.analyse
.. autofunction:: model.Beam.get_bending_moment
.. autofunction:: model.Beam.get_shear_force
.. autofunction:: model.Beam.get_normal_force
.. autofunction:: model.Beam.get_deflection
.. autofunction:: model.Beam.add_query_points
.. autofunction:: model.Beam.remove_query_points
.. autofunction:: model.Beam.plot
.. autofunction:: model.Beam.plot_beam_diagram
.. autofunction:: model.Beam.plot_normal_force
.. autofunction:: model.Beam.plot_shear_force
.. autofunction:: model.Beam.plot_bending_moment
.. autofunction:: model.Beam.plot_deflection

PointTorque
------------
.. autoclass:: model.PointTorque

PointLoad
---------
.. autoclass:: model.PointLoad
.. autoclass:: model.PointLoadH
.. autoclass:: model.PointLoadV

DistributedLoad
---------------
.. autoclass:: model.DistributedLoadV
