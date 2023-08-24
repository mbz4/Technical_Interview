
### Task Instructions

```
Description of the problem:
Vehicle has a GNSS module with installation height of 1500mm above the moving plane.
Vehicle moves forward on rugged terrain. The GNSS position and vehicle orientation is given (see links below).
Positive roll corresponds to the orientation when the right side of the vehicle is being lower than
the left side. Positive pitch corresponds to the orientation when the front part of the vehicle is
being lower than the rear part.
Task:
1. For each point calculate the projection of the GNSS module post on the moving plane
2. For each point calculate the vehicles heading (vehicle is moving smoothly straight
ahead)
Requirements:
Problem must be solved using Python 3 language
Evaluation criterias:
● Solution correctness and robustness
● Code cleanness and reusability
● Problem decomposition approach
● Data visualization
```
## [Original task instructions (pdf)](https://github.com/mbz4/Technical_Interview/blob/main/Python_test/Test%20task%20for%20Python%20language%20skills.pdf)

## [Task data (csv)](https://github.com/mbz4/Technical_Interview/blob/main/Python_test/input_data.csv)

| **time_s**         | **x_mm** | **y_mm** | **roll_deg** | **pitch_deg** |
|--------------------|----------|----------|--------------|---------------|
| 1621693264.0155628 | 9521     | -35074   | 3.92         | -1.35         |
| 1621693264.1979840 | 9450     | -34970   | 3.93         | -1.22         |
| 1621693264.4237902 | 9365     | -34853   | 3.85         | -1.24         |
| 1621693264.6384845 | 9291     | -34759   | 3.85         | -1.12         |
| 1621693264.8448036 | 9211     | -34649   | 3.77         | -0.99         |
| 1621693265.0378000 | 9140     | -34547   | 3.70         | -0.90         |
| 1621693265.2572992 | 9071     | -34444   | 3.70         | -0.70         |
| 1621693265.4631655 | 8988     | -34334   | 3.59         | -0.55         |
| 1621693265.6851535 | 8917     | -34231   | 3.59         | -0.49         |
| 1621693265.8768837 | 8839     | -34126   | 3.56         | -0.46         |
| 1621693266.1154845 | 8767     | -34021   | 3.66         | -0.38         |
| 1621693266.2963840 | 8689     | -33914   | 3.78         | -0.44         |
| 1621693266.5014370 | 8614     | -33808   | 3.74         | -0.53         |
| 1621693266.7386210 | 8540     | -33704   | 3.73         | -0.75         |
| 1621693266.9416296 | 8452     | -33590   | 3.66         | -0.91         |
| 1621693267.1762938 | 8392     | -33494   | 3.55         | -0.97         |
| 1621693267.3843954 | 8326     | -33399   | 3.63         | -1.00         |
| 1621693267.5642680 | 8255     | -33292   | 3.77         | -0.89         |
| 1621693267.7781956 | 8176     | -33189   | 3.90         | -1.00         |
| 1621693268.0044500 | 8112     | -33099   | 3.88         | -1.24         |
| 1621693268.2188272 | 8044     | -32986   | 3.82         | -1.58         |
| 1621693268.4177945 | 7969     | -32892   | 3.75         | -1.95         |
| 1621693268.6272150 | 7906     | -32804   | 3.77         | -2.05         |
| 1621693268.8552556 | 7835     | -32705   | 3.80         | -1.95         |
| 1621693269.0375066 | 7759     | -32616   | 3.81         | -1.72         |
| 1621693269.2567391 | 7677     | -32504   | 3.88         | -1.31         |
| 1621693269.4572983 | 7593     | -32391   | 3.98         | -1.04         |
| 1621693269.8621871 | 7453     | -32193   | 4.07         | -1.17         |
| 1621693270.0862586 | 7386     | -32103   | 4.06         | -1.31         |
| 1621693270.2752004 | 7301     | -31996   | 4.06         | -1.56         |


# Solution

## DiffGNSSProcessor: how it works, features

