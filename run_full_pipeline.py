# run_full_pipeline.py
"""
Full End-to-End Compliance Pipeline Orchestrator

This script orchestrates the complete workflow from camera capture to compliance validation:
1. LiveProcessor: Captures images and produces preliminary messy JSON
2. DataRefiner: Cleans the messy JSON and formats it perfectly
3. ComplianceValidator: Validates the clean JSON against Legal Metrology rules

Usage:
    python run_full_pipeline.py
"""

import sys
import os
import json
import cv2
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the three main pipeline components
from live_processor import LiveProcessor
from data_refiner.refiner import DataRefiner
from lmpc_checker.compliance_validator import ComplianceValidator

# Camera selection imports
try:
    from pygrabber.dshow_graph import FilterGraph
    PYGRABBER_AVAILABLE = True
except ImportError:
    PYGRABBER_AVAILABLE = False
    print("Note: pygrabber not available. Camera selection will be limited.")

class FullPipelineOrchestrator:
    """
    Main orchestrator class that manages the complete compliance pipeline workflow
    """
    
    def __init__(self):
        """Initialize all pipeline components"""
        print("🔧 Initializing Full Compliance Pipeline...")
        print("=" * 60)
        
        # First, let user select camera
        self.selected_camera_index = self._select_camera()
        
        try:
            # Initialize LiveProcessor
            print("📷 Loading OCR and Camera systems...")
            self.processor = LiveProcessor()
            # Set the selected camera index
            self.processor.camera_index = self.selected_camera_index
            print("✅ LiveProcessor initialized")
            
            # Initialize DataRefiner
            print("🛠️  Loading Data Refinement module...")
            self.refiner = DataRefiner()
            print("✅ DataRefiner initialized")
            
            # Initialize ComplianceValidator
            print("📋 Loading Compliance Validation rules...")
            self.validator = ComplianceValidator()
            print("✅ ComplianceValidator initialized")
            
            print("\n🎉 All systems ready!")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise
    
    def _list_cameras_with_names(self) -> List[tuple]:
        """List camera devices with names"""
        cameras = []
        
        if PYGRABBER_AVAILABLE:
            try:
                devices = FilterGraph().get_input_devices()
                for i, device_name in enumerate(devices):
                    cameras.append((i, device_name))
                return cameras
            except Exception as e:
                print(f"⚠️  pygrabber failed: {e}")
        
        # Fallback: Test cameras by trying to open them
        print("🔍 Scanning for available cameras...")
        for i in range(10):  # Test first 10 camera indices
            import cv2
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append((i, f"Camera {i}"))
                cap.release()
            else:
                break
        
        return cameras
    
    def _select_camera(self) -> int:
        """Let user select camera with device names"""
        print("\n📹 CAMERA SELECTION")
        print("-" * 25)
        
        available_cameras = self._list_cameras_with_names()
        
        if not available_cameras:
            print("❌ No cameras detected!")
            print("   Please ensure a camera is connected and try again.")
            raise RuntimeError("No cameras available")
        
        if len(available_cameras) == 1:
            camera_index, camera_name = available_cameras[0]
            print(f"📷 Using only available camera: {camera_name} (Index {camera_index})")
            return camera_index
        
        print("📋 Available cameras:")
        for i, (camera_index, camera_name) in enumerate(available_cameras):
            print(f"   [{i+1}] {camera_name} (Index {camera_index})")
        
        while True:
            try:
                choice = input(f"\n👉 Select camera [1-{len(available_cameras)}]: ").strip()
                
                if choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(available_cameras):
                        selected_camera_index, selected_camera_name = available_cameras[choice_idx]
                        print(f"✅ Selected: {selected_camera_name} (Index {selected_camera_index})")
                        return selected_camera_index
                
                print(f"❌ Invalid choice. Please enter a number between 1 and {len(available_cameras)}")
                
            except KeyboardInterrupt:
                print("\n❌ Camera selection cancelled")
                raise RuntimeError("Camera selection cancelled by user")
    
    
    def display_welcome(self):
        """Display welcome message and instructions"""
        print("\n" + "=" * 60)
        print("🏛️  LEGAL METROLOGY COMPLIANCE PIPELINE")
        print("=" * 60)
        print("📱 This tool will:")
        print("   1. Select your preferred camera device")
        print("   2. Capture product label from camera")
        print("   3. Extract and clean product information") 
        print("   4. Validate against Legal Metrology rules")
        print("   5. Generate comprehensive compliance report")
        print("\n📋 Instructions:")
        print("   • Position product label clearly in camera view")
        print("   • Ensure good lighting and focus")
        print("   • Press SPACE when ready to capture")
        print("   • Follow on-screen prompts")
        print("=" * 60)
    
    def run_single_scan(self) -> bool:
        """
        Execute a single complete pipeline scan
        
        Returns:
            bool: True if scan completed successfully, False if cancelled
        """
        print("\n🚀 Starting New Compliance Scan")
        print("-" * 40)
        
        # Stage 1: Capture and Initial Extraction
        print("\n📷 STAGE 1: Camera Capture & Initial OCR")
        print("-" * 40)
        print("🎯 Launching camera interface...")
        
        messy_data = self.processor.process_single_capture(self.selected_camera_index)
        
        if not messy_data:
            print("❌ Scan cancelled or failed. Returning to main menu.")
            return False
        
        print("\n📄 Raw OCR Output Retrieved:")
        self._display_stage_data("STAGE 1: Initial OCR Output", messy_data)
        
        # Stage 2: Data Refinement
        print("\n🛠️  STAGE 2: Data Refinement & Formatting")
        print("-" * 40)
        print("🔄 Processing messy data through refinement engine...")
        
        try:
            clean_data = self.refiner.refine(messy_data)
            print("✅ Data refinement completed!")
            
            self._display_stage_data("STAGE 2: Refined & Structured JSON", clean_data)
            
        except Exception as e:
            print(f"❌ Data refinement failed: {e}")
            return False
        
        # Stage 3: Compliance Validation
        print("\n📋 STAGE 3: Legal Metrology Compliance Validation")
        print("-" * 40)
        print("⚖️  Validating against Legal Metrology (Packaged Commodities) Rules, 2011...")
        
        try:
            violations = self.validator.validate(clean_data)
            print("✅ Compliance validation completed!")
            
            # Stage 4: Final Report
            self._display_compliance_report(clean_data, violations)
            
        except Exception as e:
            print(f"❌ Compliance validation failed: {e}")
            return False
        
        return True
    
    def _display_stage_data(self, stage_title: str, data: Dict[str, Any]):
        """Display formatted stage data"""
        print(f"\n--- {stage_title} ---")
        
        # Count populated fields
        populated_fields = sum(1 for v in data.values() if v is not None and v != "")
        total_fields = len(data)
        
        print(f"📊 Fields Populated: {populated_fields}/{total_fields}")
        
        # Display key extracted data
        key_fields = ['mrp', 'net_quantity', 'manufacturer_details', 'date_of_manufacture', 
                     'country_of_origin', 'consumer_care', 'category']
        
        print("🔍 Key Extracted Data:")
        for field in key_fields:
            value = data.get(field)
            if value and value != "":
                status = "✅"
                display_value = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
            else:
                status = "❌"
                display_value = "Not found"
            print(f"   {status} {field}: {display_value}")
        
        # Show complete JSON in compact format
        print(f"\n📋 Complete JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _display_compliance_report(self, product_data: Dict[str, Any], violations: List[Dict[str, str]]):
        """Display comprehensive compliance report"""
        print("\n" + "=" * 60)
        print("📊 FINAL COMPLIANCE REPORT")
        print("=" * 60)
        
        # Basic product info
        product_id = product_data.get('product_id', 'Unknown')
        category = product_data.get('category', 'Unknown')
        mrp = product_data.get('mrp', 'Not specified')
        
        print(f"🏷️  Product ID: {product_id}")
        print(f"📦 Category: {category}")
        print(f"💰 MRP: {mrp}")
        print(f"📅 Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "-" * 60)
        
        if not violations:
            print("🎉 COMPLIANCE STATUS: ✅ FULLY COMPLIANT ✅")
            print("\n🏆 This product meets all Legal Metrology requirements!")
            print("📋 No violations detected in:")
            print("   • Mandatory field declarations")
            print("   • Format specifications")
            print("   • Consumer protection requirements")
            print("   • Import/export regulations")
        else:
            print(f"⚠️  COMPLIANCE STATUS: ❌ {len(violations)} VIOLATION(S) DETECTED")
            
            # Group violations by severity
            violations_by_severity = {}
            for violation in violations:
                severity = violation.get('severity', 'Unknown')
                if severity not in violations_by_severity:
                    violations_by_severity[severity] = []
                violations_by_severity[severity].append(violation)
            
            # Display violations by severity
            severity_order = ['Critical', 'High', 'Medium', 'Low']
            severity_icons = {
                'Critical': '🚨',
                'High': '⚠️',
                'Medium': '⚡',
                'Low': 'ℹ️'
            }
            
            for severity in severity_order:
                if severity in violations_by_severity:
                    icon = severity_icons.get(severity, '⚠️')
                    violations_list = violations_by_severity[severity]
                    
                    print(f"\n{icon} {severity.upper()} VIOLATIONS ({len(violations_list)}):")
                    print("-" * 30)
                    
                    for i, violation in enumerate(violations_list, 1):
                        rule_id = violation.get('rule_id', 'Unknown')
                        description = violation.get('description', 'No description')
                        field = violation.get('field', 'Unknown field')
                        
                        print(f"   {i}. Rule: {rule_id}")
                        print(f"      Field: {field}")
                        print(f"      Issue: {description}")
                        print()
            
            # Compliance recommendations
            print("📋 RECOMMENDED ACTIONS:")
            print("-" * 25)
            
            critical_count = len(violations_by_severity.get('Critical', []))
            high_count = len(violations_by_severity.get('High', []))
            
            if critical_count > 0:
                print(f"🚨 URGENT: Address {critical_count} critical violation(s) immediately")
                print("   → Product may not be legally compliant for sale")
            
            if high_count > 0:
                print(f"⚠️  HIGH PRIORITY: Resolve {high_count} high-priority issue(s)")
                print("   → Required for full Legal Metrology compliance")
            
            print("📞 Contact your legal/compliance team for guidance")
        
        print("\n" + "=" * 60)
    
    def run_main_loop(self):
        """Main application loop"""
        self.display_welcome()
        
        scan_count = 0
        
        while True:
            print(f"\n📋 Main Menu (Scans completed: {scan_count})")
            print("-" * 30)
            print("Options:")
            print("  [ENTER] Start new compliance scan")
            print("  [q]     Quit application")
            
            try:
                action = input("\n👉 Your choice: ").strip().lower()
                
                if action == 'q' or action == 'quit':
                    print("\n👋 Thank you for using the Legal Metrology Compliance Pipeline!")
                    print("🔒 Exiting safely...")
                    break
                elif action == '' or action == 'scan':
                    # Start new scan
                    success = self.run_single_scan()
                    if success:
                        scan_count += 1
                        print("\n✅ Scan completed successfully!")
                        input("Press ENTER to continue...")
                else:
                    print("❓ Invalid option. Please press ENTER to scan or 'q' to quit.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Application interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Please try again or press 'q' to quit.")


def main():
    """Main entry point"""
    print("🚀 Legal Metrology Compliance Pipeline")
    print("=" * 45)
    
    try:
        # Initialize the orchestrator
        orchestrator = FullPipelineOrchestrator()
        
        # Run the main application loop
        orchestrator.run_main_loop()
        
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("Please check your setup and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()