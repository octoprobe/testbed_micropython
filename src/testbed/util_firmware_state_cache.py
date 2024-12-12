"""
Goal:
  * Flash a required firmware, if it has changed
  * Skip flashing if the required firmware is already installed.

Problems:
  * 'micropython_version_text' does NOT include the firmware variant!
    Consequence: Firmware change is NOT detected.
  * When the firmware source directory is touched, 'micropython_version_text' will contain '...dirty...'.
    Consequence: Firmware change is NOT detected.

Proposal 'firmware_state_cache'
  * A persistent dictionary in '~/octprobe_downloads/firmware_state_cache'
    * Key: Tentacle identification '452b-ESP8266_GENERIC'
    * Value: 
      * Firmware binary hash
      * Datetime when this entry was updated
      * 
"""
