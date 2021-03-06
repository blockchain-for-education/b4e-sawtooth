# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import enum
import hashlib

FAMILY_NAME = 'b4e'
FAMILY_VERSION = '1.2'
NAMESPACE = hashlib.sha512(FAMILY_NAME.encode('utf-8')).hexdigest()[:6]
ACTOR_PREFIX = '000'
VOTING_PREFIX = '001'
PORTFOLIO_PREFIX = '010'
CLASS_PREFIX = '011'
RECORD_PREFIX = '100'
JOB_PREFIX = '101'

ENVIRONMENT_ADDRESS = NAMESPACE + str(10 ** 64)[1:]


@enum.unique
class AddressSpace(enum.IntEnum):
    ACTOR = 0
    VOTING = 1
    PORTFOLIO = 2
    CLASS = 3
    RECORD = 4
    ENVIRONMENT = 5

    JOB = 6

    OTHER_FAMILY = 100


def get_environment_address():
    return ENVIRONMENT_ADDRESS


def get_actor_address(public_key):
    return NAMESPACE + ACTOR_PREFIX + hashlib.sha512(
        public_key.encode('utf-8')).hexdigest()[:61]


def get_voting_address(public_key):
    return NAMESPACE + VOTING_PREFIX + hashlib.sha512(
        public_key.encode('utf-8')).hexdigest()[:61]


def get_class_address(class_id, institution_public_key):
    institution_prefix = hashlib.sha512(
        institution_public_key.encode('utf-8')).hexdigest()[-10:]
    return NAMESPACE + CLASS_PREFIX + institution_prefix + hashlib.sha512(
        class_id.encode('utf-8')).hexdigest()[:51]


def get_record_address(record_id, owner_public_key, manager_public_key):
    owner_prefix = hashlib.sha512(
        owner_public_key.encode('utf-8')).hexdigest()[-10:]
    manager_prefix = hashlib.sha512(
        manager_public_key.encode('utf-8')).hexdigest()[-10:]
    return NAMESPACE + RECORD_PREFIX + owner_prefix + manager_prefix \
           + hashlib.sha512(record_id.encode('utf-8')).hexdigest()[:41]


def get_portfolio_address(id, owner_public_key, manager_public_key):
    owner_prefix = hashlib.sha512(
        owner_public_key.encode('utf-8')).hexdigest()[-10:]
    manager_prefix = hashlib.sha512(
        manager_public_key.encode('utf-8')).hexdigest()[-20:]
    return NAMESPACE + PORTFOLIO_PREFIX + owner_prefix + manager_prefix \
           + hashlib.sha512(id.encode('utf-8')).hexdigest()[:31]


def get_job_address(job_id, company_public_key, candidate_public_key):
    company_prefix = hashlib.sha512(
        company_public_key.encode('utf-8')).hexdigest()[-10:]
    candidate_prefix = hashlib.sha512(
        candidate_public_key.encode('utf-8')).hexdigest()[-20:]
    return NAMESPACE + JOB_PREFIX + company_prefix + candidate_prefix \
           + hashlib.sha512(job_id.encode('utf-8')).hexdigest()[:31]


def get_address_type(address):
    if address[:len(NAMESPACE)] != NAMESPACE:
        return AddressSpace.OTHER_FAMILY
    if address == ENVIRONMENT_ADDRESS:
        return AddressSpace.ENVIRONMENT
    infix = address[6:9]

    if infix == ACTOR_PREFIX:
        return AddressSpace.ACTOR
    if infix == VOTING_PREFIX:
        return AddressSpace.VOTING
    if infix == CLASS_PREFIX:
        return AddressSpace.CLASS
    if infix == RECORD_PREFIX:
        return AddressSpace.RECORD
    if infix == PORTFOLIO_PREFIX:
        return AddressSpace.PORTFOLIO
    if infix == JOB_PREFIX:
        return AddressSpace.JOB
    return AddressSpace.OTHER_FAMILY


def is_owner(record_address, owner_public_key):
    infix = record_address[6:9]
    if infix != RECORD_PREFIX:
        return False
    if record_address[9:19] == hashlib.sha512(
            owner_public_key.encode('utf-8')).hexdigest()[-10:]:
        return True
    return False


def is_manager(record_address, manager_public_key):
    infix = record_address[6:9]
    if infix != RECORD_PREFIX:
        return False
    if record_address[19:29] == manager_public_key[-10:]:
        return True
    return False
