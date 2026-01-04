#!/usr/bin/env python3
"""
Quick test script for FIRMS API to verify it returns live wildfire data
"""
import sys
from firms import fetch_recent_fires_global

def test_firms_api():
    """Test the FIRMS API and display results"""
    print("=" * 60)
    print("Testing NASA FIRMS API - Live Wildfire Data")
    print("=" * 60)
    print("\nFetching recent fires from USA/Canada (last 7 days)...\n")
    
    try:
        fires = fetch_recent_fires_global(days_back=7, max_results=100)
        
        if not fires:
            print("❌ No fires returned from API")
            print("   This could mean:")
            print("   - No active fires in the region (unlikely)")
            print("   - API connection issue")
            print("   - API key issue")
            return False
        
        print(f"✅ Successfully fetched {len(fires)} fires!\n")
        print("Sample fires:")
        print("-" * 60)
        
        for i, fire in enumerate(fires[:10], 1):
            print(f"{i}. Fire at ({fire['lat']:.4f}, {fire['lon']:.4f})")
            print(f"   Confidence: {fire['confidence_level']}")
            print(f"   Power: {fire['frp']:.0f} MW")
            print(f"   Date: {fire['acq_date']} {fire['acq_time']}")
            print(f"   Satellite: {fire['satellite']}")
            print()
        
        if len(fires) > 10:
            print(f"... and {len(fires) - 10} more fires\n")
        
        print("=" * 60)
        print("✅ API Test PASSED - Map should display live wildfires!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify FIRMS_API_KEY in firms.py")
        print("3. Check NASA FIRMS API status: https://firms.modaps.eosdis.nasa.gov/")
        return False

if __name__ == "__main__":
    success = test_firms_api()
    sys.exit(0 if success else 1)

