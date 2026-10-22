from setuptools import find_packages, setup

package_name = 'g03_prii3_move_jetbot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='molipic',
    maintainer_email='martinolipic@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'draw3 = g03_prii3_move_jetbot.draw3:main',
            'collision_avoidance = g03_prii3_move_jetbot.collision_avoidance:main',
            'obstacle_avoidance = g03_prii3_move_jetbot.obstacle_avoidance:main',    
        ],
    },
)
