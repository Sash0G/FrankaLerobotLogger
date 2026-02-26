Requires a set up usb_cam ros2 package working already

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

For setting camera, point cameras_path to the config folder of the cameras, it will then assume config_camerai.yaml for the respecting camera and launch it.

# Converting episodes to Lerobot format

```bash
ros2 run franka_loger convert_to_lerobot --config <name of config file>
```
default config file is convert_param.yaml
You need to build after changing to config file


