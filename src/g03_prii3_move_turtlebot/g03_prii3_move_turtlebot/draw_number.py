import math
import rclpy

from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv   import Trigger

class DrawNumber(Node):
    def __init__(self):
        super().__init__('draw_number')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.create_service(Trigger, '/g03/pause', self.pause_callback)
        self.create_service(Trigger, '/g03/resume', self.resume_callback)
        self.create_service(Trigger, '/g03/restart', self.restart_callback)

        # Valores moderados para TurtleBot3 en Gazebo.
        # Radio de cada arco: v / omega = 0.30 m.
        self.linear_speed = 0.15   # m/s
        self.angular_speed = 0.50  # rad/s
        self.turn_speed = 0.70     # rad/s

        # (velocidad lineal, velocidad angular, duracion)
        self.movements = [
            (self.linear_speed, -self.angular_speed,
             math.pi / self.angular_speed),       # arco superior (180 grados)
            (0.0, self.turn_speed,
             math.pi / self.turn_speed),          # girar 180 grados en el centro
            (self.linear_speed, -self.angular_speed,
             math.pi / self.angular_speed),       # arco inferior (180 grados)
        ]

        self.current_movement = 0
        self.elapsed_time = 0.0
        self.paused = True       # Esperar a /g03/resume antes de moverse
        self.finished = False
        self.last_time = self.get_clock().now()

        self.timer = self.create_timer(0.05, self.control_loop)  # 20 Hz

        self.get_logger().info(
            'Nodo draw_number preparado. Usa /g03/resume para empezar.'
        )

    def send_velocity(self, linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.publisher.publish(msg)

    def stop_robot(self):
        self.send_velocity()

    def control_loop(self):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        # Ignorar saltos de tiempo grandes (p. ej., arranque de Gazebo).
        dt = max(0.0, min(dt, 0.2))

        if self.paused or self.finished:
            self.stop_robot()
            return

        linear, angular, duration = self.movements[self.current_movement]

        if self.elapsed_time >= duration:
            self.stop_robot()
            self.current_movement += 1
            self.elapsed_time = 0.0

            if self.current_movement >= len(self.movements):
                self.finished = True
                self.get_logger().info('Dibujo del numero 3 terminado')
            else:
                self.get_logger().info(
                    f'Iniciando movimiento {self.current_movement + 1}/'
                    f'{len(self.movements)}'
                )
            return

        self.send_velocity(linear, angular)
        self.elapsed_time += dt

    def pause_callback(self, request, response):
        self.paused = True
        self.stop_robot()
        response.success = True
        response.message = 'Dibujo pausado'
        return response

    def resume_callback(self, request, response):
        if self.finished:
            response.success = False
            response.message = 'Dibujo terminado. Usa /g03/restart.'
            return response

        self.paused = False
        self.last_time = self.get_clock().now()
        response.success = True
        response.message = 'Dibujo reanudado'
        return response

    def restart_callback(self, request, response):
        self.stop_robot()
        self.current_movement = 0
        self.elapsed_time = 0.0
        self.finished = False
        self.paused = True
        self.last_time = self.get_clock().now()
        response.success = True
        response.message = 'Secuencia reiniciada. Usa /g03/resume.'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = DrawNumber()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.stop_robot()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()