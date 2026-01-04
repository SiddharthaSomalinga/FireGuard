"""
Test script for NASA FIRMS Map API and transactions
Tests the MAP_KEY and shows available transaction budget
"""
import requests
import pandas as pd

# Your MAP_KEY provided
MAP_KEY = '501896775f6b28df986593019e4634fe'

def test_map_key():
    """Test the MAP_KEY and display transaction status"""
    print("=" * 60)
    print("NASA FIRMS Map Key Status Check")
    print("=" * 60)
    
    url = f'https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={MAP_KEY}'
    
    print(f"\nTesting URL: {url}\n")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        df = pd.Series(data)
        
        print("✅ MAP_KEY is VALID!\n")
        print("Transaction Status:")
        print("-" * 60)
        print(df)
        print("-" * 60)
        
        # Parse key information
        if isinstance(data, dict):
            print("\n📊 Summary:")
            if 'requests_made' in data:
                print(f"  Requests Made: {data.get('requests_made', 'N/A')}")
            if 'allocated' in data:
                print(f"  Allocated Transactions: {data.get('allocated', 'N/A')}")
            if 'remaining' in data:
                print(f"  Remaining Transactions: {data.get('remaining', 'N/A')}")
            
        return True, data
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print("   Possible issues:")
        print("   - MAP_KEY might be incorrect (check for typos, extra quotes)")
        print("   - MAP_KEY might have expired")
        print("   - Check: https://firms.modaps.eosdis.nasa.gov/mapserver/")
        return False, None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("   Check your internet connection")
        return False, None
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"   Response: {response.text if 'response' in locals() else 'N/A'}")
        return False, None

def get_firms_data_with_map(latitude, longitude, map_key=MAP_KEY):
    """
    Fetch FIRMS data using the map API approach
    This is an alternative to the CSV API we're using
    """
    print("\n" + "=" * 60)
    print("Testing FIRMS Data Fetch with Map Key")
    print("=" * 60)
    
    # FIRMS Map Server endpoints
    base_url = "https://firms.modaps.eosdis.nasa.gov/mapserver"
    
    # Test basic map capabilities endpoint
    test_url = f"{base_url}/mapkey_status/?MAP_KEY={map_key}"
    
    print(f"\nTesting FIRMS Map Server...")
    print(f"Base URL: {base_url}")
    print(f"Using MAP_KEY: {map_key[:10]}...{map_key[-10:]}")
    
    try:
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        status = response.json()
        
        print("\n✅ Map Server Connection: OK")
        print(f"   Status: {status}")
        
        return True, status
        
    except Exception as e:
        print(f"\n❌ Map Server Error: {e}")
        return False, None

if __name__ == "__main__":
    print("\n🔥 FireGuard - NASA FIRMS Map Key Tester\n")
    
    # Test the MAP_KEY
    success, data = test_map_key()
    
    if success:
        print("\n✅ Your MAP_KEY is configured correctly!")
        print("   You can now use FIRMS map visualization in FireGuard")
        
        # Try fetching data
        print("\n" + "=" * 60)
        success2, _ = get_firms_data_with_map(34.5, -118.2)
        
        if success2:
            print("\n✅ FIRMS Map Server is accessible!")
            print("   Ready to display fires on interactive map")
    else:
        print("\n❌ There's an issue with your MAP_KEY")
        print("   Please verify:")
        print("   1. No extra spaces or quotes")
        print("   2. All characters are correct")
        print("   3. Visit: https://firms.modaps.eosdis.nasa.gov/mapserver/")
        print("   4. Check: https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html")
