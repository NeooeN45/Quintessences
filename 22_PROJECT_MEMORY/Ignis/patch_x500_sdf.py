import sys

path = sys.argv[1]
with open(path, 'r') as f:
    content = f.read()

# Change commandSubTopic from relative "command/motor_speed" to absolute "/x500_0/command/motor_speed"
# This makes the Gazebo plugin listen on the same topic the gz_bridge publishes to
content = content.replace(
    '<commandSubTopic>command/motor_speed</commandSubTopic>',
    '<commandSubTopic>/x500_0/command/motor_speed</commandSubTopic>'
)

with open(path, 'w') as f:
    f.write(content)
print('SDF patched OK')
