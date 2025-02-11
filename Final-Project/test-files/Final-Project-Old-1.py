import numpy as np
import matplotlib.pyplot as plt

fileName = "Final-Project"

height = 200
width = 500

num_time_steps = 1

cylinder_diameter = 50
cylinder_radius = cylinder_diameter / 2
cylinder_center = [(height / 2), 100]

error_limit = 0.01                  # 1% maximum change for convergence

U_inf = 2                           # m/s uniform inflow
F = 1.9                             # over-relaxation factor
free_lid = U_inf * (height / 2)     # free-lid streamfunction constant

Re_D = 200                          # Given Reynolds number

T_surface = 400                     # K
T_boundary = 300                    # K
T_init = min(T_surface, T_boundary) # Bulk fluid initial temp

# Constants picked for air around room temp
rho = 3000              # kg/m^3
c = 840                 # J/(kg*C)
#h = 28                  # W/(m^2*C)  Convective Heat Transfer Coefficient
k = 5.2                 # W/(m*C)    Thermal Conductivity
alpha = k / (rho * c)   # m^2/s      Thermal Diffusivity
nu = 1.48 * 10**(-5)    # m^s/s      kinematic viscosity

h_1 = 9 * nu / U_inf #10 * nu / U_inf
h_2 = 9 * alpha / U_inf #10 * alpha / U_inf
h = min(h_1, h_2)       # grid spacing

dt = (h / U_inf) / 2


omega = np.zeros((width, height))           # vorticity
psi = np.zeros((width, height))             # streamfunction
temp = np.zeros((width, height)) + T_init   # temperature


def in_circle(x, y): 
    """ Determine if parameters x and y are in the cylinder's 2d circle profile. """
    dist = np.sqrt((x - cylinder_center[0])**2 + (y - cylinder_center[1])**2)
    if (dist <= cylinder_radius):
        return True
    return False

def is_boundary_condition(x, y):
    """ @return: True if (x,y) is a position determined by boundary conditions. """
    if (y == 0):
        return True
    if (y == (height - 1)):
        return True
    if (x == 0):
        return True
    if (x == (width - 1)):
        return True
    if in_circle(x, y):
        return True
    return False

def solid_boundary(x, y, checked = False):
    """ 
    Determine if (x,y) is a point along the wall of a solid body.

    @param checked: False if checking whether the point is a solid body.
                    True if determining what the adjacent free (outside of solid body) point is. 
    
    @return: if checked = False: True if a wall point (adjacent to fluid) of body.
             if checked = True: returns (x, y) values of the adjacent point in the fluid (i.e. outside of the solid body).
    """
    if not checked: 
        if in_circle(x, y) and (not in_circle(x - 1, y) or not in_circle(x + 1, y) or not in_circle(x, y - 1) or not in_circle(x, y + 1)): 
            return True
    if checked: 
        if in_circle(x, y):
            if not in_circle(x - 1, y):
                return (x - 1, y)
            if not in_circle(x + 1, y):
                return (x + 1, y)
            if not in_circle(x, y - 1):
                return (x, y - 1)
            if not in_circle(x, y + 1):
                return (x, y + 1)
    return False

def is_outflow_boundary(x, y):
    """ Determine if (x,y) is at outflow boundary. """
    if (x == (width - 1)) and (y != 0) and (y != (height - 1)):
        return True
    return False

def gauss_seidel_iteration(data, error_limit, omega = "", initial = False):
    """ 
    Perform Gauss-Seidel Iteration 

    @param data: 2D array (width, height) of values to be relaxed by Gauss-Seidel Iteration
    @param omega (necesary not necessary for initial): omega array used to calculate new psi.
    @param initial: Determines which Poisson/Laplacian equation will be used.

    @return: Data array post-relaxation iteration (same dimensions as @param data). 
    """
    error_flag = True
    while error_flag:
        large_error_term_found = False

        for i in range(width):
            for j in range(height): 
                datum_old = data[i, j]

                if not is_boundary_condition(i, j):
                    datum_old = data[i, j]
                    if initial:
                        data[i, j] = data[i, j] + (F / 4) * (data[i + 1, j] + data[i - 1, j] + data[i, j + 1] + data[i, j - 1] - 4 * data[i, j])
                    else:
                        data[i, j] = data[i, j] + (F / 4) * (data[i + 1, j] + data[i - 1, j] + data[i, j + 1] + data[i, j - 1] + 4 * (h ** 2) * omega[i, j] - 4 * psi[i, j]) 
                    
                    if not large_error_term_found:
                        error_term = abs((data[i, j] - datum_old) / datum_old)
                        if (error_term <= error_limit):
                            error_flag = False
                        else:
                            error_flag = True
                            large_error_term_found = True
                
                if (i == 1):
                    psi[0, j] = psi[i + 2, j]
                elif (i == (width - 2)):
                    psi[i + 1, j] = psi[i, j]
    return data



