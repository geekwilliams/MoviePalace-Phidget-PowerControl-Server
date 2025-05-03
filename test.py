from devices.Projector import Projector
from devices.Dolby import Dolby
from time import sleep

p = Projector()
d = Dolby()
while(True): 
    cooldown = p.getCooldown()
    print(cooldown)
    if(cooldown != 0):
        sleep(5)
    elif(cooldown == 0): 
        break
    else:
        # this case catches any missed responses from projector
        sleep(5)
        if(timeout == 5): 
            break
        timeout += 1 # make sure shutdown process doesn't hang