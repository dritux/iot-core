import argparse
import datetime
import time
from time import gmtime, strftime
import subprocess
import random
import ssl

import jwt
import paho.mqtt.client as mqtt

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1

# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 32

# Whether to wait with exponential backoff before publishing.
should_backoff = False


def create_jwt(project_id, private_key_file, algorithm):

    token = {
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
        'aud': project_id
    }

    with open(private_key_file, 'r') as f:
        private_key = f.read()

    print('Creating JWT using {} from private key file {}'.format(algorithm, private_key_file))

    return jwt.encode(token, private_key, algorithm=algorithm)


def error_str(rc):
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
    print('on_connect', error_str(rc))
    global should_backoff
    global minimum_backoff_time
    should_backoff = False
    minimum_backoff_time = 1


def on_disconnect(unused_client, unused_userdata, rc):
    print('on_disconnect', error_str(rc))
    global should_backoff
    should_backoff = True


def on_publish(unused_client, unused_userdata, unused_mid):
    print('on_publish')


def parse_command_line_args():
    parser = argparse.ArgumentParser(
        description=(
                'Example Google Cloud IoT Core MQTT device connection code.'))
    parser.add_argument(
            '--project_id',
            required=True,
            help='GCP cloud project name')
    parser.add_argument(
            '--registry_id',
            required=True,
            help='Cloud IoT Core registry id')
    parser.add_argument(
            '--device_id',
            required=True,
            help='Cloud IoT Core device id')
    parser.add_argument(
            '--private_key_file',
            required=True,
            help='Path to private key file.')
    parser.add_argument(
            '--algorithm',
            choices=('RS256', 'ES256'),
            required=True,
            help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument(
            '--cloud_region', default='us-central1', help='GCP cloud region')
    parser.add_argument(
            '--ca_certs',
            default='./roots.pem',
            help=('CA root certificate from https://pki.google.com/roots.pem'))
    parser.add_argument(
            '--mqtt_bridge_hostname',
            default='mqtt.googleapis.com',
            help='MQTT bridge hostname.')
    parser.add_argument(
            '--mqtt_bridge_port', default=443, help='MQTT bridge port.')

    return parser.parse_args()


def main():
    global minimum_backoff_time
    args = parse_command_line_args()

    client = mqtt.Client(
            client_id=(
                    'projects/{}/locations/{}/registries/{}/devices/{}'
                    .format(
                            args.project_id, args.cloud_region,
                            args.registry_id, args.device_id)))

    client.username_pw_set(
            username='unused',
            password=create_jwt(
                    args.project_id, args.private_key_file, args.algorithm))


    client.tls_set(ca_certs=args.ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)
    client.loop_start()

    if should_backoff:

        if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
            print('Exceeded maximum backoff time. Giving up.')
        else:
            delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
            print('Waiting for {} before reconnecting.'.format(delay))
            time.sleep(delay)
            minimum_backoff_time *= 2
            client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)

    mqtt_topic = '/devices/{}/events'.format(args.device_id)

    if subprocess.call(["which", "/opt/vc/bin/vcgencmd"]) == 0:
        temp = subprocess.check_output(["sudo", "/opt/vc/bin/vcgencmd", "measure_temp"]).split('=', 1)[-1].rstrip()

    elif subprocess.call(["which", "istats"]) == 0:
        #temp = subprocess.check_output(["istats"]).decode().split(":")[-1].split("\n")[0]
        #temp = "".join(subprocess.check_output(["istats"]).decode().split()).split(":")[-1].split("F")[0]
        temp = 40
    else:
        temp = 40

    payload = '{}/{} Time {} temperature {}'.format(
            args.registry_id, args.device_id, strftime("%Y-%m-%d %H:%M:%S", gmtime()), temp)
    print('Publishing message {}'.format(payload))

    client.publish(mqtt_topic, payload, qos=1)

    client.loop_stop()
    print('Finished.')


if __name__ == '__main__':
    main()
