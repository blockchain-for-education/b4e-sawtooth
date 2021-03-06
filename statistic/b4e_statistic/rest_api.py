import asyncio
import json
import logging
import sys
import nest_asyncio

from aiohttp import web

from aiohttp.web import json_response

from addressing.b4e_addressing import addresser
from statistic.b4e_statistic.errors import ApiNotFound

LOGGER = logging.getLogger(__name__)


class StudentAPI(object):
    def __init__(self, database, host="0.0.0.0", port=8000):
        self._database = database
        self._host = host
        self._port = port
        pass

    def run(self):
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()

        app = web.Application(loop=loop)
        # WARNING: UNSAFE KEY STORAGE
        # In a production application these keys should be passed in more securely
        app['aes_key'] = 'ffffffffffffffffffffffffffffffff'
        app['secret_key'] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        LOGGER.info('Starting Student REST API on %s:%s', self._host, self._port)

        app.router.add_get('/student/data/{student_public_key}', self.student_data)
        app.router.add_get('/record/{address}', self.record_address)
        app.router.add_get('/', self.hello_student)
        app.router.add_get('/records', self.get_records)
        app.router.add_get('/statistic', self.get_statistic)
        app.router.add_get('/statistic/certificates-for-years', self.cert_for_years)
        app.router.add_get('/statistic/certificates-of-university/{public_key}', self.cert_of_university)

        web.run_app(
            app,
            host=self._host,
            port=self._port,
            access_log=LOGGER,
            access_log_format='%r: %s status, %b size, in %Tf s'
        )

    def student_data(self, request):
        public_key = request.match_info.get('student_public_key', '')
        records = self._database.get_student_data(public_key)
        # records = list(records)
        certificates = []
        subjects = []
        for record in records:
            record_id = record.get("record_id")
            owner_public_key = record.get("owner_public_key")
            manager_public_key = record.get("manager_public_key")
            address = addresser.get_record_address(record_id, owner_public_key, manager_public_key)
            record_data = {"address": address,
                           "versions": self.standard_versions(record.get("versions"))}

            if record.get("record_type") == "SUBJECT":
                subjects.append(record_data)
            elif record.get("record_type") == "CERTIFICATE":
                certificates.append(record_data)

            student_data = {
                "certificates": certificates,
                "subjects": subjects
            }
        return json_response(student_data)

    async def get_statistic(self, request):
        records = await self._database.get_cert_by_year()
        return json_response(records)

    async def cert_for_years(self, request):
        records = await  self._database.get_cert_by_year()

        cert_by_year = {}
        for record in records:
            schoolName = record[0]
            numCert = record[1]
            year = str(int(record[2]))
            if not cert_by_year.get(year):
                cert_by_year[year] = {}

            cert_by_year[year][schoolName] = numCert

        return json_response(cert_by_year)

    async def cert_of_university(self, request):
        public_key = request.match_info.get('public_key', '')
        records = await self._database.get_certs_of_university(public_key)
        certs_of_university = {}
        for record in records:
            year = str(int(record[0]))
            edu_program = record[1]
            cert = record[2]

            if not certs_of_university.get(year):
                certs_of_university[year] = {}
            if not certs_of_university[year].get(edu_program):
                certs_of_university[year][edu_program] = []

            certs_of_university[year][edu_program].append(cert)

        return json_response(certs_of_university)

    def record_address(self, request):
        address = request.match_info.get('address', '')

        try:
            record = self._database.get_record_by_address(address)
            record_data = {"address": address,
                           "versions": self.standard_versions(record.get("versions"))}
        except Exception as e:
            record_data = {"err": str(e)}

        return json_response(record_data)

    def hello_student(self, request):
        return "hello"

    async def get_records(self, request):
        all_records = await self._database.get_records()
        all_blocks = await self._database.get_blocks()
        all_edu = await self._database.get_edus()
        all_classes = await self._database.get_classes()
        all_actors = await self._database.get_actors()
        all_records = date_to_string_record(all_records)
        all_edu = date_to_string_record(all_edu)
        all_classes = date_to_string_record(all_classes)
        all_actors = date_to_string_record(all_actors)

        return json_response({
            "all_blocks": list(all_blocks),
            "all_records": all_records,
            "edus": all_edu,
            "classes": all_classes,
            "actors": all_actors,
        })

    def standard_versions(self, versions):
        for version in versions:
            status = version.get("record_status")
            version['type'] = self._version_status_type(status)
            del version['record_status']
            version['txid'] = version['transaction_id']
            del version["transaction_id"]

        return versions

    def _version_status_type(self, i):
        switch = {
            "CREATED": "create",
            "REVOKED": "revoke",
            "REACTIVATED": "reactive"
        }
        return switch.get(i)


def date_to_string_record(list_record):
    new_list = []
    for record in list_record:
        to_list = list(record)
        to_list[-2] = to_list[-2].strftime("%H:%M:%S")
        new_list.append(to_list)
    list_record = new_list
    return new_list
