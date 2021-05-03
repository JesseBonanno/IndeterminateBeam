import os
import sys
sys.path.insert(0, os.path.abspath('../'))

from sympy import oo
from indeterminatebeam.indeterminatebeam import (
    Support, 
    Beam, 
    PointTorque,
    PointLoad,
    PointLoadV, 
    PointLoadH,
    DistributedLoad, 
    DistributedLoadV, 
    DistributedLoadH,
    TrapezoidalLoad,
    TrapezoidalLoadV,
    TrapezoidalLoadH,
)
import unittest


##The unit testing refers to example 1 as described in the full documentation.
##In future more complex indeterminate beams should be added to ensure the validity of the program.
##In future more attention should be paid to raising error based on incorrect user values.

class SupportTestCase(unittest.TestCase):

    def test_initialisation(self):
        ##set up
        a = Support()
        b = Support(0,(1,1,1))
        c = Support(1, (1,0,1))
        d = Support(2, (1,1,1), ky =50, kx = 40)

        ##check default set up
        #self.assertEqual(a,b)

        ##check position
        self.assertEqual(a._position,0)
        self.assertEqual(c._position,1)

        ##check translation
        self.assertEqual(c._DOF, [1,0,1])
        self.assertEqual(d._stiffness, [40,50,oo])

    


class BeamTestCase(unittest.TestCase):
    
    def setUp(self):
        ##create example 1 problem
        beam = Beam(6000)

        a = Support()
        c = Support(6000,(0,1,0))

        beam.add_supports(a,c)
        beam.add_loads(PointLoad(-15000,3000,90))

        beam.analyse()

        self.beam = beam

    def test_analyse_correct(self):
        ##check the beam properties are consistent
        beam = self.beam

        ##Use get reactions function to assert correct reactions
        ##get reactions returns reaction force rounded to 5 dp
        #{'x': [(0.0, 0)], 'y': [(4.6875, 6), (10.3125, 0)], 'm': [(16.875, 0)]} if add_supports(c,a)
        self.assertEqual(beam.get_reaction(0,'x'),0)
        self.assertEqual(beam.get_reaction(0,'y'),10312.50)
        self.assertEqual(beam.get_reaction(0,'m'),16875000)
        self.assertEqual(beam.get_reaction(6000,'x'),0)
        self.assertEqual(beam.get_reaction(6000,'y'),4687.5)
        self.assertEqual(beam.get_reaction(6000,'m'),0)

        ##check the forces on the beam, round to 1 dp to reduce error chance
            ##normal forces
        self.assertEqual(round(beam.get_normal_force(1000),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_max=True),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_min=True),1), 0)
            ##shear forces
        self.assertEqual(round(beam.get_shear_force(1000),1), 10312.5)
        self.assertEqual(round(beam.get_shear_force(return_max=True),1), 10312.5)
        self.assertEqual(round(beam.get_shear_force(return_min=True),1), -4687.5)
            ##bending moments
        self.assertEqual(round(beam.get_bending_moment(0),1), -16.875*10**6)   
        self.assertEqual(round(beam.get_bending_moment(return_max=True),1), 14.0625*10**6)
        self.assertEqual(round(beam.get_bending_moment(return_min=True),1), -16.875*10**6)
            ##deflection
        self.assertEqual(round(beam.get_deflection(3000),1), -16.3)
        self.assertEqual(round(beam.get_deflection(return_max=True),1), 0)
        self.assertEqual(round(beam.get_deflection(return_min=True),1), -16.7)

    def test_setup_correct(self):
        beam = self.beam

        self.assertEqual(beam._E, 2*10**5)
        self.assertEqual(beam._x0,0)
        self.assertEqual(beam._x1,6000)
        self.assertEqual(beam._I,9.05*10**6)

        ##check there are two supports and 1 load
        self.assertEqual(len(beam._supports),2)
        self.assertEqual(len(beam._loads),1)

    def test_query(self):
        beam = self.beam
        ##check initialised as empty
        self.assertEqual(beam._query, [])
        ##check can add points
        beam.add_query_points(1000,2000)
        beam.add_query_points(3000)
        self.assertEqual(beam._query, [1000,2000,3000])

        ##check can remove points
        beam.remove_query_points(1000,2000)
        self.assertEqual(beam._query, [3000])
        beam.remove_query_points(3000)
        self.assertEqual(beam._query, [])

    def test_loads(self):
        load_beam = Beam(5000)

        a = PointLoad(-15000,1000,0)      ##when use the add_load function this actually turns into c due to angle lol
        b = PointLoadV(-15000,1000)
        c = PointLoadH(-15000,1000)
        d = PointTorque(-15000,1000)
        e = DistributedLoad(5,(0,1000),45)
        f = DistributedLoadV(5,(0,1000))
        g = DistributedLoadH(5,(0,1000))
        h = TrapezoidalLoad((0,1),(0,1000),45)
        i = TrapezoidalLoadV((0,1),(0,1000))
        j = TrapezoidalLoadH((0,1),(0,1000))

        load_beam.add_loads(a,b,c,d,e,f,g,h,i,j)
        load_beam.remove_loads(f,g,h,i,j)
        load_beam.remove_loads(a)   
        load_beam.remove_loads(b,c) 

        self.assertEqual(load_beam._loads, [d,e])

        load_beam.add_loads(b,c)

        self.assertEqual(load_beam._loads, [d,e,b,c])

    def test_plot(self):
        beam = self.beam

        fig = beam.plot_beam_external()
        fig = beam.plot_beam_internal()

        fig = beam.plot_beam_diagram()
        fig = beam.plot_reaction_force()

        fig = beam.plot_normal_force()
        fig = beam.plot_shear_force()
        fig = beam.plot_bending_moment()
        fig = beam.plot_deflection()
        
if __name__ == '__main__':
    unittest.main(verbosity=2)