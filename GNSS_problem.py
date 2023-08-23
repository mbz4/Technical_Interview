import math
import matplotlib.pyplot as plt
import csv
import numpy as np
import datetime

data = [(1621693264.0155628, 9521, -35074, 3.92, -1.35),
(1621693264.1979840, 9450, -34970, 3.93, -1.22),
(1621693264.4237902, 9365, -34853, 3.85, -1.24),
(1621693264.6384845, 9291, -34759, 3.85, -1.12),
(1621693264.8448036, 9211, -34649, 3.77, -0.99),
(1621693265.0378000, 9140, -34547, 3.70, -0.90),
(1621693265.2572992, 9071, -34444, 3.70, -0.70),
(1621693265.4631655, 8988, -34334, 3.59, -0.55),
(1621693265.6851535, 8917, -34231, 3.59, -0.49),
(1621693265.8768837, 8839, -34126, 3.56, -0.46),
(1621693266.1154845, 8767, -34021, 3.66, -0.38),
(1621693266.2963840, 8689, -33914, 3.78, -0.44),
(1621693266.5014370, 8614, -33808, 3.74, -0.53),
(1621693266.7386210, 8540, -33704, 3.73, -0.75),
(1621693266.9416296, 8452, -33590, 3.66, -0.91),
(1621693267.1762938, 8392, -33494, 3.55, -0.97),
(1621693267.3843954, 8326, -33399, 3.63, -1.00),
(1621693267.5642680, 8255, -33292, 3.77, -0.89),
(1621693267.7781956, 8176, -33189, 3.90, -1.00),
(1621693268.0044500, 8112, -33099, 3.88, -1.24),
(1621693268.2188272, 8044, -32986, 3.82, -1.58),
(1621693268.4177945, 7969, -32892, 3.75, -1.95),
(1621693268.6272150, 7906, -32804, 3.77, -2.05),
(1621693268.8552556, 7835, -32705, 3.80, -1.95),
(1621693269.0375066, 7759, -32616, 3.81, -1.72),
(1621693269.2567391, 7677, -32504, 3.88, -1.31),
(1621693269.4572983, 7593, -32391, 3.98, -1.04),
(1621693269.8621871, 7453, -32193, 4.07, -1.17),
(1621693270.0862586, 7386, -32103, 4.06, -1.31),
(1621693270.2752004, 7301, -31996, 4.06, -1.56)]

def calculate_projection(data):
    projected_points = []
    for point in data:
        x_mm, y_mm, roll_deg, pitch_deg = point[1], point[2], point[3], point[4]
        x_offset = 1500 * math.tan(math.radians(roll_deg))
        y_offset = 1500 * math.tan(math.radians(pitch_deg))
        x_projected = x_mm + x_offset
        y_projected = y_mm + y_offset
        projected_points.append((x_projected, y_projected))
    return projected_points

def calculate_heading(data, projected_points):
    headings = []
    for i in range(1, len(data)):
        delta_x = projected_points[i][0] - projected_points[i-1][0]
        delta_y = projected_points[i][1] - projected_points[i-1][1]
        heading = math.degrees(math.atan2(delta_y, delta_x))
        headings.append(heading)
    return headings

def calculate_velocity(data):
    velocities = []
    for i in range(len(data) - 1):  # Skip the last point because there's no next point for it
        dx = data[i+1][1] - data[i][1]
        dy = data[i+1][2] - data[i][2]
        dt = data[i+1][0] - data[i][0]
        
        vi = np.sqrt(dx**2 + dy**2) / dt
        velocities.append(vi)
    return velocities

def calculate_norm_velocity(data):
    velocities = []
    for i in range(len(data) - 1):  # Skip the last point because there's no next point for it
        dx = data[i+1][1] - data[i][1]
        dy = data[i+1][2] - data[i][2]
        dt = data[i+1][0] - data[i][0]
        
        vi = np.sqrt(dx**2 + dy**2) / dt
        velocities.append(vi)
    
    # Normalize velocities to range [0, 1]
    max_velocity = max(velocities)
    normalized_velocities = [v/max_velocity for v in velocities]
    
    return normalized_velocities