###############################################################
#  Initial Conditions
###############################################################
for i in range(width):
    for j in range(height):
        if in_circle(i, j):
            psi[i, j] = 0
            temp[i, j] = T_surface
            
        # establish initial uniform gradient in psi
        if not is_boundary_condition(i, j):
            psi[i, j] = U_inf * j - free_lid
        
        # # Boundary Conditions for psi
        # if (i == 1):
        #         psi[0, j] = psi[i + 2, j]
        # elif (i == (width - 2)):
        #     psi[i + 1, j] = psi[i, j]

    psi[i, cylinder_center[1]] = 0 
    psi[i, 0] = -free_lid
    psi[i, (height - 1)] = free_lid

    omega[i, 0] = T_boundary
    omega[i, (height - 1)] = T_boundary

# psi = gauss_seidel_iteration(psi, error_limit, initial = True)



###############################################################
#  Initial Conditions established, now "turn on" vorticity
###############################################################
u = np.zeros((width, height))
v = np.zeros((width, height))

omega_history = [omega.copy()]
psi_history = [psi.copy()]
temp_history = [temp.copy()]


# for n in range(1, num_time_steps):
#     for i in range(width):
#         for j in range(height):
#             if not is_boundary_condition(i, j):
#                 # Bulk Fluid
#                 u[i, j] = (psi[i, j + 1] - psi[i, j - 1]) / (2 * h)
#                 v[i, j] = (psi[i - 1, j] - psi[i + 1, j]) / (2 * h)

#                 delta_u_omega = 0
#                 if (u[i, j] < 0):
#                     delta_u_omega = u[i + 1, j] * omega[i + 1, j] - u[i, j] * omega[i, j]
#                 elif (u[i, j] > 0):
#                     delta_u_omega = u[i, j] * omega[i, j] - u[i - 1, j]
                    
#                 delta_v_omega = 0
#                 if (v[i, j] < 0):
#                     delta_v_omega = v[i, j + 1] * omega[i, j + 1] - v[i, j] * omega[i, j]
#                 elif (v[i, j] > 0):
#                     delta_v_omega = v[i, j] * omega[i, j] - v[i, j - 1] * omega[i, j - 1]

#                 vorticity_laplacian = (omega[i + 1, j] + omega[i - 1, j] + omega[i, j + 1] + omega[i, j - 1] - 4 * omega[i, j]) / (h ** 2)

#                 omega[i, j] = omega[i, j] + dt * (-delta_u_omega / h - delta_v_omega / h + nu * vorticity_laplacian)


#                 psi = gauss_seidel_iteration(psi, error_limit, omega)


#                 u_delta_T = 0
#                 if (u[i, j] < 0):
#                     u_delta_T = u[i, j] * (temp[i + 1, j] - temp[i, j])
#                 elif (u[i, j] < 0): 
#                     u_delta_T = u[i, j] * (temp[i, j] - temp[i - 1, j])

#                 v_delta_T = 0
#                 if (v[i, j] < 0):
#                     v_delta_T = v[i, j] * (temp[i, j + 1] - temp[i, j])
#                 elif (v[i, j] > 0):
#                     v_delta_T = v[i, j] * (temp[i, j] - temp[i, j - 1])
                
#                 temp_laplacian = (temp[i + 1, j] + temp[i - 1, j] + temp[i, j + 1] + temp[i, j - 1] - 4 * temp[i, j]) / (h ** 2)

#                 temp[i, j] = temp[i, j] + dt * (- u_delta_T / h - v_delta_T / h + alpha * temp_laplacian)

#             if solid_boundary(i, j, checked = False):
#                 (adj_ext_pt_x, adj_ext_pt_y) = solid_boundary(i, j, checked = True)
#                 omega[i, j] = -2 * (psi[adj_ext_pt_x, adj_ext_pt_y] - psi[i, j]) / (h ** 2)

#             if is_outflow_boundary(i, j):
#                 psi[i, j] = 2 * psi[i - 1, j] - psi[i - 2, j]
#                 omega[i, j] = omega[i - 1, j]
            

#     omega_history.append(omega.copy())
#     psi_history.append(psi.copy())
#     temp_history.append(temp.copy())



###############################################################
#  Graphs and Plots
###############################################################
def print_data_in_console():
    """ Print the data in the console (readable format) """
    print(np.rot90(psi))
# print_data_in_console()

def plot_streamlines():
    data_graphable = np.flipud(np.rot90(psi))

    fig = plt.figure(figNum)
    plt.axes().set_aspect('equal')


    num_streamlines = 31
    max_streamline = np.max(data_graphable)
    min_streamline = np.min(data_graphable)
    contours_before = np.linspace(min_streamline, max_streamline, num=(num_streamlines + 3))
    contours = contours_before[(contours_before != 0) & (contours_before != min_streamline) & (contours_before != max_streamline)]

    plt.contour(data_graphable, levels = contours, colors = 'black', linestyles = 'solid')


    plt.xlim(0, width)
    plt.ylim(0, height)
    plt.xticks(np.arange(0, width + 1, 50))
    plt.yticks(np.arange(0, height + 1, 20))
    plt.tick_params(top=True, right=True)

    plt.style.use('grayscale')
    heatmap = plt.pcolor(data_graphable)
    plt.clim(np.amin(data_graphable), np.amax(data_graphable))

    plt.savefig(fileName + "/images/" + fileName + "-Figure-" + str(figNum) + ".png")
    plt.show()

