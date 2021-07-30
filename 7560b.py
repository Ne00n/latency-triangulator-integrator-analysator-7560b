import subprocess, json, time, re
from multiprocessing import Queue
from threading import Thread

class Latency:
    def __init__(self,config="machina.json"):
        print("Loading",config)
        with open(config) as handle:
            self.machina = json.loads(handle.read())

    def cmd(self,cmd):
        p = subprocess.run(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return [p.stdout.decode('utf-8'),p.stderr.decode('utf-8')]

    def getAvrg(self,row):
        result = 0
        for entry in row:
            result += float(entry[1])
        return float(result / len(row))

    def fpingSource(self,server,ip):
        lastByte = re.findall("^([0-9.]+)\.([0-9]+)",server, re.MULTILINE | re.DOTALL)
        result = self.cmd("ssh root@"+server+" fping -c5 "+ip)[0]
        parsed = re.findall("([0-9.]+).*?([0-9]+.[0-9]).*?([0-9])% loss",result, re.MULTILINE)
        return parsed,result,lastByte

    def fpingWorker(self,queue,outQueue):
        while queue.qsize() > 0 :
            data = queue.get()
            parsed,result,lastByte = self.fpingSource(data['server'],data['ip'])
            outQueue.put({"parsed":parsed,"result":result,"lastByte":lastByte,"ip":data['ip'],"server":data['server']})

    def debug(self):
        ip = input("IP: ")
        print("Running fping")
        count,queue,outQueue = 0,Queue(),Queue()
        for server in self.machina:
            queue.put({"server":server,"ip":ip})
        threads = [Thread(target=self.fpingWorker, args=(queue,outQueue,)) for _ in range(int(len(self.machina) / 2))]
        for thread in threads:
            thread.start()
        results = {}
        while len(self.machina) != count:
            while not outQueue.empty():
                data = outQueue.get()
                if data['parsed']:
                    results[data['server']] = self.getAvrg(data['parsed'])
                else:
                    print(data['ip']+" is not reachable via "+data['server'])
                count += 1
            time.sleep(0.05)
        for thread in threads:
            thread.join()
        results = {k: results[k] for k in sorted(results, key=results.get)}
        print("--- Top 10 ---")
        count = 0
        for server, latency in results.items():
            if count <= 10: print('Got %.2f' %latency,"from",server)
            count = count +1

Latency = Latency()
Latency.debug()
