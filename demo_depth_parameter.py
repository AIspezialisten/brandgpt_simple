#!/usr/bin/env python3
"""
Simple demonstration of the URL depth parameter feature.
This script shows how different depth values affect scraping behavior.
"""

import asyncio
from brandgpt.ingestion.url_processor import URLProcessor


async def demo_depth_parameter():
    """Demonstrate URL scraping with different depth parameters"""
    
    print("🌐 URL Depth Parameter Demonstration")
    print("=" * 50)
    
    # Initialize the URL processor
    processor = URLProcessor()
    
    # Test URL - a simple Wikipedia page
    test_url = "https://en.wikipedia.org/wiki/Web_scraping"
    
    # Test different depth levels
    depth_tests = [
        {"depth": 1, "description": "Only the main page"},
        {"depth": 2, "description": "Main page + linked pages"},
    ]
    
    for test in depth_tests:
        print(f"\n🔍 Testing depth={test['depth']}: {test['description']}")
        print("-" * 40)
        
        # Create metadata with the depth parameter
        metadata = {
            "max_depth": test["depth"],
            "max_links_per_page": 5,  # Limit for demo purposes
            "test_run": True
        }
        
        try:
            # Process the URL with the specified depth
            documents = await processor.process(test_url, metadata)
            
            # Analyze results
            unique_urls = set()
            depth_counts = {}
            
            for doc in documents:
                url = doc.metadata.get('url', '')
                depth = doc.metadata.get('depth', 0)
                
                unique_urls.add(url)
                depth_counts[depth] = depth_counts.get(depth, 0) + 1
            
            print(f"📊 Results for depth={test['depth']}:")
            print(f"   📄 Total chunks: {len(documents)}")
            print(f"   🔗 Unique URLs: {len(unique_urls)}")
            print(f"   📈 Chunks by depth: {depth_counts}")
            
            # Show sample URLs
            print(f"   🌐 Sample URLs:")
            for i, url in enumerate(list(unique_urls)[:3]):
                if url:
                    print(f"      {i+1}. {url}")
            
            if len(unique_urls) > 3:
                print(f"      ... and {len(unique_urls) - 3} more")
                
        except Exception as e:
            print(f"❌ Error testing depth {test['depth']}: {str(e)}")
    
    print("\n✅ Depth parameter demonstration complete!")
    print("\n📚 Key Takeaways:")
    print("   • depth=1: Scrapes only the provided URL")
    print("   • depth=2: Scrapes the URL plus pages it links to")
    print("   • Higher depths exponentially increase content volume")
    print("   • Use max_links_per_page to control crawling scope")


if __name__ == "__main__":
    # Note: This demo requires network access and may not work in all environments
    print("🚀 Starting URL Depth Parameter Demo")
    print("⚠️  Note: This demo requires network access to Wikipedia")
    
    try:
        asyncio.run(demo_depth_parameter())
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("💡 This is normal if you don't have network access or required dependencies")