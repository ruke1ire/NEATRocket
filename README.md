# NEATRocket

Training a rocket controller using the NEAT algorithm.

### Dependencies:

1. pymunk 5.7.0
2. pyglet 1.5.7
3. neat-python 0.92

### Usage:

- Manually control the rocket with your arrow keys.

```python
python3 manual.py
```

- Train the network

```python
python3 train.py
```

- Automatic rocket control

```python
python3 auto.py
```

### NEAT Setup

- *States/Input:*
    - x error = current x position - desired x position
    - y error = current y position - desired y position
    - a error = current angular position - desired angular position
    - vx error = current x velocity - desired x velocity
    - vy error = current y velocity - desired y velocity
    - va error = current angular velocity - desired angular velocity
- *Output:*
    - longitudinal thrust states: clamped [-1,+1]
    - top lateral booster states: clamped [-1,+1]
    - bottom lateral booster states: clamped [-1,+1]
- *fitness function* : Summation of weighted squared errors of the positional states across time
