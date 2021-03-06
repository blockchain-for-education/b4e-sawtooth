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

import argparse
import asyncio
import concurrent.futures
import logging
import sys
import nest_asyncio

from zmq.asyncio import ZMQEventLoop

from multiprocessing import Process

from statistic.b4e_statistic.database import Database
from statistic.b4e_statistic.rest_api import StudentAPI
from statistic.b4e_statistic.subscriber import Subscriber
from statistic.b4e_statistic.event_handling import get_events_handler

from config.config import SawtoothConfig, MongoDBConfig, SubscriberConfig

KNOWN_COUNT = 15
LOGGER = logging.getLogger(__name__)


def parse_args(args):
    parser = argparse.ArgumentParser(add_help=False)

    subparsers = parser.add_subparsers(title='subcommands', dest='command')
    subparsers.required = True

    database_parser = argparse.ArgumentParser(add_help=False)
    database_parser.add_argument(
        '-B', '--bind',
        help='identify host and port for api to run on',
        default='localhost:8000')
    database_parser.add_argument(
        '--db-name',
        help='The name of the database',
        default='b4e-statistic')
    database_parser.add_argument(
        '--db-host',
        help='The host of the database',
        default='localhost')
    database_parser.add_argument(
        '--db-port',
        help='The port of the database',
        default='5432')
    database_parser.add_argument(
        '--rest-api-default',
        help='The rest api default of sawtooth',
        default='rest-api-0:8008 ')
    database_parser.add_argument(
        '--subscriber-host-url',
        help='The host of the subscriber',
        default='http://localhost:1212')
    database_parser.add_argument(
        '--db-user',
        help='The authorized user of the database',
        default='')
    database_parser.add_argument(
        '--db-password',
        help="The authorized user's password for database access",
        default='')
    database_parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Increase output sent to stderr')

    subparsers.add_parser(
        'init',
        parents=[database_parser])

    subscribe_parser = subparsers.add_parser(
        'subscribe',
        parents=[database_parser])
    subscribe_parser.add_argument(
        '-C', '--connect',
        help='The url of the validator to subscribe to',
        default='tcp://localhost:4004')

    return parser.parse_args(args)


def init_logger(level):
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    if level == 1:
        logger.setLevel(logging.INFO)
    elif level > 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARN)


def do_subscribe(opts):
    LOGGER.info('Starting subscriber...')
    try:
        dsn = 'dbname={} user={} password={} host={} port={}'.format(
            opts.db_name,
            opts.db_user,
            opts.db_password,
            opts.db_host,
            opts.db_port)

        database = Database(dsn)
        database.connect()
        subscriber = Subscriber(opts.connect)
        subscriber.add_handler(get_events_handler(database))
        known_blocks = database.fetch_last_known_blocks(KNOWN_COUNT)
        known_ids = [block['block_id'] for block in known_blocks]
        subscriber.start(known_ids=known_ids)

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as err:  # pylint: disable=broad-except
        LOGGER.exception(err)
        sys.exit(1)

    finally:
        try:
            database.disconnect()
            subscriber.stop()
        except UnboundLocalError:
            pass

    LOGGER.info('Subscriber shut down successfully')


def rest_api(opts, host, port):
    try:
        LOGGER.info('Run Statistic API ......')
        dsn = 'dbname={} user={} password={} host={} port={}'.format(
            opts.db_name,
            opts.db_user,
            opts.db_password,
            opts.db_host,
            opts.db_port)
        database = Database(dsn)
        database.connect()
        rest_api = StudentAPI(database, host, port)
        rest_api.run()
    except Exception as e:
        LOGGER.error(e)


def do_init(opts):
    LOGGER.info('Initializing subscriber...')
    try:
        dsn = 'dbname={} user={} password={} host={} port={}'.format(
            opts.db_name,
            opts.db_user,
            opts.db_password,
            opts.db_host,
            opts.db_port)
        database = Database(dsn)
        database.connect()
        database.create_tables()

    except Exception as err:  # pylint: disable=broad-except
        LOGGER.exception('Unable to initialize subscriber database: %s', err)

    finally:
        database.disconnect()


def main():
    loop = ZMQEventLoop()
    asyncio.set_event_loop(loop)

    opts = parse_args(sys.argv[1:])
    init_logger(opts.verbose)
    if opts.command == 'subscribe':
        MongoDBConfig.USER_NAME = opts.db_user
        MongoDBConfig.PASSWORD = opts.db_password
        MongoDBConfig.HOST = opts.db_host
        MongoDBConfig.PORT = opts.db_port

        SawtoothConfig.VALIDATOR_TCP = opts.connect

        LOGGER.info("DB HOST:" + opts.db_host)

        try:
            host, port = opts.bind.split(":")
            port = int(port)
        except ValueError:
            print("Unable to parse binding {}: Must be in the format"
                  " host:port".format(opts.bind))
            sys.exit(1)
        Process(target=rest_api, args=(opts, host, port)).start()
        Process(target=do_subscribe, args=(opts,)).start()
    elif opts.command == 'init':
        LOGGER.info("run init")
        do_init(opts)
    else:
        LOGGER.exception('Invalid command: "%s"', opts.command)


if __name__ == '__main__':
    # do_init()
    main()
