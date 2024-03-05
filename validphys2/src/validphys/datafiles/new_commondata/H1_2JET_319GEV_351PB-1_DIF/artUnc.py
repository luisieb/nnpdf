import numpy
import yaml

# The following is the correlation matrix as an array for jet and dijet that was obtained by hand
# from the paper, it was not implemented as the paper does not make it clear whether it corresponds
# to sys, stat or both. It is however kept to avoid redoing the by-hand copying of the matrix
# if the information mentioned above is made clear in the future.

corMatArray = [
    100,-20,-11,-2,-14,2,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,1,-2,0,-5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
-20,100,2,-1,4,-13,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-6,25,-1,-1,1,-3,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
-11,2,100,6,1,0,-13,-1,0,0,2,0,0,0,0,0,0,0,1,0,0,0,0,0,-1,-3,48,1,0,0,-6,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,
-2,-1,6,100,0,0,0,-14,0,0,0,2,0,0,0,0,0,0,0,1,0,0,0,1,0,1,-6,71,0,0,0,-10,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,
-14,4,1,0,100,-21,-10,-2,-11,2,1,0,-1,0,0,0,-1,0,0,0,0,0,0,0,-5,0,0,0,34,0,-1,0,-4,0,0,0,-1,0,0,0,-1,0,0,0,0,0,0,0,
2,-13,0,0,-21,100,2,-1,3,-10,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,1,-4,0,0,-7,27,-1,0,1,-3,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,
1,0,-13,0,-10,2,100,7,1,1,-12,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,-7,0,-1,-3,49,-2,0,1,-6,0,0,0,0,0,0,0,-1,0,0,0,0,0,
0,0,-1,-14,-2,-1,7,100,0,0,0,-11,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,1,-11,0,-1,-1,69,0,0,1,-7,0,0,0,0,0,0,0,-1,0,0,0,0,
1,0,0,0,-11,3,1,0,100,-23,-12,-2,-8,1,1,0,-1,0,0,0,0,0,0,0,1,0,0,0,-5,1,0,0,35,1,-1,0,-3,0,0,0,0,0,0,0,0,0,0,0,
0,2,0,0,2,-10,1,0,-23,100,0,-2,2,-8,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,-3,0,0,-6,25,0,-2,0,-2,0,0,0,-1,0,0,0,0,0,0,
0,0,2,0,1,0,-12,0,-12,0,100,5,1,1,-8,0,0,0,-1,0,0,0,0,0,0,0,1,0,0,1,-7,0,-1,-5,51,-1,0,0,-5,0,0,0,-1,0,0,0,-1,0,
0,0,0,2,0,0,0,-11,-2,-2,5,100,0,0,0,-8,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,-8,0,-1,-3,66,0,0,0,-6,0,0,0,-1,0,0,0,0,
0,0,0,0,-1,0,0,0,-8,2,1,0,100,-22,-11,-2,-4,1,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,-3,1,0,0,35,0,-1,0,-2,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,1,-8,1,0,-22,100,-1,-2,1,-4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-2,0,0,-6,25,-1,-1,0,-2,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,1,0,-8,0,-11,-1,100,5,0,1,-4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4,0,-1,-2,48,-3,0,0,-3,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,-8,-2,-2,5,100,0,0,0,-5,0,0,0,0,0,0,0,0,0,0,0,-1,0,0,0,-6,1,-1,-1,70,0,0,1,-4,0,0,0,1,
0,0,0,0,-1,0,0,0,-1,0,0,0,-4,1,0,0,100,-24,-12,-2,-1,0,0,0,1,0,0,0,-1,0,0,0,0,0,0,0,-2,0,0,0,32,1,-1,0,0,0,0,0,
0,0,0,0,0,-1,0,0,0,0,0,0,1,-4,1,0,-24,100,1,-2,0,-1,0,0,0,0,0,0,0,-1,0,0,0,0,1,0,0,-2,1,0,-7,24,-1,0,0,0,0,0,
0,0,1,0,0,0,-1,0,0,0,-1,0,0,0,-4,0,-12,1,100,3,0,0,-1,0,0,0,1,0,0,0,-1,0,0,0,-1,0,0,0,-3,1,-1,-4,50,-2,0,0,-1,0,
0,0,0,1,0,0,0,-1,0,0,0,0,0,0,0,16,-2,-2,3,100,0,0,0,-2,0,0,0,1,0,0,0,-1,0,0,1,-1,0,0,0,-4,0,0,-8,73,0,0,0,-2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,0,0,100,-21,-15,-3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,2,-2,-1,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,0,-21,100,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-8,21,0,-2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-15,-1,100,-2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-3,-3,44,-7,
0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-2,-3,0,-2,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,0,-2,-2,66,
35,-6,-1,0,-5,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,100,-44,11,3,-3,6,-2,0,11,-1,0,0,9,0,0,0,8,0,0,0,2,0,0,0,
1,25,-3,1,0,-4,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-44,100,-36,-9,7,-13,5,1,-1,2,-1,0,0,1,0,0,0,1,0,0,0,0,0,0,
-2,-1,48,-6,0,0,-7,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,11,-36,100,6,-1,4,-14,0,0,-1,2,0,0,0,1,0,0,0,1,0,0,0,1,0,
0,-1,1,71,0,0,0,-11,0,0,0,2,0,0,0,0,0,0,0,1,0,0,0,0,3,-9,6,100,0,1,0,-14,0,0,0,2,0,0,0,0,0,0,0,1,0,0,0,1,
-5,1,0,0,34,-7,-1,0,-5,1,0,0,-1,0,0,0,-1,0,0,0,0,0,0,0,-3,7,-1,0,100,-44,10,2,-4,6,-1,0,4,1,0,0,4,1,0,0,1,0,0,0,
0,-3,0,0,0,27,-3,-1,1,-3,1,0,1,0,0,0,0,-1,0,0,0,0,0,0,6,-13,4,1,-44,100,-34,-8,7,-11,4,1,1,-1,0,0,2,-1,0,0,0,0,0,0,
0,0,-6,0,-1,-1,49,-1,0,0,-7,0,0,0,0,0,0,0,-1,0,0,0,0,0,-2,5,-14,0,10,-34,100,2,-1,4,-12,0,0,0,0,0,0,0,-1,0,0,0,-1,0,
0,0,0,-10,0,0,-2,69,0,0,0,-8,0,0,0,-1,0,0,0,-1,0,0,0,0,0,1,0,-14,2,-8,2,100,0,1,1,-11,0,0,0,0,0,0,1,-2,0,1,1,0,
1,0,0,0,-4,1,0,0,35,-6,-1,0,-3,1,0,0,0,0,0,0,0,0,0,0,11,-1,0,0,-4,7,-1,0,100,-47,11,3,-3,5,-1,0,4,1,0,0,1,0,0,0,
0,1,0,0,0,-3,1,0,1,25,-5,-1,1,-2,0,0,0,0,0,0,0,0,0,0,-1,2,-1,0,6,-11,4,1,-47,100,-34,-10,5,-8,3,1,1,0,0,0,0,0,0,0,
0,0,1,0,0,0,-6,1,-1,0,51,-3,0,0,-4,0,0,1,-1,1,0,0,0,0,0,-1,2,0,-1,4,-12,1,11,-34,100,2,-1,3,-8,0,0,0,-1,1,0,0,-1,0,
0,0,0,1,0,0,0,-7,0,-2,-1,66,0,0,0,-6,0,0,0,-1,0,0,0,0,0,0,0,2,0,1,0,-11,3,-10,2,100,0,1,0,-9,0,0,0,-1,0,0,0,0,
0,0,0,0,-1,0,0,0,-3,0,0,0,35,-6,-1,1,-2,0,0,0,0,0,0,0,9,0,0,0,4,1,0,0,-3,5,-1,0,100,-45,11,3,-1,3,0,0,1,0,0,0,
0,0,0,0,0,0,0,0,0,-2,0,0,0,25,-2,-1,0,-2,0,0,0,0,0,0,0,1,0,0,1,-1,0,0,5,-8,3,1,-45,100,-36,-11,3,-4,2,1,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,-5,0,-1,-1,48,-1,0,1,-3,0,0,0,0,0,0,0,1,0,0,0,0,0,-1,3,-8,0,11,-36,100,4,0,2,-5,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,-6,0,-1,-3,70,0,0,1,-4,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,-9,3,-11,4,100,0,0,1,-6,0,0,1,1,
0,0,0,0,-1,0,0,0,0,0,0,0,-2,0,0,0,32,-7,-1,0,0,0,0,0,8,0,0,0,4,2,0,0,4,1,0,0,-1,3,0,0,100,-46,10,2,1,1,0,0,
0,0,0,0,0,-1,0,0,0,-1,0,0,0,-2,0,0,1,24,-4,0,0,0,0,0,0,1,0,0,1,-1,0,0,1,0,0,0,3,-4,2,0,-46,100,-35,-8,1,-1,0,0,
0,0,0,0,0,0,-1,0,0,0,-1,0,0,0,-3,1,-1,-1,50,-8,0,0,-1,0,0,0,1,0,0,0,-1,1,0,0,-1,0,0,2,-5,1,10,-35,100,-3,0,1,-1,-1,
0,0,0,0,0,0,0,-1,0,0,0,-1,0,0,0,-4,0,0,-2,73,0,0,0,-1,0,0,0,1,0,0,0,-2,0,0,1,-1,0,1,0,-6,2,-8,-3,100,0,0,1,2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,-8,-3,0,2,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,1,0,0,100,-41,7,2,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,21,-3,-2,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,-1,1,0,-41,100,-36,-9,
0,0,0,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,-1,0,-2,0,44,-2,0,0,1,0,0,0,-1,1,0,0,-1,0,0,0,0,1,0,0,-1,1,7,-36,100,-13,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,-2,-1,-2,-7,66,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,-1,2,2,-9,-13,100
]

