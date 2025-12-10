import requests
import sys
import json
import os
from datetime import datetime
import time

class ProcurementAPITester:
    def __init__(self, base_url="https://procure-insights-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {'PASS' if success else 'FAIL'}")
        if details:
            print(f"   Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'} if not files else {}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if success and response.content:
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        details += f" | Response keys: {list(response_data.keys())}"
                    elif isinstance(response_data, list):
                        details += f" | Response count: {len(response_data)}"
                except:
                    details += " | Non-JSON response"
            
            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_pipeline_health(self):
        """Test pipeline health endpoint"""
        return self.run_test("Pipeline Health", "GET", "pipeline-health", 200)

    def test_data_quality(self):
        """Test data quality endpoint"""
        return self.run_test("Data Quality Logs", "GET", "data-quality", 200)

    def test_tenders_empty(self):
        """Test tenders endpoint (may be empty initially)"""
        return self.run_test("Get Tenders (Empty)", "GET", "tenders", 200)

    def test_validation_trigger(self):
        """Test validation trigger"""
        return self.run_test("Trigger Validation", "POST", "validate", 200)

    def test_search_without_data(self):
        """Test search endpoint without data"""
        search_data = {"query": "cloud infrastructure", "limit": 5}
        return self.run_test("Search Without Data", "POST", "search", 200, data=search_data)

    def test_file_upload(self):
        """Test file upload with sample data"""
        try:
            # Read sample CSV file
            with open('/app/sample_data.csv', 'rb') as f:
                files = {'file': ('sample_data.csv', f, 'text/csv')}
                success, response = self.run_test("File Upload & Ingestion", "POST", "ingest", 200, files=files)
                
                if success:
                    # Wait a moment for processing
                    time.sleep(2)
                    return True, response
                return False, {}
        except FileNotFoundError:
            self.log_test("File Upload & Ingestion", False, "Sample CSV file not found")
            return False, {}
        except Exception as e:
            self.log_test("File Upload & Ingestion", False, f"Upload error: {str(e)}")
            return False, {}

    def test_tenders_with_data(self):
        """Test tenders endpoint after data upload"""
        return self.run_test("Get Tenders (With Data)", "GET", "tenders?limit=10", 200)

    def test_search_with_data(self):
        """Test search endpoint with data"""
        search_data = {"query": "cloud infrastructure upgrade", "limit": 5}
        return self.run_test("Search With Data", "POST", "search", 200, data=search_data)

    def test_pipeline_health_after_ingestion(self):
        """Test pipeline health after data ingestion"""
        return self.run_test("Pipeline Health (After Ingestion)", "GET", "pipeline-health", 200)

    def test_data_quality_after_ingestion(self):
        """Test data quality after ingestion"""
        return self.run_test("Data Quality (After Ingestion)", "GET", "data-quality", 200)

def main():
    print("🚀 Starting Procurement Intelligence Pipeline API Tests")
    print("=" * 60)
    
    tester = ProcurementAPITester()
    
    # Phase 1: Basic API Tests
    print("\n📋 Phase 1: Basic API Functionality")
    tester.test_root_endpoint()
    tester.test_pipeline_health()
    tester.test_data_quality()
    tester.test_tenders_empty()
    tester.test_validation_trigger()
    tester.test_search_without_data()
    
    # Phase 2: Data Ingestion Tests
    print("\n📤 Phase 2: Data Ingestion & Processing")
    upload_success, upload_response = tester.test_file_upload()
    
    if upload_success:
        print(f"   📊 Ingestion Results: {upload_response}")
        
        # Phase 3: Post-Ingestion Tests
        print("\n🔍 Phase 3: Post-Ingestion Functionality")
        tester.test_tenders_with_data()
        tester.test_search_with_data()
        tester.test_pipeline_health_after_ingestion()
        tester.test_data_quality_after_ingestion()
    else:
        print("   ⚠️  Skipping post-ingestion tests due to upload failure")
    
    # Results Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        
        # Print failed tests
        failed_tests = [t for t in tester.test_results if t['status'] == 'FAIL']
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())