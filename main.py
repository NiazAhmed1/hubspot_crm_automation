import json
import sys
from pathlib import Path
from agents.orchestrator import DynamicGlobalOrchestrator


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = {
            "openai": ["api_key", "model"],
            "hubspot": ["api_key", "base_url"],
            "email": ["smtp_server", "smtp_port", "sender_email", "sender_password"]
        }
        
        for section, fields in required_fields.items():
            if section not in config:
                raise ValueError(f"Missing '{section}' section in config")
            for field in fields:
                if field not in config[section]:
                    raise ValueError(f"Missing '{field}' in '{section}' section")
        
        return config
        
    except FileNotFoundError:
        print(f"❌ Error: Configuration file '{config_path}' not found.")
        print("Please create config.json with your API credentials.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)



#main entry point of project
def main():
    """Main application loop"""
    print("=" * 70)
    print("🤖 Multi-Agent CRM System - DYNAMIC VERSION")
    print("=" * 70)
    print()
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    print("✅ Configuration loaded successfully\n")
    
    # Initialize orchestrator
    print("🔧 Initializing dynamic agents...")
    orchestrator = DynamicGlobalOrchestrator(config)
    print("✅ Agents initialized successfully\n")
    
    print("=" * 70)
    print("System Ready! Enter your queries below.")
    print("Type 'exit' or 'quit' to stop, 'examples' for query ideas.")
    print("=" * 70)
    print()
    


    # Main loop
    while True:
        try:
    
            # Get user input
            user_query = input("🎯 Your query: ").strip()
            
    
            # Check for exit commands
            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! Thanks for using the Multi-Agent CRM System.")
                break
    
            
            # Skip empty queries
            if not user_query:
                continue
            
            print("\n🔄 Processing your request...\n")
            
            # Process query
            result = orchestrator.process_query(user_query)
            
            # Display results
            print("-" * 70)
            print("📊 RESULTS:")
            print("-" * 70)
            print(f"Operation: {result['operation']}")
            print(f"Object Type: {result.get('object_type', 'N/A')}")
            if result.get('properties'):
                print(f"Properties: {json.dumps(result['properties'], indent=2)}")
            print()
            print(result['response'])
            print("-" * 70)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            continue





def run_single_query(query: str, config_path: str = "config.json"):
    """Run a single query without interactive mode"""
    config = load_config(config_path)
    orchestrator = DynamicGlobalOrchestrator(config)
    result = orchestrator.process_query(query)
    
    print("\n" + "=" * 70)
    print("📊 RESULT:")
    print("=" * 70)
    print(result['response'])
    print("=" * 70 + "\n")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_single_query(query)
    else:
        main()