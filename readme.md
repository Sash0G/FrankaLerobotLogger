Requires a set up usb_cam ros2 package working already

# To setup the camera

```bash
ros2 run usb_cam usb_cam_node_exe --ros-args --params-file <yamlfile> -r /image_raw:=/cam<i>/image_raw 
```
where i is the number of the camera, beginning from 0


f.e. 
```bash
ros2 run usb_cam usb_cam_node_exe --ros-args --params-file src/franka_loger/config/test_camera.yaml -r /image_raw:=/cam0/image_raw
```

# To setup the loger
There is a default logger_params.yaml file in config, but you can easily add a new one. Just remember to build
```bash
colcon build --packages-select franka_loger
source install/setup.bash
```
After that just run

```bash
ros2 run franka_loger franka_loger --ros-args --params-file <yaml_file>
```
You cal also run, with the default yaml
```bash
ros2 run franka_loger franka_loger
```



f.e.
```bash
ros2 run franka_loger franka_loger --ros-args --params-file src/franka_loger/config/logger_params.yaml
```
