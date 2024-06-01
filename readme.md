# AbfahrtDemo

Dieses Projekt zeigt die nächsten Abfahrten von öffentlichen Verkehrsmitteln auf einem e-Paper-Display an. Die Haltestellen und andere Einstellungen können über ein Web-Frontend konfiguriert werden.

## Voraussetzungen

- Raspberry Pi mit Raspbian (oder einem anderen kompatiblen Betriebssystem)
- Waveshare e-Paper Display (2.13 Zoll)
- Python 3.x
- Git

## Erlangung des API-Schlüssels

Um einen API-Schlüssel für die OpenTransportData API zu erhalten, folgen Sie diesen Schritten:

1. Registrieren Sie sich auf der [OpenTransportData-Plattform](https://opentransportdata.swiss/de/).
2. Nach der Registrierung und Anmeldung gehen Sie zu Ihrem Benutzerkonto und erstellen Sie ein neues Projekt.
3. Nach der Erstellung des Projekts erhalten Sie einen API-Schlüssel. Diesen Schlüssel benötigen Sie während des Setups, um die API-Anfragen authentifizieren zu können.


## Installation

1. Klonen Sie dieses Repository auf Ihren Raspberry Pi:
    ```bash
    git clone https://github.com/IHR-GITHUB-USERNAME/AbfahrtDemo.git
    cd AbfahrtDemo
    ```

2. Führen Sie das Setup-Skript aus, um alle notwendigen Abhängigkeiten zu installieren und das Projekt zu konfigurieren. Das Skript wird Sie nach Ihrem OpenTransportData API-Schlüssel fragen:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

3. Starten Sie die Flask-Anwendung und das Display-Skript:
    ```bash
    sudo systemctl start abfahrtdemo.service
    ```

4. Stellen Sie sicher, dass der Dienst beim Booten gestartet wird:
    ```bash
    sudo systemctl enable abfahrtdemo.service
    ```

5. Öffnen Sie einen Webbrowser und navigieren Sie zur IP-Adresse Ihres Raspberry Pi auf Port 5000, um das Web-Frontend zu verwenden:
    ```
    http://<IP-Adresse-Ihres-Raspberry-Pi>:5000
    ```


## Konfiguration

Die Konfiguration erfolgt über die Datei `config.ini`, die sich im Projektverzeichnis befindet. Die Datei wird automatisch erstellt und kann über das Web-Frontend geändert werden.

### Beispiel `config.ini`

```ini
[Settings]
stop_point_ref = YOUR_STOP_POINT_REF
stop_title = YOUR_STOP_TITLE
number_of_results = 5
desired_destinations = all
threshold = 5
api_key = YOUR_API_KEY
```

- **stop_point_ref**: Der Referenzpunkt für die Haltestelle, deren Abfahrtsinformationen Sie anzeigen möchten. Ersetzen Sie `YOUR_STOP_POINT_REF` durch die tatsächliche Referenznummer der Haltestelle.
- **stop_title**: Der Titel der Haltestelle, die auf dem Display angezeigt werden soll. Ersetzen Sie `YOUR_STOP_TITLE` durch den tatsächlichen Namen der Haltestelle.
- **number_of_results**: Die Anzahl der angezeigten Ergebnisse. Standardwert ist `5`.
- **desired_destinations**: Die gewünschten Ziele für die Abfahrten. Standardwert ist `all`.
- **threshold**: Die Mindestanzahl von Minuten bis zur Abfahrt, die angezeigt werden sollen. Standardwert ist `5`.
- **api_key**: Ihr API-Schlüssel von der OpenTransportData-Plattform. Ersetzen Sie `YOUR_API_KEY` durch Ihren tatsächlichen API-Schlüssel.

## Dienstverwaltung

Um den Dienst zu stoppen:
```bash
sudo systemctl stop abfahrtdemo.service
```

Um den Dienst neu zu starten:
```bash
sudo systemctl restart abfahrtdemo.service
```

## Fehlerbehebung

Bei Problemen überprüfen Sie die Log-Dateien unter `/var/log/syslog` oder die spezifischen Log-Dateien des Projekts.
