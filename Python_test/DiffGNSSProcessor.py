#/usr/bin/env python3 

import csv, time, matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use('Qt5Agg')
plt.style.use('seaborn-v0_8-whitegrid')

def time_it(func):
    def wrapper(self, *args, **kwargs):
        start = time.perf_counter()
        result = func(self, *args, **kwargs)
        end = time.perf_counter()
        print(f'{func.__name__} executed in {1000*(end - start):.03f} ms.')
        return result
    return wrapper

class DiffGNSSProcessor: # class definition
    def __init__(self, file_path): # constructor
        self.data = []
        self.load_data(file_path)
        self.projected_points = []
        self.headings = []
        self.velocities = []
        self.normalized_velocities = []
        self.output_data = []
          
    def load_data(self, file_path):
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                time_s = float(row[0])
                x_m = float(int(row[1])) / 1000  # Convert to meters (makes more sense in this context)
                y_m = float(int(row[2])) / 1000
                roll_deg = float(row[3])
                pitch_deg = float(row[4])
                data_tuple = (time_s, x_m, y_m, roll_deg, pitch_deg)
                self.data.append(data_tuple)
    
    def calculate_projection(self):
        for point in self.data:
            x_m, y_m, roll_deg, pitch_deg = point[1], point[2], point[3], point[4]
            x_offset = 1.5 * np.tan(np.radians(roll_deg))  # 1.5 meters is the distance from the GNSS module to the center of the vehicle
            y_offset = 1.5 * np.tan(np.radians(pitch_deg))
            self.projected_points.append((x_m + x_offset, y_m + y_offset))
    
    def calculate_heading(self): # calculate heading between two points
        for i in range(1, len(self.data)): # start at 1 b/c we need to calculate heading between two points
            delta_x = self.projected_points[i][0] - self.projected_points[i-1][0] # calculate delta x and y
            delta_y = self.projected_points[i][1] - self.projected_points[i-1][1] 
            self.headings.append(np.degrees(np.arctan2(delta_y, delta_x))) # calculate heading & add it to list
    
    def calculate_velocity(self):
        for i in range(len(self.data) - 1): # start at 0 b/c we need to calculate velocity between two points
            dx = self.data[i+1][1] - self.data[i][1] # calculate delta x and y
            dy = self.data[i+1][2] - self.data[i][2]
            dt = self.data[i+1][0] - self.data[i][0] # calculate delta t
            vi = np.sqrt(dx**2 + dy**2) / dt # calculate velocity
            self.velocities.append(vi) # add velocity to list
        self.normalized_velocities = [v/(max(self.velocities)) for v in self.velocities] # normalize all velocities

    def save_to_csv(self):
        with open('output_data.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, 
                                    fieldnames = ['timestamp',
                                                  'x_m',   # Changed to meters
                                                  'y_m',   
                                                  'roll_deg', 
                                                  'pitch_deg', 
                                                  'heading_deg', 
                                                  'velocity'])
            writer.writeheader()
            for i in range(len(self.data) - 1):
                writer.writerow({
                    'timestamp': self.data[i][0],
                    'x_m': self.data[i][1],   # Changed to meters
                    'y_m': self.data[i][2],   
                    'roll_deg': self.data[i][3],
                    'pitch_deg': self.data[i][4],
                    'heading_deg': self.headings[i],
                    'velocity': self.velocities[i]})
    
    @time_it # measured taking ~1ms to complete 
    def process_data(self): # process data
        self.data = sorted(self.data, key=lambda x: x[0])  # sort by timestamps
        self.calculate_projection()
        self.calculate_heading()
        self.calculate_velocity()
        self.save_to_csv()

    def plot_quiver(self, ax):
        U = np.cos(np.radians(self.headings))
        V = np.sin(np.radians(self.headings))
        X = [point[0] for point in self.projected_points]
        Y = [point[1] for point in self.projected_points]
        min_length = min(len(U), len(X)) # ugly hack to make sure all lists are the same length...
        U, V = U[:min_length], V[:min_length]
        X, Y = X[:min_length], Y[:min_length]
        ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=8, color='b', alpha=0.5, width=0.0045, headwidth=2.8, headlength=3.8, headaxislength=3.5)
        ax.set_title("Speed & Heading on Moving Plane")
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")

    def plot_time_series(self, ax):
        times = [point[0] for point in self.data][1:]
        roll = [point[3] for point in self.data][1:]
        pitch = [point[4] for point in self.data][1:]
        yaw = self.headings
        # window_size = 5 # tried smoothing yaw but it didn't work well
        # yaw = np.convolve(self.headings, np.ones(window_size)/window_size, mode='valid')
        # adjusted_times = times[int(window_size/2): -int(window_size/2)]
        ax.plot(times, roll, label="Roll", color="blue", alpha=0.5)
        ax.plot(times, pitch, label="Pitch", color="red", alpha=0.5)
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Roll & Pitch [°]")
        ax.legend(loc='upper left')

        ax2 = ax.twinx()
        ax2.set_ylabel('Yaw [°]', color='green')
        ax2.plot(times, yaw, label="Yaw", color="green", alpha=0.5)
        ax2.tick_params(axis='y', labelcolor='green')
        ax.set_title("Roll, Pitch, Yaw / Time")

    def plot_velocity_vs_time(self, ax):
        times = [point[0] for point in self.data] # get times
        smoothed_velocities = np.convolve(self.velocities, np.ones(5)/5, mode='valid') # simple moving average to smoothen the velocities
        truncated_times = times[len(times) - len(smoothed_velocities):] # truncate times to match the length of the smoothed velocities
        ax.plot(truncated_times, smoothed_velocities, label="Velocity", color="purple", alpha=0.5)
        ax.set_title("Velocity / Time")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Velocity [m/s]")
  
    def plot_polar(self, ax):
        angles = np.radians(self.headings)
        radii = self.velocities
        ax.scatter(angles, radii, color='g', s=20, alpha=0.5)
        # for i, (angle, radius) in enumerate(zip(angles, radii)): # tried annotations for clarity but it was too cluttered
        #     if i % 5 == 0:
        #         ax.annotate(f"{radius:.2f} m/s", (angle, radius), textcoords="offset points", xytext=(0,5), ha='center', fontsize=8)   
        ax.set_title("Heading [°] / Velocity [m/s]")
        ax.grid(True)
        ax.set_theta_zero_location("S")
        ax.set_theta_direction(-1)
        ax.set_rlim(0.4, None)
        ax.set_thetamin(90)
        ax.set_thetamax(180)
    
    def visualize_data(self, savefig):

        fig = plt.figure(figsize=(14, 8))
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2, projection='polar')
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)

        self.plot_quiver(ax1)
        self.plot_polar(ax2)
        self.plot_time_series(ax3)
        self.plot_velocity_vs_time(ax4)
        
        plt.subplots_adjust(hspace=0.3, wspace=0.3)
        plt.draw() # predraw the plot
        manager = plt.get_current_fig_manager() # get the current figure manager
        manager.window.showMaximized() # maximize the window
        if savefig:
            fig.savefig('analysis.png', dpi=300)
        plt.show() 
    
    def run(self, savefig=False):
        self.process_data()
        self.visualize_data(savefig)

if __name__ == "__main__":
    DiffGNSSProcessor("input_data.csv").run(savefig=True)