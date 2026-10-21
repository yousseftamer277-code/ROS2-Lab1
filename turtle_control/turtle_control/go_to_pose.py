import math
import threading
import time

import rclpy
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtle_interfaces.action import GoToPose
from turtle_interfaces.srv import SetSpeed


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class GoToPoseServer(Node):
    def __init__(self):
        super().__init__('go_to_pose_server')
        self.group = ReentrantCallbackGroup()
        self.declare_parameter('max_linear_speed', 2.0)
        self.declare_parameter('max_angular_speed', 2.0)
        self.add_on_set_parameters_callback(self.validate_parameters)
        self.pose = None
        self.pose_lock = threading.Lock()
        self.motion_lock = threading.Lock()
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10,
                                 callback_group=self.group)
        self.create_service(SetSpeed, '/set_speed', self.set_speed,
                            callback_group=self.group)
        self.server = ActionServer(
            self, GoToPose, '/go_to_pose', execute_callback=self.execute,
            goal_callback=self.accept_goal, cancel_callback=self.cancel_goal,
            callback_group=self.group)

    def validate_parameters(self, params):
        for param in params:
            if param.name in ('max_linear_speed', 'max_angular_speed'):
                if param.type_ != param.Type.DOUBLE or not math.isfinite(param.value) or param.value <= 0:
                    return SetParametersResult(successful=False, reason='Speed must be a positive finite double')
        return SetParametersResult(successful=True)

    def set_speed(self, request, response):
        values = (request.max_linear_speed, request.max_angular_speed)
        if any(not math.isfinite(v) or v <= 0 for v in values):
            response.success = False
            response.message = 'Both speeds must be positive finite numbers'
            return response
        from rclpy.parameter import Parameter
        results = self.set_parameters([
            Parameter('max_linear_speed', Parameter.Type.DOUBLE, values[0]),
            Parameter('max_angular_speed', Parameter.Type.DOUBLE, values[1])])
        response.success = all(r.successful for r in results)
        response.message = 'Speed limits updated' if response.success else 'Parameter update failed'
        return response

    def pose_callback(self, pose):
        with self.pose_lock:
            self.pose = pose

    def accept_goal(self, goal):
        t = goal.target
        if not all(math.isfinite(v) for v in (t.x, t.y, t.yaw)) or not (0.5 < t.x < 10.5 and 0.5 < t.y < 10.5):
            self.get_logger().warn('Rejected target: use finite coordinates within (0.5, 10.5)')
            return GoalResponse.REJECT
        if self.motion_lock.locked():
            self.get_logger().warn('Another goal is already moving the turtle')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_goal(self, goal_handle):
        return CancelResponse.ACCEPT

    def stop(self):
        self.publisher.publish(Twist())

    def execute(self, goal_handle):
        result = GoToPose.Result()
        if not self.motion_lock.acquire(blocking=False):
            goal_handle.abort()
            result.message = 'Another goal is in progress'
            return result
        try:
            target = goal_handle.request.target
            start = time.monotonic()
            while rclpy.ok():
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.message = 'Canceled'
                    return result
                if time.monotonic() - start > 120.0:
                    goal_handle.abort()
                    result.message = 'Timeout after 120 seconds'
                    return result
                with self.pose_lock:
                    pose = self.pose
                if pose is None:
                    time.sleep(0.05)
                    continue
                dx, dy = target.x - pose.x, target.y - pose.y
                distance = math.hypot(dx, dy)
                final_error = wrap_angle(target.yaw - pose.theta)
                command = Twist()
                max_linear = self.get_parameter('max_linear_speed').value
                max_angular = self.get_parameter('max_angular_speed').value
                if distance > 0.08:
                    heading_error = wrap_angle(math.atan2(dy, dx) - pose.theta)
                    if abs(heading_error) > 0.12:
                        command.angular.z = max(-max_angular, min(max_angular, 3.0 * heading_error))
                    else:
                        command.linear.x = min(max_linear, 1.5 * distance)
                        command.angular.z = max(-max_angular, min(max_angular, 2.0 * heading_error))
                elif abs(final_error) > 0.04:
                    command.angular.z = max(-max_angular, min(max_angular, 3.0 * final_error))
                else:
                    self.stop()
                    goal_handle.succeed()
                    result.success = True
                    result.message = 'Target pose reached'
                    return result
                self.publisher.publish(command)
                feedback = GoToPose.Feedback()
                feedback.remaining_distance = distance
                feedback.remaining_yaw = final_error
                goal_handle.publish_feedback(feedback)
                time.sleep(0.04)
            goal_handle.abort()
            result.message = 'ROS shutdown'
            return result
        finally:
            self.stop()
            self.motion_lock.release()


def main():
    rclpy.init()
    node = GoToPoseServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