def save_to_csv(data, headings, velocities):
    with open('output_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'x_mm', 'y_mm', 'roll_deg', 'pitch_deg', 'heading_deg', 'velocity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(len(data) - 1):  # Again, skipping the last data point
            writer.writerow({
                'timestamp': data[i][0],
                'x_mm': data[i][1],
                'y_mm': data[i][2],
                'roll_deg': data[i][3],
                'pitch_deg': data[i][4],
                'heading_deg': headings[i],
                'velocity': velocities[i]
            })


def plot_quiver(data, headings, velocities):
    x = [point[1] for point in data[:-1]]  # Skip the last point
    y = [point[2] for point in data[:-1]]  # Skip the last point
    
    # Multiply by normalized velocities to adjust arrow lengths
    u = np.cos(np.radians(headings)) * velocities
    v = np.sin(np.radians(headings)) * velocities

    plt.figure(figsize=(10, 7))
    plt.quiver(x, y, u, v, angles='xy', scale_units='xy', scale=2, color='m', width=0.003, alpha=0.5)
    plt.scatter(x, y, color='b', alpha=0.2, edgecolors='g')
    plt.title("Quiver Plot showing the Heading and Velocity")
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.show()


def plot_time_series(data):
    times = [point[0] for point in data]
    roll = [point[3] for point in data]
    pitch = [point[4] for point in data]

    plt.figure(figsize=(10, 7))
    plt.plot(times, roll, label="Roll (degrees)", color="blue")
    plt.plot(times, pitch, label="Pitch (degrees)", color="red")
    plt.title("Time-Series plot of Roll and Pitch")
    plt.xlabel("Time (s)")
    plt.ylabel("Degrees")
    plt.legend()
    plt.show()

def plot_histogram(headings):
    plt.figure(figsize=(10, 7))
    plt.hist(headings, bins=20, color="skyblue", edgecolor="black")
    plt.title("Histogram of Headings (Yaw)")
    plt.xlabel("Heading (degrees)")
    plt.ylabel("Frequency")
    plt.show()

def plot_projected_points(x_projected_values, y_projected_values):
    plt.scatter(x_projected_values, y_projected_values, '-o')
    plt.title("GNSS Module Projection on Moving Plane")
    plt.xlabel("x (mm)")
    plt.ylabel("y (mm)")
    plt.grid(True)
    plt.show()

def plot_headings(headings):    
    plt.plot(headings)
    plt.title("Vehicle's Heading")
    plt.xlabel("Time (index)")
    plt.ylabel("Heading (degrees)")
    plt.grid(True)
    plt.show()

def plot_velocity_vs_time(data, velocities):
    # Extracting time information, but remember to exclude the last timestamp since we don't have a velocity for it
    timestamps = [point[0] for point in data[:-1]]
    
    # Convert UNIX timestamps to a human-readable format for better x-axis labels (optional but can be helpful)
    times = [datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S') for ts in timestamps]

    plt.figure(figsize=(12, 6))
    plt.plot(times, velocities, '-o', color='b', markersize=4)
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.title("Velocity vs. Time")
    plt.xlabel("Time")
    plt.ylabel("Normalized Velocity")
    plt.tight_layout()  # Adjust layout for better label fitting
    plt.show()

projected_points = calculate_projection(data)
headings = calculate_heading(data, projected_points)
velocities = calculate_velocity(data)
norm_velocities = calculate_norm_velocity(data)
save_to_csv(data, headings, velocities)
plot_velocity_vs_time(data, velocities)

x_projected_values = [point[0] for point in projected_points]
y_projected_values = [point[1] for point in projected_points]

# plot_quiver(data, headings, norm_velocities)
plot_quiver(data, headings, velocities)
# plot_time_series(data)
# plot_histogram(headings)