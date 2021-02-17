import sys, os
sys.path.insert(0, os.path.abspath('../'))

from indeterminatebeam.indeterminatebeam import (
    Support, 
    Beam, 
    oo
)

from indeterminatebeam.loading import (
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
import time


##The unit testing refers to example 1 as described in the full documentation.
##In future more complex indeterminate beams should be added to ensure the validity of the program.
##In future more attention should be paid to raising error based on incorrect user values.

class BeamTestCase(unittest.TestCase):
    def test_speed(self):
        self.store_speeds = []
        self.filename_speeds = input('What is the test name?')
        # case 1
        t1 = time.perf_counter()

        beam = Beam(5)

        a = PointLoad(-15,1,0)      ##when use the add_load function this actually turns into c due to angle lol
        b = PointLoadV(-15,1)
        c = PointLoadH(-15,1)
        d = PointTorque(-15,1)
        # e = DistributedLoad(5,(0,1),45)
        # f = DistributedLoadV(5,(0,1))
        # g = DistributedLoadH(5,(0,1))
        h = TrapezoidalLoad((0,1),(0,1),45)
        i = TrapezoidalLoadV((0,1),(0,1))
        j = TrapezoidalLoadH((0,1),(0,1))

        beam.add_loads(a,b,c,d,h,i,j)
        beam.add_supports(
            Support(),
            Support(5,(1,1,0))
        )
        beam.analyse()

        fig = beam.plot_beam_external()
        fig = beam.plot_beam_internal()

        self.store_speeds.append(t1-time.perf_counter())

        # case 2
        t1 = time.perf_counter()

        beam = Beam(5)

        a = PointLoad(-15,1,0)      ##when use the add_load function this actually turns into c due to angle lol
        b = PointLoadV(-15,1)
        c = PointLoadH(-15,1)
        d = PointTorque(-15,1)
        e = DistributedLoad(5,(0,1),45)
        f = DistributedLoadV(5,(0,1))
        g = DistributedLoadH(5,(0,1))
        h = TrapezoidalLoad((0,1),(0,1),45)
        i = TrapezoidalLoadV((0,1),(0,1))
        j = TrapezoidalLoadH((0,1),(0,1))

        beam.add_loads(a,b,c,d,h,i,j)
        beam.add_supports(
            Support(),
        )

        beam.analyse()

        fig = beam.plot_beam_external()
        fig = beam.plot_beam_internal()

        self.store_speeds.append(t1-time.perf_counter())

        filename = self.filename_speeds + ".txt"

        with open(filename, 'w') as file_object:
            file_object.write(str(self.store_speeds))

        
if __name__ == '__main__':
    unittest.main(verbosity=2)