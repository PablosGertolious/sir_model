
import pandas as pd
import numpy as np
from numpy import linalg
from scipy.optimize import minimize
from scipy.integrate import odeint
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pandas.plotting import register_matplotlib_converters

from numpy import genfromtxt
from numpy import recfromcsv

n=5

r = np.array([ 0.79,0.78808938,0.78591626,0.7834463,0.78064114,0.77745805,0.77384974,0.76976402,0.76514366,0.75992621,0.75404413,0.74742492,0.73999156,0.73166322,0.72235628,0.71198575,0.70046716,0.68771887,0.67366497,0.65823856,0.64138546,0.62306824,0.6032703,0.58199978,0.55929305,0.53521732,0.50987214,0.48338934,0.45593144,0.42768814,0.3988712,0.3697079,0.34043347,0.31128313,0.282484,0.25424812,0.22676632,0.20020352,0.17469604,0.15035005,0.12724239,0.10542139,0.08490967,0.06570762,0.04779632,0.03114108,0.01569735,0.00140765,-0.01178756,-0.02395396,-0.03516184,-0.04546731,-0.05494743,-0.06365787,-0.07166258,-0.07901849,-0.08577703,-0.09199118,-0.09770321,-0.1029565,-0.10779551,-0.1122548,-0.1163642,-0.12015717,-0.12365968,-0.12689376,-0.12988605,-0.13265891,-0.13522796,-0.13761075,-0.13982497,-0.14188233,-0.14379604,-0.14557922,-0.1472436,-0.14879437,-0.15024265,-0.1515969,-0.15286226,-0.15404713,-0.15515612,-0.15619868,-0.15717454,-0.15808998,-0.15895025,-0.15975975,-0.16052034,-0.16123771,-0.16191416,-0.16255131,-0.16315079,-0.16371789,-0.16425276,-0.16475861,-0.16523667,-0.16569117,-0.16611995,-0.16652491,-0.16690922,-0.16727383,-0.16761959,-0.16794395,-0.16825633])

print(len(np.append(r,r)))
