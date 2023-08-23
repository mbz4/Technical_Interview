#/usr/bin/env python3 

import csv, time, matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use('Qt5Agg')


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

    def load_data(self, file_path): # load data from csv file
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader) # Skip the header row
            for row in reader: # Convert the data in the row to their appropriate types and add to the data list
                time_s = float(row[0]) # convert to float (need to perform ops on it later, cant use strings)
                x_mm = int(row[1]) # convert to int
                y_mm = int(row[2])
                roll_deg = float(row[3])
                pitch_deg = float(row[4])
                data_tuple = (time_s, x_mm, y_mm, roll_deg, pitch_deg) 
                self.data.append(data_tuple) # add tuple to list     
    
    def calculate_projection(self): # calculate projection of GNSS module on moving plane
        for point in self.data:
            x_mm, y_mm, roll_deg, pitch_deg = point[1], point[2], point[3], point[4] # unpack data
            x_offset = 1500 * np.tan(np.radians(roll_deg)) # 1500 mm is the distance from the GNSS module to the center of the vehicle
            y_offset = 1500 * np.tan(np.radians(pitch_deg)) 
            self.projected_points.append((x_mm + x_offset, y_mm + y_offset)) # add offset to x and y values, then add projected point to list
    
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

    def save_to_csv(self): # save data to csv file
        with open('output_data.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, 
                                    fieldnames = ['timestamp',
                                                  'x_mm', 
                                                  'y_mm', 
                                                  'roll_deg', 
                                                  'pitch_deg', 
                                                  'heading_deg', 
                                                  'velocity']) # create writer object
            writer.writeheader() # write header
            for i in range(len(self.data) - 1):
                writer.writerow({
                    'timestamp': self.data[i][0],
                    'x_mm': self.data[i][1],
                    'y_mm': self.data[i][2],
                    'roll_deg': self.data[i][3],
                    'pitch_deg': self.data[i][4],
                    'heading_deg': self.headings[i],
                    'velocity': self.velocities[i]}) # write data to csv file
    
    @time_it
    def process_data(self): # process data
        self.data = sorted(self.data, key=lambda x: x[0])  # sort by timestamps
        self.calculate_projection()
        self.calculate_heading()
        self.calculate_velocity()
        self.save_to_csv()

    def plot_quiver(self, ax):
        U = np.cos(np.radians(self.headings))
        V = np.sin(np.radians(self.headings))
        
        # Fixing the X and Y extraction
        X = [point[0] for point in self.projected_points]
        Y = [point[1] for point in self.projected_points]

        # Ensure lengths match
        min_length = min(len(U), len(X))  # get the minimum length
        U, V = U[:min_length], V[:min_length]
        X, Y = X[:min_length], Y[:min_length]

        ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=0.009, color='b')
        ax.set_title("Quiver Plot with Projections")
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")

    def plot_time_series(self, ax):
        times = [point[0] for point in self.data]
        roll = [point[3] for point in self.data]
        pitch = [point[4] for point in self.data]
        ax.plot(times, roll, label="Roll", color="blue")
        ax.plot(times, pitch, label="Pitch", color="red")
        ax.set_title("Roll & Pitch / Time")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Angle [°]")
        ax.legend() 

    def plot_velocity_vs_time(self, ax):
        times = [point[0] for point in self.data] # get times
        smoothed_velocities = np.convolve(self.velocities, np.ones(5)/5, mode='valid') # simple moving average to smoothen the velocities
        truncated_times = times[len(times) - len(smoothed_velocities):] # truncate times to match the length of the smoothed velocities
        ax.plot(truncated_times, smoothed_velocities, label="Velocity", color="purple")
        ax.set_title("Velocity / Time")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Velocity [m/s]")
  
    def plot_polar(self, ax):
        angles = np.radians(self.headings)
        radii = self.normalized_velocities
        ax.scatter(angles, radii, color='g', s=5)  # scatter plot with small points
        ax.set_title("Heading & Velocity")
        ax.grid(True)
        ax.set_theta_zero_location("N")  # Set 0 degrees to the top
        ax.set_theta_direction(-1)  # Clockwise direction
    
    def visualize_data(self):

        fig = plt.figure(figsize=(14, 8))
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2, projection='polar')
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)

        self.plot_quiver(ax1)
        self.plot_polar(ax2)
        self.plot_time_series(ax3)
        self.plot_velocity_vs_time(ax4)
        
        plt.draw()
        manager = plt.get_current_fig_manager()
        manager.window.showMaximized()
        plt.tight_layout()
        plt.show()
    
    def run(self):
        self.process_data()
        self.visualize_data()

if __name__ == "__main__":
    DiffGNSSProcessor("input_data.csv").run()