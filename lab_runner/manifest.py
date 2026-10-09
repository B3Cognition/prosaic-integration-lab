def validate_resource(resource, resource_id, owner):
    labels = resource.get('Labels') or resource.get('Config', {}).get('Labels') or {}
    actual = resource.get('Id') or resource.get('ID') or resource.get('Name')
    if actual != resource_id or labels.get('io.prosaic.lab.owner') != owner:
        raise ValueError('resource ownership mismatch; refusing mutation')
