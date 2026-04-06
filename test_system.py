#!/usr/bin/env python3
"""
Test script to verify all modules work correctly.
Run this on the Raspberry Pi before deployment.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pi"))


def test_imports():
    print("Testing imports...")
    try:
        import cv2

        print(f"  ✓ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"  ✗ OpenCV: {e}")
        return False

    try:
        import dlib

        print(f"  ✓ dlib: {dlib.__version__}")
    except ImportError as e:
        print(f"  ✗ dlib: {e}")
        return False

    try:
        import numpy as np

        print(f"  ✓ NumPy: {np.__version__}")
    except ImportError as e:
        print(f"  ✗ NumPy: {e}")
        return False

    try:
        import yaml

        print(f"  ✓ PyYAML")
    except ImportError as e:
        print(f"  ✗ PyYAML: {e}")
        return False

    try:
        import serial

        print(f"  ✓ pyserial")
    except ImportError as e:
        print(f"  ✗ pyserial: {e}")
        return False

    try:
        import pynmea2

        print(f"  ✓ pynmea2")
    except ImportError as e:
        print(f"  ✗ pynmea2: {e}")
        return False

    try:
        import requests

        print(f"  ✓ requests")
    except ImportError as e:
        print(f"  ✗ requests: {e}")
        return False

    return True


def test_dlib_model():
    print("\nTesting dlib model...")
    import dlib
    import os

    model_path = os.path.join(
        os.path.dirname(__file__), "shape_predictor_68_face_landmarks.dat"
    )
    if os.path.exists(model_path):
        print(f"  ✓ Model file exists")
        try:
            detector = dlib.get_frontal_face_detector()
            predictor = dlib.shape_predictor(model_path)
            print(f"  ✓ Model loads correctly")
            return True
        except Exception as e:
            print(f"  ✗ Model load failed: {e}")
            return False
    else:
        print(f"  ✗ Model file not found: {model_path}")
        return False


def test_config():
    print("\nTesting config.yaml...")
    import yaml

    config_path = os.path.join(os.path.dirname(__file__), "pi", "config.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            print(f"  ✓ Config loads")
            print(f"    Camera source: {config['camera']['source']}")
            print(f"    EAR threshold: {config['detection']['ear_threshold']}")
            print(f"    Dashboard port: {config['dashboard']['port']}")
            return True
        except Exception as e:
            print(f"  ✗ Config parse failed: {e}")
            return False
    else:
        print(f"  ✗ Config not found")
        return False


def test_hardware():
    print("\nTesting hardware module...")
    try:
        import yaml
        from pi import hardware

        config_path = os.path.join(os.path.dirname(__file__), "pi", "config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)["hardware"]

        hw = hardware.HardwareAlerts(config)
        print(f"  ✓ Hardware module initializes")
        hw.cleanup()
        return True
    except Exception as e:
        print(f"  ✗ Hardware test failed: {e}")
        return False


def test_gps():
    print("\nTesting GPS module...")
    try:
        import yaml
        from pi import gps

        config_path = os.path.join(os.path.dirname(__file__), "pi", "config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)["gps"]

        gps_reader = gps.GPSReader(config)
        lat, lon = gps_reader.get_coordinates()
        print(f"  ✓ GPS module initializes")
        print(f"    Coordinates: {lat}, {lon}")
        gps_reader.stop()
        return True
    except Exception as e:
        print(f"  ✗ GPS test failed: {e}")
        return False


def test_publisher():
    print("\nTesting publisher module...")
    try:
        import yaml
        from pi import publisher

        config_path = os.path.join(os.path.dirname(__file__), "pi", "config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)["dashboard"]

        pub = publisher.DataPublisher(config)
        print(f"  ✓ Publisher module initializes")
        pub.push({"ear": 0.25, "status": "ALERT", "lat": 18.52, "lon": 73.85})
        pub.stop()
        return True
    except Exception as e:
        print(f"  ✗ Publisher test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Driver Drowsiness Detection - System Test")
    print("=" * 50)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("dlib Model", test_dlib_model()))
    results.append(("Hardware", test_hardware()))
    results.append(("GPS", test_gps()))
    results.append(("Publisher", test_publisher()))

    print("\n" + "=" * 50)
    print("Results Summary")
    print("=" * 50)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    sys.exit(0 if all_passed else 1)
