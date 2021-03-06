import base64
import json
import logging

import requests

from decoder.b4e_decoder.decoding import deserialize_data
from protobuf.b4e_protobuf import payload_pb2

from config.config import SawtoothConfig
from addressing.b4e_addressing import addresser
from google.protobuf.json_format import MessageToDict
import google


LOGGER = logging.getLogger(__name__)


def enum_value_to_name(val):
    desc = payload_pb2.B4EPayload.Action.DESCRIPTOR
    for (k, v) in desc.values_by_name.items():
        if v.number == val:
            return k
    return None


def get_data_from_transaction(transaction_id):
    url = SawtoothConfig.REST_API + "/transactions/" + str(transaction_id)
    response = requests.get(url)
    if response.status_code == 200:
        try:
            transaction_dict = json.loads(response.content)
            payload_string = transaction_dict['data']['payload']
            data_model = payload_pb2.B4EPayload()
            data_model.ParseFromString(base64.b64decode(payload_string))
            return MessageToDict(data_model)

        except Exception as e:
            print("err:", e)
            LOGGER.warning(e)
            return None


def get_record_transaction(transaction_id):
    url = SawtoothConfig.REST_API + "/transactions/" + str(transaction_id)

    response = requests.get(url)
    if response.status_code == 200:
        try:
            transaction_dict = json.loads(response.content)
            payload_string = transaction_dict['data']['payload']
            data_model = payload_pb2.B4EPayload()
            data_model.ParseFromString(base64.b64decode(payload_string))
            data = dict(MessageToDict(data_model))

            if data.get('createRecord'):
                res = {
                    'ok': True,
                    'cipher': data['createRecord']['recordData'],
                    'timestamp': data['timestamp']
                }
            elif data.get('updateRecord'):
                res = {
                    'ok': True,
                    'cipher': data['updateRecord']['recordData'],
                    'timestamp': data['timestamp']
                }
            elif data.get('createCert'):
                res = {
                    'ok': True,
                    'cipher': data['createCert']['recordData'],
                    'timestamp': data['timestamp']
                }
            elif data.get('createSubject'):
                res = {
                    'ok': True,
                    'cipher': data['createSubject']['recordData'],
                    'timestamp': data['timestamp']
                }
            else:
                res = {
                    'ok': False,
                    'msg': 'Transaction record not found'
                }
            return res

        except Exception as e:
            print("err:", e)
            LOGGER.warning(e)
            return {'ok': False}
    return {'ok': False, 'msg': 'Transaction  not found'}


def get_payload_from_block(block_id, address):
    url = SawtoothConfig.REST_API + "/blocks/" + str(block_id)
    response = requests.get(url)
    if response.status_code == 200:
        try:
            block = json.loads(response.content)
            batches = block['data']['batches']
            for batch in batches:

                for transaction in batch['transactions']:
                    tran = json.loads(json.dumps(transaction))

                    if address in transaction['header']['outputs']:
                        return transaction['payload']

            return None

        except Exception as e:
            print("err:", e)
            return {'msg': "err"}


def get_data_payload(payload_string):
    try:
        data_model = payload_pb2.B4EPayload()
        data_model.ParseFromString(base64.b64decode(payload_string))

        return data_model

    except Exception as e:
        print("err:", e)
        return {'msg': "err"}


def get_state(sawtooth_address):
    url = SawtoothConfig.REST_API + "/state/" + str(sawtooth_address)
    response = requests.get(url)
    if response.status_code == 200:
        try:
            state_dict = json.loads(response.content)
            payload_string = state_dict['data']
            data = deserialize_data(sawtooth_address, base64.b64decode(payload_string))[0]

            return data

        except Exception as e:
            print("err:", e)
            return {'msg': "err"}


def _parse_proto(proto_class, data):
    deserialized = proto_class()
    deserialized.ParseFromString(data)
    return deserialized


def _convert_proto_to_dict(proto):
    result = {}

    for field in proto.DESCRIPTOR.fields:
        key = field.name
        value = getattr(proto, key)

        if field.type == field.TYPE_MESSAGE:
            if field.label == field.LABEL_REPEATED:
                result[key] = [_convert_proto_to_dict(p) for p in value]
            else:
                result[key] = _convert_proto_to_dict(value)

        elif field.type == field.TYPE_ENUM:
            number = int(value)
            name = field.enum_type.values_by_number.get(number).name
            result[key] = name

        else:
            if type(value) == google.protobuf.pyext._message.RepeatedScalarContainer:
                value = list(value)
            result[key] = value

    return result


def get_student_data(student_public_key):
    url = SawtoothConfig.REST_API + "/state"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            state_dict = json.loads(response.content)
            # print(state_dict['data'])
            cert = []
            subjects = []
            for state in state_dict['data']:
                if addresser.is_owner(state['address'], student_public_key):
                    deserialize = deserialize_data(state['address'], base64.b64decode(state['data']))[0]

                    # get latest record data in record
                    # latest_record_data = max(deserialize['record_data'], key=lambda obj: obj['timestamp'])
                    record = {'address': state['address'], 'versions': []}

                    for record_data in deserialize['versions']:
                        record['versions'].append({
                            'txid': record_data['transaction_id'],
                            'timestamp': record_data['timestamp'],
                            'type': record_data['record_status'],
                            'cipher': record_data['cipher'],
                            'hash': record_data['hash'],

                        })
                    if deserialize['record_type'] == 'CERTIFICATE':
                        cert.append(record)
                    elif deserialize['record_type'] == 'SUBJECT':
                        subjects.append(record)

            data = {'publicKeyHex': student_public_key,
                    'certificate': cert,
                    'subjects': subjects}
            return data

        except Exception as e:
            print("err:", e)
            LOGGER.warning(e)
            return {'msg': "err"}
