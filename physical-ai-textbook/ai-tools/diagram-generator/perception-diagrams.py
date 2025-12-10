#!/usr/bin/env python3
"""
AI-Powered Diagram Generator for Physical AI Perception Systems
This module provides tools for generating diagrams related to perception systems
"""

import os
import json
import base64
from flask import Flask, request, jsonify, send_file
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
import re
from typing import Dict, List, Tuple, Optional


class PerceptionDiagramGenerator:
    """A class to generate diagrams for Physical AI perception systems"""

    def __init__(self):
        self.diagram_types = [
            'sensor_fusion_pipeline',
            'camera_setup',
            'object_detection',
            'tracking_system',
            'perception_architecture'
        ]

    def generate_sensor_fusion_pipeline(self, sensors: List[str] = None) -> str:
        """Generate a sensor fusion pipeline diagram"""
        if sensors is None:
            sensors = ['Camera', 'LIDAR', 'IMU', 'GPS']

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        # Define positions for sensors
        y_pos = 0.7
        sensor_width = 0.8
        sensor_height = 0.15

        # Draw sensors
        for i, sensor in enumerate(sensors):
            x_pos = 0.1 + i * 0.2
            rect = patches.Rectangle(
                (x_pos, y_pos),
                sensor_width/len(sensors),
                sensor_height,
                linewidth=2,
                edgecolor='blue',
                facecolor='lightblue',
                label=sensor
            )
            ax.add_patch(rect)
            ax.text(
                x_pos + sensor_width/(2*len(sensors)),
                y_pos + sensor_height/2,
                sensor,
                ha='center',
                va='center',
                fontsize=10,
                fontweight='bold'
            )

        # Draw fusion block
        fusion_x = 0.5
        fusion_y = 0.4
        fusion_width = 0.3
        fusion_height = 0.15
        fusion_rect = patches.Rectangle(
            (fusion_x, fusion_y),
            fusion_width,
            fusion_height,
            linewidth=2,
            edgecolor='red',
            facecolor='lightcoral',
            label='Fusion'
        )
        ax.add_patch(fusion_rect)
        ax.text(
            fusion_x + fusion_width/2,
            fusion_y + fusion_height/2,
            'Fusion\nEngine',
            ha='center',
            va='center',
            fontsize=10,
            fontweight='bold'
        )

        # Draw arrows from sensors to fusion
        for i in range(len(sensors)):
            x_pos = 0.1 + i * 0.2 + sensor_width/(2*len(sensors))
            ax.annotate(
                '',
                xy=(fusion_x + fusion_width/2, fusion_y),
                xytext=(x_pos, y_pos + sensor_height),
                arrowprops=dict(arrowstyle='->', lw=2, color='black')
            )

        # Draw output arrow
        ax.annotate(
            '',
            xy=(0.65, 0.2),
            xytext=(fusion_x + fusion_width/2, fusion_y),
            arrowprops=dict(arrowstyle='->', lw=2, color='green')
        )
        ax.text(0.65, 0.15, 'Fused Output', ha='center', va='center', fontsize=10)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Sensor Fusion Pipeline', fontsize=14, fontweight='bold')

        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()

        return self._buffer_to_base64(img_buffer)

    def generate_camera_setup(self, camera_config: str = 'stereo') -> str:
        """Generate a camera setup diagram"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

        if camera_config == 'stereo':
            # Draw stereo camera setup
            # Left camera
            left_cam = patches.Rectangle((0.2, 0.4), 0.1, 0.2, linewidth=2, edgecolor='blue', facecolor='lightblue')
            ax.add_patch(left_cam)
            ax.text(0.25, 0.5, 'Left\nCamera', ha='center', va='center', fontsize=10)

            # Right camera
            right_cam = patches.Rectangle((0.7, 0.4), 0.1, 0.2, linewidth=2, edgecolor='blue', facecolor='lightblue')
            ax.add_patch(right_cam)
            ax.text(0.75, 0.5, 'Right\nCamera', ha='center', va='center', fontsize=10)

            # Scene
            scene = patches.Rectangle((0.4, 0.2), 0.2, 0.4, linewidth=2, edgecolor='green', facecolor='lightgreen')
            ax.add_patch(scene)
            ax.text(0.5, 0.4, 'Scene', ha='center', va='center', fontsize=10)

            # Draw rays
            ax.plot([0.2, 0.4], [0.5, 0.4], 'k--', alpha=0.5)
            ax.plot([0.2, 0.4], [0.5, 0.3], 'k--', alpha=0.5)
            ax.plot([0.8, 0.6], [0.5, 0.4], 'k--', alpha=0.5)
            ax.plot([0.8, 0.6], [0.5, 0.3], 'k--', alpha=0.5)

            ax.set_title('Stereo Camera Setup', fontsize=14, fontweight='bold')

        elif camera_config == 'rgb_depth':
            # Draw RGB-D camera setup
            cam = patches.Rectangle((0.4, 0.4), 0.2, 0.2, linewidth=2, edgecolor='blue', facecolor='lightblue')
            ax.add_patch(cam)
            ax.text(0.5, 0.5, 'RGB-D\nCamera', ha='center', va='center', fontsize=10)

            # Scene
            scene = patches.Rectangle((0.4, 0.2), 0.2, 0.15, linewidth=2, edgecolor='green', facecolor='lightgreen')
            ax.add_patch(scene)
            ax.text(0.5, 0.275, 'Scene', ha='center', va='center', fontsize=10)

            # Draw depth rays
            for i in range(5):
                x_offset = 0.1 * i - 0.2
                ax.plot([0.5, 0.5 + x_offset], [0.5, 0.3], 'k--', alpha=0.5)

            ax.set_title('RGB-D Camera Setup', fontsize=14, fontweight='bold')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()

        return self._buffer_to_base64(img_buffer)

    def generate_object_detection(self, classes: List[str] = None) -> str:
        """Generate an object detection diagram"""
        if classes is None:
            classes = ['Person', 'Car', 'Bicycle', 'Traffic Light']

        fig, ax = plt.subplots(1, 1, figsize=(10, 8))

        # Draw scene
        scene = patches.Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=2, edgecolor='black', facecolor='lightgray')
        ax.add_patch(scene)

        # Draw some objects with bounding boxes
        objects = [
            {'class': 'Person', 'bbox': (0.2, 0.6, 0.1, 0.2)},
            {'class': 'Car', 'bbox': (0.5, 0.3, 0.2, 0.1)},
            {'class': 'Bicycle', 'bbox': (0.3, 0.4, 0.1, 0.1)},
            {'class': 'Traffic Light', 'bbox': (0.7, 0.7, 0.05, 0.15)}
        ]

        colors = {'Person': 'blue', 'Car': 'red', 'Bicycle': 'green', 'Traffic Light': 'orange'}

        for obj in objects:
            x, y, w, h = obj['bbox']
            # Draw bounding box
            bbox = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor=colors[obj['class']], facecolor='none')
            ax.add_patch(bbox)
            # Add label
            ax.text(x, y + h + 0.02, obj['class'], fontsize=8, color=colors[obj['class']], fontweight='bold')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Object Detection Example', fontsize=14, fontweight='bold')

        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()

        return self._buffer_to_base64(img_buffer)

    def generate_tracking_system(self) -> str:
        """Generate a tracking system diagram"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        # Draw timeline
        ax.axhline(y=0.5, color='gray', linestyle='-', linewidth=2)
        ax.text(0.05, 0.55, 'Time →', fontsize=12, fontweight='bold')

        # Draw frames
        frames = [0.1, 0.3, 0.5, 0.7, 0.9]
        for i, frame_x in enumerate(frames):
            ax.text(frame_x, 0.6, f'Frame {i+1}', ha='center', va='bottom', fontsize=10)

        # Draw object positions across frames (simulated tracking)
        obj1_positions = [(0.1, 0.4), (0.3, 0.42), (0.5, 0.45), (0.7, 0.47), (0.9, 0.5)]
        obj2_positions = [(0.1, 0.3), (0.3, 0.28), (0.5, 0.25), (0.7, 0.23), (0.9, 0.2)]

        # Draw object 1
        for i, (x, y) in enumerate(obj1_positions):
            circle = patches.Circle((x, y), 0.02, color='red', zorder=5)
            ax.add_patch(circle)
            if i < len(obj1_positions) - 1:
                next_x, next_y = obj1_positions[i+1]
                ax.arrow(x, y, next_x-x, next_y-y, head_width=0.01, head_length=0.01, fc='red', ec='red')

        # Draw object 2
        for i, (x, y) in enumerate(obj2_positions):
            circle = patches.Circle((x, y), 0.02, color='blue', zorder=5)
            ax.add_patch(circle)
            if i < len(obj2_positions) - 1:
                next_x, next_y = obj2_positions[i+1]
                ax.arrow(x, y, next_x-x, next_y-y, head_width=0.01, head_length=0.01, fc='blue', ec='blue')

        # Add legend
        ax.plot([], [], 'ro', label='Object 1', markersize=8)
        ax.plot([], [], 'bo', label='Object 2', markersize=8)
        ax.legend(loc='upper right')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Object Tracking Over Time', fontsize=14, fontweight='bold')

        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()

        return self._buffer_to_base64(img_buffer)

    def generate_perception_architecture(self) -> str:
        """Generate a perception system architecture diagram"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))

        # Define layers
        layers = [
            {'name': 'Raw Sensors', 'y': 0.85, 'items': ['Cameras', 'LIDAR', 'IMU', 'GPS']},
            {'name': 'Preprocessing', 'y': 0.7, 'items': ['Image Enhancement', 'Noise Reduction', 'Calibration']},
            {'name': 'Feature Extraction', 'y': 0.55, 'items': ['Edges', 'Corners', 'Descriptors']},
            {'name': 'Object Detection', 'y': 0.4, 'items': ['CNN', 'YOLO', 'R-CNN']},
            {'name': 'Tracking', 'y': 0.25, 'items': ['Kalman Filter', 'Data Association']},
            {'name': 'Scene Understanding', 'y': 0.1, 'items': ['Semantic Segmentation', '3D Reconstruction']}
        ]

        for layer in layers:
            # Draw layer box
            ax.text(0.5, layer['y'], layer['name'], ha='center', va='center',
                   fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', edgecolor='blue'))

            # Draw items
            for i, item in enumerate(layer['items']):
                x_pos = 0.3 + i * 0.15
                ax.text(x_pos, layer['y'] - 0.05, item, ha='center', va='center',
                       fontsize=9, style='italic',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='gray'))

        # Draw arrows between layers
        for i in range(len(layers) - 1):
            ax.annotate('',
                       xy=(0.5, layers[i+1]['y'] + 0.05),
                       xytext=(0.5, layers[i]['y'] - 0.05),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Perception System Architecture', fontsize=16, fontweight='bold')

        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()

        return self._buffer_to_base64(img_buffer)

    def _buffer_to_base64(self, buffer: BytesIO) -> str:
        """Convert image buffer to base64 string"""
        buffer.seek(0)
        img_bytes = buffer.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return img_base64


# Initialize Flask app
app = Flask(__name__)
diagram_generator = PerceptionDiagramGenerator()


@app.route('/generate-diagram', methods=['POST'])
def generate_diagram():
    """
    API endpoint to generate perception system diagrams
    Expected JSON format: {"type": "diagram_type", "params": {...}}
    """
    try:
        data = request.get_json()

        if not data or 'type' not in data:
            return jsonify({
                'error': 'Missing diagram type in request body',
                'message': 'Please provide diagram type to generate'
            }), 400

        diagram_type = data['type']
        params = data.get('params', {})

        # Generate the appropriate diagram
        if diagram_type == 'sensor_fusion_pipeline':
            sensors = params.get('sensors', None)
            diagram_base64 = diagram_generator.generate_sensor_fusion_pipeline(sensors)
        elif diagram_type == 'camera_setup':
            config = params.get('config', 'stereo')
            diagram_base64 = diagram_generator.generate_camera_setup(config)
        elif diagram_type == 'object_detection':
            classes = params.get('classes', None)
            diagram_base64 = diagram_generator.generate_object_detection(classes)
        elif diagram_type == 'tracking_system':
            diagram_base64 = diagram_generator.generate_tracking_system()
        elif diagram_type == 'perception_architecture':
            diagram_base64 = diagram_generator.generate_perception_architecture()
        else:
            return jsonify({
                'error': 'Unsupported diagram type',
                'message': f'Diagram type must be one of: {diagram_generator.diagram_types}'
            }), 400

        return jsonify({
            'diagram_type': diagram_type,
            'image_base64': diagram_base64,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({
            'error': 'An error occurred while generating diagram',
            'message': str(e)
        }), 500


@app.route('/list-diagram-types', methods=['GET'])
def list_diagram_types():
    """List available diagram types"""
    return jsonify({
        'diagram_types': diagram_generator.diagram_types,
        'description': 'Available perception system diagram types'
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Physical AI Perception Diagram Generator',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("Starting Physical AI Perception Diagram Generator...")
    print("API endpoints:")
    print("  POST /generate-diagram - Generate perception system diagrams")
    print("  GET  /list-diagram-types - List available diagram types")
    print("  GET  /health - Health check")
    app.run(host='0.0.0.0', port=5002, debug=True)