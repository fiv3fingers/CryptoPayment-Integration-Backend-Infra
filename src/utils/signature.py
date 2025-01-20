import hashlib
import time

from src.utils.types import AuthHeaderType

def validate_signature(authHeader:str, secret:str):
    header_parts = parse_header(authHeader)

    try:
        # Convert the timestamp to an integer
        client_timestamp = int(header_parts.timestamp)
    except ValueError:
        print("Invalid timestamp")
        return False

    # Validate if the timestamp is within an acceptable range (5 minutes)
    current_time = int(time.time())
    if abs(current_time - client_timestamp) > 300:
        print("Signature Expired")
        return False

    # Reconstruct the expected signature
    data = f"{header_parts.apikey}{secret}{client_timestamp}"
    hash_object = hashlib.sha512(data.encode())
    expected_signature = hash_object.hexdigest()

    return expected_signature == header_parts.signature

#  apikey=5409jmg8qikli06ujhl3jjvokh,signature=2ee76043a90a1d1d10f1a6776dbd39f92a0f59b939d5736008e8332ba3e6963847877978666c3427fd85304cdf3b5b7dcebc3810495352d689ebb40c67993c59,timestamp=1737106896
def parse_header(auth_header: str) -> AuthHeaderType:
    parts = auth_header.split(',')
    
    parsed_header: AuthHeaderType = {}
    
    for part in parts:
        # Split each part into key and value by the '=' sign
        key, value = part.split('=', 1)
        # Strip any whitespace and add to the dictionary
        parsed_header[key.strip()] = value.strip()
    
    return parsed_header