def plot_vorticity(fig, sub_num):
    data_graphable = np.flipud(np.rot90(omega))

    plt.figure(figNum)
    plt.axes().set_aspect('equal')
    plt.style.use('classic')

    heatmap = plt.pcolor(data_graphable)

    plt.axis("off")

    plt.xlim(0, width)
    plt.ylim(0, height)

    cbar = plt.colorbar(heatmap)
    cbar.set_label("Temperature (\N{DEGREE SIGN}C)")
    plt.clim(np.amin(data_graphable), np.amax(data_graphable))

    plt.savefig(fileName + "/images/" + fileName + "-Figure-" + str(figNum) + ".png")
    plt.show()

def plot_temperatures():
    data_graphable = np.flipud(np.rot90(temp))

    plt.figure(figNum)
    plt.axes().set_aspect('equal')
    plt.style.use('classic')

    heatmap = plt.pcolor(data_graphable)

    plt.axis("off")

    plt.xlim(0, width)
    plt.ylim(0, height)

    cbar = plt.colorbar(heatmap)
    cbar.set_label("Temperature (\N{DEGREE SIGN}C)")
    plt.clim(np.amin(data_graphable), np.amax(data_graphable))

    plt.savefig(fileName + "/images/" + fileName + "-Figure-" + str(figNum) + ".png")
    plt.show()


figNum = 1

# fig, (sub1, sub2, sub3) = plt.subplots(3, 1)

fig = plt.figure(figNum)
sub1 = fig.add_subplot(311)
sub2 = fig.add_subplot(312)
sub3 = fig.add_subplot(313)

##### Steamfunction Plot #####
# sub1 = plt.subplot(3, 1, 1, aspect = 'equal')
data_graphable = np.flipud(np.rot90(psi))

sub1.set_title("Streamfunction")

num_streamlines = 31
max_streamline = np.max(data_graphable)
min_streamline = np.min(data_graphable)
contours_before = np.linspace(min_streamline, max_streamline, num=(num_streamlines + 3))
contours = contours_before[(contours_before != 0) & (contours_before != min_streamline) & (contours_before != max_streamline)]

sub1.contour(data_graphable, levels = contours, colors = 'black', linestyles = 'solid')


plt.style.use('grayscale')
sub1.set_xticks(np.arange(0, width + 1, 50))
sub1.set_yticks(np.arange(0, height + 1, 20))
sub1.tick_params(top=True, right=True)

# plt.axis("off")

sub1.pcolor(data_graphable)
# plt.colorbar()

# fig.colorbar(sub1.imshow(np.flipud(data_graphable)), ax = sub1)
fig.colorbar(sub1.imshow(data_graphable, origin='lower', interpolation='none', aspect = 'auto'), ax = sub1)




##### Vorticity Plot #####
# sub2 = plt.subplot(3, 1, 2, aspect = 'equal')
data_graphable = np.flipud(np.rot90(omega))

sub2.set_title("Vorticity")

# plt.style.use('grayscale')
# plt.xticks(np.arange(0, width + 1, 50))
# plt.yticks(np.arange(0, height + 1, 20))
# plt.tick_params(top=True, right=True)
plt.axis("off")

sub2.pcolor(data_graphable)
# sub2.colorbar()
# fig.colorbar(sub2.imshow(data_graphable, interpolation = 'none'), ax = sub2)
fig.colorbar(sub2.imshow(data_graphable, origin='lower', interpolation='none', aspect = 'auto'), ax = sub2)



##### Temperature Plot #####
# sub3 = plt.subplot(3, 1, 3, aspect = 'equal')
data_graphable = np.flipud(np.rot90(temp))

sub3.set_title("Temperature")


plt.style.use('classic')
# plt.xticks(np.arange(0, width + 1, 50))
# plt.yticks(np.arange(0, height + 1, 20))
# plt.tick_params(top=True, right=True)
plt.axis("off")
sub3.pcolor(data_graphable)
fig.colorbar(sub3.imshow(data_graphable, origin='lower', interpolation='none', aspect = 'auto'),ax = sub3)

# fig.colorbar(data_graphable, ax = sub3)
# fig.colorbar(sub3.imshow(data_graphable), ax = sub3)




# plt.axes().set_aspect('equal')


plt.savefig(fileName + "/images/" + fileName + "-Figure-" + str(figNum) + ".png")
plt.show()

