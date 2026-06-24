# Fur Affinity Status

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FurAffinityDotNet&repository=hass-furaffinity&category=integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant integration that monitors the [Fur Affinity status page](https://status.furaffinity.net) and exposes the current state of services, alerts, incidents, maintenance, and individual monitor uptimes to Home Assistant.

## Features

- Overall `overall_status` exposed as an enum sensor (`up` / `down` / `paused`)
- Counts and details of:
  - Active alerts
  - Active incidents
  - Active maintenance
- A binary sensor for each "has alerts / incidents / maintenance" so you can trigger automations when the status changes.
- Per-monitor sensors for each service (e.g. `Main Site`, `Sphinx Search`, `FACDN`, `API`) including:
  - Current status
  - 24h / 72h / 7d uptime percentages
  - Last checked timestamp and check interval
- Overall average uptime across all monitors (24h / 72h / 7d)
- A `furaffinity.refresh` service to force an immediate update.

## Installation

### HACS (recommended)

1. Make sure [HACS](https://hacs.xyz) is installed.
2. Add this repository as a custom repository in HACS:
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/FurAffinityDotNet/hass-furaffinity`
   - Category: Integration
3. Install the **Fur Affinity Status** integration.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and search for **Fur Affinity Status**.

### Manual

1. Copy `custom_components/furaffinity/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via the UI.

## Configuration

Configuration is performed entirely via the UI. The available options are:

| Option | Description | Default |
| --- | --- | --- |
| `scan_interval` | How often to poll the status API (in minutes). | `5` |

## Entities

For each installation, the integration creates the following device **Fur Affinity Status** with the entities below.

### Sensors

| Entity | Description |
| --- | --- |
| `sensor.fur_affinity_status_overall_status` | The overall status string from the API. |
| `sensor.fur_affinity_status_active_alerts` | Number of active alerts (full list in attributes). |
| `sensor.fur_affinity_status_active_incidents` | Number of active incidents (full list in attributes). |
| `sensor.fur_affinity_status_active_maintenance` | Number of active maintenance items (full list in attributes). |
| `sensor.fur_affinity_status_overall_uptime_24h` | Average uptime across all monitors over the last 24h. |
| `sensor.fur_affinity_status_overall_uptime_72h` | Average uptime across all monitors over the last 72h. |
| `sensor.fur_affinity_status_overall_uptime_7d` | Average uptime across all monitors over the last 7 days. |
| `sensor.<monitor_name>` | One sensor per monitor exposing the current status and uptime attributes. |

### Binary sensors

| Entity | Description |
| --- | --- |
| `binary_sensor.fur_affinity_status_has_alerts` | `ON` when at least one alert is active. |
| `binary_sensor.fur_affinity_status_has_incidents` | `ON` when at least one incident is active. |
| `binary_sensor.fur_affinity_status_has_maintenance` | `ON` when at least one maintenance is active. |
| `binary_sensor.fur_affinity_status_operational` | `ON` when `overall_status` is `up`. |

## Example automations

```yaml
automation:
  - alias: "Notify when Fur Affinity has an active alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.fur_affinity_status_has_alerts
        to: "on"
    action:
      - service: notify.persistent_notification
        data:
          title: "Fur Affinity status alert"
          message: >-
            {{ state_attr('binary_sensor.fur_affinity_status_has_alerts', 'alerts')
               | map(attribute='title') | join(', ') }}

  - alias: "Notify when Fur Affinity goes down"
    trigger:
      - platform: state
        entity_id: binary_sensor.fur_affinity_status_operational
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "Fur Affinity down"
          message: >-
            Current overall status:
            {{ states('sensor.fur_affinity_status_overall_status') }}
```

## Data source

Data is fetched from the public Fur Affinity status API:

```
https://status.furaffinity.net/api/v1/status/
```

## License

MIT
