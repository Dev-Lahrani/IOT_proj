#!/usr/bin/env python3
"""
Test script to verify all modules work correctly.
Run this on the Raspberry Pi before deployment.
"""

import sys
import os
import importlib

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PI_DIR = os.path.join(PROJECT_ROOT, "legacy_pi")
sys.path.insert(0, PI_DIR)


def test_imports():
    print("Testing imports...")
    required = [
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("yaml", "PyYAML"),
        ("serial", "pyserial"),
        ("pynmea2", "pynmea2"),
        ("requests", "requests"),
        ("paho.mqtt.client", "paho-mqtt"),
        ("flask", "Flask"),
        ("flask_socketio", "Flask-SocketIO"),
    ]
    optional = [
        ("RPi.GPIO", "RPi.GPIO (optional for non-Pi environments)"),
    ]

    all_required_present = True

    for module_name, label in required:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", None)
            if version:
                print(f"  ✓ {label}: {version}")
            else:
                print(f"  ✓ {label}")
        except ImportError as e:
            all_required_present = False
            print(f"  ✗ {label}: {e}")

    for module_name, label in optional:
        try:
            importlib.import_module(module_name)
            print(f"  ✓ {label}")
        except ImportError:
            print(f"  ! {label}: not installed")

    return all_required_present


def test_opencv_assets():
    print("\nTesting OpenCV Haar cascades...")
    try:
        import cv2
    except ImportError as e:
        print(f"  ✗ OpenCV import failed: {e}")
        return False

    cascade_dir = cv2.data.haarcascades
    required = [
        os.path.join(cascade_dir, "haarcascade_frontalface_default.xml"),
        os.path.join(cascade_dir, "haarcascade_eye.xml"),
    ]
    missing = [path for path in required if not os.path.exists(path)]
    if missing:
        print("  ✗ Missing cascade files:")
        for path in missing:
            print(f"    - {path}")
        return False

    print("  ✓ Haar cascade files found")
    return True


def test_config():
    print("\nTesting config.yaml...")
    import yaml

    config_path = os.path.join(os.path.dirname(__file__), "legacy_pi", "config.yaml")
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
        import hardware

        config_path = os.path.join(PI_DIR, "config.yaml")
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
        import gps

        config_path = os.path.join(PI_DIR, "config.yaml")
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
        import publisher

        config_path = os.path.join(PI_DIR, "config.yaml")
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
    results.append(("OpenCV Assets", test_opencv_assets()))
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
