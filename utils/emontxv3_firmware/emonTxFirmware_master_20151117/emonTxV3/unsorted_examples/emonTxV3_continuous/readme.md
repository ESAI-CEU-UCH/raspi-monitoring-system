#Revised version of 4-channel continuous monitoring code for the emonTx V3.  

Changes include:

- The RFM12B is now always active rather than being routinely sent to sleep.  This avoids any gaps in the sampling process.
- The Jeelib routine rf12_sendNow() is used rather than rf12_sendStart(). This appears to minimise any disturbance to the sampled data.
- the datalogging period can be changed.  Previously it was fixed to once per second.
- for test purposes, RF messages can be restricted to just 1 in N datalogging periods.
- the on-board LED gives a 40mS flash whenever an RF message is sent.

Robin Emley, 9th June 2014

For older version see: <https://github.com/openenergymonitor/emonTxFirmware/tree/master/emonTxV3/RFM12B/Examples/Dev_test_examples>
