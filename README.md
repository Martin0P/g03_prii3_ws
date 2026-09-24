# PRII3 Sprint 1 - Grupo 03

## Requisitos
- Ubuntu 22.04
- ROS 2 Humble
- turtlesim

## Compilar
```bash
source /opt/ros/humble/setup.bash
cd ~/g03_prii3_ws
colcon build --symlink-install
source install/setup.bash
```
## Ejecutar
```bash
ros2 launch g03_prii3_turtlesim turtlesim_g03.launch.py
```
## Servicios
### Pausar:
```bash
ros2 service call /g03/pause std_srvs/srv/Trigger "{}"
```

### Reanudar:
```bash
ros2 service call /g03/resume std_srvs/srv/Trigger "{}"
```

### Reiniciar:
```bash
ros2 service call /g03/restart std_srvs/srv/Trigger "{}"
```
