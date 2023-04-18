from typing import List, Dict
import hmac
import hashlib
import re
from fastapi import Request, HTTPException
from pokedex import pokemon_pb2

condition_dict = {}
reason_dict = {}
SECRET_KEY = 'secretKey'


async def verify_hmac(request: Request, request_body):
    signature = request.headers.get('X-Grd-Signature', '')
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    expected_signature = hmac.new(key=SECRET_KEY, msg=request_body, digestmod=hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_signature.hexdigest()):
        raise HTTPException(status_code=401, detail="Invalid X-Grd-Signature header")


def handle_config_schema(config: Dict) -> bool:
    if not isinstance(config, Dict):
        return False

    if 'rules' not in config:
        return False

    rules = config['rules']
    if not isinstance(rules, List):
        return False

    for rule in rules:
        if not isinstance(rule, Dict):
            return False

        if 'url' not in rule or not isinstance(rule['url'], str):
            return False

        if 'reason' not in rule or not isinstance(rule['reason'], str):
            return False

        if 'match' not in rule or not isinstance(rule['match'], List):
            return False

        match_list_duplicate = []
        pokemon = pokemon_pb2.Pokemon()
        pokemon_all_fields = [field.name for field in pokemon.DESCRIPTOR.fields]
        allowed_operators = {'==', '!=', '<', '>'}

        for condition in rule['match']:

            is_operator_contain = any(op in condition for op in allowed_operators)
            if not isinstance(condition, str) or not is_operator_contain:
                return False

            for op in allowed_operators:
                if op in condition:
                    regex = r"\s*" + re.escape(op) + r"\s*"
                    match = re.split(regex, condition)
                    match_field_name = match[0]
                    match_field_value = match[1]
                    if has_special_chars_and_spaces(match_field_value):
                        return False
                    if match_field_name not in pokemon_all_fields or match_field_name in match_list_duplicate:
                        return False
                    else:
                        match_list_duplicate.append(match_field_name)
                        condition_dict[match_field_name] = [op, match_field_value]

    reason_dict[rule['reason']] = condition_dict
    return True


def has_special_chars_and_spaces(string):
    pattern = r"[\W\s]"
    match = re.search(pattern, string)
    if match:
        return True
    else:
        return False


def protobuf_to_dict(proto_obj):
    key_list = proto_obj.DESCRIPTOR.fields_by_name.keys()
    d = {}
    for key in key_list:
        d[key] = getattr(proto_obj, key)
    return d


def validate_pokemon_against_the_list_of_rules(request_body: bytes):
    pokemon = pokemon_pb2.Pokemon()
    pokemon.ParseFromString(request_body)
    pokemon_dict = protobuf_to_dict(pokemon)
    for reason in reason_dict:
        for condition in reason_dict.get(reason):
            condition_dicts = reason_dict.get(reason)
            if condition in pokemon_dict.keys():
                attr = str(pokemon_dict[condition])
                operator = condition_dicts[condition][0]
                value = condition_dicts[condition][1]
                if not validate_operators(attr, operator, value):
                    return None
            else:
                return None
    return {'data': pokemon_dict, 'reason': reason}


def validate_operators(attr: str, op: str, val: str) -> bool:
    if op == '==':
        result = attr == val
    elif op == '!=':
        result = attr != val
    elif op == '<':
        result = int(attr) < int(val)
    elif op == '>':
        result = int(attr) > int(val)

    return result
