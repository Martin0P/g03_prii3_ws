
#!/usr/bin/env python3

import math
import rclpy

from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class ObstacleAvoidance(Node):

    def __init__(self):
        super().__init__('obstacle_avoidance')

        # Publicar velocidades
        self.cmd_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        # Recibir los datos del LiDAR
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.laser_callback, 10
        )

        # Recibir la posicion real del robot
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )

        # Servicios del grupo 3; iniciar solo por orden explicita.
        self.create_service(Trigger, '/g03/pause', self.pause_callback)
        self.create_service(Trigger, '/g03/resume', self.resume_callback)
        self.create_service(Trigger, '/g03/restart', self.restart_callback)

        # Configuracion del detector
        self.safe_distance = 1.00
        self.critical_distance = 0.45
        self.front_angle = math.radians(30)

        # Velocidades del dibujo
        self.linear_speed = 0.06
        self.angular_speed = 0.20
        self.turn_speed = 0.28

        # Secuencia del numero 3
        # (velocidad lineal, angular, duracion)
        self.steps = [
            (0.06, -0.20, math.pi / 0.20),
            (0.0, 0.28, math.pi / 0.28),
            (0.06, -0.20, math.pi / 0.20)
        ]

        self.step = 0
        self.elapsed = 0.0
        self.finished = False
        self.paused = True

        # Datos del LiDAR
        self.front_distance = float('inf')
        self.left_distance = float('inf')
        self.right_distance = float('inf')
        self.last_scan_time = None

        # Datos de odometria
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_odom_time = None

        # Estado de la evitacion
        self.avoiding = False
        self.aligning = False
        self.waypoints = []
        self.waypoint_index = 0
        self.original_heading = 0.0

        # Temporizador ROS
        self.last_time = self.get_clock().now()
        self.timer = self.create_timer(
            0.05, self.control_callback
        )

        self.get_logger().info(
            'JetBot Obstacle Avoidance preparado y en pausa.'
        )

    # Enviar velocidad al robot
    def publish_velocity(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_pub.publish(msg)

    def stop(self):
        self.publish_velocity(0.0, 0.0)

    # Obtener posicion y orientacion de /odom
    def odom_callback(self, msg):
        self.last_odom_time = self.get_clock().now()

        pose = msg.pose.pose

        self.x = pose.position.x
        self.y = pose.position.y

        q = pose.orientation

        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y*q.y + q.z*q.z)

        self.yaw = math.atan2(siny, cosy)

    # Procesar las lecturas del LiDAR
    def laser_callback(self, msg):
        self.last_scan_time = self.get_clock().now()

        front = []
        left = []
        right = []

        for i, distance in enumerate(msg.ranges):

            if not math.isfinite(distance):
                continue

            if not (msg.range_min <= distance <= msg.range_max):
                continue

            angle = msg.angle_min + i * msg.angle_increment
            angle = normalize_angle(angle)

            if abs(angle) <= self.front_angle:
                front.append(distance)

            if math.radians(30) < angle <= math.radians(110):
                left.append(distance)

            if -math.radians(110) <= angle < -math.radians(30):
                right.append(distance)

        self.front_distance = (
            min(front) if front else float('inf')
        )

        self.left_distance = (
            min(left) if left else float('inf')
        )

        self.right_distance = (
            min(right) if right else float('inf')
        )

    # Convertir un punto local a coordenadas globales
    def local_to_global(self, forward, lateral):
        c = math.cos(self.original_heading)
        s = math.sin(self.original_heading)

        gx = self.start_x + forward*c - lateral*s
        gy = self.start_y + forward*s + lateral*c

        return (gx, gy)

    # Preparar la maniobra alrededor del cubo
    def start_avoidance(self):
        self.avoiding = True
        self.aligning = False

        # Guardar la posicion donde aparece el obstaculo
        self.start_x = self.x
        self.start_y = self.y
        self.original_heading = self.yaw

        # Elegir el lado con mayor espacio libre
        if self.left_distance >= self.right_distance:
            side = 1.0
            side_name = 'izquierda'
        else:
            side = -1.0
            side_name = 'derecha'

        # Puntos de paso para rodear el cubo
        # Coordenadas relativas a la posicion inicial
        self.waypoints = [
            self.local_to_global(0.10, side * 0.85),
            self.local_to_global(1.45, side * 0.85),
            self.local_to_global(1.85, 0.0)
        ]

        self.waypoint_index = 0

        self.get_logger().warn(
            f'Obstaculo detectado. '
            f'Esquivando por la {side_name}.'
        )

    # Seguir los puntos de paso
    def follow_waypoints(self):

        if self.waypoint_index >= len(self.waypoints):
            self.aligning = True
            return

        target_x, target_y = self.waypoints[
            self.waypoint_index
        ]

        dx = target_x - self.x
        dy = target_y - self.y

        distance = math.hypot(dx, dy)

        # Pasar al siguiente punto
        if distance < 0.12:
            self.waypoint_index += 1

            self.get_logger().info(
                f'Punto de desvio '
                f'{self.waypoint_index} alcanzado'
            )
            return

        # Calcular la direccion hacia el objetivo
        target_angle = math.atan2(dy, dx)

        error = normalize_angle(
            target_angle - self.yaw
        )

        # Velocidad angular proporcional al error
        angular = max(-0.40, min(0.40, 1.5 * error))

        # Reducir velocidad si necesita girar mucho
        if abs(error) > 1.0:
            linear = 0.015
        elif abs(error) > 0.5:
            linear = 0.03
        else:
            linear = 0.06

        # No avanzar si hay riesgo inmediato de choque
        if self.front_distance < self.critical_distance:
            self.publish_velocity(0.0, angular)
            return

        self.publish_velocity(linear, angular)

    # Recuperar la orientacion original
    def align_heading(self):

        error = normalize_angle(
            self.original_heading - self.yaw
        )

        if abs(error) < 0.10:
            self.avoiding = False
            self.aligning = False

            self.get_logger().info(
                'Obstaculo esquivado. '
                'Continuando el numero 3.'
            )
            return

        angular = max(-0.35, min(0.35, 1.5 * error))

        # Pequeño avance durante la reorientacion
        if self.front_distance < self.critical_distance:
            self.publish_velocity(0.0, angular)
        else:
            self.publish_velocity(0.015, angular)

    # Bucle principal de control
    def control_callback(self):

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        dt = max(0.0, min(dt, 0.2))

        if self.finished or self.paused:
            self.stop()
            return

        # Comprobar que los sensores publican datos
        scan_ok = (
            self.last_scan_time is not None
            and 0 <= (
                now - self.last_scan_time
            ).nanoseconds / 1e9 < 1.0
        )

        odom_ok = (
            self.last_odom_time is not None
            and 0 <= (
                now - self.last_odom_time
            ).nanoseconds / 1e9 < 1.0
        )

        if not scan_ok or not odom_ok:
            self.stop()
            return

        # Si estamos esquivando, seguir la maniobra
        if self.avoiding:
            if self.aligning:
                self.align_heading()
            else:
                self.follow_waypoints()
            return

        # Detectar obstaculos durante el dibujo
        if self.front_distance < self.safe_distance:
            self.start_avoidance()
            return

        # Continuar dibujando el numero 3
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
            return

        self.publish_velocity(linear, angular)
        self.elapsed += dt


    def pause_callback(self, request, response):
        self.paused = True
        self.stop()
        response.success = True
        response.message = 'Robot pausado'
        return response

    def resume_callback(self, request, response):
        if self.finished:
            response.success = False
            response.message = 'Secuencia terminada; reiniciar primero'
            return response
        self.paused = False
        self.last_time = self.get_clock().now()
        response.success = True
        response.message = 'Movimiento habilitado'
        return response

    def restart_callback(self, request, response):
        self.stop()
        self.step = 0
        self.elapsed = 0.0
        self.finished = False
        self.avoiding = False
        self.aligning = False
        self.waypoints = []
        self.waypoint_index = 0
        self.paused = True
        self.last_time = self.get_clock().now()
        response.success = True
        response.message = 'Secuencia reiniciada y pausada; NO reposiciona el robot'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()

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

