
from matplotlib.pylab import plot, figure, show, ylim, cm, axis, xlabel, ylabel, legend, xlim
from networkx import Graph, spectral_layout, draw_networkx_nodes, draw_networkx_labels, draw_networkx_edges, spring_layout
from numpy import amax, amin, append, arange, empty, frompyfunc, where, zeros

from ..helper_functions import generate_n_colors
from ..model_components.power_network import PowerNetwork


class Plotter(object):
    
    def __init__(self, power_network, cmap='Accent'):
        if isinstance(power_network, PowerNetwork) is False:
            raise TypeError('')
        else:
            self.network = power_network
        
        self.cmap = getattr(cm, cmap)
        color_gen = generate_n_colors(len(self.network), self.cmap)

        self.network_graph = Graph()
        
        for bus in self.network:
            hex_color, color_num = next(color_gen)
            self.network_graph.add_node(bus,
                                        hex_color=hex_color,
                                        color_num=color_num)

            if bus.has_generator_model() is True:
                model_label = r'$G_%i$' % bus.get_id()
            else:
                model_label = r'$L_%i$' % bus.get_id()
            self.network_graph.add_node(bus.model, hex_color=hex_color, color_num=color_num, label=model_label)
            self.network_graph.add_edge(bus, bus.model)
        
        for power_line in self.network.power_lines:
            bi, bj = power_line.get_incident_buses()
            Gij, Bij = self.network.get_admittance_value_from_bus_ids(bi.get_id(), bj.get_id())
            self.network_graph.add_edge(bi, bj, g=Gij, b=Bij)


    def draw_power_network_graph(self):
        pos = spectral_layout(self.network_graph)
        bus_node_list = [bus for bus in self.network]
        color_nums = []
        model_node_list = []
        bus_label_list = {}
        model_label_list = {}
        bus_model_edge_list = []
        
        for bus in bus_node_list:
            color_nums.append(self.network_graph.node[bus]['color_num'])
            model_node_list.append(bus.model)
            bus_label_list[bus] = r'$B_%i$' % bus.get_id()
            model_label_list[bus.model] = self.network_graph.node[bus.model]['label']
            bus_model_edge_list.append((bus, bus.model))
            
        power_line_edge_list = []
        for power_line in self.network.power_lines:
            power_line_edge_list.append(power_line.get_incident_buses())
        
        draw_networkx_nodes(self.network_graph, pos, nodelist=bus_node_list, node_size=1000, cmap=cm.Accent, node_color=color_nums)
        draw_networkx_nodes(self.network_graph, pos, nodelist=model_node_list, node_size=750, cmap=cm.Accent, node_color=color_nums)
        draw_networkx_labels(self.network_graph, pos , bus_label_list, font_size=14, nodelist=bus_node_list)
        draw_networkx_labels(self.network_graph, pos , model_label_list, font_size=10, nodelist=model_node_list)
        draw_networkx_edges(self.network_graph, pos, edgelist=bus_model_edge_list, width=3)
        draw_networkx_edges(self.network_graph, pos, edgelist=power_line_edge_list, width=6)
        axis('off')
        

    def generate_tikz_preamble(self, xmin, xmax, ymin, ymax, x_label, y_label, colors=[]):
        ydist = abs(ymax-ymin)
        if ymin != 0.:
            ymin += 0.1*ymin
        else:
            ymin -= 0.05*ydist

        if ymax != 0.:
            ymax += 0.1*ymax
        else:
            ymax += 0.05*ydist

        preamble = [r'\begin{tikzpicture}']
        preamble.extend(colors)
        preamble.extend([r'\begin{axis}[',
            r'xlabel={{0}},'.format(x_label),
            r'ylabel={{0}},'.format(y_label),
            'xmin={0:.3f}, xmax={1:.3f},'.format(xmin, xmax),
            'ymin={0:.5f}, ymax={1:.5f},'.format(ymin, ymax),
            'axis on top,',
            r'width=\figurewidth,',
            r'height=\figureheight]',
            ''
        ])
        return preamble
        
    
    def generate_color_defintion(self, color_name, color_num):
        r, g, b = self.cmap(color_num)[0:3]
        return r'\definecolor{{{0}}}{{rgb}}{{{1:.5f},{2:.5f},{3:.5f}}}'.format(color_name, r, g, b)


    def plot_bus_voltage_angles(self, t_vector, output_tikz=False, rnd=4):
        fig = figure()
        ax = fig.add_subplot(111)
        labels = []
        x_label = 'time, ' + r'$t$' + ' [s]'
        y_label = r'$\theta$ [rad]'
        if output_tikz is True:
            xmin = t_vector[0]
            xmax = t_vector[-1]
            ymin = 0
            ymax = 0
            thetas = []
            color_names = []
            tikz_colors = []

        for bus in self.network:
            color = self.network_graph.node[bus]['hex_color']
            if output_tikz is True:
                ymin = min(ymin, amin(bus.theta[0:-1]))
                ymax = max(ymax, amax(bus.theta[0:-1]))
                thetas.append(bus.theta[0:-1])
                color_name = 'color{0}'.format(bus.get_id())
                color_names.append(color_name)
                tikz_colors.append(self.generate_color_defintion(color_name, self.network_graph.node[bus]['color_num']))

            ax.plot(t_vector, bus.theta[0:-1], color=color, linewidth=1.5)
            labels.append((r'$\theta_%i$' % bus.get_id()))
        
        if output_tikz is True:
            tikz_file_contents = self.generate_tikz_preamble(xmin, xmax, ymin, ymax, x_label, y_label, colors=tikz_colors)
            for index, theta in enumerate(thetas):
                tikz_file_contents.extend([r'\addplot[{0}, line width=1.25pt]'.format(color_names[index]), 
                                           r'coordinates {'])

                for index, theta_i in enumerate(theta):
                    if index > 0 and index < (len(theta) - 1): 
                        rounded_theta = round(theta_i, rnd)
                        if(round(theta[index-1], rnd) == rounded_theta and round(theta[index+1], rnd) != rounded_theta or
                           round(theta[index-1], rnd) != rounded_theta and round(theta[index+1], rnd) == rounded_theta):
                           tikz_file_contents.append('({0:.4f}, {1:.4f})'.format(t_vector[index], theta_i))
                    else:
                        tikz_file_contents.append('({0:.4f}, {1:.4f})'.format(t_vector[index], theta_i))
                        #
                        # if rounded_theta != prev_theta:
                        #
                        #
                        # tikz_file_contents.append('({0:.4f}, {1:.4f})'.format(t_vector[index], theta_i))
                        # prev_theta = rounded_theta
                        
                
                tikz_file_contents.append(r'};')
            
            tikz_file_contents.extend([r'\end{axis}', r'\end{tikzpicture}'])
            tikz_file = open('bus_voltage_angles.tikz', 'w')
            tikz_file.write('\n'.join(tikz_file_contents))
            tikz_file.close()

        legend(labels)
        xlim((t_vector[0], t_vector[-1]))
        xlabel(x_label)
        ylabel(y_label)

 
    def plot_average_bus_frequency(self, t_vector, ax=None, output_tikz=False):
        if ax is None:
            fig = figure()
            ax = fig.add_subplot(111)
        # shape = amax([bus.model.w.shape[0] for bus in self.network])
        def compute_average_frequency(index):
            w_avg_i_num = 0.
            w_avg_i_dem = 0.
            for bus in self.network:
                w_avg_i_num += bus.model.D*bus.w[index]
                w_avg_i_dem += bus.model.D
        
            return w_avg_i_num/w_avg_i_dem
        
        w_avg = frompyfunc(compute_average_frequency, 1, 1)(arange(0, amax([bus.w.shape[0] for bus in self.network])))
        
        ax.plot(t_vector, w_avg[0:-1])
        if output_tikz is True:
            tikz_file_contents = self.generate_tikz_preamble(t_vector[0], t_vector[-1],
                                                             amin(w_avg), amax(w_avg),
                                                             'time, $t$ [s]',
                                                             r'$\Delta \overline{\omega}$ [rad/s]')

            tikz_file_contents.extend([r'\addplot [blue, line width=1.25pt]', r'coordinates {'])
            for index, w_avg_i in enumerate(w_avg[0:-1]):
                tikz_file_contents.append('({0:.4f}, {1:.4f})'.format(t_vector[index], w_avg_i))

            tikz_file_contents.extend([r'};', r'\end{axis}', r'\end{tikzpicture}'])
            tikz_file = open('bus_frequency.tikz', 'w')
            tikz_file.write('\n'.join(tikz_file_contents))
            tikz_file.close()

    
    def plot_bus_frequency(self, t_vector, include_avg=False):
        fig = figure()
        ax = fig.add_subplot(111)
        labels = []
        
        for bus in self.network:
            color = self.network_graph.node[bus]['hex_color']
            ax.plot(t_vector, bus.w[0:-1], color=color, linewidth=1.25)
            labels.append((r'$\omega_%i$' % bus.get_id()))

        legend(labels)
        xlim((t_vector[0], t_vector[-1]))
        xlabel('time, ' + r'$t$' + ' [s]')
        ylabel(r'$\omega$ [rad/s]')
        
        if include_avg is True:
            self.plot_average_bus_frequency(t_vector, ax=ax)


    def plot_generator_setpoints(self, t_vector, include_sums=False, ax=None, output_tikz=False):
        if include_sums is True:
            total_generation = zeros(t_vector.shape[0])
        
        if ax is None:
            fig = figure()
            ax = fig.add_subplot(111)

        if output_tikz is True:
            setpoints = []
            time_changes = []
            xmin = t_vector[0]
            xmax = t_vector[-1]
            ymin = 0
            ymax = 0
            color_names = []
            tikz_colors = []

        labels = []
        for bus in [bus for bus in self.network if bus.has_generator_model() is True]:
            if output_tikz is True:
                setpoints.append(bus.model.u)
                time_changes.append(bus.model._setpoint_change_time)
                xmin = min(xmin, amin(bus.model.u))
                xmax = max(xmax, amax(bus.model.u))
                color_name = 'color{0}'.format(bus.get_id())
                color_names.append(color_name)
                tikz_colors.append(self.generate_color_defintion(color_name, self.network_graph.node[bus]['color_num']))

            u_bus = empty(0)
            for index, t in enumerate(t_vector):
                try:
                    t_u = where(bus.model._setpoint_change_time == t)[0][0]
                    u = bus.model.u[t_u]
                except IndexError:
                    u = u_bus[-1]
                
                u_bus = append(u_bus, u)
                if include_sums is True:
                    total_generation[index] += u
                
            color = self.network_graph.node[bus]['hex_color']
            ax.plot(t_vector, u_bus, color=color, linewidth=2)
            labels.append((r'$u_%i$' % bus.get_id()))
        
        if output_tikz is True:
            tikz_file_contents = self.generate_tikz_preamble(xmin, xmax, ymin, ymax, '', '', colors=tikz_colors)
            for i, setpoint_array in enumerate(setpoints):
                tikz_file_contents.extend([r'\addplot[{0}, line width=1.25pt]'.format(color_names[i]), 
                                           r'coordinates {'])

                for j, setpoint in enumerate(setpoint_array):
                    tikz_file_contents.append('({0:.4f}, {1:.4f})'.format(time_changes[i][j], setpoint))
                
                tikz_file_contents.append(r'};')
            
            tikz_file_contents.extend([r'\end{axis}', r'\end{tikzpicture}'])
            tikz_file = open('gen_setpoints.tikz', 'w')
            tikz_file.write('\n'.join(tikz_file_contents))
            tikz_file.close()

        legend(labels)
        xlim((t_vector[0], t_vector[-1]))
        xlabel('time, ' + r'$t$' + ' [s]')
        ylabel(r'$u$ [pu]')
        
        if include_sums is True:
            ax.plot(t_vector, total_generation, linewidth=2, alpha=0.8)
