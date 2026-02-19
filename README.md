Notes:

- What is the best way to hook into input? the eventgraph is cooked.
- Do I need to hook into inputs? do we even need inputs?
- Component based system - flexibility?
- telemetry configure node should print to screen or provide some notifier if its connected or not, if not - avoid spamming errors
- remove logging if in editor (or at least tag differently)
- how to handle players afking? (screws over dwell time)
- 




## Ideal schema includes:

##### Base Packet

GameTime (float)
Frames (int)
MachineName (str)
UserName (str)
SessionID (str)
RunID (int)
*PIE?* (bool)
Position (vector 3)

##### Interval based:

send base Packet

##### Damage:

send Base Packet
Incoming damage (float)
Health (float)

##### Death:
