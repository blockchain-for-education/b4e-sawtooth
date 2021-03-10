import datetime
from json.decoder import JSONDecodeError
import logging
import time

from aiohttp.web import json_response
import bcrypt
from Crypto.Cipher import AES
from itsdangerous import BadSignature
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from rest_api.b4e_rest_api.errors import ApiBadRequest
from rest_api.b4e_rest_api.errors import ApiNotFound
from rest_api.b4e_rest_api.errors import ApiUnauthorized

from rest_api.b4e_rest_api.blockchain_get_data import get_data_from_transaction
from rest_api.b4e_rest_api.blockchain_get_data import get_state
from rest_api.b4e_rest_api.blockchain_get_data import get_student_data
from rest_api.b4e_rest_api.blockchain_get_data import get_record_transaction

from config.config import SawtoothConfig
from rest_api.b4e_rest_api.route_handler.route_handler import decode_request, validate_fields, tolist, slice_per, \
    get_time

LOGGER = logging.getLogger(__name__)


class BlockchainRouteHandler(object):
    def __init__(self, loop, messenger, database):
        self._messenger = messenger
        self._database = database

    async def get_student_data(self, request):
        pass

    async def get_record(self, request):
        pass

    def add_route(self, app):
        pass