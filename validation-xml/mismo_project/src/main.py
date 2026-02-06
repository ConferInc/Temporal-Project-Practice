
import json
import traceback
from lxml import etree
import os

from validator import validate_inputs
from generator import generate_mismo_xml

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def validate_xsd(xml_string, xsd_path):
    try:
        xmlschema_doc = etree.parse(xsd_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        
        # Parse the XML string
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))
        
        is_valid = xmlschema.validate(xml_doc)
        
        if is_valid:
            return "PASSED", []
        else:
            # Collect errors
            error_log = [str(error) for error in xmlschema.error_log]
            return "FAILED", error_log
            
    except Exception as e:
        return "FAILED", [str(e)]

def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    canonical_path = os.path.join(base_dir, 'data', 'canonical_data.json')
    context_path = os.path.join(base_dir, 'data', 'document_understanding.json')
    xsd_path = os.path.join(base_dir, 'schemas', 'MISMO_3.6.1_B371 (1).xsd')
    output_path = os.path.join(base_dir, '..', 'output', 'result.json') # Save to parent output
    
    # Ensure output dir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = {
        "processing_status": "FAILURE",
        "validation_details": {
            "is_identity_verified": False,
            "is_us_mortgage_compliant": False,
            "errors_found": []
        },
        "mismo_xml_output": None,
        "xsd_validation_status": "NOT_ATTEMPTED"
    }

    try:
        # 1. Load Data
        print(f"Loading data from {canonical_path}...")
        canonical = load_json(canonical_path)
        context = load_json(context_path)
        
        # 2. Logical Validation
        print("Performing Logical Validation...")
        is_valid, errors = validate_inputs(canonical, context)
        
        result['validation_details']['is_identity_verified'] = True # Assuming success means verified, else false
        result['validation_details']['is_us_mortgage_compliant'] = True
        result['validation_details']['errors_found'] = errors
        
        if not is_valid:
            print("Logical Validation FAILED.")
            result['validation_details']['is_identity_verified'] = False # Correction
            return
            
        print("Logical Validation PASSED.")
        
        # 3. Generate XML
        print("Generating MISMO XML...")
        xml_output = generate_mismo_xml(canonical)
        result['mismo_xml_output'] = xml_output
        result['processing_status'] = "SUCCESS"
        
        # 4. XSD Validation
        print(f"Validating against XSD {xsd_path}...")
        xsd_status, xsd_errors = validate_xsd(xml_output, xsd_path)
        result['xsd_validation_status'] = xsd_status
        if xsd_status == "FAILED":
             result['validation_details']['errors_found'].extend(xsd_errors)
             print("XSD Validation FAILED.")
        else:
             print("XSD Validation PASSED.")

    except Exception as e:
        print(f"System Error: {e}")
        traceback.print_exc()
        result['validation_details']['errors_found'].append(f"System Exception: {str(e)}")
        
    finally:
        # Write Output
        print(json.dumps(result, indent=2))
        with open("final_output.json", "w") as f:
            json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
