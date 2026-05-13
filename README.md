# Person from MQTT Wizard

A custom component for Home Assistant that creates a `device_tracker` entity updated via MQTT messages containing JSON payloads with GPS coordinates. 
This entity can be easily linked to a "Person" in Home Assistant to track their location.

## Features

- **Fully UI Configurable:** Set up everything straight from the Home Assistant UI without touching any YAML.
- **Multi-Broker Support:** Choose between Home Assistant's native MQTT integration or a standalone remote MQTT broker.
- **Custom JSON Parsing:** Flexibility to specify the exact JSON keys used for latitude and longitude in your specific payload.
- **Options Flow:** Modify broker credentials, topics, or JSON keys at any time after the initial installation.
- **Multi-language:** Includes translations for English and Italian.

## Installation

### Manual Installation

1. Download or clone this repository.
2. Copy the `custom_components/person_from_mqtt_wizard` folder into your Home Assistant `config/custom_components` directory.
3. Restart Home Assistant.

### HACS (Home Assistant Community Store)

1. Go to HACS -> Integrations.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this repository, select **Integration** as the category, and click Add.
4. Search for "Person from MQTT Wizard" in HACS, install it, and restart Home Assistant.

## Configuration

1. In Home Assistant, navigate to **Settings > Devices & Services**.
2. Click **+ Add Integration** and search for **Person from MQTT Wizard**.
3. Follow the setup wizard:
   - **Step 1:** Enter the tracker's name, the MQTT topic, and choose if you want to use a remote broker.
   - **Step 2 (Optional):** If you selected a remote broker, enter the IP, port, and credentials. The integration will test the connection before proceeding.
   - **Step 3:** Enter the JSON keys that contain the latitude and longitude data (default: `lat` and `lon`).

## Usage

Once configured, a new `device_tracker` entity (e.g., `device_tracker.mqtt_person_tracker`) will be created. 

To assign it to a person:
1. Go to **Settings > People**.
2. Select the person you want to track.
3. Add the newly created `device_tracker` entity to their "Track device" list.

## Payload Example

Send a message to your configured topic (e.g., `location/tracker`) with a payload like this:
```json
{"lat": 41.902782, "lon": 12.496366}
```