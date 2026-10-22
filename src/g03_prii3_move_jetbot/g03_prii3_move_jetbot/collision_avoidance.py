
#!/usr/bin/env python3

import math
import rclpy

from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger


class CollisionAvoidance(Node):

    def __init__(self):
        super().__init__('collision_avoidance')

        # Publicador de velocidad del robot
        self.publisher = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        # Suscriptor al LiDAR
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.laser_callback, 10
        )

        # Servicios ROS
        self.create_service(
            Trigger, '/g03/pause', self.pause_callback
        )
        self.create_service(
            Trigger, '/g03/resume', self.resume_callback
        )
        self.create_service(
            Trigger, '/g03/restart', self.restart_callback
        )

        # Configuracion del LiDAR
        self.safe_distance = 0.80
        self.front_angle = math.radians(30)

        self.obstacle = False
        self.last_scan_time = None

        # Velocidades del numero 3
        self.linear_speed = 0.06
        self.angular_speed = 0.20
        self.turn_speed = 0.28

        # Duraciones de movimiento
        self.arc_time = math.pi / self.angular_speed
        self.turn_time = math.pi / self.turn_speed

        # Secuencia del dibujo
        # (velocidad lineal, velocidad angular, duracion)
        self.steps = [
            (self.linear_speed, -self.angular_speed,
             self.arc_time),

            (0.0, self.turn_speed,
             self.turn_time),

            (self.linear_speed, -self.angular_speed,
             self.arc_time)
        ]

        # Estado del robot
        self.step = 0
        self.elapsed = 0.0
        self.paused = True
        self.finished = False

        self.last_time = self.get_clock().now()

        # Temporizador a 20 Hz
        self.timer = self.create_timer(
            0.05, self.control_callback
        )

        self.get_logger().info(
            'JetBot Collision Avoidance preparado y en pausa.'
        )

    # Procesamiento de los datos del LiDAR
    def laser_callback(self, msg):

        self.last_scan_time = self.get_clock().now()
        distances = []

        for i, distance in enumerate(msg.ranges):

            angle = msg.angle_min + i * msg.angle_increment

            # Normalizar el angulo entre -pi y pi
            angle = math.atan2(
                math.sin(angle),
                math.cos(angle)
            )

            # Detectar unicamente delante del robot
            if abs(angle) <= self.front_angle:

                if math.isfinite(distance):
                    if msg.range_min <= distance <= msg.range_max:
                        distances.append(distance)

        # Obstaculo dentro de la distancia de seguridad
        detected = (
            len(distances) > 0
            and min(distances) < self.safe_distance
        )

        if detected != self.obstacle:

            self.obstacle = detected

            if detected:
                self.get_logger().warn(
                    'Obstaculo detectado. Robot detenido.'
                )
                self.stop()
            else:
                self.get_logger().info(
                    'Camino libre. Reanudando dibujo.'
                )

    # Enviar velocidades
    def send_velocity(self, linear, angular):

        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)

        self.publisher.publish(msg)

    # Detener el robot
    def stop(self):
        self.send_velocity(0.0, 0.0)

    # Control principal
    def control_callback(self):

        now = self.get_clock().now()

        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        dt = max(0.0, min(dt, 0.2))

        # Comprobar que llegan datos recientes del LiDAR
        scan_ok = (
            self.last_scan_time is not None
            and 0 <= (now - self.last_scan_time).nanoseconds / 1e9 < 1.0
        )

        # Detener durante una pausa, obstaculo
        # o perdida de datos del sensor
        if (self.paused or self.finished
                or self.obstacle or not scan_ok):
            self.stop()
            return

        linear, angular, duration = self.steps[self.step]

        # Cambiar al siguiente movimiento
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
                    f'Movimiento {self.step + 1}'
                )

            return

        # Ejecutar movimiento
        self.send_velocity(linear, angular)
        self.elapsed += dt

    # Servicio de pausa
    def pause_callback(self, request, response):

        self.paused = True
        self.stop()

        response.success = True
        response.message = 'Dibujo pausado'
        return response

    # Servicio de reanudacion
    def resume_callback(self, request, response):

        if self.finished:
            response.success = False
            response.message = 'El dibujo ha terminado'
            return response

        self.paused = False
        self.last_time = self.get_clock().now()

        response.success = True
        response.message = 'Dibujo reanudado'
        return response

    # Servicio de reinicio
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
    node = CollisionAvoidance()

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

