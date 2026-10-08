import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv   import Trigger

class DrawNumber(Node):

    def __init__(self):
        super().__init__('draw_number')

        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.movements = [
            (0.20, -0.80, 2.0),
            (0.20, -0.80, 2.0),
            (-0.20, -0.80, 2.0),
            (-0.20, -0.80, 2.0)
        ]

        # Estado programa
        self.current_movement = 0
        self.elapsed_time = 0.0

        self.paused = True
        self.finished = False

        # Temporizadores
        self.timer_period = 0.1

        self.timer = self.create_timer(
            self.timer_period,
            self.control_loop
        )

        # Servicios 
        self.create_service(
            Trigger,
            '/g03/pause',
            self.pause_callback
        )

        self.create_service(
            Trigger,
            '/g03/resume',
            self.resume_callback
        )

        self.create_service(
            Trigger,
            '/g03/restart',
            self.restart_callback
        )

        self.get_logger().info(
            'Nodo draw_number del Grupo 03'
        )

        self.get_logger().info(
            'Esperando orden /g03/resume'
        )

    def control_loop(self):

        if self.paused:
            return

        if self.finished:
            return
     
        # Si hemos terminado todos los movimientos
        if self.current_movement >= len(self.movements):

            self.stop_robot()

            self.finished = True

            self.get_logger().info(
                'Dibujo del número 3 terminado'
            )

            return

        linear_x, angular_z, duration = self.movements[
            self.current_movement
        ]

        # Crear mensaje Twist
        msg = Twist()

        msg.linear.x = linear_x
        msg.angular.z = angular_z

        # Publicar velocidad
        self.publisher.publish(msg)

        # Actualizar tiempo
        self.elapsed_time += self.timer_period


        if self.elapsed_time >= duration:
            self.current_movement += 1
            self.elapsed_time = 0.0

            self.get_logger().info(
                f'Movimiento '
                f'{self.current_movement}/'
                f'{len(self.movements)}'
            )


    def stop_robot(self): # Parar el robot
        if not rclpy.ok():
            return

        msg = Twist()

        msg.linear.x = 0.0
        msg.angular.z = 0.0

        self.publisher.publish(msg)

    def pause_callback(self, request, response): # Servicio de parada
        self.paused = True
        self.stop_robot()

        response.success = True
        response.message = 'Dibujo Detenido'

        self.get_logger().info('Dibujo pausado')

        return response

    def resume_callback(self, request, response):

        if self.finished:

            response.success = False
            response.message = (
                'El dibujo ya ha terminado. '
                'Utiliza /g03/restart para comenzar de nuevo.'
            )

            return response

        self.paused = False

        response.success = True
        response.message = 'Dibujo reanudado'

        self.get_logger().info('Dibujo reanudado')

        return response

    def restart_callback(self, request, response):

        self.stop_robot()

        self.current_movement = 0
        self.elapsed_time = 0.0
        self.finished = False

        self.paused = True

        response.success = True
        response.message = 'Dibujo reiniciado'

        self.get_logger().info('Dibujo reiniciado')

        return response

    def destroy_node(self):
        if rclpy.ok():
            self.stop_robot()

        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)

    node = DrawNumber()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()