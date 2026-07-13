paths = [
    '/home/camil/.simulation-gazebo/models/x500/model.sdf',
    '/home/camil/gsie-feu/PX4-Autopilot/Tools/simulation/gz/models/x500/model.sdf',
]
for p in paths:
    with open(p, 'r') as f:
        c = f.read()
    c = c.replace(
        '<commandSubTopic>/x500_0/command/motor_speed</commandSubTopic>',
        '<commandSubTopic>command/motor_speed</commandSubTopic>'
    )
    with open(p, 'w') as f:
        f.write(c)
    print(f'Reverted {p}')
