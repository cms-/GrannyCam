# GrannyCam
Secure remote monitoring for caregivers

An eldery family member's change in health necessitated close monitoring, even while caregiver was out of the room.
Using available parts (Pi clone, webcam, (wireless) LAN), I created a client-server system to display live video streams in other rooms. Using Python Qt bindings for display, SSL authentication for security.

The [first approach](https://gist.github.com/cms-/1cd8ff5083884a4355bd65f084eda927) for the viewer was sluggish running on the target hardware, so a [second approach](https://gist.github.com/cms-/1cd8ff5083884a4355bd65f084eda927) using PyQt was undertaken. Through testing, the parsing technique for locating JPEG headers was ultimately identified as a major bottleneck, as it translated to a nested loop. A simpler approach was used for extracting the image data from the series of HTTP headers. A spin-off project modifies the MJPEG-Streamer application and removes the HTTP headers to eliminate the need for parsing while streaming using [UDP over WiFi](https://github.com/cms-/dtls-streamer/blob/master/programs/ssl/ssl_server2.c).
