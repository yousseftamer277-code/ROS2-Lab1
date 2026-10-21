import math
import threading

import rclpy
from rclpy.action import ActionClient, ActionServer, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import Trigger
from turtle_interfaces.action import DrawSquare, GoToPose


class SquareServer(Node):
    def __init__(self):
        super().__init__('square_server')
        group = ReentrantCallbackGroup()
        self.reset_client = self.create_client(Trigger, '/reset_turtle', callback_group=group)
        self.pose_client = ActionClient(self, GoToPose, '/go_to_pose', callback_group=group)
        self.server = ActionServer(self, DrawSquare, '/draw_square',
                                   goal_callback=self.accept_goal,
                                   execute_callback=self.execute, callback_group=group)
        self.busy = threading.Lock()

    def accept_goal(self, request):
        side = request.side_length
        if not math.isfinite(side) or side <= 0 or side > 4.5 or self.busy.locked():
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    @staticmethod
    def wait(future, timeout=130.0):
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        if not event.wait(timeout):
            raise RuntimeError('Timed out waiting for ROS response')
        return future.result()

    def execute(self, goal_handle):
        result = DrawSquare.Result()
        if not self.busy.acquire(blocking=False):
            goal_handle.abort()
            result.message = 'Another square is in progress'
            return result
        try:
            if not self.reset_client.wait_for_service(timeout_sec=5.0):
                raise RuntimeError('Reset service unavailable')
            reset_response = self.wait(self.reset_client.call_async(Trigger.Request()), 10.0)
            if not reset_response.success:
                raise RuntimeError('Reset failed: ' + reset_response.message)
            if not self.pose_client.wait_for_server(timeout_sec=5.0):
                raise RuntimeError('goToPose action unavailable')
            x = y = 5.544445
            s = goal_handle.request.side_length
            # Four separate goals, one for each corner; final goal closes the square.
            corners = [(x+s, y, math.pi/2), (x+s, y+s, math.pi),
                       (x, y+s, -math.pi/2), (x, y, 0.0)]
            for number, (tx, ty, yaw) in enumerate(corners, start=1):
                goal = GoToPose.Goal()
                goal.target.x = tx
                goal.target.y = ty
                goal.target.yaw = yaw
                handle = self.wait(self.pose_client.send_goal_async(goal), 10.0)
                if not handle.accepted:
                    raise RuntimeError('Corner goal %d rejected' % number)
                response = self.wait(handle.get_result_async(), 130.0)
                if not response.result.success:
                    raise RuntimeError('Corner %d failed: %s' % (number, response.result.message))
                feedback = DrawSquare.Feedback()
                feedback.completed_sides = number
                goal_handle.publish_feedback(feedback)
            goal_handle.succeed()
            result.success = True
            result.message = 'Square completed using 4 goToPose goals'
        except Exception as error:
            goal_handle.abort()
            result.message = str(error)
        finally:
            self.busy.release()
        return result


def main():
    rclpy.init()
    node = SquareServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
