#!/usr/bin/env python3

import cv2
import rclpy

from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32
from cv_bridge import CvBridge


class DetectorAruco(Node):

    def __init__(self):
        super().__init__('detector_aruco')

        self.bridge = CvBridge()

        # Diccionario exigido por el profesor
        self.diccionario = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_5X5_100
        )

        # Compatible con distintas versiones de OpenCV
        if hasattr(cv2.aruco, 'DetectorParameters'):
            parametros = cv2.aruco.DetectorParameters()
        else:
            parametros = cv2.aruco.DetectorParameters_create()

        if hasattr(cv2.aruco, 'ArucoDetector'):
            self.detector = cv2.aruco.ArucoDetector(
                self.diccionario, parametros
            )
        else:
            self.detector = None
            self.parametros = parametros

        # Subscriber: cámara del TurtleBot3 en Gazebo
        self.suscriptor = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.callback_imagen,
            qos_profile_sensor_data
        )

        # Publishers
        self.pub_detecciones = self.create_publisher(
            String, '/aruco/detections', 10
        )

        self.pub_id = self.create_publisher(
            Int32, '/aruco_id', 10
        )

        self.ultimo_resultado = None

        self.get_logger().info(
            'Detector ArUco iniciado. Esperando imagen...'
        )

    def callback_imagen(self, msg):

        try:
            imagen = self.bridge.imgmsg_to_cv2(
                msg, desired_encoding='bgr8'
            )

            gris = cv2.cvtColor(
                imagen, cv2.COLOR_BGR2GRAY
            )

            if self.detector is not None:
                esquinas, ids, _ = self.detector.detectMarkers(gris)
            else:
                esquinas, ids, _ = cv2.aruco.detectMarkers(
                    gris,
                    self.diccionario,
                    parameters=self.parametros
                )

            resultados = []

            if ids is not None:
                for i, identificador in enumerate(ids.flatten()):

                    puntos = esquinas[i][0]

                    x = int(puntos[:, 0].mean())
                    y = int(puntos[:, 1].mean())

                    resultados.append(
                        f'ID: {int(identificador)}, X: {x}, Y: {y}'
                    )

                # ID del primer marcador detectado
                self.pub_id.publish(
                    Int32(data=int(ids.flatten()[0]))
                )

            else:
                # -1 indica que no se ve ningún ArUco
                self.pub_id.publish(Int32(data=-1))

            texto = (
                ' | '.join(resultados)
                if resultados
                else 'Sin ArUcos detectados'
            )

            self.pub_detecciones.publish(String(data=texto))

            # Mostrar cambios sin saturar la terminal
            if texto != self.ultimo_resultado:
                self.get_logger().info(texto)
                self.ultimo_resultado = texto

        except Exception as error:
            self.get_logger().error(str(error))


def main(args=None):
    rclpy.init(args=args)

    nodo = DetectorAruco()

    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
