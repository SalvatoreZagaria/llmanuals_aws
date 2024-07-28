def lambda_handler(event, context):
    org_name = event['request']['userAttributes'].get('custom:organization_name')
    if not (isinstance(org_name, str) and len(org_name) >= 3):
        raise Exception("Attribute organization_name is required and should be at least 3 characters")

    return event
