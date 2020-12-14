import sys, os
sys.path.insert(0, os.path.abspath('../'))
from indeterminatebeam.indeterminatebeam import Support, Beam, PointLoad, PointTorque, DistributedLoadV, PointLoadH, PointLoadV
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
        c._id = 1

        ##check default set up
        #self.assertEqual(a,b)

        ##check position
        self.assertEqual(a._position,0)
        self.assertEqual(c._position,1)

        ##check id
        self.assertFalse(a._id)
        self.assertEqual(c._id, 1)

        ##check translation
        self.assertEqual(c._DOF, (1,0,1))
        self.assertEqual(c._translation, ["Fixed", "Free", "Fixed"])

    


class BeamTestCase(unittest.TestCase):
    
    def setUp(self):
        ##create example 1 problem
        beam = Beam(6)

        a = Support()
        c = Support(6,(0,1,0))

        beam.add_supports(a,c)
        beam.add_loads(PointLoad(-15,3,90))

        beam.analyse()

        self.beam = beam

    def test_analyse_correct(self):
        ##check the beam properties are consistent
        beam = self.beam

        ##check the determinancy is 1
        self.assertEqual(beam.check_determinancy(),1)

        ##check the reaction forces, appears as a tuple where order of supports added matters
        #{'x': [(0.0, 0)], 'y': [(4.6875, 6), (10.3125, 0)], 'm': [(16.875, 0)]} if add_supports(c,a)
        self.assertEqual(round(beam._reactions['x'][0][0],1), 0)
        self.assertEqual(round(beam._reactions['y'][0][0],1), 10.3)
        self.assertEqual(round(beam._reactions['y'][1][0],1), 4.7)
        self.assertEqual(round(beam._reactions['m'][0][0],1), 16.9)

        ##check the forces on the beam, round to 1 dp to reduce error chance
            ##normal forces
        self.assertEqual(round(beam.get_normal_force(1)[0],1), 0)
        self.assertEqual(round(beam.get_normal_force(return_max=True),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_min=True),1), 0)
            ##shear forces
        self.assertEqual(round(beam.get_shear_force(1)[0],1), 10.3)
        self.assertEqual(round(beam.get_shear_force(return_max=True),1), 10.3)
        self.assertEqual(round(beam.get_shear_force(return_min=True),1), -4.7)
            ##bending moments
        self.assertEqual(round(beam.get_bending_moment(0)[0],1), -16.9)   
        self.assertEqual(round(beam.get_bending_moment(return_max=True),1), 14.1)
        self.assertEqual(round(beam.get_bending_moment(return_min=True),1), -16.9)
            ##deflection
        self.assertEqual(round(beam.get_deflection(3)[0],1), -16.3)
        self.assertEqual(round(beam.get_deflection(return_max=True),1), 0)
        self.assertEqual(round(beam.get_deflection(return_min=True),1), -16.7)

    def test_setup_correct(self):
        beam = self.beam

        self.assertEqual(beam._E, 2*10**5)
        self.assertEqual(beam._x0,0)
        self.assertEqual(beam._x1,6)
        self.assertEqual(beam._I,9.05*10**6)

        ##check there are two supports and 1 load
        self.assertEqual(len(beam._supports),2)
        self.assertEqual(len(beam._loads),1)

    def test_query(self):
        beam = self.beam
        ##check initialised as empty
        self.assertEqual(beam._query, [])
        ##check can add points
        beam.add_query_points(1,2)
        beam.add_query_points(3)
        self.assertEqual(beam._query, [1,2,3])

        ##check can remove points
        beam.remove_query_points(1,2)
        self.assertEqual(beam._query, [3])
        beam.remove_query_points(3)
        self.assertEqual(beam._query, [])

    def test_loads(self):
        load_beam = Beam(5)

        a = PointLoad(-15,1,0)      ##when use the add_load function this actually turns into c due to angle lol
        b = PointLoadV(-15,1)
        c = PointLoadH(-15,1)
        d = PointTorque(-15,1)
        e = DistributedLoadV(5,(0,1))

        load_beam.add_loads(a,b,c,d,e)
        load_beam.remove_loads(a)   
        load_beam.remove_loads(b,c) 

        self.assertEqual(load_beam._loads, [d,e])

        load_beam.add_loads(b,c)

        self.assertEqual(load_beam._loads, [d,e,b,c])

    def test_plot(self):
        beam = self.beam

        fig = beam.plot()
        self.assertEqual(str(type(fig)), "<class 'matplotlib.figure.Figure'>")
        
if __name__ == '__main__':
    unittest.main(verbosity=2)