#!/usr/bin/env python3
"""
Demo script for the Agentic Document Extraction Platform
Processes the sample LoanDisclosure.pdf file
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from services.document_processor import processor
from agents.simple_workflow import workflow
from services.storage import storage


async def run_demo():
    """Run demo with LoanDisclosure.pdf"""
    print("🚀 Agentic Document Extraction Platform Demo")
    print("=" * 50)
    
    # Check if sample file exists
    sample_file = "LoanDisclosure.pdf"
    if not os.path.exists(sample_file):
        print(f"❌ Sample file '{sample_file}' not found")
        print("Please ensure the LoanDisclosure.pdf file is in the project root")
        return
    
    print(f"📄 Processing: {sample_file}")
    print(f"📊 File size: {os.path.getsize(sample_file):,} bytes")
    
    try:
        # Start processing
        print("\n🔄 Starting multi-agent processing workflow...")
        start_time = time.time()
        
        transaction_id = await workflow.process_document(sample_file, sample_file)
        
        # Monitor processing
        print(f"📋 Transaction ID: {transaction_id}")
        
        # Wait for completion
        max_wait = 120  # 2 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            result = await storage.get_result(transaction_id)
            if result:
                print(f"⏱️  Status: {result.status.value} ({wait_time}s)")
                
                if result.status.value == "completed":
                    break
                elif result.status.value == "failed":
                    print(f"❌ Processing failed: {result.error_message}")
                    return
            
            await asyncio.sleep(2)
            wait_time += 2
        
        # Get final results
        result = await storage.get_result(transaction_id)
        if not result:
            print("❌ Failed to get processing results")
            return
        
        processing_time = time.time() - start_time
        
        # Display results
        print("\n" + "=" * 50)
        print("✅ Processing Complete!")
        print("=" * 50)
        
        print(f"⏱️  Total time: {processing_time:.2f} seconds")
        print(f"📄 Document: {result.metadata.filename}")
        print(f"📊 Pages: {result.metadata.page_count}")
        print(f"🔤 Elements extracted: {len(result.extracted_elements)}")
        
        # Summary by type
        element_types = {}
        for element in result.extracted_elements:
            element_types[element.type] = element_types.get(element.type, 0) + 1
        
        print("\n📋 Elements by type:")
        for elem_type, count in element_types.items():
            print(f"   {elem_type}: {count}")
        
        # Show sample extractions
        print("\n📝 Sample extractions:")
        text_elements = [e for e in result.extracted_elements if e.type == "text"][:3]
        for i, element in enumerate(text_elements, 1):
            content = str(element.content)[:100]
            if len(str(element.content)) > 100:
                content += "..."
            print(f"   {i}. {content}")
            print(f"      Page: {element.grounding.page_number}, Confidence: {element.confidence:.2f}")
        
        # Show tables if any
        table_elements = [e for e in result.extracted_elements if e.type == "table"]
        if table_elements:
            print(f"\n📊 Found {len(table_elements)} table(s):")
            for i, table in enumerate(table_elements, 1):
                if isinstance(table.content, dict) and 'rows' in table.content:
                    rows = table.content['rows']
                    print(f"   Table {i}: {len(rows)} rows")
                    if rows:
                        print(f"      Headers: {rows[0] if rows else 'N/A'}")
        
        # Export results
        output_file = f"demo_results_{transaction_id[:8]}.json"
        with open(output_file, 'w') as f:
            json.dump(result.dict(), f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Processing log
        if result.processing_log:
            print("\n📋 Processing log:")
            for log_entry in result.processing_log[-5:]:  # Last 5 entries
                print(f"   {log_entry}")
        
        print("\n🎉 Demo completed successfully!")
        print("\n🌐 To view in the web interface:")
        print("1. Start the backend: cd backend && uvicorn main:app --reload")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Open: http://localhost:5173")
        print(f"4. Upload the same file or use transaction ID: {transaction_id}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    if sys.platform == "win32":
        # Windows specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
