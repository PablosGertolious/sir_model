import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import Bounds

from numpy import linalg
from scipy.integrate import odeint
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()



def loadData(src):

    population = 60.36e6

    # Get Data
    baseURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"
    def downloadData(fileName, columnName):
        data = pd.read_csv(baseURL + fileName) \
                 .drop(['Lat', 'Long'], axis=1) \
                 .melt(id_vars=['Province/State', 'Country/Region'],
                     var_name='date', value_name=columnName) \
                 .astype({'date':'datetime64[ns]', columnName:'Int64'},
                     errors='ignore')
        data['Province/State'].fillna('<all>', inplace=True)
        data[columnName].fillna(0, inplace=True)
        return data

    if src==1:
        # Load data from John's Hopkins
        df = downloadData("time_series_covid19_confirmed_global.csv", "CumConfirmed").merge(downloadData("time_series_covid19_deaths_global.csv", "CumDeaths")).merge(downloadData("time_series_covid19_recovered_global.csv", "CumRecovered"))
        df.to_csv('all_data.csv')
    elif src==2:
        df = pd.read_csv('all_data.csv')
        df = df[df["Country/Region"] == "Italy"]

        S, I, R = sir_model(range(0,df.shape[0]),0.18079949, 0.04784786, 0.69894923,ics)
        sample_df = pd.DataFrame(data={'I':I,'R':R})
        df["CumInfected"] = sample_df["I"].values.tolist()
        df["CumRecovered"] = sample_df["R"].values.tolist()
        df["CumInfected"] = df["CumInfected"].apply(lambda x: x*population)
        df["CumRecovered"] = df["CumRecovered"].apply(lambda x: x*population)
        df["CumConfirmed"] = df["CumInfected"] + df["CumRecovered"] + df["CumDeaths"]

    else:
        # load data from file, for speed
        df = pd.read_csv('all_data.csv')

    # Select desired data/sort
    countries = df['Country/Region'].unique()
    countries.sort()
    country_df = df[df["Country/Region"] == "Italy"]

    country_df = country_df[["date","CumDeaths","CumConfirmed","CumRecovered"]]
    country_df["date"] = pd.to_datetime(df["date"])
    dates=country_df["date"]
    country_df.set_index("date", inplace = True)
    country_df.sort_index(inplace = True)

    country_df["CumRecovered"] = country_df["CumRecovered"].apply(lambda x: x/population)
    country_df["CumDeaths"] = country_df["CumDeaths"].apply(lambda x: x/population)
    country_df["CumConfirmed"] = country_df["CumConfirmed"].apply(lambda x: x/population)
    country_df["CumInfected"] = country_df["CumConfirmed"] - country_df["CumRecovered"] - country_df["CumDeaths"]

    if src!=2:
        country_df, dates = country_df[40:], dates[40:]

    return country_df, dates

def sir_model(t,beta,gamma,N,initalConditions):
    # Initial number of infected and recovered individuals, I0 and R0.
    I0, R0 = initalConditions[1], initalConditions[2]
    # Everyone else, S0, is susceptible to infection initially.
    S0 = N

    # The SIR model differential equations.
    def deriv(y, t, N, beta, gamma):
        S, I, R = y
        dSdt = -beta * S * I
        dIdt = beta * S * I - gamma * I
        dRdt = gamma * I
        return dSdt, dIdt, dRdt

    # Initial conditions vector
    y0 = S0, I0, R0
    # Integrate the SIR equations over the time grid, t.

    ret = odeint(deriv, y0, t, args=(N, beta, gamma))

    return ret.T

def plot_results(N,index,S,I,R,df):

    # Plot the data on three separate curves for S(t), I(t) and R(t)
    fig = plt.figure(facecolor='w')
    ax = fig.add_subplot(111, axisbelow=True)
    # ax.plot(index, S, 'b', alpha=0.5, lw=2, label='Susceptible(Model)',dashes=[3, 3, 3, 3])
    ax.plot(index, I, 'r', alpha=0.5, lw=2, label='Infected(Model)',dashes=[3, 3, 3, 3])
    ax.plot(index, R, 'g', alpha=0.5, lw=2, label='Recovered with immunity(Model)',dashes=[3, 3, 3, 3])

    ax.plot(index, country_df["CumInfected"].divide(1), 'r', alpha=0.5, lw=2, label='Infected')
    ax.plot(index, country_df["CumRecovered"].divide(1), 'g', alpha=0.5, lw=2, label='Recovered')
    ax.set_xlabel('Time /days')
    ax.set_ylabel('Percentage of Pop.')
    # ax.set_ylim(0,.002)
    legend = ax.legend()
    legend.get_frame().set_alpha(0.5)
    for spine in ('top', 'right', 'bottom', 'left'):
        ax.spines[spine].set_visible(False)
    plt.show()

