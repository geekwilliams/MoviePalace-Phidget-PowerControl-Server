from PowerControlServer import PowerControlServer
import signal
import sys


# Setup
pcs = PowerControlServer()

def main():
    pcs.run()
    # Deal with Ctrl^C 
    signal.signal(signal.SIGINT, sig_handler)

def sig_handler(sig, frame):
    print("SIGINT Received.  Cleaning up and exiting...\n")
    try: 
        pcs.stop()
    except: 
        print("Error running cleanup of RelayControl()\n")

    print("Exiting.\n")
    sys.exit(0)

if __name__ == "__main__":
    main()

