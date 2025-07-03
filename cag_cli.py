#!/usr/bin/env python3
import os
import sys
from cag_system import CAGSystem
from dotenv import load_dotenv

load_dotenv()


def print_banner():
    """Print a nice banner for the CAG system"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║       CAG - Context Augmentation Generation System        ║
    ║                   Powered by CrewAI                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        sys.exit(1)
    
    print_banner()
    print("\n🚀 Initializing CAG System...")
    
    try:
        cag = CAGSystem()
        print("✅ CAG System initialized successfully!")
        print("\n📚 Knowledge base loaded from BellaTerra folder")
        print("\nType 'help' for available commands or 'quit' to exit\n")
        
        while True:
            query = input("\n🤖 Ask me anything about Bella Terra > ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            elif query.lower() == 'help':
                print("\n📖 Available commands:")
                print("  - Type any question about Bella Terra's menu, wines, etc.")
                print("  - 'help' - Show this help message")
                print("  - 'quit' or 'exit' - Exit the system")
                continue
            
            elif not query:
                continue
            
            try:
                result = cag.process_query(query)
                print("\n" + "="*60)
                print("🎯 AUGMENTED RESPONSE:")
                print("="*60)
                print(result['augmented_response'])
                print("="*60)
                
            except Exception as e:
                print(f"\n❌ Error processing query: {str(e)}")
                print("Please try again with a different question.")
    
    except Exception as e:
        print(f"\n❌ Error initializing CAG System: {str(e)}")
        print("Please check your setup and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()