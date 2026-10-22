# PRII3 - Grupo 03
Workspace ROS 2 del grupo 03. Contiene las prácticas de **Turtlesim (Sprint 1)** y **movimiento y evitación de obstáculos del TurtleBot3 en Gazebo (Sprint 2)**.

## 1. Requisitos

- Ubuntu 22.04 y ROS 2 Humble.
- Python 3, `colcon` y los paquetes ROS 2 `rclpy`, `geometry_msgs`, `sensor_msgs`, `nav_msgs` y `std_srvs`.
- Simulador Gazebo Classic con `turtlebot3_gazebo` instalado.
- Modelo del robot: TurtleBot3 **Burger**.


## 2. Compilar
Desde una terminal:

```bash
source /opt/ros/humble/setup.bash
cd ~/g03_prii3_ws
colcon build --symlink-install
source install/setup.bash
```

Comprobar los programas disponibles del paquete de simulación:
```bash
ros2 pkg executables g03_prii3_move_turtlebot
```

## 3. Sprint 1 — Turtlesim

### Lanzar Turtlesim
```bash
source /opt/ros/humble/setup.bash
source ~/g03_prii3_ws/install/setup.bash
ros2 launch g03_prii3_turtlesim turtlesim_g03.launch.py
```

## Servicios
Ejecutarlos desde otra terminal que tenga cargado el entorno:

# Pausar:
```bash
ros2 service call /g03/pause std_srvs/srv/Trigger "{}"
```

# Reanudar:
```bash
ros2 service call /g03/resume std_srvs/srv/Trigger "{}"
```

# Reiniciar:
```bash
ros2 service call /g03/restart std_srvs/srv/Trigger "{}"
```

## 4. Sprint 2 — TurtleBot3 en Gazebo

### 4.1. Iniciar el simulador (Terminal 1)
```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo empty_world.launch.py
```

Se puede comprobar la disponibilidad de los tópicos desde otra terminal:
```bash
ros2 topic list -t | grep -E '/cmd_vel|/scan|/odom'
```

Tópicos empleados:

| Tópico | Tipo | Uso |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Velocidades de movimiento |
| `/scan` | `sensor_msgs/msg/LaserScan` | Distancias medidas por el LiDAR |
| `/odom` | `nav_msgs/msg/Odometry` | Posición y orientación estimadas |

### 4.2. Demostración 1: dibujar el número 3
**Terminal 2:**
```bash
source ~/g03_prii3_ws/install/setup.bash
ros2 run g03_prii3_move_turtlebot draw_number --ros-args -p use_sim_time:=true
```
El programa arranca **pausado** y espera una orden de reanudación.

**Terminal 3:**
```bash
source ~/g03_prii3_ws/install/setup.bash

# Iniciar el dibujo
ros2 service call /g03/resume std_srvs/srv/Trigger "{}"

# Pausar el dibujo
ros2 service call /g03/pause std_srvs/srv/Trigger "{}"

# Continuar desde donde se pausó
ros2 service call /g03/resume std_srvs/srv/Trigger "{}"

# Reiniciar la secuencia (queda pausada)
ros2 service call /g03/restart std_srvs/srv/Trigger "{}"

# Volver a iniciarla tras reiniciar
ros2 service call /g03/resume std_srvs/srv/Trigger "{}"
```

### 4.3. Preparar el obstáculo de Gazebo
**Terminal libre — insertar cubo de 50 cm:**
```bash
ros2 run gazebo_ros spawn_entity.py \
  -file ~/g03_prii3_ws/src/g03_prii3_move_turtlebot/models/cubo.sdf \
  -entity cubo \
  -x 0.45 -y -0.30 -z 0.25
```
### 4.4. Demostración B: detección y parada automática con LiDAR
```bash
source ~/g03_prii3_ws/install/setup.bash
ros2 run g03_prii3_move_turtlebot obstacle_avoidance --ros-args -p use_sim_time:=true
```


### 4.5. Demostración C: esquivar un cubo y completar el recorrido
```bash
source ~/g03_prii3_ws/install/setup.bash
ros2 run g03_prii3_move_turtlebot obstacle_esquivar --ros-args -p use_sim_time:=true
```
