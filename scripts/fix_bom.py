import json

# Path to your bedrock_body.json
#json_path = "D:/Sola/DEV/Github/genai-cloud-gateway/scripts/bedrock_body.json"

def fix(json_path: str) -> str:
    # Read the file with BOM handling
    try:
        # Try reading with utf-8-sig (which handles BOM)
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Parse to validate it's proper JSON
        data = json.loads(content)
        
        # Write back without BOM
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print("✅ Fixed BOM and saved valid JSON")
        print(f"Content of {json_path}:")
        print(json.dumps(data, indent=2))
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON is invalid: {e}")
        print("Fixing just the BOM...")
        # If JSON is invalid, just remove BOM
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Removed BOM, but JSON may still need fixing")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print(fix("D:/Sola/DEV/Github/genai-cloud-gateway/scripts/bedrock_body.json"))

print(fix("D:/Sola/DEV/Github/genai-cloud-gateway/scripts/bedrock_body.json"))