- inputs: file path (data), preference to show and/or save resulting figure (arguments)
- outputs: data as csv (adds velocity & yaw columns), combined fullscreen windows w/ relevant figures
- Kalman filter (use flag ```--filter``` to try)
- processing: ~0.3-1 ms (w/o filter) ~3-4ms (w/ filter)
- based on task context, generates plots:
    - quiver: yaw (heading) vector w/ projection to moving plane
    - polar: yaw plot (radius: normalized velocity)
    - line: RPY / time line plot
    - line: velocity / time line plot (velocity smoothed)

### Features

- abstracted, extendable class structure
- option to save data, plots
- time complexity w/o filter: O(n) up to O(3n) (w/o filter)
- portable for real time applications (ROS node)
- only uses standard python library dependencies (no extra pip install required)
    - csv, 
    - time, 
    - matplotlib, 
    - numpy
    - argparse

### Setup:

#### 1. git clone repo
```bash
git clone https://github.com/mbz4/Technical_Interview.git
```
#### 2. navigate to app directory
```bash
cd Technical_Interview/Python_test
```
#### 3. run DiffGNSSProcessor.py
```bash
python DiffGNSSProcessor.py -h

usage: DiffGNSSProcessor.py [-h] [--file_path FILE_PATH] [--filter] [--noshow] [--save]

DiffGNSSProcessor: Process and visualize GNSS data.

options:
  -h, --help            show this help message and exit
  --file_path FILE_PATH
                        Path to data. Default: 'input_data.csv'
  --filter              Apply a Kalman filter on X, Y, Roll, Pitch data.
  --noshow              Don't show the plot.
  --save                Save plots ('analysis.png') & data ('output_data.csv').
```

Resulting plot w/ given task data (no filtering; last uploaded version displayed):

![alt text](https://github.com/mbz4/Technical_Interview/blob/main/Python_test/analysis.png)


## Refresher ~ Kalman filters

### 1. Guess of system state

It starts with an initial guess of the state of a system and its believed uncertainty.

### 2. Prediction step

For each timestep, it makes a prediction about the new/next state based on an internal model. 

**State Prediction:**  
$`\hat{x}_{k|k-1} = F_k \hat{x}_{k-1|k-1} + B_k u_k`$  
Where:  
- $`\hat{x}_{k|k-1}`$: Predicted state  
- $`F_k`$: State transition model  
- $`\hat{x}_{k-1|k-1}`$: Previous state estimate  
- $`B_k`$: Control input model  
- $`u_k`$: Control vector  

**Error Covariance Prediction:**  
$`P_{k|k-1} = F_k P_{k-1|k-1} F_k^T + Q_k`$  
Where:  
- $`P_{k|k-1}`$: Predicted error covariance  
- $`P_{k-1|k-1}`$: Previous error covariance  
- $`Q_k`$: Process noise covariance  

### 3. Update step

When a new measurement is available, it updates its prediction based on this measurement.
More weight is given to the prediction/measurement depending on specified uncertainties.

**Kalman Gain:**  
$`K_k = P_{k|k-1} H_k^T (H_k P_{k|k-1} H_k^T + R_k)^{-1}`$  
Where:  
- $`K_k`$: Kalman gain  
- $`H_k`$: Observation model  
- $`R_k`$: Measurement noise covariance  

**State Update:**  
$`\hat{x}_{k|k} = \hat{x}_{k|k-1} + K_k (z_k - H_k \hat{x}_{k|k-1})`$  
Where:  
- $`\hat{x}_{k|k}`$: Updated state estimate  
- $`z_k`$: Actual measurement  

**Error Covariance Update:**  
$`P_{k|k} = (I - K_k H_k) P_{k|k-1}`$  
Where:  
- $`P_{k|k}`$: Updated error covariance  
- $`I`$: Identity matrix  

## Nice to have / Future

- check data variability
    - if standard deviation exceeds some threshold
        - adjust tuning of process & measurement covariance, then
            - apply Kalman filter on data
    