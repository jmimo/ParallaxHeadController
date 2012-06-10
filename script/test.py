import time

localtime = time.localtime()
DATETIME = time.strftime("%Y-%m-%d-%H:%M:%S", localtime)

print "{0}-IMG-{1:03d}.CR2".format(DATETIME,1)
