from .utils import merge_dicts

singular_forms = {
    'pools': 'pool',
    'collectors': 'collector',
    'buffer_pools': 'buffer_pool',
    'shards': 'index',
}
excluded_keys = [
    'timestamp',
    'commit',
    'fielddata',
    'seq_no',
    'shard_path',
    'attributes',
]
bucket_dict_keys = [
    'pools',
    'collectors',
    'buffer_pools',
    'thread_pool',
    'shards',
    'shard_id',
]
# Specifies keys that will be ignored, 
# when building the metric name
excluded_metric_keys = [
    'shard_id',
]
bucket_list_keys = {
    'data': 'path',
    'devices': 'device_name'
}


def parse_block(block, metric=[], labels={}):
    result = []

    for key, value in block.items():
        if key not in excluded_keys:
            if isinstance(value, bool):
                result.append((metric + [key], labels, int(value)))
            elif isinstance(value, (int, float)):
                result.append((metric + [key], labels, value))
            elif isinstance(value, dict):
                if key in bucket_dict_keys:
                    if key in singular_forms:
                        singular_key = singular_forms[key]
                    else:
                        singular_key = key
                    for n_key, n_value in value.items():
                        if isinstance(n_value, list):
                            if key == 'shards':
                                n_list = [{'shard_id': d} for d in n_value]
                                for n_value in n_list:
                                    result.extend(parse_block(n_value, metric=metric + [key], labels=merge_dicts(labels, {singular_key: [n_key]})))
                        else:
                            if key in excluded_metric_keys:
                                result.extend(parse_block(n_value, metric=metric, labels=merge_dicts(labels, {singular_key: [n_key]})))
                            else:
                                result.extend(parse_block(n_value, metric=metric + [key], labels=merge_dicts(labels, {singular_key: [n_key]})))
                else:
                    result.extend(parse_block(value, metric=metric + [key], labels=labels))
            elif isinstance(value, list) and key in bucket_list_keys:
                bucket_name_key = bucket_list_keys[key]

                for n_value in value:
                    bucket_name = n_value[bucket_name_key]
                    result.extend(parse_block(n_value, metric=metric + [key], labels=merge_dicts(labels, {bucket_name_key: [bucket_name]})))

    return result


def parse_node(node, metric=[], labels={}):
    labels = merge_dicts(labels, node_name=[node['name']])

    return parse_block(node, metric=metric, labels=labels)


def parse_response(response, metric=[]):
    result = []

    if '_nodes' not in response or not response['_nodes']['failed']:
        for key, value in response['nodes'].items():
            result.extend(parse_node(value, metric=metric, labels={'node_id': [key]}))

    return result
