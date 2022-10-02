# Cambrionix Serial Command Line API
#### Purpose:
Power management USB Hubs can be used to mitigate the overcharged mobile device batteries (e.g. mobile automation), 
in order to automate this process a python based serial interface wrapper was introduced  
on top of the [serial command line of the Cambrionix Power Management USB Hubs](https://www.cambrionix.com/cli) in order to:

- Expose the serial command line interface as an API using an [XML-RPC server](https://docs.python.org/3/library/xmlrpc.server.html).
- Remotely automate the USB Hub port state (e.g. Ansible), even through a scheduler (e.g Cronjob).

#### About:
Cambrionix Power Management USB serial interface wrapper.

Supports the following [Universal Series](https://www.cambrionix.com/product-user-manuals):

* PPxx
* Uxx
* ThunderSync

#### Usage:

1. Install the Cambrionix Power Management USB Hub on the host machine.
2. Install Python [tox](https://pypi.org/project/tox/) on the host machine.
3. Move inside the project root folder and start the interactive interpreter:

```bash
tox -e ipython
```

```python
In [1]: from cambrionix import Cambrionix
In [2]: with Cambrionix('DO02DM7Y') as c:
          c.set_mode('S', 1)
          c.show_state(1)
```

#### Limitations:

1. Unit testing is supported only for ``Python2.x`` due to [serial_mock](https://serialmock.readthedocs.io/en/latest/)
2. Source code is being written to support ``Python2.x`` and ``Python3.x`` (without any guarantee).
