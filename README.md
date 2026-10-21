# ROS 2 Lab 1 - Turtlesim

Design of Mechatronics Systems - Alexandria University

Team members (add our names and IDs here before submitting):
- Student 1:
- Student 2:
- Student 3:

## What we made

For this lab we used ROS 2 Humble and turtlesim. The idea is to send the turtle a position, let it move there, reset its drawing, and use the same movement action four times to draw a square. We also added a way to change the speed while the program is running.

There are two packages:
- `turtle_interfaces`: our message, two actions, and speed service definitions.
- `turtle_control`: the Python nodes that move and reset the turtle, draw the square, and launch everything.

## Before running

We used Ubuntu 22.04 with ROS 2 Humble. We need turtlesim and colcon installed. If ROS 2 is already installed, there is no need to reinstall it.

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install ros-humble-turtlesim python3-colcon-common-extensions
```

## How we built it

After extracting the ZIP into Downloads, we put the two packages in a ROS workspace:

```bash
mkdir -p ~/ros2_ws/src
cp -r ~/Downloads/ros2_lab1_project/turtle_interfaces ~/ros2_ws/src/
cp -r ~/Downloads/ros2_lab1_project/turtle_control ~/ros2_ws/src/
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

If the extracted folder is somewhere else, the two `cp` paths need to be changed.

## Running the project

In the first terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch turtle_control system.launch.py
```

Leave that terminal open. In each new terminal, run the two `source` commands again.

## Commands we used for testing

Check nodes and interfaces:

```bash
ros2 node list
ros2 interface show turtle_interfaces/msg/TargetPose
ros2 interface show turtle_interfaces/action/GoToPose
ros2 interface show turtle_interfaces/action/DrawSquare
ros2 interface show turtle_interfaces/srv/SetSpeed
ros2 action list -t
ros2 service list
ros2 topic list
```

Move the turtle to x=7, y=7 and yaw=1.57 radians:

```bash
ros2 action send_goal /go_to_pose turtle_interfaces/action/GoToPose "{target: {x: 7.0, y: 7.0, yaw: 1.57}}" --feedback
```

Check its position (Ctrl+C to stop):

```bash
ros2 topic echo /turtle1/pose
```

Reset the turtle and clear the screen:

```bash
ros2 service call /reset_turtle std_srvs/srv/Trigger "{}"
```

Draw a square with side length 3:

```bash
ros2 action send_goal /draw_square turtle_interfaces/action/DrawSquare "{side_length: 3.0}" --feedback
```

Check and change the speed:

```bash
ros2 param get /go_to_pose_server max_linear_speed
ros2 param get /go_to_pose_server max_angular_speed
ros2 param set /go_to_pose_server max_linear_speed 1.0
ros2 param set /go_to_pose_server max_angular_speed 1.0
ros2 service call /set_speed turtle_interfaces/srv/SetSpeed "{max_linear_speed: 1.5, max_angular_speed: 1.2}"
ros2 service call /set_speed turtle_interfaces/srv/SetSpeed "{max_linear_speed: -1.0, max_angular_speed: 2.0}"
```

The last call is an invalid-input test, so it should return failure.

We can also restart the launch with different speed settings:

```bash
ros2 launch turtle_control system.launch.py linear_speed:=0.8 angular_speed:=1.0
```

## How the square works

The square server first calls our reset service. Then it sends four goals to the go-to-pose server, one for each corner, waiting for each movement to finish before sending the next. It reports the completed sides as feedback.

## Extra notes

We separated the movement, reset and square logic into different nodes to make the project easier to follow. This is separation of responsibilities, not a claim that we implemented one of the named design patterns for the bonus.

The rosbag bonus has not been recorded or tested yet. If we do it, we should record `/turtle1/cmd_vel` while drawing, check the bag with `ros2 bag info`, and replay it starting from the same turtle position.

## GitHub submission

Upload only `turtle_interfaces`, `turtle_control` and this `README.md`. Do not upload the `build`, `install` or `log` directories. We still need to run and verify everything on Ubuntu before submitting.
