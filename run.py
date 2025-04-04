import os
import sys
import argparse

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def parse_args():
    parser = argparse.ArgumentParser(description='Climate Control Center')
    parser.add_argument('--mock', action='store_true', 
                        help='Run in mock mode without real hardware')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.mock:
        # Use mock hardware implementation
        os.environ['USE_MOCK_HARDWARE'] = 'true'
        print("Running in MOCK mode (no physical hardware required)")
        from src.mock.app import main
    else:
        # Use real hardware implementation
        from src.app import main
    
    # Run the application
    main()