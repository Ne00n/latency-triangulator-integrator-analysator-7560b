import subprocess, json, time, sys, re
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
        parsed = re.findall("([0-9.:a-z]+).*?([0-9]+.[0-9]).*?([0-9])% loss",result, re.MULTILINE)
        return parsed,result,lastByte

    def fpingWorker(self,queue,outQueue):
        while queue.qsize() > 0 :
            data = queue.get()
            parsed,result,lastByte = self.fpingSource(data['server'],data['ip'])
            outQueue.put({"parsed":parsed,"result":result,"lastByte":lastByte,"ip":data['ip'],"server":data['server']})

    def shortIP(self,ip):
        if "." in ip: cut = ip.split(".")
        else: cut = ip.split(":")
        return cut[len(cut) -1]

    def debug(self,ips):
        results = {}
        ips = ips.split(",")
        for ip in ips:
            print("Running fping for",ip)
            count,queue,outQueue = 0,Queue(),Queue()
            for server in self.machina:
                queue.put({"server":server,"ip":ip})
            threads = [Thread(target=self.fpingWorker, args=(queue,outQueue,)) for _ in range(int(len(self.machina) / 2))]
            for thread in threads:
                thread.start()
            while len(self.machina) != count:
                while not outQueue.empty():
                    data = outQueue.get()
                    if data['parsed']:
                        if not ip in results: results[ip] = {}
                        results[ip][data['server']] = self.getAvrg(data['parsed'])
                    else:
                        print(data['ip']+" is not reachable via "+data['server'])
                    count += 1
                time.sleep(0.05)
            for thread in threads:
                thread.join()
            results[ip] = {k: results[ip][k] for k in sorted(results[ip], key=results[ip].get)}
            print("--- Top 35 ---")
            count = 0
            for server, latency in results[ip].items():
                if count <= 35: print('Got %.2f' %latency,"from",server)
                count = count +1

        loc = {}
        for ip,locations in results.items():
            for location,data in locations.items():
                if location not in loc: loc[location] = {}
                loc[location][ip] = data
                loc[location] = {k: v for k, v in sorted(loc[location].items(), key=lambda item: item[1])}

        score,best = {},{}
        print("--- Top Locations ---")
        for location, data in loc.items():
            best[location] = {"latency":0,"diff":0}
            for ip, latency in data.items():
                if ip not in score: score[ip] = 0
                if best[location]['latency'] == 0 or latency < best[location]['latency']:
                    best[location]['latency'],best[location]['ip'] = latency,ip
                if latency > best[location]['latency']:
                    best[location]['diff'] = latency - best[location]['latency']
            score[best[location]['ip']] += 1    
            print(location,f"Diff by {best[location]['diff']:.2f}ms {best[location]['ip']}")
        score = {k: v for k, v in sorted(score.items(), key=lambda item: item[1])}

        print("--- Score ---")
        for ip, points in score.items():
            print(points,ip)

Latency = Latency()
Latency.debug(sys.argv[1])
