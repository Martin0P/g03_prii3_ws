
#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger


class Draw3(Node):

    def __init__(self):
        super().__init__('draw3')

        # Publicador de velocidad del JetBot
        self.publisher = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        # Servicios ROS 2
        self.create_service(
            Trigger, '/g03/pause', self.pause_callback
        )
        self.create_service(
            Trigger, '/g03/resume', self.resume_callback
        )
        self.create_service(
            Trigger, '/g03/restart', self.restart_callback
        )

        # Velocidades
        self.linear_speed = 0.06
        self.angular_speed = 0.20
        self.turn_speed = 0.28

        # Duracion de los movimientos
        self.arc_time = math.pi / self.angular_speed
        self.turn_time = math.pi / self.turn_speed

        # Secuencia: (lineal, angular, duracion)
        self.steps = [
            # Primera semicircunferencia
            (self.linear_speed, -self.angular_speed,
             self.arc_time),

            # Giro sobre si mismo
            (0.0, self.turn_speed,
             self.turn_time),

            # Segunda semicircunferencia
            (self.linear_speed, -self.angular_speed,
             self.arc_time)
        ]

        # Estado del dibujo
        self.step = 0
        self.elapsed = 0.0
        self.paused = True
        self.finished = False

        self.last_time = self.get_clock().now()

        # Temporizador de 20 Hz
        self.timer = self.create_timer(
            0.05, self.control_callback
        )

        self.get_logger().info(
            'JetBot preparado y en pausa. Usar /g03/resume para iniciar.'
        )

    # Publicar velocidades
    def send_velocity(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.publisher.publish(msg)

    # Detener el robot
    def stop(self):
        self.send_velocity(0.0, 0.0)

    # Control principal del movimiento
    def control_callback(self):

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        dt = max(0.0, min(dt, 0.2))

        if self.paused or self.finished:
            self.stop()
            return

        linear, angular, duration = self.steps[self.step]

        if self.elapsed >= duration:
            self.stop()
            self.step += 1
            self.elapsed = 0.0

            if self.step >= len(self.steps):
                self.finished = True
                self.get_logger().info(
                    'Dibujo del numero 3 terminado'
                )
            else:
                self.get_logger().info(
                    f'Iniciando movimiento {self.step + 1}'
                )
            return

        self.send_velocity(linear, angular)
        self.elapsed += dt

    # Servicio PAUSE
    def pause_callback(self, request, response):

        self.paused = True
        self.stop()

        response.success = True
        response.message = 'Dibujo pausado'
        return response

    # Servicio RESUME
    def resume_callback(self, request, response):

        if self.finished:
            response.success = False
            response.message = 'Dibujo terminado. Reinicia.'
            return response

        self.paused = False
        self.last_time = self.get_clock().now()

        response.success = True
        response.message = 'Dibujo reanudado'
        return response

    # Servicio RESTART
    def restart_callback(self, request, response):

        self.stop()

        self.step = 0
        self.elapsed = 0.0
        self.paused = True
        self.finished = False
        self.last_time = self.get_clock().now()

        response.success = True
        response.message = 'Secuencia reiniciada'
        return response


def main(args=None):

    rclpy.init(args=args)
    node = Draw3()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        if rclpy.ok():
            node.stop()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

