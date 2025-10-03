#!/usr/bin/env python3
"""
Quick test script to verify the QuitTxt Protocol Testing setup
"""
import sys
import os

def test_imports():
    """Test that all required packages are installed"""
    print("🔍 Testing imports...")
    try:
        import fastapi
        import uvicorn
        import streamlit
        import google.generativeai as genai
        from dotenv import load_dotenv
        import requests
        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_env():
    """Test that environment variables are set"""
    print("\n🔍 Testing environment configuration...")
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_API_KEY found (length: {len(api_key)})")
        return True
    else:
        print("❌ GOOGLE_API_KEY not found in .env")
        return False

def test_protocol_document():
    """Test that protocol document exists and can be loaded"""
    print("\n🔍 Testing protocol document...")
    try:
        with open('protocol_document.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Protocol document loaded ({len(content)} characters)")
        print(f"   First 100 chars: {content[:100]}...")
        return True
    except FileNotFoundError:
        print("❌ protocol_document.txt not found")
        return False

def test_protocol_manager():
    """Test the protocol manager"""
    print("\n🔍 Testing protocol manager...")
    try:
        from protocol_manager import ProtocolContextManager
        
        manager = ProtocolContextManager('protocol_document.txt')
        print(f"✅ Protocol manager initialized")
        print(f"   Total sections: {len(manager.sections)}")
        print(f"   Keywords: {list(manager.keyword_map.keys())}")
        
        # Test relevance scoring
        test_message = "I'm having a craving"
        context = manager.get_relevant_context(test_message, max_sections=2)
        print(f"\n   Test: Getting context for '{test_message}'")
        print(f"   Context length: {len(context)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Protocol manager error: {e}")
        return False

def test_gemini_api():
    """Test connection to Google Gemini API"""
    print("\n🔍 Testing Gemini API connection...")
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Test with a simple prompt
        response = model.generate_content("Say 'Hello from QuitTxt!'")
        
        print(f"✅ Gemini API connected successfully")
        print(f"   Test response: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚭 QuitTxt Protocol Testing - System Verification")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Environment Variables", test_env),
        ("Protocol Document", test_protocol_document),
        ("Protocol Manager", test_protocol_manager),
        ("Gemini API", test_gemini_api),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! System is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Start the servers: ./start.sh")
        print("   2. Open browser to: http://localhost:8501")
        print("   3. Start testing protocol-guided conversations!")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
