import rclpy
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger
from std_srvs.srv import Empty
from turtlesim.srv import TeleportAbsolute


def main():
    # INICIAR ROS 2
    rclpy.init()

    # Crear nuestro nodo
    node = rclpy.create_node('turtle_controller')


    # PUBLISHER
    # Publicamos velocidades en /turtle1/cmd_vel
    publisher = node.create_publisher(
        Twist,
        '/turtle1/cmd_vel',
        10
    )
 
    # CLEAN
    clear_client = node.create_client(
        Empty,
        '/clear'
    )

    # COMANDOS PARA DIBUJAR EL 3
    # 8 ciclos = 0.8 segundos
    comandos = [
        (2.0, -2.0, 8),
        (2.0, -2.0, 8),
        (-2.0, -2.0, 8),
        (-2.0, -2.0, 8)
    ]


    # ESTADO DEL PROGRAMA
    estado = {
        'comando': 0,
        'ciclos': 0,
        'pausado': True,
        'terminado': False
    }


    # CLIENTES DE SERVICIOS DE TURTLESIM
    # Servicio para reiniciar turtlesim
    reset_client = node.create_client(
        Empty,
        '/reset'
    )

    # Servicio para colocar la tortuga
    teleport_client = node.create_client(
        TeleportAbsolute,
        '/turtle1/teleport_absolute'
    )


    # FUNCIÓN PARA DETENER LA TORTUGA
    def parar_tortuga():
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        publisher.publish(msg)


    # COLOCAR TORTUGA EN POSICIÓN INICIAL
    def colocar_inicio():
        request = TeleportAbsolute.Request()
        request.x = 5.5
        request.y = 7.5
        request.theta = 0.0
        future = teleport_client.call_async(request)
        future.add_done_callback(
            inicio_terminado
        )


    def inicio_terminado(future):
        future_clear = clear_client.call_async(
            Empty.Request()
        )

        future_clear.add_done_callback(
            limpieza_terminada
        )


    def limpieza_terminada(future):
        estado['pausado'] = False
        node.get_logger().info(
            'Tortuga colocada y pantalla limpia'
        )



    # REINICIAR DIBUJO
    def reiniciar_dibujo():
        estado['pausado'] = True
        estado['terminado'] = False
        estado['comando'] = 0
        estado['ciclos'] = 0
        parar_tortuga()
        future = reset_client.call_async(
            Empty.Request()
        )
        future.add_done_callback(
            lambda future: colocar_inicio()
        )


    # TIMER PRINCIPAL
    def mover_tortuga():
        if estado['pausado']:

            return

        if estado['terminado']:
            return

        if estado['comando'] >= len(comandos):
            parar_tortuga()
            estado['terminado'] = True
            node.get_logger().info(
                'Dibujo terminado'
            )
            return
        
        linear_x, angular_z, duracion = comandos[
            estado['comando']
        ]
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        publisher.publish(msg)
        estado['ciclos'] += 1
        if estado['ciclos'] >= duracion:
            estado['comando'] += 1
            estado['ciclos'] = 0


    # SERVICIO PAUSE
    def pause_callback(request, response):
        estado['pausado'] = True
        parar_tortuga()
        response.success = True
        response.message = 'Dibujo detenido'
        node.get_logger().info(
            'Dibujo detenido'
        )
        return response


    # SERVICIO RESUME
    def resume_callback(request, response):
        if estado['terminado']:
            response.success = False
            response.message = (
                'El dibujo ya ha terminado. '
                'Usa restart para volver a empezar.'
            )
            return response

        estado['pausado'] = False
        response.success = True
        response.message = 'Dibujo reanudado'
        node.get_logger().info(
            'Dibujo reanudado'
        )
        return response


    # SERVICIO RESTART
    def restart_callback(request, response):
        reiniciar_dibujo()
        response.success = True
        response.message = 'Dibujo reiniciado'
        node.get_logger().info(
            'Dibujo reiniciado'
        )
        return response


    # CREAR SERVICIOS
    node.create_service(
        Trigger,
        '/g03/pause',
        pause_callback
    )

    node.create_service(
        Trigger,
        '/g03/resume',
        resume_callback
    )

    node.create_service(
        Trigger,
        '/g03/restart',
        restart_callback
    )


    # CREAR TIMER
    # mover_tortuga() se ejecuta cada 0.1 segundos
    node.create_timer(
        0.1,
        mover_tortuga
    )


    # ESPERAR A TURTLESIM
    node.get_logger().info(
        'Esperando servicios de turtlesim...'
    )
    reset_client.wait_for_service()
    teleport_client.wait_for_service()
    clear_client.wait_for_service()

    # COMENZAR DIBUJO
    reiniciar_dibujo()
    node.get_logger().info(
        'Controlador Grupo 03 iniciado'
    )


    # MANTENER NODO FUNCIONANDO
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


    # CERRAR
    parar_tortuga()
    node.destroy_node()
    rclpy.shutdown()


# EJECUTAR MAIN
if __name__ == '__main__':
    main()