#!/usr/bin/env python

import sys

from rcl_interfaces.srv import SetParameters
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import PointCloud2
from std_srvs.srv import Trigger
import time

class Sample(Node):

    def __init__(self):
        super().__init__('sample_capture_py')

        self.capture_service = self.create_client(Trigger, 'capture')
        # while not self.capture_service.wait_for_service(timeout_sec=3.0):
        #     self.get_logger().info('capture service not available, waiting again...')

        self._set_settings()

        self.subscription = self.create_subscription(
            PointCloud2, 'points/xyzrgba', self.on_points, 10
        )

    def _set_settings(self):
        self.get_logger().info('Setting parameter `settings_yaml`')
        settings_parameter = Parameter(
            'settings_yaml',
            Parameter.Type.STRING,
            """
__version__:
  serializer: 1
  data: 25
Settings:
  Acquisitions:
    - Acquisition:
        Aperture: 3.67
        Brightness: 1.5
        ExposureTime: 20000
        Gain: 1
  Diagnostics:
    Enabled: no
  Engine: omni
  Processing:
    Color:
      Balance:
        Blue: 1
        Green: 1
        Red: 1
      Experimental:
        Mode: automatic
      Gamma: 1.3
    Filters:
      Cluster:
        Removal:
          Enabled: yes
          MaxNeighborDistance: 6
          MinArea: 500
      Experimental:
        ContrastDistortion:
          Correction:
            Enabled: no
            Strength: 0
          Removal:
            Enabled: no
            Threshold: 0.4
      Hole:
        Repair:
          Enabled: yes
          HoleSize: 0.7
          Strictness: 1
      Noise:
        Removal:
          Enabled: yes
          Threshold: 2
        Repair:
          Enabled: yes
        Suppression:
          Enabled: yes
      Outlier:
        Removal:
          Enabled: yes
          Threshold: 10
      Reflection:
        Removal:
          Enabled: yes
          Mode: global
      Smoothing:
        Gaussian:
          Enabled: yes
          Sigma: 1.5
    Resampling:
      Mode: disabled
  RegionOfInterest:
    Box:
      Enabled: no
      Extents: [-10, 100]
      PointA: [0, 0, 0]
      PointB: [0, 0, 0]
      PointO: [0, 0, 0]
    Depth:
      Enabled: no
      Range: [300, 1100]
  Sampling:
    Color: rgb
    Pixel: blueSubsample4x4
""",
        ).to_parameter_msg()

        param_client = self.create_client(SetParameters, 'zivid_camera/set_parameters')
        # while not param_client.wait_for_service(timeout_sec=3):
        #     self.get_logger().info('Parameter service not available, waiting again...')

        future = param_client.call_async(
            SetParameters.Request(parameters=[settings_parameter])
        )
        rclpy.spin_until_future_complete(self, future, timeout_sec=30)
        if not future.result():
            raise RuntimeError('Failed to set parameters')

        self.create_timer(3, self.capture)

    def capture(self):
        self.get_logger().info('Calling capture service')
        return self.capture_service.call_async(Trigger.Request())

    def on_points(self, msg):
        self.get_logger().info(
            f'Received point cloud of size {msg.width} x {msg.height}'
        )


def main(args=None):
    rclpy.init(args=args)

    try:
        sample = Sample()

        sample.get_logger().info('Spinning node.. Press Ctrl+C to abort.')

        # while rclpy.ok():
        # sample.capture()
        rclpy.spin(sample)
        # rclpy.spin_until_future_complete(sample, future)
        sample.get_logger().info('Capture complete')

    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        sys.exit(1)


if __name__ == '__main__':
    main()
