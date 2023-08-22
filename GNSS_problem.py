import math
import matplotlib.pyplot as plt

data = [
    # time_s, x_mm, y_mm, roll_deg, pitch_deg
    # Add your data here...
]

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

projected_points = calculate_projection(data)
headings = calculate_heading(data, projected_points)

# Visualizing the data
x_projected_values = [point[0] for point in projected_points]
y_projected_values = [point[1] for point in projected_points]

plt.plot(x_projected_values, y_projected_values, '-o')
plt.title("GNSS Module Projection on Moving Plane")
plt.xlabel("x (mm)")
plt.ylabel("y (mm)")
plt.grid(True)
plt.show()

plt.plot(headings)
plt.title("Vehicle's Heading")
plt.xlabel("Time (index)")
plt.ylabel("Heading (degrees)")
plt.grid(True)
plt.show()
