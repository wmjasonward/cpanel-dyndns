# cpanel-dyndns
Pseudo dynamic dns using a python3 script to access the cpanel api

Run this on a cron job to periodically check your external ip address and if it has changed, update an A record on a cPanel server.

Copy config.ini.example to config.ini and enter your values.

This script will create a local file with the name defined in the local section of the config which saves the external ip address. When the script runs it checks that file to see if the ip address has changed. If no change is detected it does not call the cPanel API.

Just delete that file if you to force the script to call the cPanel api and update the record.

External ip address is determined by an http call to a provider. https://api.ipify.org works well for this. Other methods could be used, but the script expects the text of the response body to only contain the ipv4 address.

You'll need "requests" installed in your python environment.