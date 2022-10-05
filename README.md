[![Linting](https://github.com/theodore86/cambrionix-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/theodore86/cambrionix-serial/actions/workflows/ci.yml)

# Cambrionix Serial Command Line API
#### Purpose:
Power management USB Hubs can be used to mitigate the overcharged mobile device batteries (e.g. mobile automation), 
in order to automate this process a python based serial interface wrapper was introduced  
on top of the [serial command line of the Cambrionix Power Management USB Hubs](https://www.cambrionix.com/cli) in order to:

- Expose the serial command line interface as an API using an [XML-RPC server](https://docs.python.org/3/library/xmlrpc.server.html).
  - Use an [XML-RPC client](https://docs.python.org/3/library/xmlrpc.client.html) to access those methods remotely.
- Automate the USB Hub port state (e.g. Ansible, Jenkins), schedule when your mobile devices will `wakeup` to **charge**.

#### About:
Cambrionix Power Management USB serial interface wrapper.

Supports the following [Universal Series](https://www.cambrionix.com/product-user-manuals):

* PPxx
* Uxx
* ThunderSync

#### Basic usage:

1. Install the Cambrionix Power Management USB Hub on the host machine.
2. Install Python [tox](https://pypi.org/project/tox/) on the host machine.
3. Move inside the project root folder and start the interactive interpreter:

```bash
tox -e ipython
```

```python
In [1]: from cambrionix import Cambrionix
In [2]: # Set port 1 to SYNC (activate) state
In [3]: with Cambrionix('DO02DM7Y') as c:
          c.set_mode('S', 1)
          c.show_state(1)
```

#### Advance usage

##### Remote access - XML-RPC

- Start and register all the power hub methods through the ``cbrxxmlrpc`` server:

```bash
python -m cambrionix.tools.cbrxxmlrpc --serial-port DO02DM7Y \
  --rpc-host 127.0.0.1 \
  --rpc-port 8999
```

- Use an [XML-RPC client](https://docs.python.org/3/library/xmlrpc.client.html) to access those methods remotely.

##### Local access
- Automate the power hub **port state** using the ``port_handler`` script (e.g cronjob):

```bash
python -m cambrionix.tools.port_handler --help
```

Requires an ``.ini`` configuration file, check the configuration file format in: ``tools/cambrionix.ini``.

#### Limitations:

1. Unit testing is supported only for ``Python2.x`` due to [serial_mock](https://serialmock.readthedocs.io/en/latest/)
2. Source code is being written to support ``Python2.x`` and ``Python3.x`` (without any guarantee).
