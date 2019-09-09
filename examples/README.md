# iot core

### Dependencies
```
$ sudo apt install build-essential libssl-dev libffi-dev python-dev python-pip

$ python3 -m venv .venv
$ source .venv/bin/activate

$ pip install pip setuptools wheel virtualenv --upgrade
$ pip install -r requirements.txt
```

### Variables
```
export project=fs-eletrowave
export region=us-central1
export registry=iot-eletrowave
export device_rsa=adriano-rs256-device
export device_ec=adriano-ec256-device
export subscription=iot-subscription
export topic_events=iot-events
export topic_state=iot-state
```
### Generation keys
```
openssl req -x509 -newkey rsa:2048 -keyout rsa_private.pem -nodes -out rsa_cert.pem
```

```
openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem
openssl ec -in ec_private.pem -pubout -out ec_public.pem
```
### Google setups

- PubSub
```
gcloud pubsub topics create $topic_events
gcloud pubsub topics create $topic_state
gcloud pubsub subscriptions create projects/$project/subscriptions/$subscription --topic=$topic_events
```
### Iot Core

- Create registry
```
gcloud iot registries create $registry \
    --project=$project \
    --region=$region \
    --event-notification-config=topic=projects/$project/topics/$topic_events \
    --state-pubsub-topic=$topic_state
```

- Create device rsa
```
gcloud iot devices create $device_rsa \
    --project=$project \
    --region=$region \
    --registry=$registry \
    --public-key path=rsa_cert.pem,type=rs256
```

- Create device ec
```
gcloud iot devices create $device_ec \
    --project=$project \
    --region=$region \
    --registry=$registry \
    --public-key path=ec_public.pem,type=es256
```

### Running telemetry 
```
python cpu_mqtt.py \
--project_id=$project \
--registry_id=$registry \
--device_id=$device_rsa \
--private_key_file=./rsa_private.pem \
--algorithm=RS256
```


```
python cpu_mqtt.py \
--project_id=$project \
--registry_id=$registry \
--device_id=$device_ec \
--private_key_file=./ec_private.pem \
--algorithm=ES256
```


gcloud pubsub subscriptions pull --auto-ack projects/$project/subscriptions/$subscription


### Download the CA root certificates from pki.google.com into the same directory as the example script you want to use:
```
wget https://pki.google.com/roots.pem
```


### Get keys to text

openssl ec -in <private-key.pem> -noout -text

