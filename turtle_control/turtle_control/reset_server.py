import threading

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import Empty, Trigger
from turtlesim.srv import TeleportAbsolute, SetPen


class ResetServer(Node):
    def __init__(self):
        super().__init__('reset_server')
        group = ReentrantCallbackGroup()
        self.clear_client = self.create_client(Empty, '/clear', callback_group=group)
        self.teleport_client = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute', callback_group=group)
        self.pen_client = self.create_client(SetPen, '/turtle1/set_pen', callback_group=group)
        self.create_service(Trigger, '/reset_turtle', self.reset, callback_group=group)
        self.lock = threading.Lock()

    def call(self, client, request):
        if not client.wait_for_service(timeout_sec=3.0):
            raise RuntimeError('Turtlesim service unavailable: ' + client.srv_name)
        future = client.call_async(request)
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        if not event.wait(timeout=5.0):
            raise RuntimeError('Service timeout: ' + client.srv_name)
        return future.result()

    def reset(self, request, response):
        if not self.lock.acquire(blocking=False):
            response.success = False
            response.message = 'Reset already in progress'
            return response
        try:
            pen_off = SetPen.Request()
            pen_off.off = 1
            self.call(self.pen_client, pen_off)
            teleport = TeleportAbsolute.Request()
            teleport.x = 5.544445
            teleport.y = 5.544445
            teleport.theta = 0.0
            self.call(self.teleport_client, teleport)
            self.call(self.clear_client, Empty.Request())
            pen_on = SetPen.Request()
            pen_on.off = 0
            pen_on.width = 2
            self.call(self.pen_client, pen_on)
            response.success = True
            response.message = 'Turtle reset and screen cleared'
        except Exception as error:
            response.success = False
            response.message = str(error)
        finally:
            self.lock.release()
        return response


def main():
    rclpy.init()
    node = ResetServer()
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
