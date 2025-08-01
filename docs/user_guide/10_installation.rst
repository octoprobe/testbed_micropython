Installation Ubuntu
=====================


Target OS: Ubuntu Server 24.04.1 LTS.

This is a recommendation to set up octoprobe on a 'server' acting both as github runner and interactive workstation.

The user `optoprobe` is used when working interactively. The user `githubrunner` has limited rights to just allow to run tests.

Software to be installed as root
----------------------------------

These software packages are required by octoprobe.

.. code::

    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y git uhubctl dfu-util docker.io docker-buildx
    sudo snap install astral-uv --classic


Installation: Users
-------------------

These users are referenced in `/etc/udev/rules.d/*`!

+----------------------+-------------------+
| Octoprobe user       | ``octoprobe``     |
+----------------------+-------------------+
| Github runner user   | ``githubrunner``  |
+----------------------+-------------------+

.. code::

    sudo adduser octoprobe
    sudo adduser githubrunner

    sudo groupadd docker
    sudo usermod -aG docker,plugdev,dialout,systemd-journal octoprobe
    sudo usermod -aG docker,plugdev,dialout,systemd-journal githubrunner


You might want to config git:

.. code::

    git config --global user.name "Hans Maerki"
    git config --global user.email "buhtig.hans.maerki@ergoinfo.ch"



Python - **without venv**
----------------------------------------------------------------------

You may use below command to run `mptest` or `op` without any venv.

.. code:: 

  uvx --python=3.13.5 --from=git+https://github.com/octoprobe/testbed_micropython.git -- mptest --help


Python - variant **without** `git clone testbed_micropython`
----------------------------------------------------------------------

Use this if you **do not plan** to change the sources of `testbed_micropython`.

.. code:: 

  mkdir ~/testbed_micropython
  cd ~/testbed_micropython
  uv venv --python=3.13.5
  uv pip install --upgrade git+https://github.com/octoprobe/testbed_micropython.git
  source .venv/bin/activate


Python - variant **with** `git clone testbed_micropython`
----------------------------------------------------------------------

Use this if you **plan** to change the sources of `testbed_micropython`.

.. code::

    git clone https://github.com/octoprobe/testbed_micropython.git ~/testbed_micropython
    cd ~/testbed_micropython
    uv venv --python=3.13.5
    source .venv/bin/activate
    uv pip install --upgrade -e .


Initial setup
---------------------------

Enable venv in ~/.bashrc
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Skip this step if you prefer to activate the venv manually.

.. code::

    echo 'source ~/testbed_micropython/.venv/bin/activate' >> ~/.profile
    # Log out and in again

.. code::

    op --install-completion
    mptest --install-completion


Later, you just might want to update: `uv pip install --upgrade -e ~/testbed_micropython`


Install udev rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As we comminicate heavely with usb devices, we have to give rights by installing udev-rules.


.. code::

    op install

Now `op install` will instruct you to:

.. code::

    echo 'PATH=$HOME/octoprobe_downloads/binaries/x86_64:$PATH' >> ~/.profile
    sudo cp /home/maerki/work_octoprobe_octoprobe/src/octoprobe/udev/*.rules /etc/udev/rules.d
    sudo sudo udevadm control --reload-rules
    sudo sudo udevadm trigger

These commands may help for debugging udev rules:

.. code::

  sudo udevadm control --log-priority=debug
  sudo journalctl -u systemd-udevd.service -f | grep 82-octoprobe

  sudo udevadm monitor -e
  sudo udevadm control --reload-rules
  sudo udevadm trigger --type=devices --action=change


Run your first tests
--------------------

Connect some tentacles:

Start the tests

.. code:: 

  git clone https://github.com/micropython/micropython.git ~/micropython
  cd ~/micropython
  mptest test

.. note::

  This now will compile the required firmware, flash it and run the tests.
  
  The testresults will be written to

     ~/testbed_micropython/testresults - if you cloned the git repo
     ~/octoprobe_downloads/testresults - if you did NOT clone the git repo