def residual(x):
    S, I, R = sir_model(range(0,country_df.shape[0]),x[0],x[1],x[2],ics)

    ir_df = pd.DataFrame(data={'I':I,'R':R})
    country_df["I"]=ir_df["I"].values.tolist()
    country_df["R"]=ir_df["R"].values.tolist()

    country_df["ErrorI"] = country_df["I"] - country_df['CumInfected']
    country_df["ErrorR"] = country_df["R"] - country_df['CumRecovered']

    #residual
    rvector = np.array(country_df["ErrorI"].to_numpy() + country_df["ErrorR"].to_numpy())

    # country_df.drop(["ErrorI","ErrorR"], axis=1)
    # ir_df.drop(["I","R"], axis=1)
    return rvector

def computeDerivatives(x,r):
    df1=[]
    e = np.identity(n)

    # Computing the Jacobian
    for i in range(0,n):
        df1.append(np.array(residual(x + delta * e[i])))
    j = (np.column_stack((df1[0],df1[1],df1[2])) - np.column_stack((r,r,r)))/delta

    # Gradient
    g= np.matmul(np.transpose(j),r)
    # Approximate hessian
    h=nearestSPD(np.matmul(np.transpose(j),j))

    return g, h, j

def step_direction(g,h):
    # Steepest descent
    p=-np.divide(g,np.linalg.norm(g))
    # p = -np.matmul(np.linalg.pinv(h),g)
    return p

def step_length(x,p_k,g):
    # Random step length that results in a descent
    max_step=1
    a=max_step

    rho =.5
    c = 10**(-1)
    # TRY ALGORITHM 3.1
    # Armijo Condition
    rTest = residual(x+a*p_k)
    while (1/2 * np.dot(rTest,rTest)-f_k[k])/(a*np.dot(g,p_k))<=c:

        a=rho*a
        if a < 1e-10:
            print('*')
            break
        rTest = residual(x+a*p_k)
    return a

def quad_model(f,g,h,p):
    return f + np.matmul(g.transpose(),p) + 1/2 * np.matmul(p.transpose(),np.matmul(h,p));

def is_pos_def(x):
    return np.all(np.linalg.eigvals(x) > 0)

def nearestSPD(A):
    L, Q = np.linalg.eig(A)
    t=[]
    for i in range(0,len(L)):

        if L[i] >= delta:
            t.append(0)
        else:
            t.append(delta - L[i])
    return A + np.matmul(Q,np.matmul(np.diag(t),Q.transpose()))


# Initialized variables
k_max=2
n=3
x = np.zeros([k_max+1,n]);
# x[0] =  [0.18124844, 0.05229869, 0.69905675]# [2.03393267e-05]
x[0] =  [0.22769259, 0.09338566, 0.71232997] #[1.78672562e-05]

# [S0, I0, R0]
ics=[x[0][2],3e-5,3e-6]

# src=1 for from text file, 2 for from a known model, and 3 from the online database
country_df, dates = loadData(1)
delta = 1e-8
f_k = np.zeros([k_max+1,1]);

max_radius = .01
radius_k = np.zeros([k_max+1,1]);
radius_k[0] = max_radius

ada = 1/4

r = residual(x[0])
f_k[0] = 1/2 * np.dot(r,r)
for k in range(0,k_max-1):
    g, h, j = computeDerivatives(x[k],r)
    # Minimizes the quadratic model
    x0 = np.array([0,0,0])

    def model_der(x):
        return g
    def model_hess(x):
        return h
    def model(p):
        return quad_model(f_k[k],g,h,p)

    bounds = Bounds(radius_k[k]*[-1, -1, -1], radius_k[k]*[1, 1, 1])
    res = minimize(model, x0, method='trust-constr', jac=model_der, hess=model_hess, bounds=bounds)

    p=res.x
    rp = residual(x[k]+p)
    fp = 1/2 * np.dot(rp,rp)

    m = model(p)

    rho = (f_k[k] - fp)/(f_k[k] - m)
    # print(rho)

    if rho < 1/4:
        # bad agreement between the model and the function
        radius_k[k+1] = (1/4)*radius_k[k]
        print("bad")
    else:
        if rho > (3/4):
            # Great agreement between the model and the function
            radius_k[k+1] = min(2*radius_k[k],max_radius)
            print("great")
        else:
            # good agreement between the model and the function
            radius_k[k+1] = radius_k[k]
            print("good")

    if rho > ada:
        x[k+1] = x[k] + p
        r = residual(x[k+1])
    else:
        x[k+1] = x[k]

    f_k[k+1] = 1/2 * np.dot(r,r)
    print(f_k[k+1]-f_k[k],x[k+1],k)

print('We just stopped at ',x[k],f_k[k])


S, I, R = sir_model(range(0,country_df.shape[0]),x[k+1][0],x[k+1][1],x[k+1][2],ics)
plot_results(x[k][2],dates,S,I,R,country_df)

# Plotting xk sequence.

xs = np.transpose(x[0:k+2])[0]
ys =np.transpose(x[0:k+2])[1]
zs =np.transpose(x[0:k+2])[2]
fs = np.array(f_k[0:k+2])

# 3D plot with f(x) on the z-axis
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('beta')
ax.set_ylabel('gamma')
ax.set_zlabel('N')

ax.scatter(xs, ys, zs)

plt.show()