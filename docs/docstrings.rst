.. _docstrings:

===========================
IndeterminateBeam Reference
===========================
.. automodule:: indeterminatebeam.indeterminatebeam

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
.. autofunction:: indeterminatebeam.Beam.analyse
.. autofunction:: indeterminatebeam.Beam.get_reaction
.. autofunction:: indeterminatebeam.Beam.get_bending_moment
.. autofunction:: indeterminatebeam.Beam.get_shear_force
.. autofunction:: indeterminatebeam.Beam.get_normal_force
.. autofunction:: indeterminatebeam.Beam.get_deflection
.. autofunction:: indeterminatebeam.Beam.add_query_points
.. autofunction:: indeterminatebeam.Beam.remove_query_points
.. autofunction:: indeterminatebeam.Beam.plot_beam_external
.. autofunction:: indeterminatebeam.Beam.plot_beam_internal
.. autofunction:: indeterminatebeam.Beam.plot_reaction_force
.. autofunction:: indeterminatebeam.Beam.plot_normal_force
.. autofunction:: indeterminatebeam.Beam.plot_shear_force
.. autofunction:: indeterminatebeam.Beam.plot_bending_moment
.. autofunction:: indeterminatebeam.Beam.plot_deflection

PointLoads
-----------
.. autoclass:: indeterminatebeam.PointTorque
.. autoclass:: indeterminatebeam.PointLoad

DistributedLoads
-----------------
.. autoclass:: indeterminatebeam.UDL
.. autoclass:: indeterminatebeam.TrapezoidalLoad
.. autoclass:: indeterminatebeam.DistributedLoad