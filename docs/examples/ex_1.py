# RUN THIS CELL FIRST TO INITIALISE GOOGLE NOTEBOOK!!!!
!pip install indeterminatebeam
%matplotlib inline

# import beam and supports
from indeterminatebeam import Beam, Support

# import loads (all load types imported for reference)
from indeterminatebeam import (
    PointTorque,
    PointLoad,
    PointLoadV,
    PointLoadH,
    UDL,
    UDLV,
    UDLH,
    TrapezoidalLoad,
    TrapezoidalLoadV,
    TrapezoidalLoadH,
    DistributedLoad,
    DistributedLoadV,
    DistributedLoadH
)

# Note: load ending in V are vertical loads
# load ending in H are horizontal loads
# load not ending in either takes angle as an input (except torque)
