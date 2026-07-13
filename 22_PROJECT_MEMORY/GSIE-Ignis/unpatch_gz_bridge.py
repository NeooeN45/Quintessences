import sys

path = sys.argv[1]
with open(path, 'r') as f:
    content = f.read()

# Revert: change /model/ back to /
content = content.replace(
    'std::string motor_speed_topic = "/model/" + model_name + "/command/motor_speed";',
    'std::string motor_speed_topic = "/" + model_name + "/command/motor_speed";'
)
content = content.replace(
    'std::string actuator_topic = "/model/" + model_name + "/command/motor_speed";',
    'std::string actuator_topic = "/" + model_name + "/command/motor_speed";'
)

with open(path, 'w') as f:
    f.write(content)
print('Reverted OK')
