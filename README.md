

# 🔌 Cisco LLDP Neighbor Collector via SSH

This Python script connects to multiple Cisco switches using SSH, runs LLDP neighbor discovery commands, and extracts detailed information for each connected port. The collected LLDP data is saved into a CSV file for further analysis or inventory tracking.

---

## 🚀 Features

- Connects to multiple switches listed in an `inventory.ini` file.
- Handles Cisco CLI prompts and pagination.
- Supports advanced authentication handling using Paramiko.
- Extracts key LLDP details like Device ID, Port ID, System Name, Serial Number, Model Name, and Management Address.
- Saves all collected data in a structured CSV format.
- Built-in logging and error handling for robust execution.

---

## 🗂️ Directory Structure

```
.
├── lldp_collector.py         # Main script
├── inventory.ini             # Inventory file with host credentials
├── lldp_info.csv             # Output CSV file with LLDP neighbor data
```

---

## 🛠️ Prerequisites

- Python 3.x
- Install required libraries:

```
pip install paramiko
```

> `time`, `re`, `configparser`, `csv`, `os`, and `logging` are part of Python's standard library.

---

## 🧾 Inventory File Format (`inventory.ini`)

```ini
[switches]
host1 = 10.0.0.1
host2 = 10.0.0.2
username = admin
password = Cisco123
```

> You can add multiple `hostN` entries under the `[switches]` section. Username and password will be shared across all.

---

## ⚙️ How It Works

1. Reads the host list and credentials from `inventory.ini`.
2. Establishes SSH connections to each switch using `paramiko`.
3. Sends LLDP discovery commands and handles prompts (`User Name:`, `Password:`).
4. Parses the command output using regex to extract LLDP neighbor data.
5. Appends the extracted data to `lldp_info.csv`.

---

## 📤 Sample Output (CSV)

| Host      | Device ID | Port ID | System Name | Serial Number | Model Name | Management Address |
|-----------|-----------|---------|--------------|----------------|-------------|---------------------|
| 10.0.0.1  | switchB   | Gi1/0/1 | core-switch | FOC1234567     | WS-C3850    | 10.0.0.2            |

---

## 🧪 Running the Script

Make sure the `inventory.ini` is correctly configured, then run:

```bash
python lldp_collector.py
```

> Adjust the `file_path` in `read_inventory()` if you move the inventory file elsewhere.

---

## 🧰 Troubleshooting

- **Connection Timeout?** Ensure SSH is enabled on the switches and reachable.
- **Authentication Failure?** Double-check the credentials in the `.ini` file.
- **Empty Output?** LLDP might be disabled or not configured on the switch interfaces.

---

## 📌 Customization

- To add support for other commands, extend the `send_command()` function.
- You can enhance regex patterns in `extract_lldp_info()` to match more fields.
- Adjust wait times in `send_command()` if dealing with slow network devices.

---

## 📜 License
 - Use, modify, and distribute as needed.

---

## 🤝 Contributions

Feel free to fork and submit pull requests to improve this tool! Whether it’s better parsing, support for more vendors, or UX enhancements—we welcome it all.
My Email:anithadamarla0313@gmail.com
---

Let me know if you want this as a downloadable `README.md` file or if you’d like to expand it with diagrams or architecture illustrations.
