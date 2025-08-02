#!/usr/bin/env python3

"""
Test script for file upload debugging
This will help identify where the upload process might be getting stuck
"""

import os
import requests
import time
from pathlib import Path

def test_upload_endpoint():
    """Test the upload functionality via HTTP requests"""
    
    print("🧪 Testing Quality Clamps Upload System")
    print("=" * 50)
    
    # Configuration
    base_url = "http://localhost:5000"  # Adjust if your app runs on different port
    admin_login_url = f"{base_url}/admin/login"
    category_url = f"{base_url}/admin/category"
    
    # Test image file (create a small test image)
    test_image_path = "test_image.jpg"
    create_test_image(test_image_path)
    
    # Start a session
    session = requests.Session()
    
    try:
        # Step 1: Test if server is running
        print("1. Testing server connectivity...")
        try:
            response = session.get(base_url, timeout=5)
            print(f"   ✅ Server is running (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Server not accessible: {e}")
            return False
        
        # Step 2: Login to admin
        print("2. Testing admin login...")
        login_data = {
            'username': 'wishmaster',  # From your .env
            'password': 'Th1$1$$3cur3'  # From your .env
        }
        
        response = session.post(admin_login_url, data=login_data, timeout=10)
        if response.status_code == 200 and 'admin' in response.url:
            print("   ✅ Admin login successful")
        else:
            print(f"   ❌ Admin login failed (Status: {response.status_code})")
            return False
        
        # Step 3: Test file upload
        print("3. Testing file upload...")
        
        category_data = {
            'name': f'Test Category {int(time.time())}',
            'description': 'This is a test category to verify upload functionality',
            'folder': f'test_category_{int(time.time())}'
        }
        
        with open(test_image_path, 'rb') as f:
            files = {'image': ('test.jpg', f, 'image/jpeg')}
            
            print(f"   📤 Uploading category with image...")
            start_time = time.time()
            
            try:
                response = session.post(
                    category_url, 
                    data=category_data, 
                    files=files,
                    timeout=30  # 30 second timeout
                )
                
                upload_time = time.time() - start_time
                print(f"   ⏱️  Upload completed in {upload_time:.2f} seconds")
                
                if response.status_code == 200:
                    if 'successfully' in response.text.lower():
                        print("   ✅ Category upload successful!")
                        return True
                    else:
                        print(f"   ⚠️  Upload completed but may have issues")
                        print(f"   Response contains: {response.text[:200]}...")
                        return False
                else:
                    print(f"   ❌ Upload failed (Status: {response.status_code})")
                    print(f"   Response: {response.text[:200]}...")
                    return False
                    
            except requests.exceptions.Timeout:
                print("   ❌ Upload timed out (>30 seconds)")
                return False
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Upload failed with error: {e}")
                return False
        
    finally:
        # Cleanup
        try:
            os.remove(test_image_path)
        except:
            pass

def create_test_image(filename):
    """Create a small test image file"""
    try:
        from PIL import Image
        
        # Create a simple 100x100 red image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(filename, 'JPEG')
        print(f"   📷 Created test image: {filename}")
        
    except ImportError:
        # If PIL is not available, create a fake image file
        with open(filename, 'wb') as f:
            # Write a minimal JPEG header
            jpeg_header = bytes([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 
                0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
                0x00, 0x48, 0x00, 0x00, 0xFF, 0xD9
            ])
            f.write(jpeg_header)
        print(f"   📷 Created minimal test image: {filename}")

def check_upload_directory():
    """Check if upload directory exists and is writable"""
    print("4. Checking upload directory...")
    
    upload_dir = "static/images"
    
    if not os.path.exists(upload_dir):
        print(f"   ⚠️  Upload directory doesn't exist: {upload_dir}")
        try:
            os.makedirs(upload_dir, exist_ok=True)
            print(f"   ✅ Created upload directory: {upload_dir}")
        except Exception as e:
            print(f"   ❌ Failed to create upload directory: {e}")
            return False
    else:
        print(f"   ✅ Upload directory exists: {upload_dir}")
    
    # Test write permissions
    test_file = os.path.join(upload_dir, "test_write.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"   ✅ Upload directory is writable")
        return True
    except Exception as e:
        print(f"   ❌ Upload directory is not writable: {e}")
        return False

def main():
    """Main test function"""
    
    print("Starting upload system tests...\n")
    
    # Check upload directory first
    if not check_upload_directory():
        print("\n❌ Upload directory check failed")
        return False
    
    # Test the upload endpoint
    if test_upload_endpoint():
        print("\n🎉 All tests passed! Upload system is working correctly.")
        return True
    else:
        print("\n⚠️  Upload tests failed. Check the Flask app logs for more details.")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
