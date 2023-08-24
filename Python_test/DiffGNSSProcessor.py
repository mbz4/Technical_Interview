#/usr/bin/env python3 

import csv, time, matplotlib
import matplotlib.pyplot as plt
import numpy as np
import argparse
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

def parse_args():
    parser = argparse.ArgumentParser(description="DiffGNSSProcessor: Process and visualize GNSS data.")
    parser.add_argument("--file_path", type=str, default="input_data.csv", help="Path to data. Default: 'input_data.csv'")
    parser.add_argument("--filter", action="store_true", default=False, help="Apply a Kalman filter on X, Y, Roll, Pitch data.")
    parser.add_argument("--noshow", action="store_false", help="Don't show the plot.")
    parser.add_argument("--save", action="store_true", default=False, help="Save plots ('analysis.png') & data ('output_data.csv').")
    return parser.parse_args()

class SimpleKalmanFilter:
    def __init__(self, initial_state, initial_covariance, process_variance, measurement_variance):
        self.x = initial_state
        self.P = initial_covariance
        self.F = np.array([[1, 1], [0, 1]])
        self.H = np.array([[1, 0]])
        self.R = measurement_variance
        self.Q = process_variance

    def predict(self):
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

    def update(self, z):
        y = z - np.dot(self.H, self.x)
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(np.dot(K, self.H), self.P)

class DiffGNSSProcessor:
    def __init__(self, file_path):
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
                x_m = float(int(row[1])) / 1000  # Convert to meters (made more sense in this context)
                y_m = float(int(row[2])) / 1000
                roll_deg = float(row[3])
                pitch_deg = float(row[4])
                data_tuple = (time_s, x_m, y_m, roll_deg, pitch_deg)
                self.data.append(data_tuple)
    
    def apply_kalman_filter(self):
        initial_state = np.array([self.data[0][1], 0])
        initial_covariance = np.array([[1000, 0], [0, 1000]])
        # the noise parameters (process_variance, measurement_variance) were chosen arbitrarily 
        process_variance = np.array([[1, 0], [0, 1]]) * 0.01
        measurement_variance = 2

        kf_x = SimpleKalmanFilter(initial_state, initial_covariance, process_variance, measurement_variance)
        kf_y = SimpleKalmanFilter(initial_state, initial_covariance, process_variance, measurement_variance)
        kf_roll = SimpleKalmanFilter(initial_state, initial_covariance, process_variance, measurement_variance)
        kf_pitch = SimpleKalmanFilter(initial_state, initial_covariance, process_variance, measurement_variance)
        
        kalman_data = []
        for point in self.data:
            kf_x.predict()
            kf_x.update(np.array([point[1]]))
            kf_y.predict()
            kf_y.update(np.array([point[2]]))
            kf_roll.predict()
            kf_roll.update(np.array([point[3]]))
            kf_pitch.predict()
            kf_pitch.update(np.array([point[4]]))
            kalman_data.append((point[0], kf_x.x[0], kf_y.x[0], kf_roll.x[0], kf_pitch.x[0]))
        return kalman_data

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
    def process_data(self, filterKalman, savefig): # process data
        self.data = sorted(self.data, key=lambda x: x[0])  # sort by timestamps
        if filterKalman:
            self.data = self.apply_kalman_filter()
        self.calculate_projection()
        self.calculate_heading()
        self.calculate_velocity()
        if savefig:
            self.save_to_csv()

    def plot_quiver(self, ax):
        U = np.cos(np.radians(self.headings))
        V = np.sin(np.radians(self.headings))
        X = [point[0] for point in self.projected_points]
        Y = [point[1] for point in self.projected_points]
        min_length = min(len(U), len(X)) # ensure data list length matches...
        U, V = U[:min_length], V[:min_length]
        X, Y = X[:min_length], Y[:min_length]
        ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=8, color='b', alpha=0.5, width=0.0045, headwidth=2.8, headlength=3.8, headaxislength=3.5)
        ax.set_title("Speed & Yaw on Moving Plane")
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
        ax.set_title("Yaw [°] / Velocity [m/s]")
        ax.grid(True)
        ax.set_theta_zero_location("S")
        ax.set_theta_direction(-1)
        ax.set_rlim(0.4, None)
        ax.set_thetamin(90)
        ax.set_thetamax(180)
    
    def visualize_data(self, showfig, savefig):

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
        if showfig:
            plt.show() 
    
    def run(self, filterKalman, showfig, savefig):
        self.process_data(filterKalman, savefig)
        self.visualize_data(showfig, savefig)

if __name__ == "__main__":
    args = parse_args()
    DiffGNSSProcessor(args.file_path).run(filterKalman=args.filter, showfig=args.noshow, savefig=args.save)
