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
        beam = Beam(6)

        a = Support()
        c = Support(6,(0,1,0))

        beam.add_supports(a,c)
        beam.add_loads(PointLoad(-15000,3,90))

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
        self.assertEqual(beam.get_reaction(0,'m'),16875.000)
        self.assertEqual(beam.get_reaction(6,'x'),0)
        self.assertEqual(beam.get_reaction(6,'y'),4687.5)
        self.assertEqual(beam.get_reaction(6,'m'),0)

        ##check the forces on the beam, round to 1 dp to reduce error chance
            ##normal forces
        self.assertEqual(round(beam.get_normal_force(1),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_max=True),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_min=True),1), 0)
            ##shear forces
        self.assertEqual(round(beam.get_shear_force(1),1), 10312.5)
        self.assertEqual(round(beam.get_shear_force(return_max=True),1), 10312.5)
        self.assertEqual(round(beam.get_shear_force(return_min=True),1), -4687.5)
            ##bending moments
        self.assertEqual(round(beam.get_bending_moment(0),1), -16.875*10**3)   
        self.assertEqual(round(beam.get_bending_moment(return_max=True),1), 14.0625*10**3)
        self.assertEqual(round(beam.get_bending_moment(return_min=True),1), -16.875*10**3)
            ##deflection
        self.assertEqual(round(beam.get_deflection(3),3), -0.016)
        self.assertEqual(round(beam.get_deflection(return_max=True),3), 0.00)
        self.assertEqual(round(beam.get_deflection(return_min=True),3), -0.017)

    def test_setup_correct(self):
        beam = self.beam

        self.assertEqual(beam._E, 200*10**9)
        self.assertEqual(beam._x0,0)
        self.assertEqual(beam._x1,6)
        self.assertEqual(beam._I,9.05*10**-6)

        ##check there are two supports and 1 load
        self.assertEqual(len(beam._supports),2)
        self.assertEqual(len(beam._loads),1)

    def test_query(self):
        beam = self.beam
        ##check initialised as empty
        self.assertEqual(beam._query, [])
        ##check can add points
        beam.add_query_points(1, 2)
        beam.add_query_points(3)
        self.assertEqual(beam._query, [1, 2, 3])

        ##check can remove points
        beam.remove_query_points(1, 2)
        self.assertEqual(beam._query, [3])
        beam.remove_query_points(3)
        self.assertEqual(beam._query, [])

    def test_loads(self):
        load_beam = Beam(5)

        a = PointLoad(-15000,1,0)      ##when use the add_load function this actually turns into c due to angle lol
        b = PointLoadV(-15000,1)
        c = PointLoadH(-15000,1)
        d = PointTorque(-15000,1)
        e = DistributedLoad(5000,(0,1),45)
        f = DistributedLoadV(5000,(0,1))
        g = DistributedLoadH(5000,(0,1))
        h = TrapezoidalLoad((0,1000),(0,1),45)
        i = TrapezoidalLoadV((0,1000),(0,1))
        j = TrapezoidalLoadH((0,1000),(0,1))

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

    def test_readme(self):
        # arbritrary example defined in README.md
        beam = Beam(7)                          # Initialize a Beam object of length 9 m with E and I as defaults
        beam_2 = Beam(9,E=2000, I =100000)      # Initializa a Beam specifying some beam parameters

        a = Support(5,(1,1,0))                  # Defines a pin support at location x = 5 m  
        b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0 m
        c = Support(7,(1,1,1))                  # Defines a fixed support at location x = 7 m
        beam.add_supports(a,b,c)    

        load_1 = PointLoadV(1000,2)                # Defines a point load of 1000 N acting up, at location x = 2 m
        load_2 = DistributedLoadV(2000,(1,4))      # Defines a 2000 N/m UDL from location x = 1 m to x = 4 m 
        load_3 = PointTorque(2*10**3, 3.5)            # Defines a 2*10**3 N.m point torque at location x = 3.5 m
        beam.add_loads(load_1,load_2,load_3)    # Assign the support objects to a beam object created earlier

        beam.analyse()

        # check plotting valid
        fig = beam.plot_beam_external()
        fig = beam.plot_beam_internal()

        fig = beam.plot_beam_diagram()
        fig = beam.plot_reaction_force()

        fig = beam.plot_normal_force()
        fig = beam.plot_shear_force()
        fig = beam.plot_bending_moment()
        fig = beam.plot_deflection()

        ##normal forces
        self.assertEqual(round(beam.get_normal_force(1),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_max=True),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_min=True),1), 0)
            ##shear forces
        self.assertEqual(round(beam.get_shear_force(1),1), -2381.5)
        self.assertEqual(round(beam.get_shear_force(return_max=True),1), 4618.5)
        self.assertEqual(round(beam.get_shear_force(return_min=True),1), -3069.2)
            ##bending moments
        self.assertEqual(round(beam.get_bending_moment(0),1), 0)   
        self.assertEqual(round(beam.get_bending_moment(return_max=True),1), 4092.3)
            ##deflection
        self.assertEqual(round(beam.get_deflection(3),4), 0.0036)
        self.assertEqual(round(beam.get_deflection(return_max=True),4), 0.0041)
        self.assertEqual(round(beam.get_deflection(return_min=True),4), -0.0003)

    def test_units(self):
        # test the validity of solutions when using the feature to change units
        # use read me example
        beam = Beam(7000, E = 200 * 10 **6, I = 9.05 * 10 **6)                          # Initialize a Beam object of length 9 m with E and I as defaults
        
        beam.update_units('length', 'mm')
        beam.update_units('force', 'kN')
        beam.update_units('distributed', 'kN/m')
        beam.update_units('moment', 'kN.m')
        beam.update_units('E', 'kPa')
        beam.update_units('I', 'mm4')
        beam.update_units('deflection', 'mm')
        a = Support(5000,(1,1,0))                  # Defines a pin support at location x = 5 m (x = 5000 mm)
        b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0 m
        c = Support(7000,(1,1,1))                  # Defines a fixed support at location x = 7 m (x = 7000 mm)
        beam.add_supports(a,b,c)    

        load_1 = PointLoadV(1,2000)                # Defines a point load of 1000 N (1 kN) acting up, at location x = 2 m
        load_2 = DistributedLoadV(2,(1000,4000))      # Defines a 2000 N/m (2 kN/m) UDL from location x = 1 m to x = 4 m 
        load_3 = PointTorque(2, 3500)            # Defines a 2*10**3 N.m (2 kN.m) point torque at location x = 3.5 m
        beam.add_loads(load_1,load_2,load_3)    # Assign the support objects to a beam object created earlier

        beam.analyse()

        # check plotting valid
        fig = beam.plot_beam_external()
        fig = beam.plot_beam_internal()

        fig = beam.plot_beam_diagram()
        fig = beam.plot_reaction_force()

        fig = beam.plot_normal_force()
        fig = beam.plot_shear_force()
        fig = beam.plot_bending_moment()
        fig = beam.plot_deflection()

        ##normal forces (kN)
        self.assertEqual(round(beam.get_normal_force(1000),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_max=True),1), 0)
        self.assertEqual(round(beam.get_normal_force(return_min=True),1), 0)
            ##shear forces (kN)
        self.assertEqual(round(beam.get_shear_force(1000),3), -2.382)
        self.assertEqual(round(beam.get_shear_force(return_max=True),3), 4.618)
        self.assertEqual(round(beam.get_shear_force(return_min=True),3), -3.069)
            ##bending moments (kN.m)
        self.assertEqual(round(beam.get_bending_moment(0),3), 0)   
        self.assertEqual(round(beam.get_bending_moment(return_max=True),3), 4.092)
            ##deflection
        self.assertEqual(round(beam.get_deflection(3000),1), 3.6)
        self.assertEqual(round(beam.get_deflection(return_max=True),1), 4.1)
        self.assertEqual(round(beam.get_deflection(return_min=True),1), -0.3) 

        
if __name__ == '__main__':
    unittest.main(verbosity=2)