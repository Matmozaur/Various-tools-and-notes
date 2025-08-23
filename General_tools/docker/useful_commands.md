# Usefull tricks/commands

## Monitoring Docker

Monitoring Docker is essential for troubleshooting, auditing, and understanding activity in your environment. Docker provides several commands to help track container, image, and volume events.

### Monitoring Events with `docker events`

The `docker events` command streams real-time events from the Docker daemon.

#### Basic Usage

```sh
docker events
```
This displays all Docker events as they happen.

#### Filtering Events

You can filter events to focus on specific containers or time ranges:

- **By Container ID:**
    ```sh
    docker events --filter container=<your_container_id>
    ```
    Replace `<your_container_id>` with the actual container ID.

- **By Time Range:**
    ```sh
    docker events --since 30m --until "2025-05-04T18:00:00"
    ```
    Shows events from the last 30 minutes up to the specified date and time.

#### Example

```sh
docker events --filter container=abc123 --since 10m
```
Displays events for container `abc123` from the last 10 minutes.

**Tip:** Use these commands to monitor container lifecycle changes, restarts, network updates, and other Docker activities.