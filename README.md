# Visage Python SDK

Zero-dependency Python SDK for the Visage B2B API. Verify AI likeness licenses, log usage events, and manage deals.

## Installation
```bash
pip install visage-sdk
```

## Quick Start
```python
from visage import Visage

client = Visage(api_key="vsg_live_xxxxxxxxxxxxxxxx")

# Verify a license before generation
result = client.verify_license("VSG-A1B2-C3D4-E5F6")
print(result.status)        # "ACTIVE"
print(result.model_sku)     # "VSG-MDL-ALEX-042"
print(result.rights_summary.media_types)  # ["digital", "social"]

# Log a usage event after generation
event = client.log_usage(
    license_key="VSG-A1B2-C3D4-E5F6",
    platform_id="your-platform",
    event_type="generation",
    units=1,
    metadata={"campaign": "Summer 2026"}
)
print(event.id)  # event UUID

# List models
models = client.list_models(limit=10)
print(f"{models.total} models available")

# Get model by SKU
model = client.get_model_by_sku("VSG-MDL-ALEX-042")
print(model.display_name)

# List active licenses
licenses = client.list_licenses(status="active")

# List completed deals
deals = client.list_deals(status="completed", limit=50)
```

## Error Handling
```python
from visage import Visage, VisageAuthError, VisageLicenseNotFoundError, VisageAPIError

client = Visage(api_key="vsg_live_xxx")

try:
    result = client.verify_license("VSG-INVALID-KEY")
except VisageAuthError as e:
    print(f"Bad API key: {e}")         # 401
except VisageLicenseNotFoundError as e:
    print(f"Not found: {e}")           # 404
except VisageAPIError as e:
    print(f"API error {e.status_code}: {e}")
```

## Requirements

Python 3.10+. Zero dependencies — uses only the standard library.

## Links

- [Documentation](https://visagelabs.net/docs)
- [API Reference](https://visagelabs.net/visage-api-spec.yaml)
- [GitHub](https://github.com/VISAGE-LABS/visage-sdk-python)
