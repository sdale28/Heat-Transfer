close all

height = 200;
width = 500;

num_time_steps = 20;

cylinder_diameter = 50;
cylinder_radius = cylinder_diameter / 2;
cylinder_center_x = height / 2;
cylinder_center_y = height / 2;

error_limit = 0.01;                  % 1% maximum change for convergence

U_inf = 0.01;                        % m/s      uniform inflow
alpha = 22.07 * 10^(-6);             % m^2/s    Thermal Diffusivity at 300K
nu = 1.48 * 10^(-5);                 % m^2/s    Kinematic Viscosity at 300K
F = 1.9;                             %          over-relaxation factor
free_lid = U_inf * (height / 2);     %          free-lid streamfunction constant

Re_D = 200;                          % Given Reynolds number

T_surface = 400;                     % K
T_boundary = 300;                    % K
T_init = min(T_surface, T_boundary); % Bulk fluid initial temp

h_1 = (10 - 1) * nu / U_inf;
h_2 = (10 - 1) * alpha / U_inf;
h = min(h_1, h_2)       % grid spacing

dt = (h / U_inf) / 2


omega = zeros(width, height);
psi = zeros(width, height);
temps = zeros(width, height);


solid_points = zeros(width, height);
for i = 1:width
    for j = 1:height
        dist = sqrt((i - cylinder_center_x)^2 + (j - cylinder_center_y)^2);
        if dist <= cylinder_radius
            solid_points(i, j) = 1;
            temps(i, j) = T_surface;
        else
            temps(i, j) = T_boundary;
%             psi = U_inf * j - free_lid;
            psi(i, j) = (U_inf * j - free_lid) * h;
        end
        
        
        
    end
end



error_flag = true;
while error_flag
    psi_old = psi;
    
    for i = 2:(width - 1)
        for j = 2:(height - 1)
            if ~solid_points(i,j)
                psi(i, j) = psi(i, j) + (F / 4) * (psi(i - 1, j) + psi(i + 1, j) + psi(i, j - 1) + psi(i, j + 1) - 4 * psi(i, j));
            end
        end
    end
    
%     psi(0, :) = psi(3, :);
    
    error_array = abs(psi - psi_old) ./ psi_old;
    error_array(isnan(error_array)) = 0;
    
    error_term = max(error_array);
    
    if (error_term <= error_limit)
        error_flag = false;
    end
    
end



for time_step = 1:num_time_steps
    for i = 2: (width - 1)
        for j = 2: (height - 1)
            if solid_points(i, j) == 1
                omega(i, j) = -2 / (h * h) * (psi(i - 1, j) + psi(i + 1, j) + psi(i, j - 1) + psi(i, j + 1));
            end
        end
    end
    
end



















% figure(1)
% hold on
% plot_data = flipud(rot90(psi));
% s = pcolor(plot_data);
% daspect([1 1 1]);
% colormap(gray);
% set(s, 'EdgeColor', 'none');
% colorbar
% contour(plot_data, 32, 'black');
% 
% hold off





figure(2)
hold on
plot_data = flipud(rot90(omega));
s = pcolor(plot_data);
daspect([1 1 1]);
colormap(gray);
set(s, 'EdgeColor', 'none');
colorbar

hold off



% figure(2)
% hold on
% s = pcolor(flipud(rot90(psi)));
% daspect([1 1 1]);
% colormap(gray);
% set(s, 'EdgeColor', 'none');
% colorbar
% 
% 
% plot_data = flipud(rot90(psi));
% contour(plot_data, 32, 'black');
% 
% hold off

