import sys
import TibcoDaemonInfoScraper
import json


class StdOutReport:    
    def Report(self: any, tibcoDetails: TibcoDaemonInfoScraper.TibcoDaemonServiceInfo):
        data = { 
            'hostname' : tibcoDetails.hostname,
            'ipinterfaces': tibcoDetails.ipinterfaces,
            'services_info': tibcoDetails.services_info
        }

        print(json.dumps(data, ensure_ascii=False, indent=4))

class NagiosStdOutReport:    
    def Report(self: any, tibcoDetails: TibcoDaemonInfoScraper.TibcoDaemonServiceInfo):
        print(tibcoDetails.hostname + '\n' + '<<mi_tibco_service>>')

        print(len(tibcoDetails.services_info), " instances:", end=' ')
        for service_info in tibcoDetails.services_info:            
            print(service_info['headline_info']['service'], end=' ')
        print()        
                
        for service_info in tibcoDetails._services_info:            
            self._print_details(service_info['headline_info'], ['clients', 'hosts', 'subscriptions', 'service'])
            self._print_details(service_info['inbound_paket_stats'], ['pkts', 'missed', 'lost MC', 'lost PTP','suppressed MC', 'bad pkts'])
            self._print_details(service_info['outbound_paket_stats'], ['pkts', 'retrans', 'lost MC', 'lost PTP','shed MC', 'bad retreqs'])

            print()
        pass

    def _print_details(self: any, datadict, items_to_print):        
        for item in items_to_print:
            print(datadict[item], end=' ')        
        
def get_tibco_details(hostname, output_target):

    daemon_scaper = TibcoDaemonInfoScraper.TibcoDaemonInfoScraper(hostname)
    tibcoServicesDetails = daemon_scaper.get_tibco_details()
    
    output_form = {
      'nagios': lambda: NagiosStdOutReport(),
      "stdout": lambda: StdOutReport()
    }
    
    output_form[output_target]().Report(tibcoServicesDetails)
    pass

def main(argv):
    ## TODO move to python command line processing
    if len(argv) < 2:
        print("Usage: webscrape machinename -o [influxdb|stdout]")
    elif len(argv) == 4:
        get_tibco_details(argv[1], argv[3])
    else:
        get_tibco_details(argv[1], 'stdout')

    pass


if __name__ == "__main__":
    main(sys.argv)
